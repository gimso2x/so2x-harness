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

    args = parser.parse_args()

    if args.version:
        print("so2x-cli 0.2.0")
        return

    if args.command == "spec":
        from cli.commands.spec import handle_spec

        handle_spec(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
