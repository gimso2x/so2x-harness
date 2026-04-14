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
from lib.manifest import write_manifest
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


def install_skip_if_exists(template_path: Path, target_path: Path) -> str:
    if target_path.exists():
        return sha256_text(target_path.read_text(encoding="utf-8"))
    return install_copy_file(template_path, target_path)


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
        else:
            rendered += ""
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
    return sha256_text(config_path.read_text(encoding="utf-8"))


def apply_claude(project_dir: Path, preset_name: str) -> dict:
    paths = PROJECT_PATHS["claude"]
    files: dict[str, dict[str, str]] = {}

    claude_template = ROOT_DIR / "templates/claude/CLAUDE.md"
    claude_target = project_dir / paths["claude_md_path"]
    files[str(paths["claude_md_path"])] = {
        "mode": "marker",
        "marker": MARKER,
        "checksum": install_marker_file(claude_template, claude_target),
    }

    agents_template = ROOT_DIR / "templates/shared/AGENTS.md"
    agents_target = project_dir / paths["agents_path"]
    files[str(paths["agents_path"])] = {
        "mode": "skip_if_exists",
        "checksum": install_skip_if_exists(agents_template, agents_target),
    }

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

    config_rel = paths["config_path"]
    project_name = project_dir.name
    files[str(config_rel)] = {
        "mode": "skip_if_exists",
        "checksum": install_project_config(
            project_dir, project_name, project_dir / config_rel, preset_name
        ),
    }

    manifest = {
        "name": "so2x-harness",
        "version": VERSION,
        "platforms": ["claude"],
        "installed_at": datetime.now(timezone.utc).isoformat(),
        "files": files,
    }
    write_manifest(project_dir, manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--platform", default="claude")
    parser.add_argument("--preset", default="general")
    args = parser.parse_args()

    project = Path(args.project).resolve()
    project.mkdir(parents=True, exist_ok=True)

    if args.platform != "claude":
        raise SystemExit(f"unsupported platform: {args.platform} (currently supported: claude)")

    manifest = apply_claude(project, args.preset)
    print(
        f"[so2x-harness] installed version={manifest['version']} platform=claude project={project}"
    )
    print(f"[so2x-harness] preset={args.preset}")
    print(f"[so2x-harness] wrote {len(manifest['files'])} managed file entries")


if __name__ == "__main__":
    main()
