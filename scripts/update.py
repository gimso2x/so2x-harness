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

            # Clean old flat-format skills (claude only)
            if platform == "claude":
                skills_installed = paths["skills_dir"]
                old_flat_dir = project_dir / skills_installed
                if old_flat_dir.exists():
                    for old_file in old_flat_dir.glob("*.md"):
                        old_file.unlink()
                        print(f"[so2x-harness] removed old-format skill: {old_file.name}")

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
    print(f"[so2x-harness] updated version {old_version} -> {new_version} platforms={platforms} project={project}")
    print(f"[so2x-harness] wrote {len(new_manifest['files'])} managed file entries")


if __name__ == "__main__":
    main()
