from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MANIFEST_RELATIVE_PATH = Path(".ai-harness/manifest.json")


def manifest_path(project_dir: Path) -> Path:
    return project_dir / MANIFEST_RELATIVE_PATH


def write_manifest(project_dir: Path, data: dict[str, Any]) -> Path:
    path = manifest_path(project_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def load_manifest(project_dir: Path) -> dict[str, Any]:
    path = manifest_path(project_dir)
    if not path.exists():
        raise FileNotFoundError(f"manifest not found: {path} (run apply.py first)")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SystemExit(f"corrupt manifest: {path} — {e}") from e
