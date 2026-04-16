from __future__ import annotations

import argparse
import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VALID_STATUSES = {"pending", "in_progress", "blocked", "error", "done"}
VALID_ROLES = {"planning", "review", "dev"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_spec(path: str | Path) -> dict[str, Any]:
    spec_path = Path(path)
    if not spec_path.exists():
        raise SystemExit(f"spec not found: {spec_path}")
    return json.loads(spec_path.read_text(encoding="utf-8"))


def save_spec(path: str | Path, spec: dict[str, Any]) -> None:
    Path(path).write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _generate_spec_id(goal: str) -> str:
    words = re.findall(r"[A-Za-z0-9]+", goal.upper())
    prefix = "-".join(words[:2]) if words else "THIN"
    return f"SPEC-{prefix}-001"


def create_initial_spec(goal: str, spec_id: str | None = None) -> dict[str, Any]:
    timestamp = now_iso()
    return {
        "meta": {
            "id": spec_id or _generate_spec_id(goal),
            "goal": goal,
            "created_at": timestamp,
            "updated_at": timestamp,
        },
        "tasks": [],
    }


def list_tasks(spec: dict[str, Any]) -> list[dict[str, Any]]:
    tasks = spec.get("tasks")
    return tasks if isinstance(tasks, list) else []


def get_task(spec: dict[str, Any], task_id: str) -> dict[str, Any] | None:
    for task in list_tasks(spec):
        if task.get("id") == task_id:
            return task
    return None


def dependencies_satisfied(spec: dict[str, Any], task: dict[str, Any]) -> bool:
    depends_on = task.get("depends_on")
    if not isinstance(depends_on, list):
        return False
    for dependency_id in depends_on:
        dependency = get_task(spec, dependency_id)
        if not dependency or dependency.get("status") != "done":
            return False
    return True


def get_next_task(spec: dict[str, Any]) -> dict[str, Any] | None:
    for task in list_tasks(spec):
        if task.get("status") == "pending" and dependencies_satisfied(spec, task):
            return task
    return None


def set_task_status(
    spec: dict[str, Any],
    task_id: str,
    status: str,
    summary: str | None = None,
    last_error: str | None = None,
) -> dict[str, Any]:
    if status not in VALID_STATUSES:
        raise ValueError(f"invalid status: {status}")
    updated = deepcopy(spec)
    task = get_task(updated, task_id)
    if task is None:
        raise KeyError(task_id)
    task["status"] = status
    task["updated_at"] = now_iso()
    if summary is not None:
        task["summary"] = summary
    if last_error is not None:
        task["last_error"] = last_error
    updated.setdefault("meta", {})["updated_at"] = now_iso()
    return updated


def validate_spec(spec: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    meta = spec.get("meta")
    if not isinstance(meta, dict):
        errors.append("meta must be an object")
    else:
        for key in ("id", "goal", "created_at", "updated_at"):
            if not meta.get(key):
                errors.append(f"meta.{key} is required")

    tasks = spec.get("tasks")
    if not isinstance(tasks, list):
        return errors + ["tasks must be an array"]

    task_ids: set[str] = set()
    for index, task in enumerate(tasks, start=1):
        label = f"tasks[{index}]"
        if not isinstance(task, dict):
            errors.append(f"{label} must be an object")
            continue
        for key in (
            "id",
            "role",
            "action",
            "status",
            "summary",
            "last_error",
            "depends_on",
            "artifacts",
            "updated_at",
        ):
            if key not in task:
                errors.append(f"{label}.{key} is required")
        task_id = task.get("id")
        if isinstance(task_id, str):
            if task_id in task_ids:
                errors.append(f"duplicate task id: {task_id}")
            task_ids.add(task_id)
        if task.get("role") not in VALID_ROLES:
            errors.append(f"{label}.role must be one of {sorted(VALID_ROLES)}")
        if task.get("status") not in VALID_STATUSES:
            errors.append(f"{label}.status must be one of {sorted(VALID_STATUSES)}")
        if not isinstance(task.get("summary"), str):
            errors.append(f"{label}.summary must be a string")
        if not isinstance(task.get("last_error"), str):
            errors.append(f"{label}.last_error must be a string")
        if not isinstance(task.get("depends_on"), list):
            errors.append(f"{label}.depends_on must be an array")
        if not isinstance(task.get("artifacts"), list):
            errors.append(f"{label}.artifacts must be an array")

    for task in tasks:
        if not isinstance(task, dict):
            continue
        for dependency_id in task.get("depends_on", []):
            if dependency_id not in task_ids:
                errors.append(
                    f"{task.get('id', '?')}.depends_on references unknown task {dependency_id}"
                )
    return errors


def summarize_spec(spec: dict[str, Any]) -> dict[str, Any]:
    counts = {status: 0 for status in ("pending", "in_progress", "blocked", "error", "done")}
    tasks = list_tasks(spec)
    for task in tasks:
        status = task.get("status")
        if status in counts:
            counts[status] += 1
    next_task = get_next_task(spec)
    blocked_task = next((task for task in tasks if task.get("status") == "blocked"), None)
    error_task = next((task for task in tasks if task.get("status") == "error"), None)
    latest_task = max(tasks, key=lambda item: str(item.get("updated_at", "")), default=None)
    return {
        "goal": spec.get("meta", {}).get("goal", ""),
        "counts": counts,
        "next_task": next_task,
        "blocked_task": blocked_task,
        "error_task": error_task,
        "latest_summary": (latest_task or {}).get("summary", ""),
        "total_tasks": len(tasks),
    }


def cmd_init(args: argparse.Namespace) -> None:
    spec = create_initial_spec(goal=args.goal, spec_id=getattr(args, "spec_id", None))
    save_spec(args.file, spec)
    print(f"[spec] created {args.file}")


def cmd_status(args: argparse.Namespace) -> None:
    spec = load_spec(args.file)
    summary = summarize_spec(spec)
    print(f"goal: {summary['goal']}")
    print(
        "counts: "
        + " ".join(
            f"{status}={summary['counts'][status]}"
            for status in ("pending", "in_progress", "blocked", "error", "done")
        )
    )
    next_task = summary["next_task"]
    if next_task:
        print(
            f"next_task: {next_task['id']} "
            f"{next_task.get('role', '')} {next_task.get('action', '')}".strip()
        )
    else:
        print("next_task: none")


def cmd_next(args: argparse.Namespace) -> None:
    spec = load_spec(args.file)
    task = get_next_task(spec)
    if task is None:
        print("next_task: none")
        return
    print(json.dumps(task, ensure_ascii=False, indent=2))


def cmd_set_status(args: argparse.Namespace) -> None:
    spec = load_spec(args.file)
    try:
        updated = set_task_status(
            spec,
            args.task_id,
            args.status,
            summary=getattr(args, "summary", None),
            last_error=getattr(args, "last_error", None),
        )
    except KeyError as exc:
        raise SystemExit(f"task not found: {exc.args[0]}") from exc
    save_spec(args.file, updated)
    print(f"[spec] updated {args.task_id} -> {args.status}")


def cmd_validate(args: argparse.Namespace) -> None:
    spec = load_spec(args.file)
    errors = validate_spec(spec)
    if errors:
        print("[validate] FAIL")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    print("[validate] PASS")
