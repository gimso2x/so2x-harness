from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
SCHEMA_PATH = ROOT_DIR / "schemas" / "spec.schema.json"


def handle_spec(args: argparse.Namespace) -> None:
    if args.spec_command == "init":
        cmd_init(args)
    elif args.spec_command == "check":
        cmd_check(args)
    elif args.spec_command == "validate":
        cmd_validate(args)
    elif args.spec_command == "status":
        cmd_status(args)
    elif args.spec_command == "set-task-status":
        cmd_set_task_status(args)
    elif args.spec_command == "guide":
        cmd_guide(args)
    else:
        print("Usage: so2x-cli spec {init|check|validate|status|guide}")


def cmd_init(args: argparse.Namespace) -> None:
    spec_id = args.id or _generate_id(args.goal)
    now = datetime.now(timezone.utc).isoformat()

    spec = {
        "meta": {
            "id": spec_id,
            "goal": args.goal,
            "status": "draft",
            "mode": "standard",
            "created_at": now,
            "updated_at": now,
        },
        "chain": {"l0_goal": args.goal},
        "gates": {
            "l0_to_l1": {"status": "pending"},
            "l1_to_l2": {"status": "pending"},
            "l2_to_l3": {"status": "pending"},
            "l3_to_l4": {"status": "pending"},
            "l4_to_l5": {"status": "pending"},
        },
    }

    output = Path(args.output)
    output.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[so2x-cli] created {output} (id={spec_id})")


def cmd_check(args: argparse.Namespace) -> None:
    spec = _load_spec(args.file)
    gate = args.gate

    if gate == "all" or gate is None:
        gates = ["l0_to_l1", "l1_to_l2", "l2_to_l3", "l3_to_l4", "l4_to_l5"]
    else:
        gates = [gate]

    any_fail = False
    for g in gates:
        passed, errors = check_gate(spec, g)
        if passed:
            print(f"[{g}] PASS")
        else:
            print(f"[{g}] FAIL")
            for e in errors:
                print(f"  - {e}")
            any_fail = True

    if any_fail:
        raise SystemExit(1)


def cmd_validate(args: argparse.Namespace) -> None:
    spec = _load_spec(args.file)
    errors = validate_spec(spec)
    if errors:
        print("[validate] FAIL")
        for e in errors:
            print(f"  - {e}")
        raise SystemExit(1)
    print("[validate] PASS")


def cmd_status(args: argparse.Namespace) -> None:
    spec = _load_spec(args.file)
    meta = spec.get("meta", {})
    chain = spec.get("chain", {})
    gates = spec.get("gates", {})

    print(f"ID:     {meta.get('id', '?')}")
    print(f"Goal:   {meta.get('goal', '?')}")
    print(f"Status: {meta.get('status', '?')}")
    print()
    print("Chain:")

    layers = [
        ("L0 Goal", "l0_goal", lambda v: "defined" if v else "empty"),
        (
            "L1 Context",
            "l1_context",
            lambda v: f"{len(v.get('assumptions', []))} assumptions" if v else "empty",
        ),
        (
            "L2 Decisions",
            "l2_decisions",
            lambda v: f"{len(v)} decisions" if v else "empty",
        ),
        (
            "L3 Requirements",
            "l3_requirements",
            lambda v: f"{len(v)} requirements" if v else "empty",
        ),
        ("L4 Tasks", "l4_tasks", lambda v: f"{len(v)} tasks" if v else "empty"),
        (
            "L5 Review",
            "l5_review",
            lambda v: v.get("status", "pending") if v else "empty",
        ),
    ]

    for label, key, fmt in layers:
        value = chain.get(key)
        print(f"  {label}: {fmt(value)}")

    print()
    print("Gates:")
    for g in ["l0_to_l1", "l1_to_l2", "l2_to_l3", "l3_to_l4", "l4_to_l5"]:
        status = gates.get(g, {}).get("status", "pending")
        print(f"  {g}: {status}")


def cmd_set_task_status(args: argparse.Namespace) -> None:
    spec = _load_spec(args.file)
    updated = False

    for task in spec.get("chain", {}).get("l4_tasks", []):
        if task.get("id") == args.task_id:
            task["status"] = args.status
            if args.summary is not None:
                task["summary"] = args.summary
            updated = True
            break

    if not updated:
        raise SystemExit(f"task not found: {args.task_id}")

    spec.setdefault("meta", {})["updated_at"] = datetime.now(timezone.utc).isoformat()
    spec_path = Path(args.file)
    spec_path.write_text(
        json.dumps(spec, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"[spec] updated {args.task_id} -> {args.status}")


def cmd_guide(args: argparse.Namespace) -> None:
    guides = {
        "l0_goal": "String. What to build, in one sentence.",
        "l1_context": (
            "Object with:\n"
            "  research: string - codebase analysis findings\n"
            "  assumptions: string[] - assumptions made\n"
            "  constraints: string[] - known constraints\n"
            "  patterns: string[] - detected patterns"
        ),
        "l2_decisions": (
            "Array of objects:\n"
            "  id: string (D1, D2, ...)\n"
            "  decision: string - what was decided\n"
            "  rationale: string - why\n"
            "  alternatives: string[] - what was considered"
        ),
        "l3_requirements": (
            "Array of objects:\n"
            "  id: string (R1, R2, ...)\n"
            "  behavior: string - what the system must do\n"
            "  scenarios: array of {given, when, then, verified_by, verify?}"
        ),
        "l4_tasks": (
            "Array of objects:\n"
            "  id: string (T1, T2, ...)\n"
            "  action: string - what to implement\n"
            "  requirement_refs: string[] (R1, R2, ...) - traceability\n"
            "  acceptance_criteria?: string\n"
            "  status?: pending | in_progress | done"
        ),
        "l5_review": (
            "Object:\n"
            "  status: pending | pass | needs_changes\n"
            "  reviewer: string\n"
            "  findings: array of {severity, message, location}"
        ),
    }

    layer = args.layer
    if layer in guides:
        print(f"[{layer}]")
        print(guides[layer])
    else:
        print(f"Unknown layer: {layer}")
        print(f"Available: {', '.join(guides.keys())}")


def _load_spec(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        raise SystemExit(f"file not found: {path}")
    return json.loads(p.read_text(encoding="utf-8"))


def _generate_id(goal: str) -> str:
    words = re.findall(r"[A-Za-z]+", goal)
    prefix = "".join(w[:3].upper() for w in words[:2]) if len(words) >= 2 else "SPEC"
    return f"SPEC-{prefix}-001"


def check_gate(spec: dict, gate: str) -> tuple[bool, list[str]]:
    chain = spec.get("chain", {})
    errors: list[str] = []

    if gate == "l0_to_l1":
        if not chain.get("l0_goal"):
            errors.append("L0: goal is empty")
        if not chain.get("l1_context"):
            errors.append("L1: context not derived yet")

    elif gate == "l1_to_l2":
        if not chain.get("l1_context"):
            errors.append("L1: context is empty")
        decisions = chain.get("l2_decisions", [])
        if not decisions:
            errors.append("L2: no decisions derived")
        for i, d in enumerate(decisions):
            if not d.get("rationale"):
                errors.append(f"L2: D{i + 1} missing rationale")

    elif gate == "l2_to_l3":
        decisions = chain.get("l2_decisions", [])
        if not decisions:
            errors.append("L2: no decisions")
        requirements = chain.get("l3_requirements", [])
        if not requirements:
            errors.append("L3: no requirements derived")
        for r in requirements:
            if not r.get("scenarios"):
                errors.append(f"L3: {r.get('id', '?')} has no scenarios")

    elif gate == "l3_to_l4":
        requirements = chain.get("l3_requirements", [])
        if not requirements:
            errors.append("L3: no requirements")
        tasks = chain.get("l4_tasks", [])
        if not tasks:
            errors.append("L4: no tasks derived")
        req_ids = {r.get("id") for r in requirements}
        covered = set()
        for t in tasks:
            for ref in t.get("requirement_refs", []):
                covered.add(ref)
        uncovered = req_ids - covered
        if uncovered:
            errors.append(f"L4: requirements not covered by tasks: {sorted(uncovered)}")

    elif gate == "l4_to_l5":
        tasks = chain.get("l4_tasks", [])
        if not tasks:
            errors.append("L4: no tasks")
        review = chain.get("l5_review")
        if not review or review.get("status") == "pending":
            errors.append("L5: review not completed")

    else:
        errors.append(f"unknown gate: {gate}")

    return len(errors) == 0, errors


def validate_spec(spec: dict) -> list[str]:
    errors: list[str] = []

    if "meta" not in spec:
        errors.append("missing 'meta' section")
    else:
        meta = spec["meta"]
        for field in ["id", "goal", "status", "created_at"]:
            if not meta.get(field):
                errors.append(f"meta.{field} is required")

    if "chain" not in spec:
        errors.append("missing 'chain' section")
    else:
        if not spec["chain"].get("l0_goal"):
            errors.append("chain.l0_goal is required")

    if "gates" not in spec:
        errors.append("missing 'gates' section")

    # Validate requirements have scenarios
    for r in spec.get("chain", {}).get("l3_requirements", []):
        if not r.get("scenarios"):
            errors.append(f"{r.get('id', '?')}: missing scenarios")

    # Validate tasks trace to requirements
    req_ids = {r.get("id") for r in spec.get("chain", {}).get("l3_requirements", [])}
    for t in spec.get("chain", {}).get("l4_tasks", []):
        for ref in t.get("requirement_refs", []):
            if ref not in req_ids:
                errors.append(f"{t.get('id', '?')}: references unknown requirement {ref}")

    return errors
