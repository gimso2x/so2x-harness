from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from cli.commands.learning_tools import (
    DEFAULT_EVENT_FILE,
    DEFAULT_HARNESS_DIR,
    DEFAULT_LEARNING_FILE,
    DEFAULT_PROMOTED_RULES_FILE,
    append_event_entries,
    append_learning_entries,
    promote_feedback_patterns,
)

DEFAULT_PATH = Path(".ai-harness/learnings.jsonl")


_FEEDBACK_PATTERNS = {
    "reject": ["아닌", "별로", "다시", "말고"],
    "refine": ["너무 복잡", "합쳐", "줄여", "단순"],
    "preference": ["다음엔", "이렇게", "남겨", "유지"],
}


def handle_learn(args: object) -> None:
    command = getattr(args, "learn_command", None)
    if command == "add":
        cmd_add(args)
    elif command == "search":
        cmd_search(args)
    elif command == "summary":
        cmd_summary(args)
    elif command == "feedback":
        cmd_feedback(args)
    else:
        print("Usage: so2x-cli learn {add|search|summary|feedback}")


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
    append_learning_entries([entry], path=path)
    print(f"[learn] added {entry['id']} to {path}")


def cmd_feedback(args: object) -> None:
    message = getattr(args, "message", "").strip()
    phase = getattr(args, "phase", "general") or "general"
    source_spec = getattr(args, "spec", "") or ""
    harness_dir = Path(getattr(args, "dir", "")) if getattr(args, "dir", None) else DEFAULT_HARNESS_DIR
    event_file = harness_dir / DEFAULT_EVENT_FILE.name
    learning_file = harness_dir / DEFAULT_LEARNING_FILE.name
    promoted_rules_file = harness_dir / DEFAULT_PROMOTED_RULES_FILE.name
    sentiment = _classify_feedback(message)

    event = {
        "type": "user_feedback_captured",
        "phase": phase,
        "source_spec": source_spec,
        "message": message,
        "sentiment": sentiment,
    }
    append_event_entries([event], path=event_file)

    tags = ["feedback", phase, sentiment]
    if sentiment != "neutral":
        rule = f"Respect user feedback in {phase}: {message}"
        append_learning_entries(
            [
                {
                    "source_spec": source_spec,
                    "source": "user-feedback",
                    "category": "decision" if sentiment == "preference" else "anti-pattern",
                    "problem": f"User feedback ({phase}): {message}",
                    "cause": phase,
                    "rule": rule,
                    "tags": tags,
                    "severity": "warning" if sentiment in {"reject", "refine"} else "info",
                }
            ],
            path=learning_file,
        )
    promoted = promote_feedback_patterns(event_file=event_file, promoted_rules_file=promoted_rules_file)
    if promoted:
        print(f"[learn] promoted feedback rules: {len(promoted)} -> {promoted_rules_file}")
    print(f"[learn] feedback captured ({sentiment}) -> {event_file}")


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


def _classify_feedback(message: str) -> str:
    text = message.lower()
    for sentiment, patterns in _FEEDBACK_PATTERNS.items():
        if any(pattern in text for pattern in patterns):
            return sentiment
    return "neutral"


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
