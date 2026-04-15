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
    parser = argparse.ArgumentParser(
        prog="so2x-cli",
        description="CLI tool for so2x-harness spec engine",
    )
    parser.add_argument("--version", action="store_true", help="Show version")

    subparsers = parser.add_subparsers(dest="command")

    spec_parser = subparsers.add_parser("spec", help="Manage spec.json files")
    spec_sub = spec_parser.add_subparsers(dest="spec_command")

    init_p = spec_sub.add_parser("init", help="Create a new spec.json")
    init_p.add_argument("goal", help="Goal description")
    init_p.add_argument("--id", help="Spec ID (e.g. SPEC-AUTH-001). Auto-generated if omitted")
    init_p.add_argument("--output", default="spec.json", help="Output file path")

    check_p = spec_sub.add_parser("check", help="Check gate status")
    check_p.add_argument("file", help="Path to spec.json")
    check_p.add_argument(
        "--gate", help="Specific gate to check (e.g. l0_to_l1). 'all' for all gates"
    )

    validate_p = spec_sub.add_parser("validate", help="Validate spec.json structure")
    validate_p.add_argument("file", help="Path to spec.json")

    status_p = spec_sub.add_parser("status", help="Show derivation status")
    status_p.add_argument("file", help="Path to spec.json")

    set_task_status_p = spec_sub.add_parser(
        "set-task-status", help="Update a task status and optional summary"
    )
    set_task_status_p.add_argument("file", help="Path to spec.json")
    set_task_status_p.add_argument("--task-id", required=True, help="Task ID (e.g. T1)")
    set_task_status_p.add_argument(
        "--status", required=True, choices=["pending", "in_progress", "blocked", "done"]
    )
    set_task_status_p.add_argument("--summary", help="Latest task summary")

    guide_p = spec_sub.add_parser("guide", help="Show layer field structure")
    guide_p.add_argument("layer", help="Layer name (e.g. l3_requirements)")

    # learn subcommand
    learn_parser = subparsers.add_parser("learn", help="Manage learnings")
    learn_sub = learn_parser.add_subparsers(dest="learn_command")

    add_p = learn_sub.add_parser("add", help="Record a learning")
    add_p.add_argument("--problem", required=True, help="What went wrong or was discovered")
    add_p.add_argument("--cause", help="Root cause")
    add_p.add_argument("--rule", required=True, help="Rule to follow next time")
    add_p.add_argument(
        "--category",
        default="pattern",
        help="pattern|anti-pattern|edge-case|decision",
    )
    add_p.add_argument("--tags", help="Comma-separated tags")
    add_p.add_argument("--severity", default="info", help="info|warning|critical")
    add_p.add_argument("--spec", help="Source spec ID")
    add_p.add_argument("--file", help="Output JSONL file path")

    search_p = learn_sub.add_parser("search", help="Search learnings")
    search_p.add_argument("query", help="Search query")
    search_p.add_argument("--file", help="JSONL file to search")

    summary_p = learn_sub.add_parser("summary", help="Show learning summary")
    summary_p.add_argument("--file", help="JSONL file to summarize")

    feedback_p = learn_sub.add_parser(
        "feedback", help="Capture user feedback as events + learnings"
    )
    feedback_p.add_argument("message", help="Raw user feedback message")
    feedback_p.add_argument(
        "--phase", default="general", help="specify|execute|review|simplify|commit|general"
    )
    feedback_p.add_argument("--spec", help="Source spec ID")
    feedback_p.add_argument("--dir", help="Harness directory (defaults to .ai-harness)")

    # run subcommand
    run_parser = subparsers.add_parser("run", help="Run agent pipeline")
    run_sub = run_parser.add_subparsers(dest="run_command")

    specify_p = run_sub.add_parser("specify", help="Run specify pipeline")
    specify_p.add_argument("goal", help="Goal description")
    specify_p.add_argument("--output", default="spec.json", help="Output spec file")

    execute_p = run_sub.add_parser("execute", help="Run execute pipeline")
    execute_p.add_argument("--file", default="spec.json", help="Spec file to execute")

    status_run_p = run_sub.add_parser("status", help="Show simplify/safe/squash status snapshots")
    status_run_p.add_argument("--dir", help="Harness directory (defaults to .ai-harness)")

    safe_commit_p = run_sub.add_parser(
        "safe-commit", help="Evaluate safe-commit preconditions from simplify status"
    )
    safe_commit_p.add_argument("--dir", help="Harness directory (defaults to .ai-harness)")

    squash_check_p = run_sub.add_parser(
        "squash-check", help="Evaluate squash preconditions from simplify/safe statuses"
    )
    squash_check_p.add_argument("--dir", help="Harness directory (defaults to .ai-harness)")

    args = parser.parse_args()

    if args.version:
        print(f"so2x-cli {get_version()}")
        return

    if args.command == "spec":
        from cli.commands.spec import handle_spec

        handle_spec(args)
    elif args.command == "learn":
        from cli.commands.learn import handle_learn

        handle_learn(args)
    elif args.command == "run":
        from cli.commands.run import handle_run

        handle_run(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
