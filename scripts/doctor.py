# ruff: noqa: E402
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
sys.path.insert(0, str(CURRENT_DIR))

from lib.install import Capability
from lib.manifest import manifest_path
from lib.platform_map import PLATFORM_CAPABILITIES, PROJECT_PATHS
from lib.project_profiles import detect_project_profiles, recommend_skill_plan
from cli.commands.spec import get_next_task, summarize_spec


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


def detect_core_files(project_dir: str | Path) -> dict[str, bool]:
    root = Path(project_dir)
    return {"CLAUDE.md": (root / "CLAUDE.md").exists(), "spec.json": (root / "spec.json").exists(), "harness.json": (root / "harness.json").exists()}


def load_project_state(project_dir: str | Path) -> dict[str, Any] | None:
    return _load_json(Path(project_dir) / "spec.json")


def _append_skill_recommendation_items(items: list[tuple[str, str, str]], skill_recommendations: dict, label_prefix: str = "") -> None:
    if not isinstance(skill_recommendations, dict):
        return
    for skill_name in sorted(skill_recommendations):
        reasons = skill_recommendations.get(skill_name)
        if not isinstance(reasons, list) or not reasons:
            continue
        items.append(("OK", f"{label_prefix}skill_recommendation.{skill_name}", " | ".join(str(reason) for reason in reasons)))


def _append_list_surface(items: list[tuple[str, str, str]], label: str, values: list[object], *, level: str = "OK") -> None:
    items.append((level, label, ", ".join(str(value) for value in values) if values else "none"))


def _append_policy_surface(items: list[tuple[str, str, str]], label: str, policy_promoted_skills: object) -> None:
    if isinstance(policy_promoted_skills, dict) and policy_promoted_skills:
        items.append(("OK", label, "; ".join(f"{skill}={reason}" for skill, reason in sorted(policy_promoted_skills.items()))))
    else:
        items.append(("OK", label, "none"))


def get_active_problem(spec: dict[str, Any] | None) -> str | None:
    if not spec:
        return None
    summary = summarize_spec(spec)
    if summary.get("blocked_task"):
        return f"blocked on {summary['blocked_task'].get('id')}"
    if summary.get("error_task"):
        return f"error on {summary['error_task'].get('id')}"
    return None


def get_latest_summary(spec: dict[str, Any] | None) -> str:
    if not spec:
        return "none"
    return summarize_spec(spec).get("latest_summary") or "none"


def _execution_items(project_dir: Path) -> list[tuple[str, str, str]]:
    spec = _load_json(project_dir / "spec.json")
    if not spec:
        return []
    tasks = spec.get("tasks") if isinstance(spec.get("tasks"), list) else spec.get("chain", {}).get("l4_tasks", [])
    if not tasks:
        return [("WARN", "execution_status", "spec.json present but no tasks found")]
    blocked = [task for task in tasks if task.get("status") == "blocked"]
    in_progress = [task for task in tasks if task.get("status") == "in_progress"]
    pending = [task for task in tasks if task.get("status") == "pending"]
    if blocked:
        current = blocked[0]
        items = [("WARN", "execution_status", f"blocked on task {current.get('id', '?')}"), ("WARN", "execution_summary", f"latest summary: {current.get('summary', 'blocked without summary')}")]
    elif in_progress:
        current = in_progress[0]
        items = [("OK", "execution_status", f"in progress on task {current.get('id', '?')}"), ("OK", "execution_summary", f"latest summary: {current.get('summary', 'in progress')}")]
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
    config = _load_json(harness_dir / "config.json") if harness_dir.exists() else None
    events_file = harness_dir / "events.jsonl"
    items: list[tuple[str, str, str]] = []
    if simplify:
        items.append((("OK" if int(simplify.get("remaining_count", 0) or 0) == 0 else "WARN"), "simplify_status", f"remaining={simplify.get('remaining_count', '?')}, stop_reason={simplify.get('stop_reason', 'unknown')}"))
    elif harness_dir.exists():
        items.append(("WARN", "simplify_status", "missing simplify-cycle.json"))
    if safe_commit:
        items.append((("OK" if str(safe_commit.get("safety_verdict", "")) == "SAFE" else "WARN"), "safe_commit_status", f"verdict={safe_commit.get('safety_verdict', 'UNKNOWN')}, verification={safe_commit.get('verification_status', 'UNKNOWN')}"))
    elif harness_dir.exists():
        items.append(("WARN", "safe_commit_status", "missing safe-commit.json"))
    if squash:
        items.append((("OK" if bool(squash.get("ready", False)) else "WARN"), "squash_status", f"ready={bool(squash.get('ready', False))}, reason={squash.get('reason', 'unknown')}"))
    elif harness_dir.exists():
        items.append(("WARN", "squash_status", "missing squash-commit.json"))
    if promoted and isinstance(promoted.get("rules"), list):
        items.append(("OK", "promoted_rules", f"{len(promoted['rules'])} promoted rule(s)"))
        latest = max(promoted["rules"], key=lambda rule: str(rule.get("promoted_at", "")), default=None)
        if latest and latest.get("rule"):
            items.append(("OK", "latest_promoted_rule", str(latest.get("rule"))))
    elif harness_dir.exists():
        items.append(("WARN", "promoted_rules", "missing promoted-rules.json"))
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
        _append_list_surface(items, "enabled_skills", [str(v) for v in enabled_skills])
        _append_list_surface(items, "recommended_skills", [str(v) for v in recommended_skills])
        _append_list_surface(items, "optional_skills", [str(v) for v in optional_skills])
        _append_list_surface(items, "enabled_optional_skills", [str(v) for v in enabled_optional_skills])
        _append_policy_surface(items, "policy_promoted_skills", policy_promoted_skills)
        _append_skill_recommendation_items(items, skill_recommendations)
        config_platforms = [str(platform) for platform in config.get("platforms", ["claude"]) if str(platform)]
        _append_list_surface(items, "config_platforms", config_platforms)
        manifest = _load_json(project_dir / ".ai-harness" / "manifest.json")
        manifest_platforms = [str(platform) for platform in (manifest or {}).get("platforms", [])]
        if manifest_platforms and manifest_platforms != config_platforms:
            items.append(("WARN", "config_platforms", f"manifest platforms={manifest_platforms} != config platforms={config_platforms}"))
        if str(config.get("preset", "")) == "auto":
            current = detect_project_profiles(project_dir)
            current_plan = recommend_skill_plan(current["detected_profiles"], current["detection_signals"], platforms=config_platforms or ["claude"], enabled_optional_skills=[str(skill) for skill in config.get("enabled_optional_skills", [])])
            _append_list_surface(items, "current_detected_profiles", [str(v) for v in current["detected_profiles"]])
            _append_list_surface(items, "current_detection_signals", [str(v) for v in current["detection_signals"]])
            _append_list_surface(items, "current_enabled_skills", [str(v) for v in current_plan["enabled_skills"]])
            _append_list_surface(items, "current_recommended_skills", [str(v) for v in current_plan["recommended_skills"]])
            _append_list_surface(items, "current_optional_skills", [str(v) for v in current_plan["optional_skills"]])
            _append_list_surface(items, "current_enabled_optional_skills", [str(v) for v in current_plan["enabled_optional_skills"]])
            _append_policy_surface(items, "current_policy_promoted_skills", current_plan["policy_promoted_skills"])
            _append_skill_recommendation_items(items, current_plan["skill_recommendations"], label_prefix="current_")
            if profiles != current["detected_profiles"] or signals != current["detection_signals"]:
                items.append(("WARN", "auto_profile_drift", f"config profiles={profiles} signals={signals} != current profiles={current['detected_profiles']} signals={current['detection_signals']}"))
            if enabled_skills != current_plan["enabled_skills"]:
                items.append(("WARN", "enabled_skill_drift", f"config enabled_skills={enabled_skills} != current enabled_skills={current_plan['enabled_skills']}"))
            if recommended_skills != current_plan["recommended_skills"] or optional_skills != current_plan["optional_skills"]:
                items.append(("WARN", "recommendation_drift", f"config recommended={recommended_skills} optional={optional_skills} != current recommended={current_plan['recommended_skills']} optional={current_plan['optional_skills']}"))
            stale_enabled_optional = [str(skill) for skill in enabled_optional_skills if str(skill) not in current_plan["optional_skills"]]
            if stale_enabled_optional:
                items.append(("WARN", "enabled_optional_skill_drift", f"config enabled_optional_skills={enabled_optional_skills} include stale skills={stale_enabled_optional}; current eligible_optional_skills={current_plan['optional_skills']}"))
            if policy_promoted_skills != current_plan["policy_promoted_skills"]:
                items.append(("WARN", "policy_promotion_drift", f"config policy_promoted_skills={policy_promoted_skills} != current policy_promoted_skills={current_plan['policy_promoted_skills']}"))
            if skill_recommendations != current_plan["skill_recommendations"]:
                items.append(("WARN", "recommendation_rationale_drift", f"config skill_recommendations={skill_recommendations} != current skill_recommendations={current_plan['skill_recommendations']}"))
    feedback_count = 0
    latest_feedback = ""
    safe_commit_events = 0
    squash_check_events = 0
    if events_file.exists():
        for line in events_file.read_text(encoding="utf-8").splitlines():
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("type") == "user_feedback_captured":
                feedback_count += 1
                latest_feedback = str(entry.get("message", "")).strip() or latest_feedback
            elif entry.get("type") == "safe_commit_completed":
                safe_commit_events += 1
            elif entry.get("type") == "squash_check_completed":
                squash_check_events += 1
    items.append(("OK" if feedback_count else "WARN", "feedback_events", f"{feedback_count} feedback event(s) captured" if feedback_count else "no feedback events captured yet"))
    if latest_feedback:
        items.append(("OK", "latest_feedback", latest_feedback))
    items.append(("OK" if safe_commit_events else "WARN", "safe_commit_events", f"{safe_commit_events} safe-commit event(s) recorded" if safe_commit_events else "no safe-commit events recorded yet"))
    items.append(("OK" if squash_check_events else "WARN", "squash_check_events", f"{squash_check_events} squash-check event(s) recorded" if squash_check_events else "no squash-check events recorded yet"))
    return items


def render_doctor_lines(project_dir: str | Path, files_ok: dict[str, bool], spec: dict[str, Any] | None) -> list[str]:
    root = Path(project_dir).resolve()
    lines = [f"[INFO] project={root}"]
    for name in ("CLAUDE.md", "spec.json", "harness.json"):
        lines.append(status_line("OK" if files_ok[name] else "WARN", name, "present" if files_ok[name] else "missing"))
    if spec:
        summary = summarize_spec(spec)
        lines.append(status_line("OK", "goal", summary["goal"]))
        next_task = get_next_task(spec)
        lines.append(status_line("OK" if next_task else "WARN", "next_task", f"{next_task['id']} {next_task.get('role', '')} {next_task.get('action', '')}".strip() if next_task else "none"))
        active_problem = get_active_problem(spec)
        lines.append(status_line("WARN" if active_problem else "OK", "execution_status", active_problem or "no blocked/error task"))
        lines.append(status_line("OK", "latest summary", get_latest_summary(spec)))
        counts = summary["counts"]
        lines.append(status_line("OK", "counts", " ".join(f"{status}={counts[status]}" for status in ("pending", "in_progress", "blocked", "error", "done"))))
    return lines


def check_project(project_dir: Path) -> list[tuple[str, str, str]]:
    items: list[tuple[str, str, str]] = []
    if project_dir.exists() and project_dir.is_dir():
        items.append(("OK", "project_dir", str(project_dir)))
    else:
        items.append(("ERROR", "project_dir", f"directory not found: {project_dir}"))
        return items
    mf = manifest_path(project_dir)
    manifest_data = _load_json(mf) if mf.exists() else None
    items.append(("OK" if mf.exists() else "WARN", "manifest", str(mf) if mf.exists() else "missing"))
    platforms = manifest_data.get("platforms", ["claude"]) if isinstance(manifest_data, dict) else ["claude"]
    for platform in platforms:
        if platform not in PROJECT_PATHS:
            items.append(("WARN", "platform", f"unknown platform: {platform}"))
            continue
        paths = PROJECT_PATHS[platform]
        caps = PLATFORM_CAPABILITIES.get(platform, {})
        rules_dir = project_dir / paths.get("rules_dir", "") if paths.get("rules_dir") else None
        skills_dir = project_dir / paths.get("skills_dir", "") if paths.get("skills_dir") else None
        claude_md_path = paths.get("claude_md_path")
        if claude_md_path:
            claude_md = project_dir / claude_md_path
            items.append(("OK" if claude_md.exists() else "WARN", f"{platform}.claude_md", "CLAUDE.md exists" if claude_md.exists() else "CLAUDE.md not found yet"))
        if rules_dir:
            items.append(("OK" if rules_dir.exists() else "WARN", f"{platform}.rules_dir", str(rules_dir)))
            items.append(("OK" if rules_dir.exists() else "WARN", "rules_dir", str(rules_dir)))
        if skills_dir:
            items.append(("OK" if skills_dir.exists() else "WARN", f"{platform}.skills_dir", str(skills_dir)))
            items.append(("OK" if skills_dir.exists() else "WARN", "skills_dir", str(skills_dir)))
            if manifest_data and isinstance(manifest_data, dict):
                config = _load_json(project_dir / ".ai-harness" / "config.json") or {}
                enabled = [str(skill) for skill in config.get("enabled_skills", [])] if isinstance(config.get("enabled_skills"), list) else []
                installed = sorted(path.name for path in skills_dir.iterdir() if path.is_dir()) if skills_dir.exists() else []
                if enabled and installed != sorted(enabled):
                    items.append(("WARN", "skills_drift", f"enabled skills={sorted(enabled)} installed skills={installed}"))
                    missing = sorted(skill for skill in enabled if skill not in installed)
                    unexpected = sorted(skill for skill in installed if skill not in enabled)
                    if missing:
                        items.append(("WARN", "missing_enabled_skills", ", ".join(missing)))
                    if unexpected:
                        items.append(("WARN", "unexpected_installed_skills", ", ".join(unexpected)))
        for capability in (Capability.RULES, Capability.SKILLS):
            capability_name = capability.value if hasattr(capability, "value") else str(capability)
            if caps.get(capability_name):
                items.append(("OK", f"{platform}.{capability_name}", "supported"))
    python_level, python_detail = detect_python()
    items.append((python_level, "python", python_detail))
    items.extend(_execution_items(project_dir))
    items.extend(_workflow_status_items(project_dir))
    return items


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only thin harness doctor")
    parser.add_argument("--project", default=".", help="Project directory")
    args = parser.parse_args()
    project_dir = Path(args.project).resolve()
    files_ok = detect_core_files(project_dir)
    spec = load_project_state(project_dir)
    for line in render_doctor_lines(project_dir, files_ok, spec):
        print(line)
    for level, label, detail in check_project(project_dir):
        if label in {"project_dir", "manifest", "rules_dir", "skills_dir", "python", "execution_status", "execution_summary", "pending_tasks", "simplify_status", "safe_commit_status", "squash_status", "promoted_rules", "latest_promoted_rule", "detected_profiles", "detection_signals", "enabled_skills", "recommended_skills", "optional_skills", "enabled_optional_skills", "policy_promoted_skills", "feedback_events", "latest_feedback", "safe_commit_events", "squash_check_events", "config_platforms", "skills_drift", "missing_enabled_skills", "unexpected_installed_skills", "auto_profile_drift", "enabled_skill_drift", "recommendation_drift", "enabled_optional_skill_drift", "policy_promotion_drift", "recommendation_rationale_drift"} or label.startswith("skill_recommendation.") or label.startswith("current_") or label.endswith(".claude_md") or label.endswith(".rules_dir") or label.endswith(".skills_dir"):
            print(status_line(level, label, detail))


if __name__ == "__main__":
    main()
