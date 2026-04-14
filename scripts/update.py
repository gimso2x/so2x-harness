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
from lib.manifest import load_manifest, write_manifest
from lib.markers import extract_marker_block, upsert_marker_block
from lib.platform_map import PROJECT_PATHS
from lib.render import render_template

MARKER = "SO2X-HARNESS"
VERSION = (ROOT_DIR / "VERSION").read_text(encoding="utf-8").strip()


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def install_marker_file(template_path: Path, target_path: Path) -> str:
    template_text = template_path.read_text(encoding="utf-8")
    marker_block = extract_marker_block(template_text, MARKER)
    existing = target_path.read_text(encoding="utf-8") if target_path.exists() else ""
    merged = upsert_marker_block(existing, marker_block, MARKER)
    write_text(target_path, merged)
    return sha256_text(marker_block)


def install_copy_file(template_path: Path, target_path: Path) -> str:
    content = template_path.read_text(encoding="utf-8")
    write_text(target_path, content)
    return sha256_text(content)


def keep_existing_file(target_path: Path) -> str:
    return sha256_text(target_path.read_text(encoding="utf-8"))


def update_project_config(project_dir: Path, config_path: Path) -> str:
    if not config_path.exists():
        template = ROOT_DIR / "templates/project/.ai-harness/config.json.tmpl"
        rendered = render_template(template, {"project_name": project_dir.name})
        write_text(config_path, rendered)
    return keep_existing_file(config_path)


def build_updated_manifest(project_dir: Path) -> dict:
    paths = PROJECT_PATHS["claude"]
    files: dict[str, dict[str, str]] = {}

    claude_template = ROOT_DIR / "templates/claude/CLAUDE.md"
    claude_rel = str(paths["claude_md_path"])
    claude_target = project_dir / paths["claude_md_path"]
    files[claude_rel] = {
        "mode": "marker",
        "marker": MARKER,
        "checksum": install_marker_file(claude_template, claude_target),
    }

    agents_template = ROOT_DIR / "templates/shared/AGENTS.md"
    agents_rel = str(paths["agents_path"])
    agents_target = project_dir / paths["agents_path"]
    if not agents_target.exists():
        checksum = install_copy_file(agents_template, agents_target)
    else:
        checksum = keep_existing_file(agents_target)
    files[agents_rel] = {"mode": "skip_if_exists", "checksum": checksum}

    shared_docs_src = ROOT_DIR / "templates/shared/docs"
    for src in sorted(shared_docs_src.glob("*.md")):
        rel = paths["shared_docs_dir"] / src.name
        files[str(rel)] = {
            "mode": "overwrite",
            "checksum": install_copy_file(src, project_dir / rel),
        }

    shared_snippets_src = ROOT_DIR / "templates/shared/snippets"
    for src in sorted(shared_snippets_src.glob("*.md")):
        rel = paths["shared_snippets_dir"] / src.name
        files[str(rel)] = {
            "mode": "overwrite",
            "checksum": install_copy_file(src, project_dir / rel),
        }

    rules_src = ROOT_DIR / "templates/claude/rules"
    for src in sorted(rules_src.glob("*.md")):
        rel = paths["rules_dir"] / src.name
        files[str(rel)] = {
            "mode": "overwrite",
            "checksum": install_copy_file(src, project_dir / rel),
        }

    skills_src = ROOT_DIR / "templates/claude/skills"
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

    # 이전 플랫 포맷(.claude/skills/so2x-harness/*.md) 정리
    skills_installed = paths["skills_dir"]
    old_flat_dir = project_dir / skills_installed
    if old_flat_dir.exists():
        for old_file in old_flat_dir.glob("*.md"):
            old_file.unlink()
            print(f"[so2x-harness] removed old-format skill: {old_file.name}")

    agents_src = ROOT_DIR / "templates/claude/agents"
    if agents_src.exists():
        for src in sorted(agents_src.glob("*.md")):
            rel = paths["agents_dir"] / src.name
            files[str(rel)] = {
                "mode": "overwrite",
                "checksum": install_copy_file(src, project_dir / rel),
            }

    hooks_src = ROOT_DIR / "templates/claude/hooks"
    for src in sorted(hooks_src.iterdir()):
        if src.is_file():
            rel = paths["hooks_dir"] / src.name
            files[str(rel)] = {
                "mode": "overwrite",
                "checksum": install_copy_file(src, project_dir / rel),
            }

    plugin_src = ROOT_DIR / "templates/claude/plugin"
    for src in sorted(plugin_src.iterdir()):
        if src.is_file():
            rel = paths["plugin_dir"] / src.name
            files[str(rel)] = {
                "mode": "overwrite",
                "checksum": install_copy_file(src, project_dir / rel),
            }

    config_rel = str(paths["config_path"])
    files[config_rel] = {
        "mode": "skip_if_exists",
        "checksum": update_project_config(project_dir, project_dir / paths["config_path"]),
    }

    return {
        "name": "so2x-harness",
        "version": VERSION,
        "platforms": ["claude"],
        "installed_at": datetime.now(timezone.utc).isoformat(),
        "files": files,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    args = parser.parse_args()

    project = Path(args.project).resolve()
    old_manifest = load_manifest(project)
    if "claude" not in old_manifest.get("platforms", []):
        raise SystemExit("only claude manifest is supported in v0.1")

    new_manifest = build_updated_manifest(project)
    write_manifest(project, new_manifest)
    old_version = old_manifest.get("version", "unknown")
    new_version = new_manifest["version"]
    print(f"[so2x-harness] updated version {old_version} -> {new_version} project={project}")
    print(f"[so2x-harness] wrote {len(new_manifest['files'])} managed file entries")


if __name__ == "__main__":
    main()
