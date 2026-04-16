from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json_file(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def load_active_run_id(project_dir: str | Path) -> str | None:
    harness_path = Path(project_dir) / "harness.json"
    harness = load_json_file(harness_path)
    if not harness:
        return None
    active_run_id = harness.get("active_run_id")
    return str(active_run_id) if active_run_id else None


def set_active_run_id(project_dir: str | Path, run_id: str) -> Path:
    harness_path = Path(project_dir) / "harness.json"
    harness = load_json_file(harness_path) or {}
    harness["active_run_id"] = run_id
    harness_path.write_text(json.dumps(harness, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return harness_path


def resolve_meta_harness_state_path(project_dir: str | Path, run_id: str | None = None) -> Path | None:
    root = Path(project_dir) / "outputs"
    if not root.exists():
        return None
    selected_run_id = run_id or load_active_run_id(project_dir)
    if selected_run_id:
        candidate = root / selected_run_id / "_state.json"
        if candidate.exists():
            return candidate
        if run_id:
            return None
    candidates = sorted(root.rglob("_state.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def load_meta_harness_state(project_dir: str | Path, run_id: str | None = None) -> dict[str, Any] | None:
    state_path = resolve_meta_harness_state_path(project_dir, run_id=run_id)
    if not state_path:
        return None
    return load_json_file(state_path)
