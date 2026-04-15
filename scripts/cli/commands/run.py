from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

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

AGENT_DIR = Path(__file__).resolve().parent.parent.parent.parent / "templates/claude/agents"
_ALLOWED_SIMPLIFY_STOP_REASONS = {
    "converged_to_zero",
    "no_safe_gain",
    "blocked_by_requirement",
    "repeated_no_progress",
    "circuit_breaker",
}


def handle_run(args: object) -> None:
    command = getattr(args, "run_command", None)
    if command == "specify":
        cmd_specify(args)
    elif command == "execute":
        cmd_execute(args)
    elif command == "status":
        cmd_status(args)
    elif command == "safe-commit":
        cmd_safe_commit(args)
    elif command == "squash-check":
        cmd_squash_check(args)
    else:
        print("Usage: so2x-cli run {specify|execute|status|safe-commit|squash-check}")


def cmd_specify(args: object) -> None:
    goal = getattr(args, "goal", "")
    spec_file = Path(getattr(args, "output", "spec.json"))
    harness_dir = spec_file.parent / DEFAULT_HARNESS_DIR
    learning_file = spec_file.parent / DEFAULT_LEARNING_FILE
    promoted_rules_file = harness_dir / DEFAULT_PROMOTED_RULES_FILE.name

    print(f"[run] specifying: {goal}")
    relevant_learnings = format_relevant_learnings(
        goal,
        learning_file=learning_file,
        promoted_rules_file=promoted_rules_file,
    )
    if relevant_learnings:
        print(relevant_learnings)

    subprocess.run(
        ["so2x-cli", "spec", "init", goal, "--output", str(spec_file)],
        check=True,
    )

    pipeline = [
        ("L0 Goal", "interviewer", "l0_to_l1", _check_l0),
        ("L1 Context", "code-explorer", "l1_to_l2", _check_l1),
        ("L2 Decisions", "interviewer", "l2_to_l3", _check_l2),
        ("L3 Requirements", "spec-writer", "l3_to_l4", _check_l3),
        ("L4 Tasks", "planner", "l4_to_l5", _check_l4),
        ("L5 Review", "reviewer", None, _check_l5),
    ]

    for label, agent, gate, checker in pipeline:
        print(f"\n[run] === {label} ({agent}) ===")

        agent_template = AGENT_DIR / f"{agent}.md"
        if not agent_template.exists():
            print(f"[run] WARN: agent template not found: {agent_template}")
            continue

        instruction = _build_instruction(agent_template, spec_file, label)
        print(instruction)
        print("[run] ↑ 위 지시를 Claude Code에 전달하세요")

        if gate:
            result = subprocess.run(
                ["so2x-cli", "spec", "check", str(spec_file), "--gate", gate],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print(
                    f"[run] GATE {gate} FAILED — "
                    "위 에이전트 지시로 spec.json을 보완한 후 다시 실행하세요"
                )
                print(result.stdout)
                sys.exit(1)
            print(f"[run] GATE {gate} PASSED")

    print(f"\n[run] specify complete: {spec_file}")


def cmd_execute(args: object) -> None:
    spec_file = Path(getattr(args, "file", "spec.json"))
    harness_dir = spec_file.parent / DEFAULT_HARNESS_DIR
    learning_file = spec_file.parent / DEFAULT_LEARNING_FILE

    if not spec_file.exists():
        print(f"[run] spec not found: {spec_file}")
        sys.exit(1)

    spec = json.loads(spec_file.read_text(encoding="utf-8"))
    tasks = spec.get("chain", {}).get("l4_tasks", [])
    pending = [t for t in tasks if t.get("status") != "done"]

    if not pending:
        print("[run] no pending tasks")
        persistence = persist_learning_bundle(
            build_auto_learning_bundle(spec),
            harness_dir=harness_dir,
            learning_file=learning_file,
        )
        _print_persistence_summary(persistence, harness_dir)
        return

    print(f"[run] executing {len(pending)} tasks from {spec_file}")

    for task in pending:
        tid = task.get("id", "?")
        action = task.get("action", "")
        req_refs = task.get("requirement_refs", [])

        print(f"\n[run] === {tid}: {action} ===")
        print(f"[run] Requirements: {', '.join(req_refs)}")
        print("[run] ↑ 이 태스크를 구현하고 관련 시나리오를 검증하세요")

        _update_task_status(spec_file, tid, "in_progress")
        print(f"[run] {tid} marked in_progress")

    verifier_template = AGENT_DIR / "verifier.md"
    if verifier_template.exists():
        print("\n[run] === Verification ===")
        instruction = _build_instruction(verifier_template, spec_file, "Verification")
        print(instruction)
        print("[run] ↑ 모든 시나리오를 독립적으로 검증하세요")

    result = subprocess.run(
        ["so2x-cli", "spec", "validate", str(spec_file)],
        capture_output=True,
        text=True,
    )
    print(result.stdout)

    refreshed_spec = json.loads(spec_file.read_text(encoding="utf-8"))
    persistence = persist_learning_bundle(
        build_auto_learning_bundle(refreshed_spec),
        harness_dir=harness_dir,
        learning_file=learning_file,
    )
    _print_persistence_summary(persistence, harness_dir)

    print(f"\n[run] execute complete: {spec_file}")


def cmd_status(args: object) -> None:
    harness_dir = (
        Path(getattr(args, "dir", "")) if getattr(args, "dir", None) else DEFAULT_HARNESS_DIR
    )
    status_dir = harness_dir / DEFAULT_STATUS_DIR.name
    simplify = read_status("simplify-cycle", status_dir)
    safe_commit = read_status("safe-commit", status_dir)
    squash = read_status("squash-commit", status_dir)

    print(f"[run] status dir: {status_dir}")
    if simplify:
        remaining = simplify.get("remaining_count")
        stop_reason = simplify.get("stop_reason")
        print(f"  simplify-cycle: remaining={remaining} stop_reason={stop_reason}")
    else:
        print("  simplify-cycle: missing")
    if safe_commit:
        verdict = safe_commit.get("safety_verdict")
        verification = safe_commit.get("verification_status")
        print(f"  safe-commit: verdict={verdict} verification={verification}")
    else:
        print("  safe-commit: missing")
    if squash:
        print(f"  squash-commit: ready={squash.get('ready')} reason={squash.get('reason')}")
    else:
        print("  squash-commit: missing")


def cmd_safe_commit(args: object) -> None:
    harness_dir = (
        Path(getattr(args, "dir", "")) if getattr(args, "dir", None) else DEFAULT_HARNESS_DIR
    )
    status_dir = harness_dir / DEFAULT_STATUS_DIR.name
    event_file = harness_dir / DEFAULT_EVENT_FILE.name
    simplify = read_status("simplify-cycle", status_dir)
    if not simplify:
        verdict = {
            "name": "safe-commit",
            "safety_verdict": "UNSAFE",
            "verification_status": "MISSING",
            "reason": "missing_simplify_cycle",
        }
        write_status("safe-commit", verdict, status_dir)
        append_event_entries(
            [
                {
                    "type": "safe_commit_completed",
                    "safety_verdict": "UNSAFE",
                    "verification_status": "MISSING",
                    "reason": "missing_simplify_cycle",
                }
            ],
            event_file,
        )
        print("[run] safe-commit FAIL: simplify-cycle status missing")
        sys.exit(1)

    remaining = int(simplify.get("remaining_count", 0) or 0)
    stop_reason = str(simplify.get("stop_reason", "")).strip()
    safe = remaining == 0 or stop_reason in _ALLOWED_SIMPLIFY_STOP_REASONS - {"converged_to_zero"}
    verdict = {
        "name": "safe-commit",
        "safety_verdict": "SAFE" if safe else "UNSAFE",
        "verification_status": simplify.get("verification_status", "UNKNOWN"),
        "remaining_count": remaining,
        "stop_reason": stop_reason,
        "reason": "ready_for_commit" if safe else "simplify_not_converged",
    }
    write_status("safe-commit", verdict, status_dir)
    append_event_entries(
        [
            {
                "type": "safe_commit_completed",
                "safety_verdict": verdict["safety_verdict"],
                "verification_status": verdict["verification_status"],
                "remaining_count": remaining,
                "stop_reason": stop_reason,
                "reason": verdict["reason"],
            }
        ],
        event_file,
    )
    if not safe:
        print(f"[run] safe-commit FAIL: remaining_count={remaining} stop_reason={stop_reason}")
        sys.exit(1)
    print(f"[run] safe-commit PASS: remaining_count={remaining} stop_reason={stop_reason}")


def cmd_squash_check(args: object) -> None:
    harness_dir = (
        Path(getattr(args, "dir", "")) if getattr(args, "dir", None) else DEFAULT_HARNESS_DIR
    )
    status_dir = harness_dir / DEFAULT_STATUS_DIR.name
    event_file = harness_dir / DEFAULT_EVENT_FILE.name
    simplify = read_status("simplify-cycle", status_dir)
    safe_commit = read_status("safe-commit", status_dir)

    if not simplify:
        snapshot = {"name": "squash-commit", "ready": False, "reason": "missing_simplify_cycle"}
        write_status("squash-commit", snapshot, status_dir)
        append_event_entries(
            [
                {
                    "type": "squash_check_completed",
                    "ready": False,
                    "reason": "missing_simplify_cycle",
                }
            ],
            event_file,
        )
        print("[run] squash-check FAIL: simplify-cycle status missing")
        sys.exit(1)
    if not safe_commit:
        snapshot = {"name": "squash-commit", "ready": False, "reason": "missing_safe_commit"}
        write_status("squash-commit", snapshot, status_dir)
        append_event_entries(
            [{"type": "squash_check_completed", "ready": False, "reason": "missing_safe_commit"}],
            event_file,
        )
        print("[run] squash-check FAIL: safe-commit status missing")
        sys.exit(1)

    remaining = int(simplify.get("remaining_count", 0) or 0)
    stop_reason = str(simplify.get("stop_reason", "")).strip()
    safe_verdict = str(safe_commit.get("safety_verdict", "")).strip()
    ready = (
        remaining == 0 or stop_reason in _ALLOWED_SIMPLIFY_STOP_REASONS - {"converged_to_zero"}
    ) and safe_verdict == "SAFE"
    reason = "ready" if ready else "preconditions_failed"
    snapshot = {
        "name": "squash-commit",
        "ready": ready,
        "reason": reason,
        "remaining_count": remaining,
        "stop_reason": stop_reason,
        "safe_commit_verdict": safe_verdict,
    }
    write_status("squash-commit", snapshot, status_dir)
    append_event_entries(
        [
            {
                "type": "squash_check_completed",
                "ready": ready,
                "reason": reason,
                "remaining_count": remaining,
                "stop_reason": stop_reason,
                "safe_commit_verdict": safe_verdict,
            }
        ],
        event_file,
    )
    if not ready:
        print(
            "[run] squash-check FAIL: "
            f"remaining_count={remaining} stop_reason={stop_reason} "
            f"safe_commit={safe_verdict}"
        )
        sys.exit(1)
    print(
        "[run] squash-check PASS: "
        f"safe_commit={safe_verdict} remaining_count={remaining} "
        f"stop_reason={stop_reason}"
    )


def _print_persistence_summary(persistence: dict[str, object], harness_dir: Path) -> None:
    added_learnings = persistence.get("learnings", [])
    added_events = persistence.get("events", [])
    promoted = persistence.get("promoted", [])
    statuses = persistence.get("statuses", [])
    print(f"[run] Auto-events captured: {len(added_events)} -> {harness_dir / 'events.jsonl'}")
    learnings_path = harness_dir / "learnings.jsonl"
    print(f"[run] Auto-learnings captured: {len(added_learnings)} -> {learnings_path}")
    print(f"[run] Promoted rules: {len(promoted)} -> {harness_dir / 'promoted-rules.json'}")
    if statuses:
        print(f"[run] Status snapshots updated: {len(statuses)}")


def _build_instruction(agent_template: Path, spec_file: Path, phase: str) -> str:
    template = agent_template.read_text(encoding="utf-8")
    parts = template.split("---", 2)
    content = parts[2].strip() if len(parts) >= 3 else template

    spec_summary = ""
    if spec_file.exists():
        spec = json.loads(spec_file.read_text(encoding="utf-8"))
        meta_json = json.dumps(spec.get("meta", {}), ensure_ascii=False, indent=2)
        spec_summary = f"\nCurrent spec.json status: {meta_json}"

    return f"[{phase}] 에이전트 지시:\n{content}\n\nSpec file: {spec_file}{spec_summary}"


def _update_task_status(
    spec_file: Path, task_id: str, status: str, summary: str | None = None
) -> None:
    spec = json.loads(spec_file.read_text(encoding="utf-8"))
    for task in spec.get("chain", {}).get("l4_tasks", []):
        if task.get("id") == task_id:
            task["status"] = status
            if summary is not None:
                task["summary"] = summary
    spec["meta"]["updated_at"] = _now_iso()
    spec_file.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _check_l0(spec: dict) -> tuple[bool, list[str]]:
    errors = []
    if not spec.get("chain", {}).get("l0_goal"):
        errors.append("Goal is empty")
    return len(errors) == 0, errors


def _check_l1(spec: dict) -> tuple[bool, list[str]]:
    return bool(spec.get("chain", {}).get("l1_context")), []


def _check_l2(spec: dict) -> tuple[bool, list[str]]:
    decisions = spec.get("chain", {}).get("l2_decisions", [])
    return len(decisions) > 0, [] if decisions else ["No decisions"]


def _check_l3(spec: dict) -> tuple[bool, list[str]]:
    reqs = spec.get("chain", {}).get("l3_requirements", [])
    return len(reqs) > 0, [] if reqs else ["No requirements"]


def _check_l4(spec: dict) -> tuple[bool, list[str]]:
    tasks = spec.get("chain", {}).get("l4_tasks", [])
    return len(tasks) > 0, [] if tasks else ["No tasks"]


def _check_l5(spec: dict) -> tuple[bool, list[str]]:
    review = spec.get("chain", {}).get("l5_review", {})
    review_passed = review.get("status") == "pass"
    return review_passed, [] if review_passed else ["Review not passed"]


def _now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()
