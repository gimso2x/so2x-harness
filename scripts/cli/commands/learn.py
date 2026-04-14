from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_PATH = Path(".ai-harness/learnings.jsonl")


def handle_learn(args: object) -> None:
    command = getattr(args, "learn_command", None)
    if command == "add":
        cmd_add(args)
    elif command == "search":
        cmd_search(args)
    elif command == "summary":
        cmd_summary(args)
    else:
        print("Usage: so2x-cli learn {add|search|summary}")


def cmd_add(args: object) -> None:
    entry = {
        "id": f"LRN-{uuid.uuid4().hex[:6].upper()}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_spec": getattr(args, "spec", "") or "",
        "category": getattr(args, "category", "pattern") or "pattern",
        "problem": getattr(args, "problem", ""),
        "cause": getattr(args, "cause", "") or "",
        "rule": getattr(args, "rule", ""),
        "tags": (getattr(args, "tags", "") or "").split(",") if getattr(args, "tags", None) else [],
        "severity": getattr(args, "severity", "info") or "info",
    }

    path = Path(getattr(args, "file", "")) if getattr(args, "file", None) else DEFAULT_PATH
    _append_entry(path, entry)
    print(f"[learn] added {entry['id']} to {path}")


def cmd_search(args: object) -> None:
    query = getattr(args, "query", "").lower()
    path = Path(getattr(args, "file", "")) if getattr(args, "file", None) else DEFAULT_PATH

    results = []
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


def cmd_summary(args: object) -> None:
    path = Path(getattr(args, "file", "")) if getattr(args, "file", None) else DEFAULT_PATH

    categories: dict[str, int] = {}
    total = 0

    for entry in _read_entries(path):
        total += 1
        cat = entry.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1

    print(f"[learn] summary ({path}):")
    print(f"  Total entries: {total}")
    for cat, count in sorted(categories.items()):
        print(f"    {cat}: {count}")


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
    return " ".join([entry.get("problem", ""), entry.get("cause", ""), entry.get("rule", "")])
