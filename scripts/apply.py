# ruff: noqa: E402
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
sys.path.insert(0, str(CURRENT_DIR))

from lib.checksum import sha256_text
from lib.install import (
    DEFAULT_PLATFORM,
    MARKER,
    SUPPORTED_PLATFORMS,
    Capability,
    install_copy_file,
    install_marker_file,
    install_skip_if_exists,
    write_text,
)
from lib.manifest import load_manifest, write_manifest
from lib.platform_map import PLATFORM_CAPABILITIES, PROJECT_PATHS
from lib.render import render_template

VERSION = (ROOT_DIR / "VERSION").read_text(encoding="utf-8").strip()


def load_preset(preset_name: str) -> dict:
    preset_path = ROOT_DIR / f"templates/project/.ai-harness/presets/{preset_name}.json"
    if not preset_path.exists():
        raise SystemExit(f"unknown preset: {preset_name} (supported: general)")
    return json.loads(preset_path.read_text(encoding="utf-8"))


def build_extra_fields_json(preset: dict) -> str:
    extras = {
        k: v
        for k, v in preset.items()
        if k
        not in {
            "preset",
            "platforms",
            "language",
            "comment_language",
            "enabled_rules",
            "enabled_skills",
        }
    }
    if not extras:
        return ""
    rendered = ",\n"
    for idx, (key, value) in enumerate(extras.items()):
        rendered += f'  "{key}": ' + json.dumps(value, ensure_ascii=False, indent=2).replace(
            "\n", "\n  "
        )
        if idx < len(extras) - 1:
            rendered += ",\n"
    return rendered


def install_project_config(
    project_dir: Path, project_name: str, config_path: Path, preset_name: str
) -> str:
    template = ROOT_DIR / "templates/project/.ai-harness/config.json.tmpl"
    preset = load_preset(preset_name)
    rendered = render_template(
        template,
        {
            "project_name": project_name,
            "preset": preset_name,
            "enabled_rules_json": json.dumps(preset["enabled_rules"], ensure_ascii=False, indent=2),
            "enabled_skills_json": json.dumps(
                preset["enabled_skills"], ensure_ascii=False, indent=2
            ),
            "extra_fields_json": build_extra_fields_json(preset),
        },
    )
    if not config_path.exists():
        write_text(config_path, rendered)
        return sha256_text(rendered)
    return sha256_text(config_path.read_text(encoding="utf-8"))


def apply_platform(project_dir: Path, platform: str, preset_name: str) -> dict:
    paths = PROJECT_PATHS[platform]
    caps = PLATFORM_CAPABILITIES[platform]
    files: dict[str, dict[str, str]] = {}

    # Platform-specific marker file (CLAUDE.md for claude only)
    claude_md_path = paths.get("claude_md_path")
    if claude_md_path:
        claude_template = ROOT_DIR / "templates/claude/CLAUDE.md"
        claude_target = project_dir / claude_md_path
        files[str(claude_md_path)] = {
            "mode": "marker",
            "marker": MARKER,
            "checksum": install_marker_file(claude_template, claude_target),
        }

    # AGENTS.md
    agents_path = paths["agents_path"]
    agents_target = project_dir / agents_path
    if platform == "codex":
        agents_template = ROOT_DIR / "templates/codex/AGENTS.md"
        files[str(agents_path)] = {
            "mode": "marker",
            "marker": MARKER,
            "checksum": install_marker_file(agents_template, agents_target),
        }
    else:
        agents_template = ROOT_DIR / "templates/shared/AGENTS.md"
        files[str(agents_path)] = {
            "mode": "skip_if_exists",
            "checksum": install_skip_if_exists(agents_template, agents_target),
        }

    # Shared docs
    shared_docs_src = ROOT_DIR / "templates/shared/docs"
    for src in sorted(shared_docs_src.glob("*.md")):
        rel = paths["shared_docs_dir"] / src.name
        files[str(rel)] = {
            "mode": "overwrite",
            "checksum": install_copy_file(src, project_dir / rel),
        }

    # Shared snippets
    shared_snippets_src = ROOT_DIR / "templates/shared/snippets"
    for src in sorted(shared_snippets_src.glob("*.md")):
        rel = paths["shared_snippets_dir"] / src.name
        files[str(rel)] = {
            "mode": "overwrite",
            "checksum": install_copy_file(src, project_dir / rel),
        }

    if caps[Capability.RULES]:
        rules_src = ROOT_DIR / f"templates/{platform}/rules"
        for src in sorted(rules_src.glob("*.md")):
            rel = paths["rules_dir"] / src.name
            files[str(rel)] = {
                "mode": "overwrite",
                "checksum": install_copy_file(src, project_dir / rel),
            }

    if caps[Capability.SKILLS]:
        skills_src = ROOT_DIR / f"templates/{platform}/skills"
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
        agents_src = ROOT_DIR / f"templates/{platform}/agents"
        if agents_src.exists():
            for src in sorted(agents_src.glob("*.md")):
                rel = paths["agents_dir"] / src.name
                files[str(rel)] = {
                    "mode": "overwrite",
                    "checksum": install_copy_file(src, project_dir / rel),
                }

    if caps[Capability.HOOKS]:
        hooks_src = ROOT_DIR / f"templates/{platform}/hooks"
        for src in sorted(hooks_src.iterdir()):
            if src.is_file():
                rel = paths["hooks_dir"] / src.name
                files[str(rel)] = {
                    "mode": "overwrite",
                    "checksum": install_copy_file(src, project_dir / rel),
                }

    # Config
    config_rel = paths["config_path"]
    project_name = project_dir.name
    files[str(config_rel)] = {
        "mode": "skip_if_exists",
        "checksum": install_project_config(
            project_dir, project_name, project_dir / config_rel, preset_name
        ),
    }

    return files


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument(
        "--platform",
        nargs="+",
        default=[DEFAULT_PLATFORM],
        choices=SUPPORTED_PLATFORMS,
    )
    parser.add_argument("--preset", default="general")
    args = parser.parse_args()

    project = Path(args.project).resolve()
    project.mkdir(parents=True, exist_ok=True)

    platforms = list(dict.fromkeys(args.platform))
    all_files: dict[str, dict[str, str]] = {}
    for platform in platforms:
        platform_files = apply_platform(project, platform, args.preset)
        all_files.update(platform_files)

    # Merge with existing manifest platforms (add-only)
    existing_platforms: list[str] = []
    try:
        existing = load_manifest(project)
        existing_platforms = existing.get("platforms", [])
    except Exception:
        pass
    merged_platforms = list(dict.fromkeys(existing_platforms + platforms))

    manifest = {
        "name": "so2x-harness",
        "version": VERSION,
        "platforms": merged_platforms,
        "installed_at": datetime.now(timezone.utc).isoformat(),
        "files": all_files,
    }
    write_manifest(project, manifest)
    print(
        f"[so2x-harness] installed version={manifest['version']} "
        f"platforms={','.join(merged_platforms)} project={project}"
    )
    print(f"[so2x-harness] preset={args.preset}")
    print(f"[so2x-harness] wrote {len(manifest['files'])} managed file entries")


if __name__ == "__main__":
    main()
