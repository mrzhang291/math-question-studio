#!/usr/bin/env python3
"""Serve the teacher workbench locally with autosave and one-click apply APIs."""

from __future__ import annotations

import argparse
from email.parser import BytesParser
from email.policy import default as email_default
import hashlib
import json
import os
import re
import socket
import subprocess
import sys
import threading
import time
import uuid
import webbrowser
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse
from urllib.request import urlopen

from apply_teacher_review import VALID_DECISIONS, apply_review_file, read_decisions


RECOMMENDER_SCRIPTS = (
    Path(__file__).resolve().parents[2]
    / "smart-question-recommender-v3"
    / "scripts"
)
if str(RECOMMENDER_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(RECOMMENDER_SCRIPTS))

from live_personalized_generation import (  # noqa: E402
    GatewayConfigurationError,
    GenerationCancelledError,
    LiveGenerationError,
    cancel_personalized_batch,
    commit_personalized_batch,
    gateway_status,
    generate_personalized_draft,
    generate_personalized_question,
    save_personalized_review,
    verify_personalized_draft,
)


MAX_BODY = 5 * 1024 * 1024
MAX_UPLOAD_BODY = 256 * 1024 * 1024
MAX_OCR_INPUTS = 8
OCR_INPUT_SUFFIXES = {".pdf", ".docx", ".doc"}
PROJECT_ROOT = Path(__file__).resolve().parents[2]
OCR_PIPELINE_SCRIPT = PROJECT_ROOT / "exam-ocr" / "scripts" / "build_ocr_to_workbench.py"
OCR_JOBS: dict[str, dict[str, Any]] = {}
OCR_JOBS_LOCK = threading.Lock()


def _bank_id(bank: Path) -> str:
    return hashlib.sha256(str(bank.resolve()).casefold().encode("utf-8")).hexdigest()[:16]


def _default_port() -> int:
    try:
        value = int(os.environ.get("TEACHER_WORKBENCH_PORT") or "8765")
    except ValueError as exc:
        raise SystemExit("TEACHER_WORKBENCH_PORT must be an integer") from exc
    if not 1 <= value <= 65535:
        raise SystemExit("TEACHER_WORKBENCH_PORT must be between 1 and 65535")
    return value


def _atomic_write_decisions(path: Path, decisions: dict[str, dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        for question_id in sorted(decisions):
            handle.write(json.dumps(decisions[question_id], ensure_ascii=False) + "\n")
    temporary.replace(path)


def _draft_path(bank: Path) -> Path:
    return bank / "review" / "teacher_review_draft.jsonl"


def _load_draft(bank: Path) -> dict[str, dict[str, Any]]:
    path = _draft_path(bank)
    return read_decisions(path) if path.exists() and path.stat().st_size else {}


def _known_question_ids(bank: Path) -> set[str]:
    path = bank / "tags" / "all_question_tags.json"
    rows = json.loads(path.read_text(encoding="utf-8"))
    return {row.get("question_id") for row in rows}


def _find_cherry_ocr_script() -> Path | None:
    configured = os.environ.get("CHERRY_STUDIO_EXAM_OCR_SCRIPT") or os.environ.get("CHERRY_STUDIO_EXAM_OCR_SKILL")
    candidates: list[Path] = []
    if configured:
        configured_path = Path(configured).expanduser()
        candidates.append(
            configured_path / "scripts" / "ocr_exam.py" if configured_path.is_dir() else configured_path
        )
    appdata = os.environ.get("APPDATA")
    if appdata:
        data_root = Path(appdata) / "CherryStudioEnterprise" / "Data"
        preferred_agent = os.environ.get("CHERRY_STUDIO_AGENT_ID") or "nxu31xwlb"
        preferred_path = data_root / "Agents" / preferred_agent / ".claude" / "skills" / "exam-ocr" / "scripts" / "ocr_exam.py"
        if preferred_path.is_file():
            return preferred_path.absolute()
        candidates.extend(sorted(data_root.glob("Agents/*/.claude/skills/exam-ocr/scripts/ocr_exam.py")))
        candidates.append(data_root / "Skills" / "exam-ocr" / "scripts" / "ocr_exam.py")
    for candidate in candidates:
        if candidate.is_file():
            return candidate.absolute()
    return None


def _safe_upload_stem(filename: str) -> str:
    stem = Path(filename.replace("\\", "/")).stem
    stem = re.sub(r"[^\w.\-\u4e00-\u9fff]+", "_", stem, flags=re.UNICODE).strip("._")
    return stem[:80] or "试卷"


def _deduplicate_uploads(files: list[tuple[str, bytes]]) -> list[tuple[str, bytes]]:
    """Keep one format for each same-named upload; PDF is preferred over Word."""
    selected: list[tuple[str, bytes]] = []
    positions: dict[str, int] = {}
    for filename, body in files:
        key = Path(filename).stem.casefold()
        position = positions.get(key)
        if position is None:
            positions[key] = len(selected)
            selected.append((filename, body))
            continue
        current_name = selected[position][0]
        if Path(filename).suffix.casefold() == ".pdf" and Path(current_name).suffix.casefold() != ".pdf":
            selected[position] = (filename, body)
    return selected


def _free_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def _update_ocr_job(job_id: str, **updates: Any) -> dict[str, Any]:
    with OCR_JOBS_LOCK:
        job = OCR_JOBS.get(job_id)
        if job is None:
            return {}
        job.update(updates)
        return dict(job)


def _ocr_job(job_id: str) -> dict[str, Any] | None:
    with OCR_JOBS_LOCK:
        job = OCR_JOBS.get(job_id)
        return dict(job) if job else None


def _ocr_stage_from_line(line: str) -> tuple[str, str] | None:
    if "== OCR ==" in line:
        return "ocr", "正在调用 Cherry Studio exam-ocr Skill 扫描试卷"
    if "== 结构化 ==" in line:
        return "structure", "OCR 完成，正在拆分题目、答案和图片"
    if "== 打标与工作台 ==" in line:
        return "tag", "正在进行知识点标注并生成工作台"
    return None


def _structured_bank_summary(structured_dir: Path) -> dict[str, Any]:
    tags_path = structured_dir / "tags" / "all_question_tags.json"
    if not tags_path.exists():
        return {}
    try:
        rows = json.loads(tags_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(rows, list):
        return {}
    preview: list[dict[str, Any]] = []
    for row in rows[:5]:
        if not isinstance(row, dict):
            continue
        tags = row.get("tags") or {}
        preview.append(
            {
                "display_id": row.get("display_id") or row.get("question_id") or "",
                "question_number": row.get("question_number"),
                "question_type": row.get("question_type") or "",
                "primary_knowledge": tags.get("primary_knowledge") or "",
                "stem_markdown": row.get("stem_markdown") or "",
                "answer": row.get("answer") or "",
                "solution_markdown": row.get("solution_markdown") or "",
            }
        )
    return {
        "question_count": len(rows),
        "review_count": sum(bool((row.get("tags") or {}).get("needs_teacher_review")) for row in rows if isinstance(row, dict)),
        "preview": preview,
    }


def _ocr_failure_message(job_log: Path, result_code: int) -> str:
    try:
        log_text = job_log.read_text(encoding="utf-8", errors="replace")[-12000:]
    except OSError:
        log_text = ""
    if "No top-level exam Markdown files found" in log_text:
        return "OCR 已完成，但没有找到试卷正文；请同时上传试卷和答案/解析文件，不能只上传答案文件。"
    if "Input file not found" in log_text:
        return "上传文件在处理过程中找不到，请重新选择试卷文件后再试。"
    if "HTTP 403" in log_text:
        return "MinerU 拒绝了本次结果查询；请避免同一份文件同时上传 DOCX 和 PDF，只保留一种格式后重试。"
    return f"OCR 流程失败（退出码 {result_code}），请检查上传文件或查看本地日志。"


def _run_ocr_job(
    job_id: str,
    input_paths: list[Path],
    skill_script: Path,
    output_prefix: Path,
    job_log: Path,
) -> None:
    _update_ocr_job(job_id, status="running", stage="ocr", message="正在调用 Cherry Studio exam-ocr Skill 扫描试卷")
    command = [
        sys.executable,
        str(OCR_PIPELINE_SCRIPT),
        *(str(path) for path in input_paths),
        "--output-prefix",
        str(output_prefix),
        "--cache-dir",
        str(PROJECT_ROOT / ".local" / "mineru_cache"),
        "--ocr-script",
        str(skill_script),
    ]
    try:
        job_log.parent.mkdir(parents=True, exist_ok=True)
        with job_log.open("w", encoding="utf-8", newline="\n") as handle:
            process = subprocess.Popen(
                command,
                cwd=str(PROJECT_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
            assert process.stdout is not None
            for line in process.stdout:
                handle.write(line)
                handle.flush()
                progress = _ocr_stage_from_line(line)
                if progress:
                    stage, message = progress
                    _update_ocr_job(job_id, stage=stage, message=message)
            result_code = process.wait()
        if result_code:
            _update_ocr_job(
                job_id,
                status="failed",
                stage="failed",
                message=_ocr_failure_message(job_log, result_code),
                log_path=str(job_log),
            )
            return

        structured_dir = output_prefix.with_name(output_prefix.name + "_structured").resolve()
        if not (structured_dir / "review" / "index.html").exists():
            raise RuntimeError("OCR 流程完成，但结构化工作台没有生成")
        port = _free_loopback_port()
        child = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), str(structured_dir), "--port", str(port)],
            cwd=str(PROJECT_ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        )
        workbench_url = f"http://127.0.0.1:{port}/review/index.html"
        ready = False
        for _ in range(60):
            try:
                with urlopen(f"http://127.0.0.1:{port}/api/health", timeout=1):
                    ready = True
                    break
            except Exception:
                time.sleep(0.25)
        if not ready:
            child.terminate()
            raise RuntimeError("新题库工作台服务未能启动")
        _update_ocr_job(
            job_id,
            status="ready",
            stage="ready",
            message="OCR、结构化、标注和工作台已完成",
            structured_dir=str(structured_dir),
            summary=_structured_bank_summary(structured_dir),
            workbench_url=workbench_url,
            server_pid=child.pid,
            log_path=str(job_log),
        )
    except Exception as exc:
        _update_ocr_job(
            job_id,
            status="failed",
            message=f"OCR 导入失败：{exc}",
            log_path=str(job_log),
        )


class WorkbenchHandler(SimpleHTTPRequestHandler):
    server_version = "TeacherWorkbench/1.0"

    def __init__(self, *args, bank: Path, **kwargs):
        self.bank = bank
        super().__init__(*args, directory=str(bank), **kwargs)

    def log_message(self, format: str, *args) -> None:
        return

    def end_headers(self) -> None:
        route = urlparse(self.path).path
        if not route.startswith("/api/") and (route.endswith(".html") or route.endswith("/review/")):
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        super().end_headers()

    def _json(self, payload: Any, status: int = 200) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            # The browser may have reached its own batch deadline.  The worker
            # still finishes cleanup, but a closed socket must not create a
            # second 500-response path or noisy traceback.
            return

    def _read_json(self) -> Any:
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError as exc:
            raise ValueError("请求长度无效") from exc
        if length < 1 or length > MAX_BODY:
            raise ValueError("请求内容为空或过大")
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def _read_uploads(self) -> list[tuple[str, bytes]]:
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError as exc:
            raise ValueError("上传长度无效") from exc
        if length < 1 or length > MAX_UPLOAD_BODY:
            raise ValueError("上传内容为空或超过 256 MB")
        content_type = self.headers.get("Content-Type") or ""
        if not content_type.lower().startswith("multipart/form-data"):
            raise ValueError("试卷上传必须使用 multipart/form-data")
        message = BytesParser(policy=email_default).parsebytes(
            f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("utf-8")
            + self.rfile.read(length)
        )
        if not message.is_multipart():
            raise ValueError("上传内容格式不正确")
        files: list[tuple[str, bytes]] = []
        for part in message.walk():
            if part.is_multipart() or part.get_content_disposition() != "form-data":
                continue
            filename = part.get_filename()
            if not filename:
                continue
            filename = str(filename).replace("\\", "/").rsplit("/", 1)[-1]
            suffix = Path(filename).suffix.lower()
            if suffix not in OCR_INPUT_SUFFIXES:
                raise ValueError("只支持 PDF、DOCX 或 DOC 试卷文件")
            body = part.get_payload(decode=True) or b""
            if not body:
                raise ValueError(f"上传文件为空：{filename}")
            files.append((filename, body))
        if not files:
            raise ValueError("没有收到试卷文件")
        if len(files) > MAX_OCR_INPUTS:
            raise ValueError(f"一次最多上传 {MAX_OCR_INPUTS} 个试卷或答案文件")
        return files

    def _start_ocr_import(self) -> None:
        skill_script = _find_cherry_ocr_script()
        if skill_script is None:
            raise ValueError("未找到 Cherry Studio exam-ocr Skill，请检查 Cherry Studio 是否已安装该 Skill")
        if not os.environ.get("MINERU_TOKEN"):
            raise ValueError("已找到 exam-ocr Skill，但当前工作台进程未配置 MINERU_TOKEN；请设置后重新启动一键启动脚本")
        raw_files = self._read_uploads()
        files = _deduplicate_uploads(raw_files)
        job_id = uuid.uuid4().hex
        job_root = PROJECT_ROOT / ".local" / "ocr_jobs" / job_id
        input_dir = job_root / "inputs"
        input_dir.mkdir(parents=True, exist_ok=True)
        input_paths: list[Path] = []
        for index, (filename, body) in enumerate(files, start=1):
            safe_filename = f"{index:02d}_{_safe_upload_stem(filename)}{Path(filename).suffix.lower()}"
            path = input_dir / safe_filename
            path.write_bytes(body)
            input_paths.append(path)
        output_prefix = self.bank.parent / f"{_safe_upload_stem(files[0][0])}_{job_id[:8]}"
        job_log = job_root / "pipeline.log"
        with OCR_JOBS_LOCK:
            OCR_JOBS[job_id] = {
                "status": "queued",
                "stage": "queued",
                "message": (
                    f"已接收 {len(raw_files)} 个文件，去重后使用 {len(files)} 个文件；等待调用 Cherry Studio exam-ocr Skill"
                    if len(files) != len(raw_files)
                    else "已接收试卷，等待调用 Cherry Studio exam-ocr Skill"
                ),
                "job_id": job_id,
                "file_names": [filename for filename, _ in files],
                "uploaded_file_count": len(raw_files),
                "deduplicated_file_count": len(files),
                "ocr_engine": "Cherry Studio exam-ocr Skill / MinerU",
            }
        threading.Thread(
            target=_run_ocr_job,
            args=(job_id, input_paths, skill_script, output_prefix, job_log),
            daemon=True,
        ).start()
        self._json({"status": "queued", "job_id": job_id, "message": "已开始 OCR 导入，请等待完成"}, status=202)

    def do_GET(self) -> None:
        route = urlparse(self.path).path
        preview_match = re.fullmatch(r"/questions/([^/]+)/preview\.html", route)
        if preview_match:
            question_id = quote(preview_match.group(1), safe="")
            self.send_response(302)
            self.send_header("Location", f"/review/index.html#preview/{question_id}")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if route == "/api/health":
            self._json({"status": "ok", "bank": self.bank.name, "bank_id": _bank_id(self.bank)})
            return
        if route == "/api/decisions":
            self._json({"decisions": list(_load_draft(self.bank).values())})
            return
        if route == "/api/personalized-generation/status":
            self._json(gateway_status())
            return
        if route.startswith("/api/ocr/jobs/"):
            job_id = route.rsplit("/", 1)[-1]
            job = _ocr_job(job_id)
            if job is None:
                self._json({"error": "OCR 任务不存在或服务已重启"}, status=404)
            else:
                self._json(job)
            return
        if route == "/api/backup":
            path = _draft_path(self.bank)
            body = path.read_bytes() if path.exists() else b""
            filename = f"review_backup_{datetime.now():%Y%m%d}.teacher-review"
            self.send_response(200)
            self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def do_POST(self) -> None:
        route = urlparse(self.path).path
        try:
            if route == "/api/ocr/import":
                self._start_ocr_import()
                return
            if route == "/api/decision":
                self._save_one(self._read_json())
                return
            if route == "/api/decisions":
                payload = self._read_json()
                rows = payload.get("decisions") if isinstance(payload, dict) else payload
                if not isinstance(rows, list):
                    raise ValueError("审核记录格式不正确")
                for row in rows:
                    self._save_one(row, respond=False)
                self._json({"status": "saved", "count": len(rows)})
                return
            if route == "/api/apply":
                self._apply_reviews()
                return
            if route == "/api/personalized-generation/generate":
                self._json(generate_personalized_question(self.bank, self._read_json()))
                return
            if route == "/api/personalized-generation/draft":
                self._json(generate_personalized_draft(self.bank, self._read_json()))
                return
            if route == "/api/personalized-generation/verify":
                self._json(verify_personalized_draft(self.bank, self._read_json()))
                return
            if route == "/api/personalized-generation/cancel":
                self._json(cancel_personalized_batch(self._read_json(), self.bank))
                return
            if route == "/api/personalized-generation/commit":
                self._json(commit_personalized_batch(self.bank, self._read_json()))
                return
            if route == "/api/personalized-generation/review":
                self._json(save_personalized_review(self.bank, self._read_json()))
                return
            if route == "/api/shutdown":
                self._json({"status": "closing"})
                threading.Thread(target=self.server.shutdown, daemon=True).start()
                return
            self._json({"error": "未找到该操作"}, status=404)
        except (ValueError, json.JSONDecodeError) as exc:
            self._json({"error": str(exc)}, status=400)
        except SystemExit as exc:
            self._json({"error": str(exc)}, status=409)
        except LiveGenerationError as exc:
            message = str(exc)
            selection_error = any(
                marker in message
                for marker in (
                    "没有所选题型的安全参考题",
                    "没有找到该知识点对应的安全生题槽位",
                    "没有找到该学生与知识点对应的安全生题槽位",
                    "安全诊断证据只有",
                    "诊断证据数必须",
                    "按学情生成时必须选择学生",
                    "题型参数不正确",
                    "生成方式不正确",
                    "缺少知识点",
                )
            )
            stage = (
                "draft"
                if route.endswith("/draft")
                else "verify"
                if route.endswith("/verify")
                else "generate"
            )
            error_code = (
                "gateway_not_configured"
                if isinstance(exc, GatewayConfigurationError)
                else "generation_cancelled"
                if isinstance(exc, GenerationCancelledError)
                else "gateway_request_failed"
                if exc.status_code == 502
                else "invalid_generation_selection"
                if selection_error
                else "question_rejected"
            )
            self._json(
                {
                    "error": message,
                    "status": "generation_failed",
                    "stage": stage,
                    "error_code": error_code,
                    "retryable": exc.status_code == 502 or (exc.status_code == 422 and not selection_error),
                },
                status=exc.status_code,
            )
        except Exception as exc:
            self._json({"error": f"操作失败：{exc}"}, status=500)

    def _save_one(self, row: dict[str, Any], respond: bool = True) -> None:
        if not isinstance(row, dict):
            raise ValueError("审核记录格式不正确")
        question_id = row.get("question_id")
        if question_id not in _known_question_ids(self.bank):
            raise ValueError("题目不存在或已更新，请刷新页面")
        decisions = _load_draft(self.bank)
        if row.get("decision") == "clear":
            decisions.pop(question_id, None)
        else:
            if row.get("decision") not in VALID_DECISIONS:
                raise ValueError("请选择通过、修改或暂缓")
            decisions[question_id] = row
        _atomic_write_decisions(_draft_path(self.bank), decisions)
        if respond:
            self._json({"status": "saved", "question_id": question_id, "count": len(decisions)})

    def _apply_reviews(self) -> None:
        path = _draft_path(self.bank)
        decisions = _load_draft(self.bank)
        actionable = {key: value for key, value in decisions.items() if value.get("decision") in {"approve", "change"}}
        if not actionable:
            raise ValueError("还没有可应用的审核结果")
        apply_path = path.with_name("teacher_review_apply_pending.jsonl")
        _atomic_write_decisions(apply_path, decisions)
        try:
            result = apply_review_file(self.bank, apply_path)
        finally:
            if apply_path.exists():
                apply_path.unlink()
        deferred = {key: value for key, value in decisions.items() if value.get("decision") == "defer"}
        _atomic_write_decisions(path, deferred)
        self._json(
            {
                "status": "applied",
                "applied": result.get("applied", 0),
                "deferred": len(deferred),
                "remaining_queue": (result.get("outputs") or {}).get("review_queue"),
            }
        )


def serve(bank: Path, host: str = "127.0.0.1", port: int = 8765, open_browser: bool = False) -> int:
    bank = bank.resolve()
    if not (bank / "review" / "index.html").exists():
        raise SystemExit("教师工作台尚未生成，请先运行打标流程。")

    def handler(*args, **kwargs):
        return WorkbenchHandler(*args, bank=bank, **kwargs)

    requested_url = f"http://{host}:{port}/review/index.html"
    try:
        server = ThreadingHTTPServer((host, port), handler)
    except OSError:
        try:
            with urlopen(f"http://{host}:{port}/api/health", timeout=1) as response:
                health = json.loads(response.read().decode("utf-8"))
        except Exception:
            health = None
        if health and health.get("bank_id") == _bank_id(bank):
            if open_browser:
                webbrowser.open(requested_url)
            return 0
        fallback_port = _free_loopback_port()
        try:
            server = ThreadingHTTPServer((host, fallback_port), handler)
        except OSError as fallback_exc:
            raise SystemExit("教师工作台启动失败，请稍后重试。") from fallback_exc
        print(f"端口 {port} 已被占用，已为题库 {bank.name} 切换到端口 {fallback_port}。")
    url = f"http://{host}:{server.server_port}/review/index.html"
    print(f"教师工作台：{url}")
    if open_browser:
        threading.Timer(0.35, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Start the local teacher workbench.")
    parser.add_argument("structured_dir", type=Path)
    parser.add_argument("--host", default=os.environ.get("TEACHER_WORKBENCH_HOST") or "127.0.0.1")
    parser.add_argument("--port", type=int, default=_default_port())
    parser.add_argument("--open", action="store_true", dest="open_browser")
    args = parser.parse_args()
    if args.host not in {"127.0.0.1", "localhost"}:
        raise SystemExit("For safety, the teacher workbench only binds to this computer.")
    return serve(args.structured_dir, args.host, args.port, args.open_browser)


if __name__ == "__main__":
    raise SystemExit(main())
