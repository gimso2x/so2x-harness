# ruff: noqa: E402
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
sys.path.insert(0, str(CURRENT_DIR))

from lib.install import Capability
from lib.manifest import manifest_path
from lib.platform_map import PLATFORM_CAPABILITIES, PROJECT_PATHS
from lib.project_profiles import detect_project_profiles, recommend_skill_plan


def status_line(level: str, label: str, detail: str) -> str:
    return f"[{level}] {label}: {detail}"


def detect_python() -> tuple[str, str]:
    python_path = shutil.which("python3") or shutil.which("python")
    if python_path:
        return ("OK", python_path)
    return ("ERROR", "python3/python not found in PATH")


def _load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _load_spec(project_dir: Path) -> dict | None:
    return _load_json(project_dir / "spec.json")


def _append_skill_recommendation_items(
    items: list[tuple[str, str, str]], skill_recommendations: dict, label_prefix: str = ""
) -> None:
    if not isinstance(skill_recommendations, dict):
        return
    for skill_name in sorted(skill_recommendations):
        reasons = skill_recommendations.get(skill_name)
        if not isinstance(reasons, list) or not reasons:
            continue
        summary = " | ".join(str(reason) for reason in reasons)
        items.append(("OK", f"{label_prefix}skill_recommendation.{skill_name}", summary))


def _append_list_surface(
    items: list[tuple[str, str, str]],
    label: str,
    values: list[object],
    *,
    level: str = "OK",
) -> None:
    if values:
        items.append((level, label, ", ".join(str(value) for value in values)))
    else:
        items.append((level, label, "none"))


def _append_policy_surface(items: list[tuple[str, str, str]], label: str, policy_promoted_skills: object) -> None:
    if isinstance(policy_promoted_skills, dict) and policy_promoted_skills:
        summary = "; ".join(
            f"{skill}={reason}" for skill, reason in sorted(policy_promoted_skills.items())
        )
        items.append(("OK", label, summary))
    else:
        items.append(("OK", label, "none"))


def _execution_items(project_dir: Path) -> list[tuple[str, str, str]]:
    spec = _load_spec(project_dir)
    if not spec:
        return []

    tasks = spec.get("chain", {}).get("l4_tasks", [])
    if not tasks:
        return [("WARN", "execution_status", "spec.json present but no l4_tasks found")]

    blocked = [task for task in tasks if task.get("status") == "blocked"]
    in_progress = [task for task in tasks if task.get("status") == "in_progress"]
    pending = [task for task in tasks if task.get("status") == "pending"]

    if blocked:
        current = blocked[0]
        task_id = current.get("id", "?")
        summary = current.get("summary", "blocked without summary")
        items = [
            ("WARN", "execution_status", f"blocked on task {task_id}"),
            ("WARN", "execution_summary", f"latest summary: {summary}"),
        ]
    elif in_progress:
        current = in_progress[0]
        task_id = current.get("id", "?")
        summary = current.get("summary", "in progress")
        items = [
            ("OK", "execution_status", f"in progress on task {task_id}"),
            ("OK", "execution_summary", f"latest summary: {summary}"),
        ]
    else:
        items = [("OK", "execution_status", "no active blocked or in_progress tasks")]

    items.append(("OK", "pending_tasks", f"{len(pending)} task(s) still pending"))
    return items


def _workflow_status_items(project_dir: Path) -> list[tuple[str, str, str]]:
    harness_dir = project_dir / ".ai-harness"
    status_dir = harness_dir / "status"
    simplify = _load_json(status_dir / "simplify-cycle.json")
    safe_commit = _load_json(status_dir / "safe-commit.json")
    squash = _load_json(status_dir / "squash-commit.json")
    promoted = _load_json(harness_dir / "promoted-rules.json")
    events_file = harness_dir / "events.jsonl"

    items: list[tuple[str, str, str]] = []

    if simplify:
        remaining = simplify.get("remaining_count", "?")
        stop_reason = simplify.get("stop_reason", "unknown")
        level = "OK" if int(remaining or 0) == 0 else "WARN"
        items.append(
            (level, "simplify_status", f"remaining={remaining}, stop_reason={stop_reason}")
        )
    elif harness_dir.exists():
        items.append(("WARN", "simplify_status", "missing simplify-cycle.json"))

    if safe_commit:
        verdict = str(safe_commit.get("safety_verdict", "UNKNOWN"))
        verification = str(safe_commit.get("verification_status", "UNKNOWN"))
        level = "OK" if verdict == "SAFE" else "WARN"
        items.append(
            (level, "safe_commit_status", f"verdict={verdict}, verification={verification}")
        )
    elif harness_dir.exists():
        items.append(("WARN", "safe_commit_status", "missing safe-commit.json"))

    if squash:
        ready = bool(squash.get("ready", False))
        reason = str(squash.get("reason", "unknown"))
        level = "OK" if ready else "WARN"
        items.append((level, "squash_status", f"ready={ready}, reason={reason}"))
    elif harness_dir.exists():
        items.append(("WARN", "squash_status", "missing squash-commit.json"))

    if promoted and isinstance(promoted.get("rules"), list):
        rules = promoted["rules"]
        items.append(("OK", "promoted_rules", f"{len(rules)} promoted rule(s)"))
        latest_rule = ""
        latest_time = ""
        for rule in rules:
            promoted_at = str(rule.get("promoted_at", ""))
            if promoted_at >= latest_time:
                latest_time = promoted_at
                latest_rule = str(rule.get("rule", "")).strip()
        if latest_rule:
            items.append(("OK", "latest_promoted_rule", latest_rule))
    elif harness_dir.exists():
        items.append(("WARN", "promoted_rules", "missing promoted-rules.json"))

    config = _load_json(harness_dir / "config.json") if harness_dir.exists() else None
    if config:
        profiles = config.get("detected_profiles", [])
        signals = config.get("detection_signals", [])
        enabled_skills = config.get("enabled_skills", [])
        recommended_skills = config.get("recommended_skills", [])
        optional_skills = config.get("optional_skills", [])
        enabled_optional_skills = config.get("enabled_optional_skills", [])
        policy_promoted_skills = config.get("policy_promoted_skills", {})
        skill_recommendations = config.get("skill_recommendations", {})
        _append_list_surface(items, "detected_profiles", [str(p) for p in profiles])
        _append_list_surface(items, "detection_signals", [str(s) for s in signals])
        _append_list_surface(items, "enabled_skills", [str(skill) for skill in enabled_skills])
        _append_list_surface(items, "recommended_skills", [str(skill) for skill in recommended_skills])
        _append_list_surface(items, "optional_skills", [str(skill) for skill in optional_skills])
        _append_list_surface(
            items,
            "enabled_optional_skills",
            [str(skill) for skill in enabled_optional_skills],
        )
        _append_policy_surface(items, "policy_promoted_skills", policy_promoted_skills)
        _append_skill_recommendation_items(items, skill_recommendations)

        if str(config.get("preset", "")) == "auto":
            current = detect_project_profiles(project_dir)
            current_plan = recommend_skill_plan(
                current["detected_profiles"],
                current["detection_signals"],
                platforms=[str(platform) for platform in config.get("platforms", ["claude"])],
                enabled_optional_skills=[str(skill) for skill in config.get("enabled_optional_skills", [])],
            )
            _append_list_surface(
                items,
                "current_detected_profiles",
                [str(profile) for profile in current["detected_profiles"]],
            )
            _append_list_surface(
                items,
                "current_detection_signals",
                [str(signal) for signal in current["detection_signals"]],
            )
            _append_list_surface(
                items,
                "current_enabled_skills",
                [str(skill) for skill in current_plan["enabled_skills"]],
            )
            _append_list_surface(
                items,
                "current_recommended_skills",
                [str(skill) for skill in current_plan["recommended_skills"]],
            )
            _append_list_surface(
                items,
                "current_optional_skills",
                [str(skill) for skill in current_plan["optional_skills"]],
            )
            _append_list_surface(
                items,
                "current_enabled_optional_skills",
                [str(skill) for skill in current_plan["enabled_optional_skills"]],
            )
            _append_policy_surface(items, "current_policy_promoted_skills", current_plan["policy_promoted_skills"])
            _append_skill_recommendation_items(
                items, current_plan["skill_recommendations"], label_prefix="current_"
            )
            if profiles != current["detected_profiles"] or signals != current["detection_signals"]:
                items.append(
                    (
                        "WARN",
                        "auto_profile_drift",
                        "config profiles="
                        f"{profiles} signals={signals} != current profiles={current['detected_profiles']} "
                        f"signals={current['detection_signals']}",
                    )
                )
            if enabled_skills != current_plan["enabled_skills"]:
                items.append(
                    (
                        "WARN",
                        "enabled_skill_drift",
                        "config enabled_skills="
                        f"{enabled_skills} != current enabled_skills={current_plan['enabled_skills']}",
                    )
                )
            if recommended_skills != current_plan["recommended_skills"] or optional_skills != current_plan[
                "optional_skills"
            ]:
                items.append(
                    (
                        "WARN",
                        "recommendation_drift",
                        "config recommended="
                        f"{recommended_skills} optional={optional_skills} != current recommended="
                        f"{current_plan['recommended_skills']} optional={current_plan['optional_skills']}",
                    )
                )
            stale_enabled_optional = [
                str(skill)
                for skill in enabled_optional_skills
                if str(skill) not in current_plan["optional_skills"]
            ]
            if stale_enabled_optional:
                items.append(
                    (
                        "WARN",
                        "enabled_optional_skill_drift",
                        "config enabled_optional_skills="
                        f"{enabled_optional_skills} include stale skills={stale_enabled_optional}; current "
                        f"eligible_optional_skills={current_plan['optional_skills']}",
                    )
                )
            if policy_promoted_skills != current_plan["policy_promoted_skills"]:
                items.append(
                    (
                        "WARN",
                        "policy_promotion_drift",
                        "config policy_promoted_skills="
                        f"{policy_promoted_skills} != current policy_promoted_skills="
                        f"{current_plan['policy_promoted_skills']}",
                    )
                )
            if skill_recommendations != current_plan["skill_recommendations"]:
                items.append(
                    (
                        "WARN",
                        "recommendation_rationale_drift",
                        "config skill_recommendations="
                        f"{skill_recommendations} != current skill_recommendations="
                        f"{current_plan['skill_recommendations']}",
                    )
                )

    feedback_count = 0
    latest_feedback = ""
    safe_commit_events = 0
    squash_check_events = 0
    if events_file.exists():
        for line in events_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            event_type = entry.get("type")
            if event_type == "user_feedback_captured":
                feedback_count += 1
                latest_feedback = str(entry.get("message", "")).strip() or latest_feedback
            elif event_type == "safe_commit_completed":
                safe_commit_events += 1
            elif event_type == "squash_check_completed":
                squash_check_events += 1
    if feedback_count > 0:
        items.append(("OK", "feedback_events", f"{feedback_count} feedback event(s) captured"))
        if latest_feedback:
            items.append(("OK", "latest_feedback", latest_feedback))
    elif harness_dir.exists():
        items.append(("WARN", "feedback_events", "no feedback events captured yet"))

    if safe_commit_events > 0:
        items.append(
            ("OK", "safe_commit_events", f"{safe_commit_events} safe-commit event(s) recorded")
        )
    elif harness_dir.exists():
        items.append(("WARN", "safe_commit_events", "no safe-commit events recorded yet"))

    if squash_check_events > 0:
        items.append(
            ("OK", "squash_check_events", f"{squash_check_events} squash-check event(s) recorded")
        )
    elif harness_dir.exists():
        items.append(("WARN", "squash_check_events", "no squash-check events recorded yet"))

    return items


def _expected_skill_inventory(config_path: Path) -> list[str] | None:
    if not config_path.exists():
        return None
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    enabled_skills = config.get("enabled_skills")
    if not isinstance(enabled_skills, list):
        return None
    return [str(skill) for skill in enabled_skills]


def check_project(project_dir: Path) -> list[tuple[str, str, str]]:
    items: list[tuple[str, str, str]] = []

    if project_dir.exists() and project_dir.is_dir():
        items.append(("OK", "project_dir", str(project_dir)))
    else:
        items.append(("ERROR", "project_dir", f"directory not found: {project_dir}"))
        return items

    mf = manifest_path(project_dir)
    manifest_data: dict | None = None
    if mf.exists():
        try:
            manifest_data = json.loads(mf.read_text(encoding="utf-8"))
        except Exception:
            pass

    platforms: list[str] = ["claude"]
    if manifest_data:
        platforms = manifest_data.get("platforms", ["claude"])

    package_json = project_dir / "package.json"
    if package_json.exists():
        items.append(("OK", "project_signal", "package.json found"))
    else:
        items.append(("WARN", "project_signal", "package.json not found — generic project mode"))

    for platform in platforms:
        prefix = f"{platform}." if len(platforms) > 1 else ""
        if platform not in PROJECT_PATHS:
            items.append(("WARN", f"{prefix}platform", f"unknown platform: {platform}"))
            continue
        paths = PROJECT_PATHS[platform]
        caps = PLATFORM_CAPABILITIES.get(platform, {})

        claude_md_path = paths.get("claude_md_path")
        if claude_md_path:
            claude_md = project_dir / claude_md_path
            if claude_md.exists():
                items.append(("OK", f"{prefix}claude_md", "CLAUDE.md exists"))
            else:
                items.append(("WARN", f"{prefix}claude_md", "CLAUDE.md not found yet"))

        agents_md = project_dir / paths["agents_path"]
        if agents_md.exists():
            items.append(("OK", f"{prefix}agents_md", "AGENTS.md exists"))
        else:
            items.append(("WARN", f"{prefix}agents_md", "AGENTS.md not found yet"))

        rules_dir_path = paths.get("rules_dir")
        if rules_dir_path and caps.get(Capability.RULES):
            rules_dir = project_dir / rules_dir_path
            if rules_dir.exists():
                count = len(list(rules_dir.glob("*.md")))
                items.append(("OK", f"{prefix}rules_dir", f"{rules_dir} ({count} files)"))
            else:
                items.append(("WARN", f"{prefix}rules_dir", f"missing: {rules_dir}"))

        if caps.get(Capability.SKILLS):
            skills_dir = project_dir / paths["skills_dir"]
            if skills_dir.exists():
                installed_skills = sorted(path.parent.name for path in skills_dir.glob("*/SKILL.md"))
                count = len(installed_skills)
                items.append(("OK", f"{prefix}skills_dir", f"{skills_dir} ({count} skills)"))
                expected_skills = _expected_skill_inventory(project_dir / paths["config_path"])
                if expected_skills is not None:
                    missing_skills = sorted(skill for skill in expected_skills if skill not in installed_skills)
                    unexpected_skills = sorted(skill for skill in installed_skills if skill not in expected_skills)
                    if missing_skills or unexpected_skills:
                        items.append(
                            (
                                "WARN",
                                f"{prefix}skills_drift",
                                "expected enabled skills="
                                f"{expected_skills} but found installed skills={installed_skills}",
                            )
                        )
                    if missing_skills:
                        items.append(
                            (
                                "WARN",
                                f"{prefix}missing_enabled_skills",
                                ", ".join(missing_skills),
                            )
                        )
                    if unexpected_skills:
                        items.append(
                            (
                                "WARN",
                                f"{prefix}unexpected_installed_skills",
                                ", ".join(unexpected_skills),
                            )
                        )
            else:
                items.append(("WARN", f"{prefix}skills_dir", f"missing: {skills_dir}"))

        hooks_dir_path = paths.get("hooks_dir")
        if hooks_dir_path and caps.get(Capability.HOOKS):
            hooks_dir = project_dir / hooks_dir_path
            if hooks_dir.exists():
                count = len([p for p in hooks_dir.iterdir() if p.is_file()])
                items.append(("OK", f"{prefix}hooks_dir", f"{hooks_dir} ({count} files)"))
            else:
                items.append(("WARN", f"{prefix}hooks_dir", f"missing: {hooks_dir}"))

        config_path = project_dir / paths["config_path"]
        config_data: dict | None = None
        if config_path.exists():
            items.append(("OK", f"{prefix}config", str(config_path)))
            try:
                config_data = json.loads(config_path.read_text(encoding="utf-8"))
                preset = str(config_data.get("preset", "unknown"))
                items.append(("OK", f"{prefix}config_preset", preset))
            except Exception as exc:
                items.append(("ERROR", f"{prefix}config_parse", f"failed to parse config: {exc}"))
        else:
            items.append(("WARN", f"{prefix}config", "config not found"))

        if config_data and manifest_data:
            config_platforms = config_data.get("platforms", [])
            manifest_platforms = manifest_data.get("platforms", [])
            if config_platforms != manifest_platforms:
                items.append(
                    (
                        "WARN",
                        f"{prefix}config_platforms_drift",
                        "config platforms="
                        f"{config_platforms} != manifest platforms={manifest_platforms}",
                    )
                )

    if manifest_data:
        items.append(("OK", "manifest", str(mf)))
        items.append(("OK", "manifest_version", str(manifest_data.get("version", "unknown"))))
        items.append(("OK", "manifest_platforms", ",".join(manifest_data.get("platforms", []))))
        items.append(("OK", "manifest_files", str(len(manifest_data.get("files", {})))))
    elif mf.exists():
        items.append(("ERROR", "manifest_parse", "manifest exists but could not be parsed"))
    else:
        items.append(("WARN", "manifest", "manifest not found — harness may not be installed"))

    items.extend(_execution_items(project_dir))
    items.extend(_workflow_status_items(project_dir))
    return items


def summarize(items: list[tuple[str, str, str]]) -> str:
    errors = sum(1 for level, _, _ in items if level == "ERROR")
    warns = sum(1 for level, _, _ in items if level == "WARN")
    oks = sum(1 for level, _, _ in items if level == "OK")
    if errors:
        health = "ERROR"
    elif warns:
        health = "WARN"
    else:
        health = "OK"
    return f"[{health}] summary: ok={oks} warn={warns} error={errors}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=".")
    args = parser.parse_args()

    project_dir = Path(args.project).resolve()
    print(f"[INFO] so2x-harness doctor: project={project_dir}")

    py_level, py_detail = detect_python()
    print(status_line(py_level, "python", py_detail))

    items = check_project(project_dir)
    for level, label, detail in items:
        print(status_line(level, label, detail))

    print(summarize([(py_level, "python", py_detail), *items]))


if __name__ == "__main__":
    main()
