# ruff: noqa: E402
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

CURRENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CURRENT_DIR))

from cli.commands.spec import get_next_task, summarize_spec


def status_line(level: str, label: str, detail: str) -> str:
    return f"[{level}] {label}: {detail}"


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def detect_core_files(project_dir: str | Path) -> dict[str, bool]:
    root = Path(project_dir)
    return {
        "CLAUDE.md": (root / "CLAUDE.md").exists(),
        "spec.json": (root / "spec.json").exists(),
        "harness.json": (root / "harness.json").exists(),
    }


def load_project_state(project_dir: str | Path) -> dict[str, Any] | None:
    return _load_json(Path(project_dir) / "spec.json")


def get_active_problem(spec: dict[str, Any] | None) -> str | None:
    if not spec:
        return None
    summary = summarize_spec(spec)
    if summary.get("blocked_task"):
        return f"blocked on {summary['blocked_task'].get('id')}"
    if summary.get("error_task"):
        return f"error on {summary['error_task'].get('id')}"
    return None


def get_latest_summary(spec: dict[str, Any] | None) -> str:
    if not spec:
        return "none"
    return summarize_spec(spec).get("latest_summary") or "none"


def render_doctor_lines(
    project_dir: str | Path,
    files_ok: dict[str, bool],
    spec: dict[str, Any] | None,
) -> list[str]:
    root = Path(project_dir).resolve()
    lines = [status_line("INFO", "project", str(root))]
    for name in ("CLAUDE.md", "spec.json", "harness.json"):
        lines.append(
            status_line(
                "OK" if files_ok[name] else "WARN",
                name,
                "present" if files_ok[name] else "missing",
            )
        )

    if not spec:
        lines.append(status_line("WARN", "goal", "missing spec.json"))
        lines.append(status_line("WARN", "next_task", "none"))
        lines.append(status_line("WARN", "execution_status", "unknown"))
        lines.append(status_line("WARN", "summary", "none"))
        lines.append(
            status_line(
                "WARN",
                "counts",
                "pending=0 in_progress=0 blocked=0 error=0 done=0",
            )
        )
        return lines

    summary = summarize_spec(spec)
    lines.append(status_line("OK", "goal", summary["goal"] or "none"))
    next_task = get_next_task(spec)
    lines.append(
        status_line(
            "OK" if next_task else "WARN",
            "next_task",
            (
                f"{next_task['id']} "
                f"{next_task.get('role', '')} {next_task.get('action', '')}".strip()
                if next_task
                else "none"
            ),
        )
    )
    active_problem = get_active_problem(spec)
    lines.append(
        status_line(
            "WARN" if active_problem else "OK",
            "execution_status",
            active_problem or "clear",
        )
    )
    lines.append(status_line("OK", "summary", get_latest_summary(spec)))
    counts = summary["counts"]
    lines.append(
        status_line(
            "OK",
            "counts",
            " ".join(
                f"{status}={counts[status]}"
                for status in ("pending", "in_progress", "blocked", "error", "done")
            ),
        )
    )
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only thin harness doctor")
    parser.add_argument("--project", default=".")
    args = parser.parse_args()

    project_dir = Path(args.project).resolve()
    files_ok = detect_core_files(project_dir)
    spec = load_project_state(project_dir)
    for line in render_doctor_lines(project_dir, files_ok, spec):
        print(line)


if __name__ == "__main__":
    main()
