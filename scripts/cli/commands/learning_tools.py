from __future__ import annotations

import json
import re
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_HARNESS_DIR = Path(".ai-harness")
DEFAULT_EVENT_FILE = DEFAULT_HARNESS_DIR / "events.jsonl"
DEFAULT_LEARNING_FILE = DEFAULT_HARNESS_DIR / "learnings.jsonl"
DEFAULT_PROMOTED_RULES_FILE = DEFAULT_HARNESS_DIR / "promoted-rules.json"
DEFAULT_STATUS_DIR = DEFAULT_HARNESS_DIR / "status"


def read_learning_entries(path: Path | None = None) -> list[dict]:
    return _read_jsonl(path or DEFAULT_LEARNING_FILE)


def read_event_entries(path: Path | None = None) -> list[dict]:
    return _read_jsonl(path or DEFAULT_EVENT_FILE)


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
        normalized.setdefault("timestamp", _now_iso())
        normalized.setdefault("tags", [])
        normalized.setdefault("severity", "info")
        normalized.setdefault("category", "pattern")
        added.append(normalized)
    if added:
        _append_jsonl(target, added)
    return added


def append_event_entries(entries: list[dict], path: Path | None = None) -> list[dict]:
    target = path or DEFAULT_EVENT_FILE
    normalized_entries: list[dict] = []
    for entry in entries:
        normalized = dict(entry)
        normalized.setdefault("id", f"EVT-{uuid.uuid4().hex[:6].upper()}")
        normalized.setdefault("timestamp", _now_iso())
        normalized_entries.append(normalized)
    if normalized_entries:
        _append_jsonl(target, normalized_entries)
    return normalized_entries


def read_status(name: str, status_dir: Path | None = None) -> dict:
    target = (status_dir or DEFAULT_STATUS_DIR) / f"{name}.json"
    if not target.exists():
        return {}
    try:
        return json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def write_status(name: str, payload: dict, status_dir: Path | None = None) -> Path:
    target = (status_dir or DEFAULT_STATUS_DIR) / f"{name}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    normalized = dict(payload)
    normalized.setdefault("updated_at", _now_iso())
    target.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def load_promoted_rules(path: Path | None = None) -> dict:
    target = path or DEFAULT_PROMOTED_RULES_FILE
    if not target.exists():
        return {"rules": []}
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"rules": []}
    rules = data.get("rules", [])
    if not isinstance(rules, list):
        return {"rules": []}
    return {"rules": rules}


def save_promoted_rules(payload: dict, path: Path | None = None) -> Path:
    target = path or DEFAULT_PROMOTED_RULES_FILE
    target.parent.mkdir(parents=True, exist_ok=True)
    normalized = {"rules": payload.get("rules", [])}
    target.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def promote_frequent_learnings(
    learning_file: Path | None = None,
    promoted_rules_file: Path | None = None,
    min_occurrences: int = 2,
) -> list[dict]:
    learnings = read_learning_entries(learning_file)
    counts = Counter(
        str(entry.get("rule", "")).strip()
        for entry in learnings
        if str(entry.get("rule", "")).strip()
    )
    promoted = load_promoted_rules(promoted_rules_file)
    existing = {str(rule.get("rule", "")).strip().lower() for rule in promoted.get("rules", [])}
    added: list[dict] = []
    for rule, occurrences in sorted(counts.items()):
        if occurrences < min_occurrences:
            continue
        if rule.strip().lower() in existing:
            continue
        sample = next(entry for entry in learnings if str(entry.get("rule", "")).strip() == rule)
        promoted_rule = {
            "id": f"PRM-{uuid.uuid4().hex[:6].upper()}",
            "rule": rule,
            "category": sample.get("category", "pattern"),
            "severity": sample.get("severity", "info"),
            "occurrences": occurrences,
            "sources": sorted(
                {
                    str(entry.get("source_spec", "")).strip()
                    for entry in learnings
                    if str(entry.get("rule", "")).strip() == rule and str(entry.get("source_spec", "")).strip()
                }
            ),
            "promotion_source": "learning-frequency",
            "promoted_at": _now_iso(),
        }
        promoted.setdefault("rules", []).append(promoted_rule)
        existing.add(rule.strip().lower())
        added.append(promoted_rule)
    if added:
        save_promoted_rules(promoted, promoted_rules_file)
    return added


def promote_feedback_patterns(
    event_file: Path | None = None,
    promoted_rules_file: Path | None = None,
    min_occurrences: int = 2,
) -> list[dict]:
    events = read_event_entries(event_file)
    normalized_messages = [
        _normalize_feedback_message(str(event.get("message", "")))
        for event in events
        if event.get("type") == "user_feedback_captured" and str(event.get("message", "")).strip()
    ]
    counts = Counter(message for message in normalized_messages if message)
    promoted = load_promoted_rules(promoted_rules_file)
    existing = {str(rule.get("rule", "")).strip().lower() for rule in promoted.get("rules", [])}
    added: list[dict] = []
    for message, occurrences in sorted(counts.items()):
        rule_text = f"Honor repeated user feedback: {message}"
        if occurrences < min_occurrences:
            continue
        if rule_text.strip().lower() in existing:
            continue
        promoted_rule = {
            "id": f"PRM-{uuid.uuid4().hex[:6].upper()}",
            "rule": rule_text,
            "category": "decision",
            "severity": "warning",
            "occurrences": occurrences,
            "sources": ["user-feedback"],
            "promotion_source": "feedback-frequency",
            "promoted_at": _now_iso(),
        }
        promoted.setdefault("rules", []).append(promoted_rule)
        existing.add(rule_text.strip().lower())
        added.append(promoted_rule)
    if added:
        save_promoted_rules(promoted, promoted_rules_file)
    return added


def find_relevant_learnings(
    goal: str,
    learning_file: Path | None = None,
    promoted_rules_file: Path | None = None,
    limit: int = 5,
) -> list[dict]:
    tokens = {token.lower() for token in goal.replace("/", " ").replace("-", " ").split() if len(token) >= 3}
    ranked: list[tuple[int, dict]] = []
    seen_rules: set[str] = set()

    promoted = load_promoted_rules(promoted_rules_file)
    for entry in promoted.get("rules", []):
        haystack = " ".join(
            [
                str(entry.get("rule", "")),
                str(entry.get("category", "")),
                str(entry.get("severity", "")),
                " ".join(str(tag) for tag in entry.get("tags", [])),
            ]
        ).lower()
        score = sum(2 for token in tokens if token in haystack)
        if score <= 0:
            continue
        rule_key = str(entry.get("rule", "")).strip().lower()
        if rule_key:
            seen_rules.add(rule_key)
        ranked.append((score, {**entry, "source": "promoted-rule"}))

    for entry in read_learning_entries(learning_file):
        haystack = " ".join(
            [
                str(entry.get("problem", "")),
                str(entry.get("cause", "")),
                str(entry.get("rule", "")),
                str(entry.get("lens", "")),
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
        ranked.append((score, {**entry, "source": entry.get("source", "learning")}))
    ranked.sort(key=lambda item: (-item[0], item[1].get("id", "")))
    return [entry for _, entry in ranked[:limit]]


def format_relevant_learnings(
    goal: str,
    learning_file: Path | None = None,
    promoted_rules_file: Path | None = None,
    limit: int = 5,
) -> str:
    entries = find_relevant_learnings(
        goal,
        learning_file=learning_file,
        promoted_rules_file=promoted_rules_file,
        limit=limit,
    )
    if not entries:
        return ""
    lines = ["Relevant learnings:"]
    for entry in entries:
        rule = entry.get("rule", "")
        problem = entry.get("problem", "") or rule
        category = entry.get("category", "pattern")
        source = entry.get("source", "learning")
        lens = entry.get("lens")
        lines.append(f"- [{category}] {problem}")
        lines.append(f"  Rule: {rule}")
        if lens:
            lines.append(f"  Lens: {lens}")
        lines.append(f"  Source: {source}")
    return "\n".join(lines)


def build_auto_learning_entries(spec: dict) -> list[dict]:
    bundle = build_auto_learning_bundle(spec)
    return bundle["learnings"]


def build_auto_learning_bundle(spec: dict) -> dict[str, list[dict]]:
    meta = spec.get("meta", {})
    spec_id = meta.get("id", "")
    goal = meta.get("goal", "")
    events: list[dict] = []
    learnings: list[dict] = []
    statuses: list[dict] = []

    for task in spec.get("chain", {}).get("l4_tasks", []):
        summary = str(task.get("summary", "")).strip()
        if not summary:
            continue
        status = task.get("status", "pending")
        action = task.get("action", "")
        event = {
            "type": "task_summary_recorded",
            "source_spec": spec_id,
            "goal": goal,
            "task_id": task.get("id", ""),
            "task_status": status,
            "action": action,
            "summary": summary,
        }
        events.append(event)
        if status == "blocked":
            learnings.append(
                {
                    "source_spec": spec_id,
                    "source": "task-summary",
                    "category": "edge-case",
                    "problem": f"Blocked task: {action}",
                    "cause": summary,
                    "rule": summary,
                    "tags": ["auto", "task", "blocked"],
                    "severity": "warning",
                }
            )
        elif status == "done":
            learnings.append(
                {
                    "source_spec": spec_id,
                    "source": "task-summary",
                    "category": "pattern",
                    "problem": f"Completed task: {action}",
                    "cause": goal,
                    "rule": summary,
                    "tags": ["auto", "task", "done"],
                    "severity": "info",
                }
            )

    review = spec.get("chain", {}).get("l5_review", {})
    review_status = str(review.get("status", "")).strip()
    findings = review.get("findings", [])
    if review_status:
        events.append(
            {
                "type": "review_cycle_completed",
                "source_spec": spec_id,
                "goal": goal,
                "review_status": review_status,
                "finding_count": len(findings),
            }
        )
    for finding in findings:
        message = str(finding.get("message", "")).strip()
        if not message:
            continue
        lens = _infer_lens(message)
        event = {
            "type": "review_finding_recorded",
            "source_spec": spec_id,
            "goal": goal,
            "message": message,
            "location": str(finding.get("location", "")).strip(),
            "severity": str(finding.get("severity", "info")),
            "lens": lens,
        }
        events.append(event)
        learnings.append(
            {
                "source_spec": spec_id,
                "source": "review-finding",
                "category": "anti-pattern",
                "problem": message,
                "cause": str(finding.get("location", "")).strip(),
                "rule": f"Review finding to prevent next time: {message}",
                "tags": ["auto", "review", "finding", lens],
                "severity": _severity_from_finding(str(finding.get("severity", "info"))),
                "lens": lens,
            }
        )

    simplify_status = _build_simplify_status(spec_id, goal, findings)
    if simplify_status:
        statuses.append(simplify_status)
        events.extend(
            [
                {
                    "type": "simplify_pass_completed",
                    "source_spec": spec_id,
                    "goal": goal,
                    "pass_index": simplify_status["passes"],
                    "remaining_count": simplify_status["remaining_count"],
                    "stop_reason": simplify_status["stop_reason"],
                },
                {
                    "type": "simplify_cycle_completed",
                    "source_spec": spec_id,
                    "goal": goal,
                    "remaining_count": simplify_status["remaining_count"],
                    "stop_reason": simplify_status["stop_reason"],
                    "lenses": simplify_status["lenses"],
                },
                {
                    "type": "verify_completed",
                    "source_spec": spec_id,
                    "goal": goal,
                    "verification_status": simplify_status["verification_status"],
                },
                {
                    "type": "safe_commit_completed",
                    "source_spec": spec_id,
                    "goal": goal,
                    "safety_verdict": simplify_status["safety_verdict"],
                    "remaining_count": simplify_status["remaining_count"],
                },
                {
                    "type": "squash_commit_completed",
                    "source_spec": spec_id,
                    "goal": goal,
                    "base_branch": "main",
                    "safety_verdict": simplify_status["safety_verdict"],
                    "verification_status": simplify_status["verification_status"],
                },
            ]
        )
        learnings.extend(_build_simplify_learning_entries(spec_id, goal, simplify_status))

    return {"events": events, "learnings": learnings, "statuses": statuses}


def persist_learning_bundle(
    bundle: dict[str, list[dict]],
    harness_dir: Path | None = None,
    learning_file: Path | None = None,
    event_file: Path | None = None,
    promoted_rules_file: Path | None = None,
    status_dir: Path | None = None,
) -> dict[str, object]:
    base = harness_dir or DEFAULT_HARNESS_DIR
    event_target = event_file or (base / DEFAULT_EVENT_FILE.name)
    learning_target = learning_file or (base / DEFAULT_LEARNING_FILE.name)
    promoted_target = promoted_rules_file or (base / DEFAULT_PROMOTED_RULES_FILE.name)
    status_target = status_dir or (base / DEFAULT_STATUS_DIR.name)

    added_events = append_event_entries(bundle.get("events", []), event_target)
    added_learnings = append_learning_entries(bundle.get("learnings", []), learning_target)
    written_statuses: list[Path] = []
    for status in bundle.get("statuses", []):
        name = str(status.get("name", "")).strip()
        if not name:
            continue
        written_statuses.append(write_status(name, status, status_target))
    promoted = promote_frequent_learnings(learning_target, promoted_target)
    promoted_feedback = promote_feedback_patterns(event_target, promoted_target)
    if promoted or promoted_feedback:
        append_event_entries(
            [
                {
                    "type": "learning_promoted",
                    "rule": entry.get("rule", ""),
                    "occurrences": entry.get("occurrences", 0),
                    "category": entry.get("category", "pattern"),
                    "promotion_source": entry.get("promotion_source", "learning-frequency"),
                }
                for entry in [*promoted, *promoted_feedback]
            ],
            event_target,
        )
    return {
        "events": added_events,
        "learnings": added_learnings,
        "promoted": [*promoted, *promoted_feedback],
        "statuses": written_statuses,
    }


def _build_simplify_status(spec_id: str, goal: str, findings: list[dict]) -> dict | None:
    if not spec_id and not goal and not findings:
        return None
    lenses = {
        "code_reuse": 0,
        "code_quality": 0,
        "efficiency": 0,
    }
    for finding in findings:
        lens = _infer_lens(str(finding.get("message", "")))
        key = lens.lower().replace(" ", "_")
        if key in lenses:
            lenses[key] += 1
    remaining = sum(lenses.values())
    stop_reason = "converged_to_zero" if remaining == 0 else "needs_another_pass"
    verification_status = "PASS" if remaining == 0 else "REVIEW_REQUIRED"
    safety_verdict = "SAFE" if remaining == 0 else "UNSAFE"
    return {
        "name": "simplify-cycle",
        "source_spec": spec_id,
        "goal": goal,
        "passes": 1,
        "remaining_count": remaining,
        "stop_reason": stop_reason,
        "verification_status": verification_status,
        "safety_verdict": safety_verdict,
        "lenses": lenses,
        "updated_at": _now_iso(),
    }


def _build_simplify_learning_entries(spec_id: str, goal: str, simplify_status: dict) -> list[dict]:
    entries: list[dict] = []
    for lens, count in simplify_status.get("lenses", {}).items():
        if count <= 0:
            continue
        entries.append(
            {
                "source_spec": spec_id,
                "source": "simplify-cycle",
                "category": "pattern",
                "problem": f"Simplify cycle found {count} remaining issue(s) in {lens}",
                "cause": goal,
                "rule": f"Run simplify-cycle until {lens} remaining count converges to zero or no_safe_gain.",
                "tags": ["auto", "simplify", lens],
                "severity": "warning",
                "lens": lens,
            }
        )
    return entries


def _infer_lens(message: str) -> str:
    text = message.lower()
    if any(token in text for token in {"duplicate", "reuse", "shared", "consolidat"}):
        return "code_reuse"
    if any(token in text for token in {"performance", "efficient", "latency", "n+1", "cache"}):
        return "efficiency"
    return "code_quality"


def _normalize_feedback_message(message: str) -> str:
    text = " ".join(message.strip().lower().split())
    text = re.sub(r"[!?.,~]+", "", text)
    text = re.sub(r"^(이건|이거|그건|그거)\s+", "", text)
    text = re.sub(r"^(좀|조금|약간|살짝|조금만|좀만)\s+", "", text)
    text = re.sub(r"\s+(해줘|해주세요|해 주세[요요]?|해주세[요요]?|해주세요요|해|해라)$", "", text)
    text = re.sub(r"\s+(해봐|해보자|하자)$", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


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


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    entries: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def _append_jsonl(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
