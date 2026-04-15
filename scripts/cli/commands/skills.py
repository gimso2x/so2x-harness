from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from lib.project_profiles import detect_project_profiles, recommend_skill_plan

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
UPDATE_SCRIPT = ROOT_DIR / "scripts" / "update.py"
DEFAULT_CONFIG_PATH = Path(".ai-harness") / "config.json"


def handle_skills(args: object) -> None:
    command = getattr(args, "skills_command", None)
    if command == "recommend":
        cmd_recommend(args)
    elif command == "enable":
        cmd_enable(args)
    else:
        print("Usage: so2x-cli skills {recommend|enable}")
        sys.exit(1)


def cmd_recommend(args: object) -> None:
    project = _project_dir(args)
    config = _load_project_config(project)
    detected = detect_project_profiles(project)
    plan = recommend_skill_plan(
        detected["detected_profiles"],
        detected["detection_signals"],
        platforms=_config_platforms(config),
        enabled_optional_skills=_enabled_optional_skills(config),
    )

    print(f"project: {project}")
    print(f"detected_profiles: {', '.join(detected['detected_profiles']) or 'none'}")
    print(f"detection_signals: {', '.join(detected['detection_signals']) or 'none'}")
    print(f"enabled_skills: {', '.join(plan['enabled_skills']) or 'none'}")
    print(f"optional_skills: {', '.join(plan['optional_skills']) or 'none'}")
    print("policy_promoted_skills:")
    for skill_name, reason in sorted(plan["policy_promoted_skills"].items()):
        print(f"  - {skill_name}: {reason}")
    print("skill_recommendations:")
    for skill_name in sorted(plan["skill_recommendations"]):
        print(f"  - {skill_name}")
        for reason in plan["skill_recommendations"][skill_name]:
            print(f"    * {reason}")


def cmd_enable(args: object) -> None:
    project = _project_dir(args)
    config = _load_project_config(project)
    requested = [str(skill) for skill in getattr(args, "skills", []) or []]
    if not requested:
        raise SystemExit("no optional skills provided")

    detected = detect_project_profiles(project)
    plan = recommend_skill_plan(
        detected["detected_profiles"],
        detected["detection_signals"],
        platforms=_config_platforms(config),
        enabled_optional_skills=requested,
    )
    optional = set(plan["optional_skills"])
    invalid = [skill for skill in requested if skill not in optional]
    if invalid:
        raise SystemExit(f"not optional for this project: {', '.join(invalid)}")

    existing_enabled_optional = _enabled_optional_skills(config)
    merged_enabled_optional = list(dict.fromkeys(existing_enabled_optional + requested))
    config["enabled_optional_skills"] = merged_enabled_optional
    config_path = project / DEFAULT_CONFIG_PATH
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    subprocess.run([sys.executable, str(UPDATE_SCRIPT), "--project", str(project)], check=True)
    print(f"[skills] enabled optional skills: {', '.join(requested)}")


def _project_dir(args: object) -> Path:
    project = Path(getattr(args, "project", ".") or ".").resolve()
    if not project.exists():
        raise SystemExit(f"project not found: {project}")
    return project


def _load_project_config(project: Path) -> dict:
    config_path = project / DEFAULT_CONFIG_PATH
    if not config_path.exists():
        raise SystemExit(f"config not found: {config_path}")
    return json.loads(config_path.read_text(encoding="utf-8"))


def _config_platforms(config: dict) -> list[str]:
    platforms = config.get("platforms", ["claude"])
    return [str(platform) for platform in platforms] if isinstance(platforms, list) else ["claude"]


def _enabled_optional_skills(config: dict) -> list[str]:
    enabled_optional = config.get("enabled_optional_skills", [])
    return [str(skill) for skill in enabled_optional] if isinstance(enabled_optional, list) else []
