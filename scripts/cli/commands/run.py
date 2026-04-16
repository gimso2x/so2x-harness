from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path
from typing import Any

from cli.commands.spec import (
    dependencies_satisfied,
    get_next_task,
    get_task,
    load_spec,
    save_spec,
    set_task_status,
)
from runtime import (
    get_max_retries_for_task,
    load_harness_config,
    run_task,
    write_meta_harness_state,
)

VALID_RESULT_STATUSES = {"done", "blocked", "error"}


def select_task_for_run(
    spec: dict[str, Any],
    task_id: str | None = None,
    use_next: bool = False,
) -> dict[str, Any]:
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


def classify_result(
    task: dict[str, Any],
    run_result: dict[str, Any],
    parsed_output: dict[str, str | None],
) -> dict[str, str | None]:
    status = parsed_output.get("status")
    summary = parsed_output.get("summary")
    error = parsed_output.get("error")

    if status in VALID_RESULT_STATUSES:
        return {"status": status, "summary": summary, "last_error": error}
    if run_result.get("exit_code") == 0:
        return {
            "status": "done",
            "summary": summary or f"{task.get('id')} completed",
            "last_error": error,
        }
    return {
        "status": "error",
        "summary": summary,
        "last_error": error or f"runner exited with code {run_result.get('exit_code')}",
    }


def apply_run_result(
    spec: dict[str, Any],
    task_id: str,
    status: str,
    summary: str | None = None,
    last_error: str | None = None,
) -> dict[str, Any]:
    return set_task_status(spec, task_id, status, summary=summary, last_error=last_error)


def run_with_retries(
    project_dir: str | Path,
    spec_path: str | Path,
    spec: dict[str, Any],
    task: dict[str, Any],
    config: dict[str, Any],
    run_id: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    current_spec = deepcopy(spec)
    max_retries = get_max_retries_for_task(task, config)
    last_error = task.get("last_error") or None
    final_result: dict[str, Any] = {}

    for attempt in range(max_retries + 1):
        current_spec = mark_task_in_progress(current_spec, task["id"])
        save_spec(spec_path, current_spec)

        run_result = run_task(
            project_dir,
            current_spec,
            get_task(current_spec, task["id"]),
            config,
            last_error=last_error,
            run_id=run_id,
        )
        parsed = parse_runner_output(run_result.get("stdout", ""), run_result.get("stderr", ""))
        classified = classify_result(task, run_result, parsed)
        current_spec = apply_run_result(
            current_spec,
            task["id"],
            classified["status"] or "error",
            summary=classified.get("summary"),
            last_error=classified.get("last_error"),
        )
        save_spec(spec_path, current_spec)
        write_meta_harness_state(
            project_dir,
            task,
            classified["status"] or "error",
            summary=classified.get("summary"),
            last_error=classified.get("last_error"),
            run_id=run_id,
        )
        final_result = run_result

        if classified["status"] != "error" or attempt >= max_retries:
            return current_spec, final_result
        last_error = classified.get("last_error") or last_error

    return current_spec, final_result


def cmd_run(args: argparse.Namespace) -> None:
    spec_path = Path(args.file)
    project_dir = spec_path.parent
    spec = load_spec(spec_path)
    config = load_harness_config(project_dir)
    task = select_task_for_run(
        spec,
        task_id=getattr(args, "task", None),
        use_next=getattr(args, "next", False),
    )
    updated_spec, run_result = run_with_retries(
        project_dir,
        spec_path,
        spec,
        task,
        config,
        run_id=getattr(args, "run_id", None),
    )
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
