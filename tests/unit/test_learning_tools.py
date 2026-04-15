from __future__ import annotations

import json
from pathlib import Path

from scripts.cli.commands.learning_tools import (
    build_auto_learning_bundle,
    build_auto_learning_entries,
    find_relevant_learnings,
    load_promoted_rules,
    persist_learning_bundle,
    promote_feedback_patterns,
    read_event_entries,
    read_status,
)


def test_find_relevant_learnings_matches_goal_and_deduplicates_by_rule(tmp_path: Path) -> None:
    harness_dir = tmp_path / ".ai-harness"
    harness_dir.mkdir(parents=True)
    learnings = harness_dir / "learnings.jsonl"
    promoted_rules = harness_dir / "promoted-rules.json"
    entries = [
        {
            "id": "LRN-001",
            "problem": "OAuth callback mismatch in staging",
            "cause": "Hardcoded callback URL",
            "rule": "Always configure OAuth callback via env",
            "tags": ["oauth", "config"],
            "category": "anti-pattern",
            "severity": "warning",
        },
        {
            "id": "LRN-002",
            "problem": "OAuth callback mismatch in prod",
            "cause": "Another hardcoded callback URL",
            "rule": "Always configure OAuth callback via env",
            "tags": ["oauth", "deploy"],
            "category": "anti-pattern",
            "severity": "warning",
        },
        {
            "id": "LRN-003",
            "problem": "Unrelated UI issue",
            "cause": "Spacing bug",
            "rule": "Check mobile layout before merge",
            "tags": ["ui"],
            "category": "pattern",
            "severity": "info",
        },
    ]
    learnings.write_text("\n".join(json.dumps(entry, ensure_ascii=False) for entry in entries) + "\n", encoding="utf-8")
    promoted_rules.write_text(
        json.dumps(
            {
                "rules": [
                    {
                        "id": "PRM-001",
                        "rule": "Prefer promoted OAuth callback rules",
                        "category": "pattern",
                        "severity": "warning",
                        "tags": ["oauth"],
                    }
                ]
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    results = find_relevant_learnings(
        "Add OAuth login with GitHub callback handling",
        learning_file=learnings,
        promoted_rules_file=promoted_rules,
    )

    assert len(results) == 2
    assert results[0]["source"] == "promoted-rule"
    assert results[1]["rule"] == "Always configure OAuth callback via env"


def test_build_auto_learning_entries_extracts_task_and_review_findings() -> None:
    spec = {
        "meta": {"id": "SPEC-AUTH-001", "goal": "Add OAuth login"},
        "chain": {
            "l4_tasks": [
                {
                    "id": "T1",
                    "action": "Handle callback configuration",
                    "status": "blocked",
                    "summary": "Need env-based callback URL per environment",
                },
                {
                    "id": "T2",
                    "action": "Polish loading state",
                    "status": "done",
                    "summary": "Reuse shared spinner component instead of custom markup",
                },
            ],
            "l5_review": {
                "status": "needs_changes",
                "findings": [
                    {
                        "severity": "high",
                        "message": "Duplicate token parsing logic in two handlers",
                        "location": "auth/callback.py:42",
                    }
                ],
            },
        },
    }

    entries = build_auto_learning_entries(spec)

    assert len(entries) == 4
    assert {entry["category"] for entry in entries} == {"edge-case", "pattern", "anti-pattern"}
    assert any("env-based callback URL" in entry["rule"] for entry in entries)
    assert any("Reuse shared spinner component" in entry["rule"] for entry in entries)
    assert any("Duplicate token parsing logic" in entry["problem"] for entry in entries)
    assert any(entry.get("lens") == "code_reuse" for entry in entries)


def test_persist_learning_bundle_writes_events_status_and_promoted_rules(tmp_path: Path) -> None:
    harness_dir = tmp_path / ".ai-harness"
    spec = {
        "meta": {"id": "SPEC-AUTH-001", "goal": "Add OAuth login"},
        "chain": {
            "l4_tasks": [
                {
                    "id": "T1",
                    "action": "Handle callback configuration",
                    "status": "done",
                    "summary": "Always configure callback URL via environment per deployment",
                },
                {
                    "id": "T2",
                    "action": "Handle callback configuration in worker",
                    "status": "done",
                    "summary": "Always configure callback URL via environment per deployment",
                },
            ],
            "l5_review": {
                "status": "needs_changes",
                "findings": [
                    {
                        "severity": "high",
                        "message": "Duplicate token parsing logic in two handlers",
                        "location": "auth/callback.py:42",
                    }
                ],
            },
        },
    }

    bundle = build_auto_learning_bundle(spec)
    summary = persist_learning_bundle(bundle, harness_dir=harness_dir)

    assert len(summary["events"]) >= 6
    assert len(summary["learnings"]) >= 4
    assert (harness_dir / "events.jsonl").exists()
    assert (harness_dir / "learnings.jsonl").exists()
    assert read_status("simplify-cycle", harness_dir / "status")["remaining_count"] == 1

    events = read_event_entries(harness_dir / "events.jsonl")
    assert any(event["type"] == "review_finding_recorded" for event in events)
    assert any(event["type"] == "learning_promoted" for event in events)

    promoted = load_promoted_rules(harness_dir / "promoted-rules.json")
    assert promoted["rules"]
    assert promoted["rules"][0]["occurrences"] >= 2


def test_promote_feedback_patterns_promotes_repeated_feedback_messages(tmp_path: Path) -> None:
    harness_dir = tmp_path / ".ai-harness"
    harness_dir.mkdir(parents=True)
    event_file = harness_dir / "events.jsonl"
    promoted_file = harness_dir / "promoted-rules.json"
    event_file.write_text(
        "\n".join(
            [
                json.dumps({"type": "user_feedback_captured", "message": "더 단순하게 해"}, ensure_ascii=False),
                json.dumps({"type": "user_feedback_captured", "message": "  좀 더 단순하게 해줘  "}, ensure_ascii=False),
                json.dumps({"type": "user_feedback_captured", "message": "이건 합쳐"}, ensure_ascii=False),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    promoted = promote_feedback_patterns(event_file=event_file, promoted_rules_file=promoted_file)

    assert len(promoted) == 1
    assert promoted[0]["promotion_source"] == "feedback-frequency"
    assert "더 단순하게" in promoted[0]["rule"]
    persisted = load_promoted_rules(promoted_file)
    assert any(rule.get("promotion_source") == "feedback-frequency" for rule in persisted["rules"])
