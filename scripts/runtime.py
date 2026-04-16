from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


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
    tasks = sorted(spec.get("tasks", []), key=lambda task: str(task.get("updated_at", "")), reverse=True)
    summaries = [str(task.get("summary", "")).strip() for task in tasks if str(task.get("summary", "")).strip()]
    return summaries[:limit]


def collect_dependency_summaries(spec: dict[str, Any], task: dict[str, Any]) -> list[str]:
    items: list[str] = []
    by_id = {item.get("id"): item for item in spec.get("tasks", [])}
    for dependency_id in task.get("depends_on", []):
        dependency = by_id.get(dependency_id)
        if dependency and str(dependency.get("summary", "")).strip():
            items.append(f"{dependency_id}: {dependency['summary']}")
    return items


def build_prompt(
    spec: dict[str, Any],
    task: dict[str, Any],
    rule_text: str,
    summaries: list[str],
    dependency_summaries: list[str] | None = None,
    last_error: str | None = None,
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


def run_subprocess(command: list[str], prompt: str, cwd: str | Path, timeout_sec: int) -> dict[str, Any]:
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
) -> dict[str, Any]:
    rule_text = read_rule_text(project_dir, config) if config.get("prompt", {}).get("include_rule_file", True) else ""
    summaries = collect_recent_summaries(spec) if config.get("prompt", {}).get("include_completed_summaries", True) else []
    dependency_summaries = collect_dependency_summaries(spec, task)
    prompt_last_error = last_error if config.get("prompt", {}).get("include_last_error", True) else None
    prompt = build_prompt(
        spec,
        task,
        rule_text,
        summaries,
        dependency_summaries=dependency_summaries,
        last_error=prompt_last_error,
    )
    command = build_command(task, config)
    timeout_sec = get_timeout_for_task(task, config)
    result = run_subprocess(command, prompt, cwd=project_dir, timeout_sec=timeout_sec)
    result["prompt"] = prompt
    return result
