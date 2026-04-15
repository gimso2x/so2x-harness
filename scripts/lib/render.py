from __future__ import annotations

from pathlib import Path


def render_template(path: Path, context: dict[str, str]) -> str:
    if not path.exists():
        raise FileNotFoundError(f"template not found: {path}")
    text = path.read_text(encoding="utf-8")
    for key, value in context.items():
        text = text.replace("{{ " + key + " }}", value)
    return text
