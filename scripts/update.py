# ruff: noqa: E402
from __future__ import annotations

import argparse
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
    install_marker_file,
    install_platform_assets,
    keep_existing_file,
    write_text,
)
from lib.manifest import load_manifest, write_manifest
from lib.platform_map import PLATFORM_CAPABILITIES, PROJECT_PATHS
from lib.render import render_template

VERSION = (ROOT_DIR / "VERSION").read_text(encoding="utf-8").strip()


def update_project_config(project_dir: Path, config_path: Path) -> str:
    if not config_path.exists():
        template = ROOT_DIR / "templates/project/.ai-harness/config.json.tmpl"
        rendered = render_template(template, {"project_name": project_dir.name})
        write_text(config_path, rendered)
        return sha256_text(rendered)
    return keep_existing_file(config_path)


def build_updated_manifest(project_dir: Path, old_manifest: dict) -> dict:
    platforms = old_manifest.get("platforms", ["claude"])
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
            files[str(claude_md_path)] = {
                "mode": "marker",
                "marker": MARKER,
                "checksum": install_marker_file(claude_template, project_dir / claude_md_path),
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

        files.update(install_platform_assets(ROOT_DIR, project_dir, platform, paths, caps))

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
            "checksum": update_project_config(project_dir, project_dir / paths["config_path"]),
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
