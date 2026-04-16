from __future__ import annotations

import argparse
import sys
from importlib import metadata
from pathlib import Path

PACKAGE_NAME = "so2x-harness"
PROGRAM_NAME = "so2x"
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=PROGRAM_NAME, description="Thin per-project harness CLI")
    parser.add_argument("--version", action="store_true", help="Show version")
    subparsers = parser.add_subparsers(dest="command")

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
    set_status_p.add_argument(
        "--status",
        required=True,
        choices=["pending", "in_progress", "blocked", "error", "done"],
    )
    set_status_p.add_argument("--summary")
    set_status_p.add_argument("--last-error")

    validate_p = subparsers.add_parser("validate", help="Validate lite spec")
    validate_p.add_argument("--file", default="spec.json", help="Spec file path")

    run_p = subparsers.add_parser("run", help="Run a task")
    run_p.add_argument("--file", default="spec.json", help="Spec file path")
    target = run_p.add_mutually_exclusive_group(required=True)
    target.add_argument("--task")
    target.add_argument("--next", action="store_true")

    doctor_p = subparsers.add_parser("doctor", help="Read-only project status surface")
    doctor_p.add_argument("--project", default=".", help="Project directory")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.version:
        print(f"{PROGRAM_NAME} {get_version()}")
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
    if args.command == "run":
        from cli.commands.run import cmd_run

        cmd_run(args)
        return
    if args.command == "doctor":
        from doctor import main as doctor_main

        sys.argv = [sys.argv[0], "--project", args.project]
        doctor_main()
        return

    parser.print_help()
    raise SystemExit(1)


if __name__ == "__main__":
    main()
