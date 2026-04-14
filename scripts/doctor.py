# ruff: noqa: E402
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
sys.path.insert(0, str(CURRENT_DIR))

from lib.manifest import manifest_path
from lib.platform_map import PROJECT_PATHS


def status_line(level: str, label: str, detail: str) -> str:
    return f"[{level}] {label}: {detail}"


def detect_python() -> tuple[str, str]:
    python_path = shutil.which("python3") or shutil.which("python")
    if python_path:
        return ("OK", python_path)
    return ("ERROR", "python3/python not found in PATH")


def _load_spec(project_dir: Path) -> dict | None:
    spec_file = project_dir / "spec.json"
    if not spec_file.exists():
        return None
    try:
        return json.loads(spec_file.read_text(encoding="utf-8"))
    except Exception:
        return None


def _execution_items(project_dir: Path) -> list[tuple[str, str, str]]:
    spec = _load_spec(project_dir)
    if not spec:
        return []

    tasks = spec.get("chain", {}).get("l4_tasks", [])
    if not tasks:
        return [("WARN", "execution_status", "spec.json present but no l4_tasks found")]

    blocked = [task for task in tasks if task.get("status") == "blocked"]
    in_progress = [task for task in tasks if task.get("status") == "in_progress"]
    pending = [task for task in tasks if task.get("status") == "pending"]

    if blocked:
        current = blocked[0]
        task_id = current.get("id", "?")
        summary = current.get("summary", "blocked without summary")
        items = [
            ("WARN", "execution_status", f"blocked on task {task_id}"),
            ("WARN", "execution_summary", f"latest summary: {summary}"),
        ]
    elif in_progress:
        current = in_progress[0]
        task_id = current.get("id", "?")
        summary = current.get("summary", "in progress")
        items = [
            ("OK", "execution_status", f"in progress on task {task_id}"),
            ("OK", "execution_summary", f"latest summary: {summary}"),
        ]
    else:
        items = [("OK", "execution_status", "no active blocked or in_progress tasks")]

    items.append(("OK", "pending_tasks", f"{len(pending)} task(s) still pending"))
    return items


def check_project(project_dir: Path) -> list[tuple[str, str, str]]:
    items: list[tuple[str, str, str]] = []

    if project_dir.exists() and project_dir.is_dir():
        items.append(("OK", "project_dir", str(project_dir)))
    else:
        items.append(("ERROR", "project_dir", f"directory not found: {project_dir}"))
        return items

    paths = PROJECT_PATHS["claude"]

    package_json = project_dir / "package.json"
    if package_json.exists():
        items.append(("OK", "project_signal", "package.json found"))
    else:
        items.append(("WARN", "project_signal", "package.json not found — generic project mode"))

    claude_md = project_dir / paths["claude_md_path"]
    if claude_md.exists():
        items.append(("OK", "claude_md", "CLAUDE.md exists"))
    else:
        items.append(("WARN", "claude_md", "CLAUDE.md not found yet"))

    agents_md = project_dir / paths["agents_path"]
    if agents_md.exists():
        items.append(("OK", "agents_md", "AGENTS.md exists"))
    else:
        items.append(("WARN", "agents_md", "AGENTS.md not found yet"))

    manifest = manifest_path(project_dir)
    if manifest.exists():
        items.append(("OK", "manifest", str(manifest)))
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
            items.append(("OK", "manifest_version", str(data.get("version", "unknown"))))
            items.append(("OK", "manifest_files", str(len(data.get("files", {})))))
        except Exception as exc:
            items.append(("ERROR", "manifest_parse", f"failed to parse manifest: {exc}"))
    else:
        items.append(("WARN", "manifest", "manifest not found — harness may not be installed"))

    config_path = project_dir / paths["config_path"]
    if config_path.exists():
        items.append(("OK", "config", str(config_path)))
        try:
            config_data = json.loads(config_path.read_text(encoding="utf-8"))
            items.append(("OK", "config_preset", str(config_data.get("preset", "unknown"))))
        except Exception as exc:
            items.append(("ERROR", "config_parse", f"failed to parse config: {exc}"))
    else:
        items.append(
            (
                "WARN",
                "config",
                "config not found — project-specific harness config missing",
            )
        )

    rules_dir = project_dir / paths["rules_dir"]
    if rules_dir.exists():
        count = len(list(rules_dir.glob("*.md")))
        items.append(("OK", "rules_dir", f"{rules_dir} ({count} files)"))
    else:
        items.append(("WARN", "rules_dir", f"missing: {rules_dir}"))

    skills_dir = project_dir / paths["skills_dir"]
    if skills_dir.exists():
        count = len(list(skills_dir.glob("*/SKILL.md")))
        items.append(("OK", "skills_dir", f"{skills_dir} ({count} skills)"))
    else:
        items.append(("WARN", "skills_dir", f"missing: {skills_dir}"))

    hooks_dir = project_dir / paths["hooks_dir"]
    if hooks_dir.exists():
        count = len([p for p in hooks_dir.iterdir() if p.is_file()])
        items.append(("OK", "hooks_dir", f"{hooks_dir} ({count} files)"))
    else:
        items.append(("WARN", "hooks_dir", f"missing: {hooks_dir}"))

    items.extend(_execution_items(project_dir))

    return items


def summarize(items: list[tuple[str, str, str]]) -> str:
    errors = sum(1 for level, _, _ in items if level == "ERROR")
    warns = sum(1 for level, _, _ in items if level == "WARN")
    oks = sum(1 for level, _, _ in items if level == "OK")
    if errors:
        health = "ERROR"
    elif warns:
        health = "WARN"
    else:
        health = "OK"
    return f"[{health}] summary: ok={oks} warn={warns} error={errors}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=".")
    args = parser.parse_args()

    project_dir = Path(args.project).resolve()
    print(f"[INFO] so2x-harness doctor: project={project_dir}")

    py_level, py_detail = detect_python()
    print(status_line(py_level, "python", py_detail))

    items = check_project(project_dir)
    for level, label, detail in items:
        print(status_line(level, label, detail))

    print(summarize([(py_level, "python", py_detail), *items]))


if __name__ == "__main__":
    main()
