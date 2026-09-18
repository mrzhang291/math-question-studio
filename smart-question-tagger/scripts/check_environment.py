#!/usr/bin/env python3
"""Run a read-only preflight check for the local teacher workbench."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any


RECOMMENDER_SCRIPTS = Path(__file__).resolve().parents[2] / "smart-question-recommender-v3" / "scripts"
if str(RECOMMENDER_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(RECOMMENDER_SCRIPTS))

try:
    from live_personalized_generation import gateway_status
    from review_server import _find_cherry_ocr_script
except Exception as exc:  # The workbench remains usable when live generation is unavailable.
    gateway_status = None
    _find_cherry_ocr_script = None
    GATEWAY_IMPORT_ERROR = str(exc)
else:
    GATEWAY_IMPORT_ERROR = ""


REQUIRED_MODULES = {"markdown": "markdown", "bs4": "beautifulsoup4"}
OPTIONAL_MODULES = {
    "latex2mathml": "latex2mathml",
    "docx": "python-docx",
    "docx2pdf": "docx2pdf",
    "openpyxl": "openpyxl",
    "pytest": "pytest",
}
REQUIRED_ARTIFACTS = (Path("tags/all_question_tags.json"), Path("review/index.html"))
RECOMMENDED_ARTIFACTS = (
    Path("manifest.json"),
    Path("structure_report.json"),
    Path("tagging_summary.json"),
    Path("audit/tag_quality_audit.csv"),
)


def _check(check_id: str, title: str, status: str, message: str, **details: Any) -> dict[str, Any]:
    return {"id": check_id, "title": title, "status": status, "message": message, **details}


def check_python() -> dict[str, Any]:
    version = ".".join(str(part) for part in sys.version_info[:3])
    if sys.version_info < (3, 11):
        return _check("python", "Python", "fail", f"需要 Python 3.11+，当前为 {version}", version=version)
    return _check("python", "Python", "pass", f"{version}，满足要求", version=version)


def check_dependencies() -> list[dict[str, Any]]:
    checks = []
    missing_required = [name for name in REQUIRED_MODULES if importlib.util.find_spec(name) is None]
    if missing_required:
        checks.append(
            _check(
                "dependencies",
                "必需依赖",
                "fail",
                "缺少：" + ", ".join(f"{name}（{REQUIRED_MODULES[name]}）" for name in missing_required),
            )
        )
    else:
        checks.append(_check("dependencies", "必需依赖", "pass", "Markdown/HTML 处理依赖已安装"))

    missing_optional = [name for name in OPTIONAL_MODULES if importlib.util.find_spec(name) is None]
    if missing_optional:
        checks.append(
            _check(
                "optional-dependencies",
                "可选依赖",
                "warn",
                "未安装：" + ", ".join(f"{name}（{OPTIONAL_MODULES[name]}）" for name in missing_optional),
            )
        )
    else:
        checks.append(_check("optional-dependencies", "可选依赖", "pass", "文档、Excel 和测试依赖已安装"))
    return checks


def check_bank(bank: Path) -> dict[str, Any]:
    if not bank.is_dir():
        return _check("bank", "题库产物", "fail", f"题库目录不存在：{bank}")

    missing_required = [str(path) for path in REQUIRED_ARTIFACTS if not (bank / path).exists()]
    if missing_required:
        return _check("bank", "题库产物", "fail", "缺少：" + ", ".join(missing_required), bank=str(bank))

    tags_path = bank / "tags" / "all_question_tags.json"
    try:
        rows = json.loads(tags_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return _check("bank", "题库产物", "fail", f"标签文件无法读取：{exc}", bank=str(bank))
    if not isinstance(rows, list):
        return _check("bank", "题库产物", "fail", "all_question_tags.json 不是 JSON 数组", bank=str(bank))

    missing_recommended = [str(path) for path in RECOMMENDED_ARTIFACTS if not (bank / path).exists()]
    status = "warn" if missing_recommended else "pass"
    message = f"{len(rows)} 道题，工作台入口有效"
    if missing_recommended:
        message += "；建议补齐：" + ", ".join(missing_recommended)
    return _check(
        "bank",
        "题库产物",
        status,
        message,
        bank=str(bank),
        question_count=len(rows),
        missing_recommended=missing_recommended,
    )


def check_gateway() -> dict[str, Any]:
    if gateway_status is None:
        return _check("cherry-studio", "Cherry Studio", "warn", f"实时生题状态无法检测：{GATEWAY_IMPORT_ERROR}")
    try:
        status = gateway_status()
    except Exception as exc:  # A local workbench should still start when the optional gateway check fails.
        return _check("cherry-studio", "Cherry Studio", "warn", f"状态检测失败：{exc}")
    if status.get("configured") and status.get("reachable") and status.get("authenticated") and status.get("model_available", True):
        return _check("cherry-studio", "Cherry Studio", "pass", status.get("message") or "已连接", model=status.get("model", ""))
    return _check("cherry-studio", "Cherry Studio", "warn", status.get("message") or "未配置或暂不可用", model=status.get("model", ""))


def check_ocr_skill() -> dict[str, Any]:
    if _find_cherry_ocr_script is None:
        return _check("cherry-ocr-skill", "Cherry Studio OCR Skill", "warn", "OCR Skill 状态无法检测")
    script = _find_cherry_ocr_script()
    if script is None:
        return _check("cherry-ocr-skill", "Cherry Studio OCR Skill", "warn", "未找到 exam-ocr Skill")
    if not os.environ.get("MINERU_TOKEN"):
        return _check(
            "cherry-ocr-skill",
            "Cherry Studio OCR Skill",
            "warn",
            "已找到 exam-ocr Skill，但当前工作台进程未发现 MINERU_TOKEN",
            script=str(script),
        )
    return _check(
        "cherry-ocr-skill",
        "Cherry Studio OCR Skill",
        "pass",
        "exam-ocr Skill / MinerU 已就绪",
        script=str(script),
    )


def run_checks(bank: Path) -> dict[str, Any]:
    checks = [check_python(), *check_dependencies(), check_bank(bank), check_gateway(), check_ocr_skill()]
    status = "fail" if any(item["status"] == "fail" for item in checks) else "warn" if any(item["status"] == "warn" for item in checks) else "pass"
    return {"status": status, "bank": str(bank), "checks": checks}


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Read-only environment check for the teacher workbench.")
    parser.add_argument("structured_dir", type=Path, help="Prepared structured question bank")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Print machine-readable JSON")
    args = parser.parse_args()
    result = run_checks(args.structured_dir.resolve())
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        labels = {"pass": "通过", "warn": "警告", "fail": "失败"}
        for item in result["checks"]:
            print(f"[{labels[item['status']]}] {item['title']}：{item['message']}")
        print(f"\n自检结果：{labels[result['status']]}")
    return 1 if result["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
