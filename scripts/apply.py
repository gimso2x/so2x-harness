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
    install_marker_content,
    install_marker_file,
    install_platform_assets,
    install_skip_if_exists,
    write_text,
)
from lib.manifest import load_manifest, write_manifest
from lib.platform_map import PLATFORM_CAPABILITIES, PROJECT_PATHS
from lib.project_profiles import resolve_preset
from lib.render import render_template

VERSION = (ROOT_DIR / "VERSION").read_text(encoding="utf-8").strip()


def load_preset(preset_name: str) -> dict:
    preset_path = ROOT_DIR / f"templates/project/.ai-harness/presets/{preset_name}.json"
    if not preset_path.exists():
        raise SystemExit(f"unknown preset: {preset_name} (supported: auto, general)")
    return json.loads(preset_path.read_text(encoding="utf-8"))


def sync_config_data(
    existing: dict,
    preset: dict,
    project_name: str,
    preset_name: str,
    platforms: list[str],
) -> dict:
    updated = dict(existing)
    updated["project_name"] = project_name
    updated["preset"] = preset_name
    updated["platforms"] = platforms
    updated["enabled_rules"] = preset["enabled_rules"]
    updated["enabled_skills"] = preset["enabled_skills"]
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
    updated.update(extras)
    return updated


def build_installed_skills_md(enabled_skills: list[str]) -> str:
    lines = "\n".join(f"- {skill}" for skill in enabled_skills)
    return lines + ("\n" if lines else "")


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
    project_dir: Path,
    project_name: str,
    config_path: Path,
    preset_name: str,
    platforms: list[str],
    preset: dict,
) -> str:
    template = ROOT_DIR / "templates/project/.ai-harness/config.json.tmpl"
    enabled_skills = preset["enabled_skills"]
    rendered = render_template(
        template,
        {
            "project_name": project_name,
            "preset": preset_name,
            "platforms_json": json.dumps(platforms, ensure_ascii=False, indent=2),
            "enabled_rules_json": json.dumps(preset["enabled_rules"], ensure_ascii=False, indent=2),
            "enabled_skills_json": json.dumps(enabled_skills, ensure_ascii=False, indent=2),
            "extra_fields_json": build_extra_fields_json(preset),
        },
    )
    if not config_path.exists():
        write_text(config_path, rendered)
        return sha256_text(rendered)

    existing = json.loads(config_path.read_text(encoding="utf-8"))
    updated_data = sync_config_data(existing, preset, project_name, preset_name, platforms)
    updated = json.dumps(updated_data, ensure_ascii=False, indent=2) + "\n"
    write_text(config_path, updated)
    return sha256_text(updated)


def cleanup_stale_skill_dirs(
    project_dir: Path,
    skills_dir: Path,
    enabled_skills: list[str],
) -> None:
    target_dir = project_dir / skills_dir
    if not target_dir.exists():
        return
    enabled = set(enabled_skills)
    for skill_dir in target_dir.iterdir():
        if skill_dir.is_dir() and skill_dir.name not in enabled:
            for child in skill_dir.rglob("*"):
                if child.is_file():
                    child.unlink()
            for child_dir in sorted(
                [p for p in skill_dir.rglob("*") if p.is_dir()],
                key=lambda p: len(p.parts),
                reverse=True,
            ):
                child_dir.rmdir()
            skill_dir.rmdir()


def apply_platform(
    project_dir: Path,
    platform: str,
    preset_name: str,
    config_platforms: list[str],
    preset: dict,
) -> dict:
    paths = PROJECT_PATHS[platform]
    caps = PLATFORM_CAPABILITIES[platform]
    enabled_skills = preset["enabled_skills"]
    files: dict[str, dict[str, str]] = {}

    # Platform-specific marker file (CLAUDE.md for claude only)
    claude_md_path = paths.get("claude_md_path")
    if claude_md_path:
        claude_template = ROOT_DIR / "templates/claude/CLAUDE.md"
        claude_target = project_dir / claude_md_path
        claude_content = render_template(
            claude_template,
            {"installed_skills_md": build_installed_skills_md(enabled_skills)},
        )
        files[str(claude_md_path)] = {
            "mode": "marker",
            "marker": MARKER,
            "checksum": install_marker_content(claude_content, claude_target),
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

    files.update(
        install_platform_assets(
            ROOT_DIR,
            project_dir,
            platform,
            paths,
            caps,
            enabled_skills=enabled_skills,
        )
    )
    if caps["skills"]:
        cleanup_stale_skill_dirs(project_dir, paths["skills_dir"], enabled_skills)

    # Config
    config_rel = paths["config_path"]
    project_name = project_dir.name
    files[str(config_rel)] = {
        "mode": "skip_if_exists",
        "checksum": install_project_config(
            project_dir,
            project_name,
            project_dir / config_rel,
            preset_name,
            config_platforms,
            preset,
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
    enabled_optional_skills: list[str] = []
    config_path = project / ".ai-harness" / "config.json"
    if config_path.exists():
        try:
            existing_config = json.loads(config_path.read_text(encoding="utf-8"))
            existing_optional = existing_config.get("enabled_optional_skills", [])
            if isinstance(existing_optional, list):
                enabled_optional_skills = [str(skill) for skill in existing_optional]
        except json.JSONDecodeError:
            enabled_optional_skills = []
    preset = resolve_preset(
        project,
        args.preset,
        load_preset(args.preset),
        platforms=platforms,
        enabled_optional_skills=enabled_optional_skills,
    )

    # Merge with existing manifest platforms (add-only)
    existing_platforms: list[str] = []
    try:
        existing = load_manifest(project)
        existing_platforms = existing.get("platforms", [])
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    merged_platforms = list(dict.fromkeys(existing_platforms + platforms))

    all_files: dict[str, dict[str, str]] = {}
    for platform in merged_platforms:
        platform_files = apply_platform(project, platform, args.preset, merged_platforms, preset)
        all_files.update(platform_files)

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
    if args.preset == "auto":
        print(
            "[so2x-harness] detected_profiles="
            f"{','.join(preset.get('detected_profiles', [])) or 'none'}"
        )
        print(
            "[so2x-harness] recommended_skills="
            f"{','.join(preset.get('recommended_skills', [])) or 'none'}"
        )
        print(
            "[so2x-harness] optional_skills="
            f"{','.join(preset.get('optional_skills', [])) or 'none'}"
        )
    print(f"[so2x-harness] wrote {len(manifest['files'])} managed file entries")


if __name__ == "__main__":
    main()
