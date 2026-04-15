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


def install_platform_assets(
    root_dir: Path,
    project_dir: Path,
    platform: str,
    paths: dict,
    caps: dict,
) -> dict[str, dict[str, str]]:
    """Install docs, snippets, rules, skills, agents, hooks for a platform."""
    files: dict[str, dict[str, str]] = {}

    shared_docs_src = root_dir / "templates/shared/docs"
    for src in sorted(shared_docs_src.glob("*.md")):
        rel = paths["shared_docs_dir"] / src.name
        files[str(rel)] = {
            "mode": "overwrite",
            "checksum": install_copy_file(src, project_dir / rel),
        }

    shared_snippets_src = root_dir / "templates/shared/snippets"
    for src in sorted(shared_snippets_src.glob("*.md")):
        rel = paths["shared_snippets_dir"] / src.name
        files[str(rel)] = {
            "mode": "overwrite",
            "checksum": install_copy_file(src, project_dir / rel),
        }

    if caps[Capability.RULES]:
        rules_src = root_dir / f"templates/{platform}/rules"
        for src in sorted(rules_src.glob("*.md")):
            rel = paths["rules_dir"] / src.name
            files[str(rel)] = {
                "mode": "overwrite",
                "checksum": install_copy_file(src, project_dir / rel),
            }

    if caps[Capability.SKILLS]:
        skills_src = root_dir / f"templates/{platform}/skills"
        for skill_dir in sorted(skills_src.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue
            rel = paths["skills_dir"] / skill_dir.name / "SKILL.md"
            files[str(rel)] = {
                "mode": "overwrite",
                "checksum": install_copy_file(skill_file, project_dir / rel),
            }

    if caps[Capability.AGENTS]:
        agents_src = root_dir / f"templates/{platform}/agents"
        if agents_src.exists():
            for src in sorted(agents_src.glob("*.md")):
                rel = paths["agents_dir"] / src.name
                files[str(rel)] = {
                    "mode": "overwrite",
                    "checksum": install_copy_file(src, project_dir / rel),
                }

    if caps[Capability.HOOKS]:
        hooks_src = root_dir / f"templates/{platform}/hooks"
        for src in sorted(hooks_src.iterdir()):
            if src.is_file():
                rel = paths["hooks_dir"] / src.name
                files[str(rel)] = {
                    "mode": "overwrite",
                    "checksum": install_copy_file(src, project_dir / rel),
                }

    return files
