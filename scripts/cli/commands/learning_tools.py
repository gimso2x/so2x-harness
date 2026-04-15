from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_LEARNING_FILE = Path(".ai-harness/learnings.jsonl")


def read_learning_entries(path: Path | None = None) -> list[dict]:
    target = path or DEFAULT_LEARNING_FILE
    if not target.exists():
        return []
    entries: list[dict] = []
    for line in target.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def append_learning_entries(entries: list[dict], path: Path | None = None) -> list[dict]:
    target = path or DEFAULT_LEARNING_FILE
    existing = read_learning_entries(target)
    known = {_dedupe_key(entry) for entry in existing}
    added: list[dict] = []
    for entry in entries:
        key = _dedupe_key(entry)
        if key in known:
            continue
        known.add(key)
        normalized = dict(entry)
        normalized.setdefault("id", f"LRN-{uuid.uuid4().hex[:6].upper()}")
        normalized.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        normalized.setdefault("tags", [])
        normalized.setdefault("severity", "info")
        normalized.setdefault("category", "pattern")
        added.append(normalized)
    if added:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as handle:
            for entry in added:
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return added


def find_relevant_learnings(goal: str, learning_file: Path | None = None, limit: int = 5) -> list[dict]:
    tokens = {token.lower() for token in goal.replace("/", " ").replace("-", " ").split() if len(token) >= 3}
    ranked: list[tuple[int, dict]] = []
    seen_rules: set[str] = set()
    for entry in read_learning_entries(learning_file):
        haystack = " ".join(
            [
                str(entry.get("problem", "")),
                str(entry.get("cause", "")),
                str(entry.get("rule", "")),
                " ".join(str(tag) for tag in entry.get("tags", [])),
            ]
        ).lower()
        score = sum(1 for token in tokens if token in haystack)
        if score <= 0:
            continue
        rule_key = str(entry.get("rule", "")).strip().lower()
        if rule_key and rule_key in seen_rules:
            continue
        if rule_key:
            seen_rules.add(rule_key)
        ranked.append((score, entry))
    ranked.sort(key=lambda item: (-item[0], item[1].get("id", "")))
    return [entry for _, entry in ranked[:limit]]


def format_relevant_learnings(goal: str, learning_file: Path | None = None, limit: int = 5) -> str:
    entries = find_relevant_learnings(goal, learning_file=learning_file, limit=limit)
    if not entries:
        return ""
    lines = ["Relevant learnings:"]
    for entry in entries:
        rule = entry.get("rule", "")
        problem = entry.get("problem", "")
        category = entry.get("category", "pattern")
        lines.append(f"- [{category}] {problem}")
        lines.append(f"  Rule: {rule}")
    return "\n".join(lines)


def build_auto_learning_entries(spec: dict) -> list[dict]:
    meta = spec.get("meta", {})
    spec_id = meta.get("id", "")
    goal = meta.get("goal", "")
    entries: list[dict] = []
    for task in spec.get("chain", {}).get("l4_tasks", []):
        summary = str(task.get("summary", "")).strip()
        if not summary:
            continue
        status = task.get("status", "pending")
        action = task.get("action", "")
        if status == "blocked":
            entries.append(
                {
                    "source_spec": spec_id,
                    "category": "edge-case",
                    "problem": f"Blocked task: {action}",
                    "cause": summary,
                    "rule": summary,
                    "tags": ["auto", "task", "blocked"],
                    "severity": "warning",
                }
            )
        elif status == "done":
            entries.append(
                {
                    "source_spec": spec_id,
                    "category": "pattern",
                    "problem": f"Completed task: {action}",
                    "cause": goal,
                    "rule": summary,
                    "tags": ["auto", "task", "done"],
                    "severity": "info",
                }
            )
    for finding in spec.get("chain", {}).get("l5_review", {}).get("findings", []):
        message = str(finding.get("message", "")).strip()
        if not message:
            continue
        entries.append(
            {
                "source_spec": spec_id,
                "category": "anti-pattern",
                "problem": message,
                "cause": str(finding.get("location", "")).strip(),
                "rule": f"Review finding to prevent next time: {message}",
                "tags": ["auto", "review", "finding"],
                "severity": _severity_from_finding(str(finding.get("severity", "info"))),
            }
        )
    return entries


def _severity_from_finding(value: str) -> str:
    normalized = value.lower()
    if normalized in {"high", "critical", "p1"}:
        return "critical"
    if normalized in {"medium", "warning", "p2", "p3"}:
        return "warning"
    return "info"


def _dedupe_key(entry: dict) -> tuple[str, str, str]:
    return (
        str(entry.get("category", "")).strip().lower(),
        str(entry.get("problem", "")).strip().lower(),
        str(entry.get("rule", "")).strip().lower(),
    )
