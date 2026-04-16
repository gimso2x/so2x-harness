from __future__ import annotations

import argparse
import sys
from importlib import metadata
from pathlib import Path

PACKAGE_NAME = "so2x-cli"
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
SCRIPTS_DIR = ROOT_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def get_version(root_dir: Path | None = None) -> str:
    version_root = root_dir or ROOT_DIR
    version_file = version_root / "VERSION"
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()
    return metadata.version(PACKAGE_NAME)


def main() -> None:
    parser = argparse.ArgumentParser(prog="so2x-cli", description="Thin per-project harness CLI")
    parser.add_argument("--version", action="store_true", help="Show version")
    subparsers = parser.add_subparsers(dest="command")

    # new thin top-level commands
    init_p = subparsers.add_parser("init", help="Create minimal spec.json")
    init_p.add_argument("--goal", required=True, help="Project goal")
    init_p.add_argument("--file", default="spec.json", help="Spec file path")
    init_p.add_argument("--spec-id", help="Optional spec id")

    status_p = subparsers.add_parser("status", help="Show spec status")
    status_p.add_argument("--file", default="spec.json", help="Spec file path")

    next_p = subparsers.add_parser("next", help="Show next runnable task")
    next_p.add_argument("--file", default="spec.json", help="Spec file path")

    set_status_p = subparsers.add_parser("set-status", help="Update task status")
    set_status_p.add_argument("--file", default="spec.json", help="Spec file path")
    set_status_p.add_argument("--task-id", required=True)
    set_status_p.add_argument("--status", required=True, choices=["pending", "in_progress", "blocked", "error", "done"])
    set_status_p.add_argument("--summary")
    set_status_p.add_argument("--last-error")

    validate_p = subparsers.add_parser("validate", help="Validate lite spec")
    validate_p.add_argument("--file", default="spec.json", help="Spec file path")

    doctor_p = subparsers.add_parser("doctor", help="Read-only project status surface")
    doctor_p.add_argument("--project", default=".", help="Project directory")

    # compatibility: spec
    spec_parser = subparsers.add_parser("spec", help="Manage spec.json files")
    spec_sub = spec_parser.add_subparsers(dest="spec_command")
    spec_init = spec_sub.add_parser("init", help="Create a new spec.json")
    spec_init.add_argument("goal")
    spec_init.add_argument("--id")
    spec_init.add_argument("--output", default="spec.json")
    spec_status = spec_sub.add_parser("status", help="Show derivation status")
    spec_status.add_argument("file")
    spec_next = spec_sub.add_parser("next", help="Show next runnable task")
    spec_next.add_argument("file")
    spec_set = spec_sub.add_parser("set-task-status", help="Update a task status and optional summary")
    spec_set.add_argument("file")
    spec_set.add_argument("--task-id", required=True)
    spec_set.add_argument("--status", required=True, choices=["pending", "in_progress", "blocked", "error", "done"])
    spec_set.add_argument("--summary")
    spec_set.add_argument("--last-error")
    spec_validate = spec_sub.add_parser("validate", help="Validate spec.json structure")
    spec_validate.add_argument("file")
    spec_check = spec_sub.add_parser("check", help="Compatibility no-op validator")
    spec_check.add_argument("file")
    spec_check.add_argument("--gate")
    spec_guide = spec_sub.add_parser("guide", help="Show thin spec guidance")
    spec_guide.add_argument("layer")

    # compatibility: learn
    learn_parser = subparsers.add_parser("learn", help="Manage learnings")
    learn_sub = learn_parser.add_subparsers(dest="learn_command")
    add_p = learn_sub.add_parser("add")
    add_p.add_argument("--problem", required=True)
    add_p.add_argument("--cause")
    add_p.add_argument("--rule", required=True)
    add_p.add_argument("--category", default="pattern")
    add_p.add_argument("--tags")
    add_p.add_argument("--severity", default="info")
    add_p.add_argument("--spec")
    add_p.add_argument("--file")
    search_p = learn_sub.add_parser("search")
    search_p.add_argument("query")
    search_p.add_argument("--file")
    summary_p = learn_sub.add_parser("summary")
    summary_p.add_argument("--file")
    feedback_p = learn_sub.add_parser("feedback")
    feedback_p.add_argument("message")
    feedback_p.add_argument("--phase", default="general")
    feedback_p.add_argument("--spec")
    feedback_p.add_argument("--dir")

    # compatibility: skills
    skills_parser = subparsers.add_parser("skills", help="Inspect and promote recommended skills")
    skills_sub = skills_parser.add_subparsers(dest="skills_command")
    recommend_p = skills_sub.add_parser("recommend")
    recommend_p.add_argument("--project", default=".")
    enable_p = skills_sub.add_parser("enable")
    enable_p.add_argument("skills", nargs="+")
    enable_p.add_argument("--project", default=".")

    # run command supports thin and legacy surfaces
    run_parser = subparsers.add_parser("run", help="Run task or workflow")
    run_sub = run_parser.add_subparsers(dest="run_command")
    run_task = run_sub.add_parser("task", help="Run selected task")
    run_task.add_argument("--file", default="spec.json")
    run_target = run_task.add_mutually_exclusive_group(required=True)
    run_target.add_argument("--task")
    run_target.add_argument("--next", action="store_true")
    run_task.set_defaults(run_command="task")
    run_specify = run_sub.add_parser("specify")
    run_specify.add_argument("goal")
    run_specify.add_argument("--output", default="spec.json")
    run_execute = run_sub.add_parser("execute")
    run_execute.add_argument("--file", default="spec.json")
    run_status = run_sub.add_parser("status")
    run_status.add_argument("--dir")
    run_safe = run_sub.add_parser("safe-commit")
    run_safe.add_argument("--dir")
    run_squash = run_sub.add_parser("squash-check")
    run_squash.add_argument("--dir")

    # direct thin run shorthand: so2x-cli run --file ... --next
    run_parser.add_argument("--file", help=argparse.SUPPRESS)
    run_parser.add_argument("--task", help=argparse.SUPPRESS)
    run_parser.add_argument("--next", action="store_true", help=argparse.SUPPRESS)

    args = parser.parse_args()
    if args.version:
        print(f"so2x-cli {get_version()}")
        return

    if args.command == "init":
        from cli.commands.spec import cmd_init
        cmd_init(args)
        return
    if args.command == "status":
        from cli.commands.spec import cmd_status
        cmd_status(args)
        return
    if args.command == "next":
        from cli.commands.spec import cmd_next
        cmd_next(args)
        return
    if args.command == "set-status":
        from cli.commands.spec import cmd_set_status
        cmd_set_status(args)
        return
    if args.command == "validate":
        from cli.commands.spec import cmd_validate
        cmd_validate(args)
        return
    if args.command == "doctor":
        from doctor import main as doctor_main
        sys.argv = [sys.argv[0], "--project", args.project]
        doctor_main()
        return
    if args.command == "spec":
        from cli.commands.spec import handle_spec
        handle_spec(args)
        return
    if args.command == "learn":
        from cli.commands.learn import handle_learn
        handle_learn(args)
        return
    if args.command == "skills":
        from cli.commands.skills import handle_skills
        handle_skills(args)
        return
    if args.command == "run":
        if getattr(args, "run_command", None) is None and (getattr(args, "task", None) or getattr(args, "next", False)):
            args.run_command = "task"
        from cli.commands.run import handle_run
        handle_run(args)
        return

    parser.print_help()
    raise SystemExit(1)


if __name__ == "__main__":
    main()
