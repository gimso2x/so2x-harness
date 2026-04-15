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
    MARKER,
    Capability,
    install_copy_file,
    install_marker_content,
    install_marker_file,
    install_platform_assets,
    keep_existing_file,
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


def update_project_config(
    project_dir: Path,
    config_path: Path,
    preset_name: str,
    platforms: list[str],
) -> str:
    template = ROOT_DIR / "templates/project/.ai-harness/config.json.tmpl"
    preset = load_preset(preset_name)
    enabled_skills = preset["enabled_skills"]
    rendered = render_template(
        template,
        {
            "project_name": project_dir.name,
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
    updated_data = sync_config_data(existing, preset, project_dir.name, preset_name, platforms)
    updated = json.dumps(updated_data, ensure_ascii=False, indent=2) + "\n"
    write_text(config_path, updated)
    return sha256_text(updated)


def cleanup_stale_skill_dirs(project_dir: Path, skills_dir: Path, enabled_skills: list[str]) -> None:
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
                [p for p in skill_dir.rglob("*") if p.is_dir()], key=lambda p: len(p.parts), reverse=True
            ):
                child_dir.rmdir()
            skill_dir.rmdir()


def build_updated_manifest(project_dir: Path, old_manifest: dict) -> dict:
    platforms = old_manifest.get("platforms", ["claude"])
    preset_name = "general"
    preset = load_preset(preset_name)
    enabled_skills = preset["enabled_skills"]
    all_files: dict[str, dict[str, str]] = {}

    for platform in platforms:
        if platform not in PROJECT_PATHS:
            continue
        paths = PROJECT_PATHS[platform]
        caps = PLATFORM_CAPABILITIES[platform]
        files: dict[str, dict[str, str]] = {}

        # CLAUDE.md (claude only)
        claude_md_path = paths.get("claude_md_path")
        if claude_md_path:
            claude_template = ROOT_DIR / "templates/claude/CLAUDE.md"
            claude_content = render_template(
                claude_template,
                {"installed_skills_md": build_installed_skills_md(enabled_skills)},
            )
            files[str(claude_md_path)] = {
                "mode": "marker",
                "marker": MARKER,
                "checksum": install_marker_content(claude_content, project_dir / claude_md_path),
            }

        # AGENTS.md
        agents_path = paths["agents_path"]
        agents_target = project_dir / agents_path
        if platform == "codex":
            agents_template = ROOT_DIR / "templates/codex/AGENTS.md"
            if agents_target.exists():
                checksum = install_marker_file(agents_template, agents_target)
            else:
                checksum = install_copy_file(agents_template, agents_target)
            files[str(agents_path)] = {"mode": "marker", "checksum": checksum}
        else:
            agents_template = ROOT_DIR / "templates/shared/AGENTS.md"
            if not agents_target.exists():
                checksum = install_copy_file(agents_template, agents_target)
            else:
                checksum = keep_existing_file(agents_target)
            files[str(agents_path)] = {"mode": "skip_if_exists", "checksum": checksum}

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
        if caps[Capability.SKILLS]:
            cleanup_stale_skill_dirs(project_dir, paths["skills_dir"], enabled_skills)

        # Clean old flat-format skills (claude only)
        if caps.get(Capability.SKILLS) and platform == "claude":
            old_flat_dir = project_dir / paths["skills_dir"]
            if old_flat_dir.exists():
                for old_file in old_flat_dir.glob("*.md"):
                    old_file.unlink()
                    print(f"[so2x-harness] removed old-format skill: {old_file.name}")

        # Config
        config_rel = str(paths["config_path"])
        files[config_rel] = {
            "mode": "skip_if_exists",
            "checksum": update_project_config(
                project_dir,
                project_dir / paths["config_path"],
                preset_name,
                platforms,
            ),
        }

        all_files.update(files)

    return {
        "name": "so2x-harness",
        "version": VERSION,
        "platforms": platforms,
        "installed_at": old_manifest.get("installed_at", datetime.now(timezone.utc).isoformat()),
        "files": all_files,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    args = parser.parse_args()

    project = Path(args.project).resolve()
    old_manifest = load_manifest(project)

    new_manifest = build_updated_manifest(project, old_manifest)
    write_manifest(project, new_manifest)
    old_version = old_manifest.get("version", "unknown")
    new_version = new_manifest["version"]
    platforms = ",".join(new_manifest["platforms"])
    print(
        "[so2x-harness] updated version "
        f"{old_version} -> {new_version} "
        f"platforms={platforms} project={project}"
    )
    print(f"[so2x-harness] wrote {len(new_manifest['files'])} managed file entries")


if __name__ == "__main__":
    main()
