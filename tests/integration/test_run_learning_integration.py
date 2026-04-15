from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def test_run_specify_includes_relevant_learnings_in_instruction(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    learning_dir = project / ".ai-harness"
    learning_dir.mkdir()
    learning_file = learning_dir / "learnings.jsonl"
    learning_file.write_text(
        json.dumps(
            {
                "id": "LRN-OAUTH-1",
                "problem": "OAuth callback mismatch",
                "cause": "Hardcoded callback URL",
                "rule": "Always configure OAuth callback via env",
                "tags": ["oauth", "config"],
                "category": "anti-pattern",
                "severity": "warning",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["python3", str(ROOT_DIR / "scripts/cli/main.py"), "run", "specify", "Add OAuth login", "--output", "spec.json"],
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "Relevant learnings:" in result.stdout
    assert "Always configure OAuth callback via env" in result.stdout


def test_run_execute_appends_auto_learnings_from_task_summaries(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    spec_file = project / "spec.json"
    learning_file = project / ".ai-harness" / "learnings.jsonl"
    spec = {
        "meta": {
            "id": "SPEC-AUTH-001",
            "goal": "Add OAuth login",
            "status": "draft",
            "mode": "standard",
            "created_at": "2026-04-15T00:00:00+00:00",
            "updated_at": "2026-04-15T00:00:00+00:00",
        },
        "chain": {
            "l0_goal": "Add OAuth login",
            "l1_context": {"assumptions": [], "constraints": [], "patterns": [], "research": ""},
            "l2_decisions": [{"id": "D1", "decision": "Use env callback", "rationale": "Deploy-safe", "alternatives": []}],
            "l3_requirements": [{"id": "R1", "behavior": "Use env callback", "scenarios": []}],
            "l4_tasks": [
                {
                    "id": "T1",
                    "action": "Handle callback configuration",
                    "requirement_refs": ["R1"],
                    "status": "done",
                    "summary": "Always configure callback URL via environment per deployment",
                }
            ],
            "l5_review": {
                "status": "needs_changes",
                "reviewer": "Verifier",
                "findings": [
                    {
                        "severity": "high",
                        "message": "Duplicate token parsing logic in two handlers",
                        "location": "auth/callback.py:42",
                    }
                ],
            },
        },
        "gates": {
            "l0_to_l1": {"status": "pass"},
            "l1_to_l2": {"status": "pass"},
            "l2_to_l3": {"status": "pass"},
            "l3_to_l4": {"status": "pass"},
            "l4_to_l5": {"status": "pass"},
        },
    }
    spec_file.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result = subprocess.run(
        ["python3", str(ROOT_DIR / "scripts/cli/main.py"), "run", "execute", "--file", str(spec_file)],
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert learning_file.exists()
    lines = [json.loads(line) for line in learning_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert any("callback URL via environment" in entry["rule"] for entry in lines)
    assert any("Duplicate token parsing logic" in entry["problem"] for entry in lines)
    assert "Auto-learnings captured:" in result.stdout
