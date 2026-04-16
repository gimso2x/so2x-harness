from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from cli.commands.spec import dependencies_satisfied, get_task, get_next_task, load_spec, save_spec, set_task_status
from cli.commands.learning_tools import (
    DEFAULT_EVENT_FILE,
    DEFAULT_HARNESS_DIR,
    DEFAULT_LEARNING_FILE,
    DEFAULT_PROMOTED_RULES_FILE,
    DEFAULT_STATUS_DIR,
    append_event_entries,
    build_auto_learning_bundle,
    format_relevant_learnings,
    persist_learning_bundle,
    read_status,
    write_status,
)
from runtime import get_max_retries_for_task, load_harness_config, run_task

_ALLOWED_SIMPLIFY_STOP_REASONS = {
    "converged_to_zero",
    "no_safe_gain",
    "blocked_by_requirement",
    "repeated_no_progress",
    "circuit_breaker",
}


def handle_run(args: argparse.Namespace) -> None:
    command = getattr(args, "run_command", None) or "task"
    if command == "task":
        cmd_run(args)
    elif command == "status":
        cmd_status(args)
    elif command == "safe-commit":
        cmd_safe_commit(args)
    elif command == "squash-check":
        cmd_squash_check(args)
    elif command == "specify":
        cmd_specify(args)
    elif command == "execute":
        cmd_execute(args)
    else:
        raise SystemExit("Usage: so2x-cli run {task|status|safe-commit|squash-check|specify|execute}")


def select_task_for_run(spec: dict[str, Any], task_id: str | None = None, use_next: bool = False) -> dict[str, Any]:
    if task_id:
        task = get_task(spec, task_id)
        if task is None:
            raise SystemExit(f"task not found: {task_id}")
        if task.get("status") == "done":
            raise SystemExit(f"task already done: {task_id}")
        if not dependencies_satisfied(spec, task):
            raise SystemExit(f"dependencies not satisfied: {task_id}")
        return task
    if use_next:
        task = get_next_task(spec)
        if task is None:
            raise SystemExit("no runnable task")
        return task
    raise SystemExit("choose --task or --next")


def mark_task_in_progress(spec: dict[str, Any], task_id: str) -> dict[str, Any]:
    return set_task_status(spec, task_id, "in_progress")


def parse_runner_output(stdout: str, stderr: str) -> dict[str, str | None]:
    parsed = {"status": None, "summary": None, "error": None}
    for raw_line in stdout.splitlines():
        line = raw_line.strip()
        if line.startswith("STATUS:"):
            parsed["status"] = line.split(":", 1)[1].strip()
        elif line.startswith("SUMMARY:"):
            parsed["summary"] = line.split(":", 1)[1].strip()
        elif line.startswith("ERROR:"):
            parsed["error"] = line.split(":", 1)[1].strip()
    if parsed["error"] is None and stderr.strip():
        parsed["error"] = stderr.strip().splitlines()[-1]
    return parsed


def classify_result(task: dict[str, Any], run_result: dict[str, Any], parsed_output: dict[str, str | None]) -> dict[str, str | None]:
    status = parsed_output.get("status")
    summary = parsed_output.get("summary")
    error = parsed_output.get("error")
    if status in {"done", "blocked", "error"}:
        return {"status": status, "summary": summary, "last_error": error}
    if run_result.get("exit_code") == 0:
        return {"status": "done", "summary": summary or f"{task.get('id')} completed", "last_error": error}
    return {"status": "error", "summary": summary or f"{task.get('id')} failed", "last_error": error or f"runner exited with code {run_result.get('exit_code')}"}


def apply_run_result(spec: dict[str, Any], task_id: str, status: str, summary: str | None = None, last_error: str | None = None) -> dict[str, Any]:
    return set_task_status(spec, task_id, status, summary=summary, last_error=last_error)


def run_with_retries(project_dir: str | Path, spec_path: str | Path, spec: dict[str, Any], task: dict[str, Any], config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    current_spec = deepcopy(spec)
    max_retries = get_max_retries_for_task(task, config)
    last_error = task.get("last_error")
    final_result: dict[str, Any] = {}
    for attempt in range(max_retries + 1):
        current_spec = mark_task_in_progress(current_spec, task["id"])
        save_spec(spec_path, current_spec)
        run_result = run_task(project_dir, current_spec, get_task(current_spec, task["id"]), config, last_error=last_error)
        parsed = parse_runner_output(run_result.get("stdout", ""), run_result.get("stderr", ""))
        classified = classify_result(task, run_result, parsed)
        current_spec = apply_run_result(current_spec, task["id"], classified["status"] or "error", summary=classified.get("summary"), last_error=classified.get("last_error"))
        save_spec(spec_path, current_spec)
        final_result = run_result
        if classified["status"] != "error" or attempt >= max_retries:
            return current_spec, run_result
        last_error = classified.get("last_error")
    return current_spec, final_result


def cmd_run(args: argparse.Namespace) -> None:
    spec_path = Path(args.file)
    project_dir = spec_path.parent
    spec = load_spec(spec_path)
    config = load_harness_config(project_dir)
    task = select_task_for_run(spec, task_id=getattr(args, "task", None), use_next=getattr(args, "next", False))
    updated_spec, run_result = run_with_retries(project_dir, spec_path, spec, task, config)
    final_task = get_task(updated_spec, task["id"])
    print(f"task: {final_task['id']}")
    print(f"status: {final_task['status']}")
    if final_task.get("summary"):
        print(f"summary: {final_task['summary']}")
    if final_task.get("last_error"):
        print(f"last_error: {final_task['last_error']}")
    print(f"exit_code: {run_result.get('exit_code')}")
    if final_task["status"] == "error":
        raise SystemExit(1)


def cmd_status(args: argparse.Namespace) -> None:
    harness_dir = Path(getattr(args, "dir", "") or DEFAULT_HARNESS_DIR)
    status_dir = harness_dir / DEFAULT_STATUS_DIR.name
    simplify = read_status("simplify-cycle", status_dir)
    safe_commit = read_status("safe-commit", status_dir)
    squash = read_status("squash-commit", status_dir)
    print(f"[run] status dir: {status_dir}")
    print(f"  simplify-cycle: remaining={simplify.get('remaining_count')} stop_reason={simplify.get('stop_reason')}" if simplify else "  simplify-cycle: missing")
    print(f"  safe-commit: verdict={safe_commit.get('safety_verdict')} verification={safe_commit.get('verification_status')}" if safe_commit else "  safe-commit: missing")
    print(f"  squash-commit: ready={squash.get('ready')} reason={squash.get('reason')}" if squash else "  squash-commit: missing")


def cmd_safe_commit(args: argparse.Namespace) -> None:
    harness_dir = Path(getattr(args, "dir", "") or DEFAULT_HARNESS_DIR)
    status_dir = harness_dir / DEFAULT_STATUS_DIR.name
    event_file = harness_dir / DEFAULT_EVENT_FILE.name
    simplify = read_status("simplify-cycle", status_dir)
    if not simplify:
        verdict = {"name": "safe-commit", "safety_verdict": "UNSAFE", "verification_status": "MISSING", "reason": "missing_simplify_cycle"}
        write_status("safe-commit", verdict, status_dir)
        append_event_entries([{"type": "safe_commit_completed", **verdict}], event_file)
        print("[run] safe-commit FAIL: simplify-cycle status missing")
        raise SystemExit(1)
    remaining = int(simplify.get("remaining_count", 0) or 0)
    stop_reason = str(simplify.get("stop_reason", "")).strip()
    safe = remaining == 0 or stop_reason in _ALLOWED_SIMPLIFY_STOP_REASONS - {"converged_to_zero"}
    verdict = {"name": "safe-commit", "safety_verdict": "SAFE" if safe else "UNSAFE", "verification_status": simplify.get("verification_status", "UNKNOWN"), "remaining_count": remaining, "stop_reason": stop_reason, "reason": "ready_for_commit" if safe else "simplify_not_converged"}
    write_status("safe-commit", verdict, status_dir)
    append_event_entries([{"type": "safe_commit_completed", **verdict}], event_file)
    if not safe:
        print(f"[run] safe-commit FAIL: remaining_count={remaining} stop_reason={stop_reason}")
        raise SystemExit(1)
    print(f"[run] safe-commit PASS: remaining_count={remaining} stop_reason={stop_reason}")


def cmd_squash_check(args: argparse.Namespace) -> None:
    harness_dir = Path(getattr(args, "dir", "") or DEFAULT_HARNESS_DIR)
    status_dir = harness_dir / DEFAULT_STATUS_DIR.name
    event_file = harness_dir / DEFAULT_EVENT_FILE.name
    simplify = read_status("simplify-cycle", status_dir)
    safe_commit = read_status("safe-commit", status_dir)
    if not simplify or not safe_commit:
        snapshot = {"name": "squash-commit", "ready": False, "reason": "preconditions_failed"}
        write_status("squash-commit", snapshot, status_dir)
        append_event_entries([{"type": "squash_check_completed", **snapshot}], event_file)
        print("[run] squash-check FAIL: preconditions missing")
        raise SystemExit(1)
    remaining = int(simplify.get("remaining_count", 0) or 0)
    stop_reason = str(simplify.get("stop_reason", "")).strip()
    safe_verdict = str(safe_commit.get("safety_verdict", "")).strip()
    ready = (remaining == 0 or stop_reason in _ALLOWED_SIMPLIFY_STOP_REASONS - {"converged_to_zero"}) and safe_verdict == "SAFE"
    snapshot = {"name": "squash-commit", "ready": ready, "reason": "ready" if ready else "preconditions_failed", "remaining_count": remaining, "stop_reason": stop_reason, "safe_commit_verdict": safe_verdict}
    write_status("squash-commit", snapshot, status_dir)
    append_event_entries([{"type": "squash_check_completed", **snapshot}], event_file)
    if not ready:
        print(f"[run] squash-check FAIL: remaining_count={remaining} stop_reason={stop_reason} safe_commit={safe_verdict}")
        raise SystemExit(1)
    print(f"[run] squash-check PASS: safe_commit={safe_verdict} remaining_count={remaining} stop_reason={stop_reason}")


def cmd_specify(args: argparse.Namespace) -> None:
    project_dir = Path.cwd()
    harness_dir = project_dir / DEFAULT_HARNESS_DIR
    learning_file = harness_dir / DEFAULT_LEARNING_FILE.name
    promoted_rules_file = harness_dir / DEFAULT_PROMOTED_RULES_FILE.name
    relevant = format_relevant_learnings(args.goal, learning_file=learning_file, promoted_rules_file=promoted_rules_file)
    print(f"[run] specifying: {args.goal}")
    if relevant:
        print(relevant)
    print("[run] thin core specify is bootstrap-only; create/edit spec.json directly.")
    raise SystemExit(1)


def cmd_execute(args: argparse.Namespace) -> None:
    spec_file = Path(getattr(args, "file", "spec.json"))
    if not spec_file.exists():
        raise SystemExit(f"[run] spec not found: {spec_file}")
    spec = json.loads(spec_file.read_text(encoding="utf-8"))
    harness_dir = spec_file.parent / DEFAULT_HARNESS_DIR
    learning_file = harness_dir / DEFAULT_LEARNING_FILE.name
    persistence = persist_learning_bundle(build_auto_learning_bundle(spec), harness_dir=harness_dir, learning_file=learning_file)
    print(f"[run] Auto-events captured: {len(persistence.get('events', []))} -> {harness_dir / 'events.jsonl'}")
    print(f"[run] Auto-learnings captured: {len(persistence.get('learnings', []))} -> {learning_file}")
    print(f"[run] Promoted rules: {len(persistence.get('promoted', []))} -> {harness_dir / 'promoted-rules.json'}")
