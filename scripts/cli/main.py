from __future__ import annotations

import argparse
import sys


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

    guide_p = spec_sub.add_parser("guide", help="Show layer field structure")
    guide_p.add_argument("layer", help="Layer name (e.g. l3_requirements)")

    # learn subcommand
    learn_parser = subparsers.add_parser("learn", help="Manage learnings")
    learn_sub = learn_parser.add_subparsers(dest="learn_command")

    add_p = learn_sub.add_parser("add", help="Record a learning")
    add_p.add_argument("--problem", required=True, help="What went wrong or was discovered")
    add_p.add_argument("--cause", help="Root cause")
    add_p.add_argument("--rule", required=True, help="Rule to follow next time")
    add_p.add_argument("--category", default="pattern", help="pattern|anti-pattern|edge-case|decision")
    add_p.add_argument("--tags", help="Comma-separated tags")
    add_p.add_argument("--severity", default="info", help="info|warning|critical")
    add_p.add_argument("--project", help="Source project name")
    add_p.add_argument("--spec", help="Source spec ID")
    add_p.add_argument("--file", help="Output JSONL file path")

    search_p = learn_sub.add_parser("search", help="Search learnings")
    search_p.add_argument("query", help="Search query")
    search_p.add_argument("--file", help="JSONL file to search")

    sync_p = learn_sub.add_parser("sync", help="Sync local learnings to central")
    sync_p.add_argument("--project", default=".", help="Project directory")

    summary_p = learn_sub.add_parser("summary", help="Show learning summary")
    summary_p.add_argument("--file", help="JSONL file to summarize")

    args = parser.parse_args()

    if args.version:
        print("so2x-cli 0.3.0")
        return

    if args.command == "spec":
        from cli.commands.spec import handle_spec

        handle_spec(args)
    elif args.command == "learn":
        from cli.commands.learn import handle_learn

        handle_learn(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
