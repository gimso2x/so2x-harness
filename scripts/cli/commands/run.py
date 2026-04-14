from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parent.parent.parent.parent / "templates/claude/agents"


def handle_run(args: object) -> None:
    command = getattr(args, "run_command", None)
    if command == "specify":
        cmd_specify(args)
    elif command == "execute":
        cmd_execute(args)
    else:
        print("Usage: so2x-cli run {specify|execute}")


def cmd_specify(args: object) -> None:
    goal = getattr(args, "goal", "")
    spec_file = Path(getattr(args, "output", "spec.json"))

    print(f"[run] specifying: {goal}")

    # Step 0: Init spec
    subprocess.run(
        ["so2x-cli", "spec", "init", goal, "--output", str(spec_file)],
        check=True,
    )

    # Pipeline: each step loads agent template, outputs instruction, checks gate
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

        # Check gate
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

    if not spec_file.exists():
        print(f"[run] spec not found: {spec_file}")
        sys.exit(1)

    spec = json.loads(spec_file.read_text(encoding="utf-8"))
    tasks = spec.get("chain", {}).get("l4_tasks", [])
    pending = [t for t in tasks if t.get("status") != "done"]

    if not pending:
        print("[run] no pending tasks")
        return

    print(f"[run] executing {len(pending)} tasks from {spec_file}")

    for task in pending:
        tid = task.get("id", "?")
        action = task.get("action", "")
        req_refs = task.get("requirement_refs", [])

        print(f"\n[run] === {tid}: {action} ===")
        print(f"[run] Requirements: {', '.join(req_refs)}")
        print("[run] ↑ 이 태스크를 구현하고 관련 시나리오를 검증하세요")

        # Mark task as in_progress
        _update_task_status(spec_file, tid, "in_progress")
        print(f"[run] {tid} marked in_progress")

    # Verifier step
    verifier_template = AGENT_DIR / "verifier.md"
    if verifier_template.exists():
        print("\n[run] === Verification ===")
        instruction = _build_instruction(verifier_template, spec_file, "Verification")
        print(instruction)
        print("[run] ↑ 모든 시나리오를 독립적으로 검증하세요")

    # Final validation
    result = subprocess.run(
        ["so2x-cli", "spec", "validate", str(spec_file)],
        capture_output=True,
        text=True,
    )
    print(result.stdout)

    print(f"\n[run] execute complete: {spec_file}")


def _build_instruction(agent_template: Path, spec_file: Path, phase: str) -> str:
    template = agent_template.read_text(encoding="utf-8")

    # Extract content after frontmatter
    parts = template.split("---", 2)
    content = parts[2].strip() if len(parts) >= 3 else template

    spec_summary = ""
    if spec_file.exists():
        spec = json.loads(spec_file.read_text(encoding="utf-8"))
        meta_json = json.dumps(spec.get("meta", {}), ensure_ascii=False, indent=2)
        spec_summary = f"\nCurrent spec.json status: {meta_json}"

    return f"[{phase}] 에이전트 지시:\n{content}\n\nSpec file: {spec_file}{spec_summary}"


def _update_task_status(spec_file: Path, task_id: str, status: str) -> None:
    spec = json.loads(spec_file.read_text(encoding="utf-8"))
    for task in spec.get("chain", {}).get("l4_tasks", []):
        if task.get("id") == task_id:
            task["status"] = status
    spec["meta"]["updated_at"] = datetime.now(timezone.utc).isoformat()
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
