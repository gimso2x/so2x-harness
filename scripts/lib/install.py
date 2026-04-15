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


def install_marker_content(content: str, target_path: Path, marker: str = MARKER) -> str:
    marker_block = extract_marker_block(content, marker)
    existing = target_path.read_text(encoding="utf-8") if target_path.exists() else ""
    merged = upsert_marker_block(existing, marker_block, marker)
    write_text(target_path, merged)
    return sha256_text(marker_block)


def install_marker_file(template_path: Path, target_path: Path, marker: str = MARKER) -> str:
    template_text = template_path.read_text(encoding="utf-8")
    return install_marker_content(template_text, target_path, marker)


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


def _install_glob_files(
    src_dir: Path,
    rel_dir: Path,
    project_dir: Path,
) -> dict[str, dict[str, str]]:
    if not src_dir.exists():
        return {}
    files: dict[str, dict[str, str]] = {}
    for src in sorted(src_dir.glob("*.md")):
        rel = rel_dir / src.name
        files[str(rel)] = {
            "mode": "overwrite",
            "checksum": install_copy_file(src, project_dir / rel),
        }
    return files


def install_platform_assets(
    root_dir: Path,
    project_dir: Path,
    platform: str,
    paths: dict,
    caps: dict,
    enabled_skills: list[str] | None = None,
) -> dict[str, dict[str, str]]:
    """Install docs, snippets, rules, skills, agents, hooks for a platform."""
    files: dict[str, dict[str, str]] = {}

    files.update(
        _install_glob_files(
            root_dir / "templates/shared/docs",
            paths["shared_docs_dir"],
            project_dir,
        )
    )
    files.update(
        _install_glob_files(
            root_dir / "templates/shared/snippets",
            paths["shared_snippets_dir"],
            project_dir,
        )
    )

    if caps[Capability.RULES]:
        files.update(
            _install_glob_files(
                root_dir / f"templates/{platform}/rules",
                paths["rules_dir"],
                project_dir,
            )
        )

    if caps[Capability.SKILLS]:
        skills_src = root_dir / f"templates/{platform}/skills"
        enabled = set(enabled_skills or [])
        for skill_dir in sorted(skills_src.iterdir()):
            if not skill_dir.is_dir():
                continue
            if enabled and skill_dir.name not in enabled:
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
        files.update(
            _install_glob_files(
                root_dir / f"templates/{platform}/agents",
                paths["agents_dir"],
                project_dir,
            )
        )

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
