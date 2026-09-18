#!/usr/bin/env python3
"""Run the existing OCR-to-workbench pipeline from one command."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OCR_SCRIPT = Path(__file__).resolve().with_name("ocr_exam.py")
STRUCTURE_SCRIPT = Path(__file__).resolve().with_name("structure_outputs.py")
TAG_SCRIPT = ROOT / "smart-question-tagger" / "scripts" / "tag_structured_bank.py"
SERVER_SCRIPT = ROOT / "smart-question-tagger" / "scripts" / "review_server.py"


def _run(label: str, command: list[str]) -> None:
    print(f"\n== {label} ==", flush=True)
    subprocess.run(command, check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a new question bank from PDF/Word inputs through OCR, structure, tagging, and workbench."
    )
    parser.add_argument("inputs", nargs="+", type=Path, help="Input .pdf, .docx, or .doc files")
    parser.add_argument("--output-prefix", required=True, type=Path, help="Output prefix, e.g. output\\new_exam")
    parser.add_argument("--cache-dir", type=Path, help="MinerU cache directory; defaults to .local/mineru_cache in the project")
    parser.add_argument(
        "--ocr-script",
        type=Path,
        help="OCR script to run; use this to reuse a Cherry Studio exam-ocr Skill",
    )
    parser.add_argument("--tag-threshold", type=float, default=0.8)
    parser.add_argument("--simulate-students", type=int, default=0)
    parser.add_argument("--force", action="store_true", help="Force a new MinerU scan")
    parser.add_argument("--open", action="store_true", dest="open_browser", help="Open the workbench after building")
    return parser.parse_args()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    inputs = [path.resolve() for path in args.inputs]
    missing = [str(path) for path in inputs if not path.is_file()]
    if missing:
        raise SystemExit("Input file not found: " + ", ".join(missing))
    prefix = args.output_prefix.resolve()
    if not prefix.name:
        raise SystemExit("--output-prefix must name an output prefix")
    ocr_dir = prefix.with_name(prefix.name + "_ocr")
    structured_dir = prefix.with_name(prefix.name + "_structured")
    if structured_dir.exists() and any(structured_dir.iterdir()):
        raise SystemExit(f"Structured output already exists and is not empty: {structured_dir}; choose another --output-prefix")
    cache_dir = (args.cache_dir or ROOT / ".local" / "mineru_cache").resolve()
    ocr_script = (args.ocr_script or OCR_SCRIPT).absolute()
    if not ocr_script.is_file():
        raise SystemExit(f"OCR script not found: {ocr_script}")

    ocr_command = [
        sys.executable,
        str(ocr_script),
        *(str(path) for path in inputs),
        "--output-dir",
        str(ocr_dir),
        "--cache-dir",
        str(cache_dir),
    ]
    if args.force:
        ocr_command.append("--force")
    _run("OCR", ocr_command)
    _run("结构化", [sys.executable, str(STRUCTURE_SCRIPT), str(ocr_dir), "--structured-output", str(structured_dir)])

    tag_command = [sys.executable, str(TAG_SCRIPT), str(structured_dir), "--threshold", str(args.tag_threshold)]
    if args.simulate_students:
        tag_command.extend(["--simulate-students", str(args.simulate_students)])
    _run("打标与工作台", tag_command)

    if args.open_browser:
        _run("打开工作台", [sys.executable, str(SERVER_SCRIPT), str(structured_dir), "--open"])
    else:
        print(f"\n工作台已生成：{structured_dir / 'review' / 'index.html'}")
        print("运行 review_server.py --open 或双击一键启动教师工作台.bat 打开。")
    print(json.dumps({"status": "ready", "ocr_dir": str(ocr_dir), "structured_dir": str(structured_dir)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        print(f"\n流程在退出码 {exc.returncode} 处停止。", file=sys.stderr)
        raise SystemExit(exc.returncode or 1) from exc
