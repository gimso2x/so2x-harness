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


def resolve_meta_harness_state_path(project_dir: str | Path, run_id: str | None = None) -> Path | None:
    root = Path(project_dir) / "outputs"
    if not root.exists():
        return None
    if run_id:
        candidate = root / run_id / "_state.json"
        return candidate if candidate.exists() else None
    candidates = sorted(root.rglob("_state.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def load_meta_harness_state(project_dir: str | Path, run_id: str | None = None) -> dict[str, Any] | None:
    state_path = resolve_meta_harness_state_path(project_dir, run_id=run_id)
    if not state_path:
        return None
    return load_json_file(state_path)
