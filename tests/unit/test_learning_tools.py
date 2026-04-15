from __future__ import annotations

import json
from pathlib import Path

from scripts.cli.commands.learning_tools import (
    build_auto_learning_entries,
    find_relevant_learnings,
)


def test_find_relevant_learnings_matches_goal_and_deduplicates_by_rule(tmp_path: Path) -> None:
    learnings = tmp_path / ".ai-harness" / "learnings.jsonl"
    learnings.parent.mkdir(parents=True)
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

    results = find_relevant_learnings(
        "Add OAuth login with GitHub callback handling",
        learning_file=learnings,
    )

    assert len(results) == 1
    assert results[0]["rule"] == "Always configure OAuth callback via env"


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

    assert len(entries) == 3
    assert {entry["category"] for entry in entries} == {"edge-case", "pattern", "anti-pattern"}
    assert any("env-based callback URL" in entry["rule"] for entry in entries)
    assert any("Reuse shared spinner component" in entry["rule"] for entry in entries)
    assert any("Duplicate token parsing logic" in entry["problem"] for entry in entries)
