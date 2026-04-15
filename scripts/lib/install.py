from __future__ import annotations

from pathlib import Path

from lib.checksum import sha256_text
from lib.markers import extract_marker_block, upsert_marker_block

MARKER = "SO2X-HARNESS"


class Capability:
    RULES = "rules"
    SKILLS = "skills"
    AGENTS = "agents"
    HOOKS = "hooks"


SUPPORTED_PLATFORMS = ("claude", "codex")
DEFAULT_PLATFORM = "claude"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def install_marker_file(template_path: Path, target_path: Path, marker: str = MARKER) -> str:
    template_text = template_path.read_text(encoding="utf-8")
    marker_block = extract_marker_block(template_text, marker)
    existing = target_path.read_text(encoding="utf-8") if target_path.exists() else ""
    merged = upsert_marker_block(existing, marker_block, marker)
    write_text(target_path, merged)
    return sha256_text(marker_block)


def install_copy_file(template_path: Path, target_path: Path) -> str:
    content = template_path.read_text(encoding="utf-8")
    write_text(target_path, content)
    return sha256_text(content)


def install_skip_if_exists(template_path: Path, target_path: Path) -> str:
    if target_path.exists():
        return sha256_text(target_path.read_text(encoding="utf-8"))
    return install_copy_file(template_path, target_path)


def keep_existing_file(target_path: Path) -> str:
    return sha256_text(target_path.read_text(encoding="utf-8"))
