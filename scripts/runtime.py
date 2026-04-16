from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from meta_state import load_meta_harness_state, resolve_meta_harness_state_path


def load_harness_config(project_dir: str | Path) -> dict[str, Any]:
    project_path = Path(project_dir)
    config_path = project_path / "harness.json"
    if not config_path.exists():
        raise SystemExit(f"harness config not found: {config_path}")
    return json.loads(config_path.read_text(encoding="utf-8"))


def resolve_rule_file(project_dir: str | Path, config: dict[str, Any]) -> Path:
    return Path(project_dir) / config.get("rule_file", "CLAUDE.md")


def read_rule_text(project_dir: str | Path, config: dict[str, Any]) -> str:
    rule_path = resolve_rule_file(project_dir, config)
    if not rule_path.exists():
        return ""
    return rule_path.read_text(encoding="utf-8")


def collect_recent_summaries(spec: dict[str, Any], limit: int = 5) -> list[str]:
    tasks = sorted(
        spec.get("tasks", []),
        key=lambda task: str(task.get("updated_at", "")),
        reverse=True,
    )
    summaries = [
        str(task.get("summary", "")).strip()
        for task in tasks
        if str(task.get("summary", "")).strip()
    ]
    return summaries[:limit]


def collect_dependency_summaries(spec: dict[str, Any], task: dict[str, Any]) -> list[str]:
    items: list[str] = []
    by_id = {item.get("id"): item for item in spec.get("tasks", [])}
    for dependency_id in task.get("depends_on", []):
        dependency = by_id.get(dependency_id)
        if dependency and str(dependency.get("summary", "")).strip():
            items.append(f"{dependency_id}: {dependency['summary']}")
    return items


def load_latest_meta_harness_state(
    project_dir: str | Path,
    run_id: str | None = None,
) -> dict[str, Any] | None:
    return load_meta_harness_state(project_dir, run_id=run_id)


def _meta_state_prompt_lines(meta_state: dict[str, Any] | None) -> list[str]:
    if not meta_state:
        return []
    lines = [
        "",
        "Meta harness state:",
        f"RUN_ID: {meta_state.get('run_id', 'unknown')}",
        f"STATUS: {meta_state.get('status', 'unknown')}",
        f"CURRENT_STAGE: {meta_state.get('current_stage', 'unknown')}",
    ]
    last_completed = meta_state.get("last_completed_stage")
    if last_completed:
        lines.append(f"LAST_COMPLETED_STAGE: {last_completed}")
    notes = meta_state.get("notes") or []
    if notes:
        lines.append("NOTES:")
        lines.extend(f"- {note}" for note in notes)
    return lines


def write_meta_harness_state(
    project_dir: str | Path,
    task: dict[str, Any],
    result_status: str,
    summary: str | None = None,
    last_error: str | None = None,
    run_id: str | None = None,
) -> dict[str, Any] | None:
    state = load_latest_meta_harness_state(project_dir, run_id=run_id)
    if not state:
        return None

    current_stage = state.get("current_stage")
    next_stage_by_stage = {
        "stage-0-interview": "stage-1-plan",
        "stage-1-plan": "stage-2-execute",
        "stage-2-execute": "stage-3-review",
        "stage-3-review": "stage-4-finalize",
        "stage-4-finalize": None,
    }
    if result_status == "done":
        if current_stage:
            state["last_completed_stage"] = current_stage
        next_stage = next_stage_by_stage.get(str(current_stage))
        if next_stage:
            state["current_stage"] = next_stage
            state["status"] = "running"
        else:
            state["status"] = "completed"
        state["awaiting_input"] = False
        state["awaiting_input_schema"] = None
    elif result_status == "blocked":
        state["status"] = "awaiting_input"
        state["awaiting_input"] = True
    elif result_status == "error":
        state["status"] = "failed"
        state["awaiting_input"] = False
        state["awaiting_input_schema"] = None
    notes = list(state.get("notes") or [])
    detail = summary or last_error or "no detail"
    notes.append(f"{task.get('id', 'task')} {result_status}: {detail}")
    state["notes"] = notes[-10:]
    state["updated_at"] = datetime.now(timezone.utc).isoformat()

    state_path = resolve_meta_harness_state_path(project_dir, run_id=run_id)
    if not state_path:
        return None
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return state


def build_prompt(
    spec: dict[str, Any],
    task: dict[str, Any],
    rule_text: str,
    summaries: list[str],
    dependency_summaries: list[str] | None = None,
    last_error: str | None = None,
    meta_state: dict[str, Any] | None = None,
) -> str:
    goal = spec.get("meta", {}).get("goal", "")
    lines = [
        "You are running a thin so2x-harness task.",
        f"GOAL: {goal}",
        f"TASK_ID: {task.get('id', '')}",
        f"ROLE: {task.get('role', '')}",
        f"ACTION: {task.get('action', '')}",
        "",
        "Return machine-readable markers:",
        "STATUS: done|blocked|error",
        "SUMMARY: <short summary>",
        "ERROR: <error text when STATUS=error>",
    ]
    if dependency_summaries:
        lines.extend(["", "Dependency summaries:", *[f"- {item}" for item in dependency_summaries]])
    if summaries:
        lines.extend(["", "Recent summaries:", *[f"- {item}" for item in summaries]])
    lines.extend(_meta_state_prompt_lines(meta_state))
    if last_error:
        lines.extend(["", "Last error:", last_error])
    if rule_text:
        lines.extend(["", "Project rules (CLAUDE.md):", rule_text])
    return "\n".join(lines).strip() + "\n"


def build_command(task: dict[str, Any], config: dict[str, Any]) -> list[str]:
    role = task.get("role")
    command = config.get("runners", {}).get(role)
    if not isinstance(command, list) or not command:
        raise SystemExit(f"runner command missing for role: {role}")
    return [str(part) for part in command]


def get_timeout_for_task(task: dict[str, Any], config: dict[str, Any]) -> int:
    timeout = config.get("timeout_sec", {})
    if isinstance(timeout, dict):
        return int(timeout.get(task.get("role"), timeout.get("default", 600)))
    return int(timeout or 600)


def get_max_retries_for_task(task: dict[str, Any], config: dict[str, Any]) -> int:
    retries = config.get("max_retries", {})
    if isinstance(retries, dict):
        return int(retries.get(task.get("role"), retries.get("default", 0)))
    return int(retries or 0)


def run_subprocess(
    command: list[str],
    prompt: str,
    cwd: str | Path,
    timeout_sec: int,
) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        input=prompt,
        text=True,
        capture_output=True,
        cwd=str(cwd),
        timeout=timeout_sec,
        check=False,
    )
    return {
        "command": command,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "exit_code": completed.returncode,
        "timeout_sec": timeout_sec,
    }


def run_task(
    project_dir: str | Path,
    spec: dict[str, Any],
    task: dict[str, Any],
    config: dict[str, Any],
    last_error: str | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    prompt_config = config.get("prompt", {})
    rule_text = (
        read_rule_text(project_dir, config) if prompt_config.get("include_rule_file", True) else ""
    )
    summaries = (
        collect_recent_summaries(spec)
        if prompt_config.get("include_completed_summaries", True)
        else []
    )
    dependency_summaries = collect_dependency_summaries(spec, task)
    prompt_last_error = last_error if prompt_config.get("include_last_error", True) else None
    meta_state = load_latest_meta_harness_state(project_dir, run_id=run_id)
    prompt = build_prompt(
        spec,
        task,
        rule_text,
        summaries,
        dependency_summaries=dependency_summaries,
        last_error=prompt_last_error,
        meta_state=meta_state,
    )
    command = build_command(task, config)
    timeout_sec = get_timeout_for_task(task, config)
    result = run_subprocess(command, prompt, cwd=project_dir, timeout_sec=timeout_sec)
    result["prompt"] = prompt
    return result
