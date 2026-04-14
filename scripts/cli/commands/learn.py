from __future__ import annotations

import argparse
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent


def handle_learn(args: argparse.Namespace) -> None:
    if args.learn_command == "add":
        cmd_add(args)
    elif args.learn_command == "search":
        cmd_search(args)
    elif args.learn_command == "sync":
        cmd_sync(args)
    elif args.learn_command == "summary":
        cmd_summary(args)
    else:
        print("Usage: so2x-cli learn {add|search|sync|summary}")


def cmd_add(args: argparse.Namespace) -> None:
    entry = {
        "id": f"LRN-{uuid.uuid4().hex[:6].upper()}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_project": args.project or "unknown",
        "source_spec": args.spec or "",
        "category": args.category or "pattern",
        "problem": args.problem,
        "cause": args.cause or "",
        "rule": args.rule,
        "tags": (args.tags or "").split(",") if args.tags else [],
        "severity": args.severity or "info",
    }

    # Write to local
    local_path = Path(args.file) if args.file else Path("learnings.jsonl")
    _append_entry(local_path, entry)

    # Write to central
    central_path = ROOT_DIR / "learnings" / "entries.jsonl"
    if central_path.parent.exists():
        _append_entry(central_path, entry)

    print(f"[learn] added {entry['id']} to {local_path}")


def cmd_search(args: argparse.Namespace) -> None:
    query = args.query.lower()
    paths = _resolve_paths(args)

    results = []
    for path in paths:
        for entry in _read_entries(path):
            text = _entry_text(entry).lower()
            if query in text or any(query in t.lower() for t in entry.get("tags", [])):
                results.append(entry)

    if not results:
        print(f"[learn] no results for '{query}'")
        return

    for entry in results:
        print(f"[{entry['id']}] [{entry.get('category', '?')}] {entry.get('problem', '')[:80]}")
        print(f"  Rule: {entry.get('rule', '')[:80]}")
        print(f"  Tags: {', '.join(entry.get('tags', []))}")
        print()


def cmd_sync(args: argparse.Namespace) -> None:
    project_dir = Path(args.project) if args.project else Path(".")
    local_path = project_dir / ".ai-harness" / "learnings.jsonl"
    central_path = ROOT_DIR / "learnings" / "entries.jsonl"

    if not local_path.exists():
        print(f"[learn] no local learnings at {local_path}")
        return

    central_ids = set()
    if central_path.exists():
        for e in _read_entries(central_path):
            central_ids.add(e.get("id"))

    synced = 0
    for entry in _read_entries(local_path):
        if entry.get("id") not in central_ids:
            _append_entry(central_path, entry)
            synced += 1

    print(f"[learn] synced {synced} entries to {central_path}")


def cmd_summary(args: argparse.Namespace) -> None:
    paths = _resolve_paths(args)

    categories: dict[str, int] = {}
    projects: set[str] = set()
    total = 0

    for path in paths:
        for entry in _read_entries(path):
            total += 1
            cat = entry.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1
            proj = entry.get("source_project", "")
            if proj:
                projects.add(proj)

    print(f"[learn] summary:")
    print(f"  Total entries: {total}")
    print(f"  Projects: {', '.join(sorted(projects)) or 'none'}")
    print(f"  Categories:")
    for cat, count in sorted(categories.items()):
        print(f"    {cat}: {count}")


def _resolve_paths(args: argparse.Namespace) -> list[Path]:
    paths = []
    central = ROOT_DIR / "learnings" / "entries.jsonl"
    if central.exists():
        paths.append(central)
    local = Path(".ai-harness/learnings.jsonl")
    if local.exists() and local not in paths:
        paths.append(local)
    if hasattr(args, "file") and args.file:
        p = Path(args.file)
        if p.exists() and p not in paths:
            paths.append(p)
    return paths


def _append_entry(path: Path, entry: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _read_entries(path: Path) -> list[dict]:
    if not path.exists():
        return []
    entries = []
    for line in path.read_text(encoding="utf-8").strip().split("\n"):
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries


def _entry_text(entry: dict) -> str:
    parts = [entry.get("problem", ""), entry.get("cause", ""), entry.get("rule", "")]
    return " ".join(parts)
