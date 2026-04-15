from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CLI = ROOT_DIR / "scripts/cli/main.py"
ENV = {**os.environ, "PYTHONPATH": str(ROOT_DIR / "scripts")}


def test_learn_feedback_captures_event_learning_and_promotion(tmp_path: Path) -> None:
    harness_dir = tmp_path / ".ai-harness"
    first = subprocess.run(
        [
            "python3",
            str(CLI),
            "learn",
            "feedback",
            "더 단순하게 해",
            "--phase",
            "simplify",
            "--spec",
            "SPEC-001",
            "--dir",
            str(harness_dir),
        ],
        capture_output=True,
        text=True,
        env=ENV,
        check=False,
    )
    second = subprocess.run(
        [
            "python3",
            str(CLI),
            "learn",
            "feedback",
            "좀 더 단순하게 해줘",
            "--phase",
            "simplify",
            "--spec",
            "SPEC-001",
            "--dir",
            str(harness_dir),
        ],
        capture_output=True,
        text=True,
        env=ENV,
        check=False,
    )

    assert first.returncode == 0
    assert second.returncode == 0
    events = [json.loads(line) for line in (harness_dir / "events.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    learnings = [json.loads(line) for line in (harness_dir / "learnings.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    promoted = json.loads((harness_dir / "promoted-rules.json").read_text(encoding="utf-8"))
    assert any(event["type"] == "user_feedback_captured" for event in events)
    assert any(entry["source"] == "user-feedback" for entry in learnings)
    assert any("더 단순하게" in entry["rule"] for entry in learnings)
    assert any(rule.get("promotion_source") == "feedback-frequency" for rule in promoted["rules"])
    assert "promoted feedback rules: 1" in second.stdout


def test_run_safe_commit_and_squash_check_enforce_status_preconditions(tmp_path: Path) -> None:
    harness_dir = tmp_path / ".ai-harness"
    status_dir = harness_dir / "status"
    status_dir.mkdir(parents=True)
    (status_dir / "simplify-cycle.json").write_text(
        json.dumps(
            {
                "name": "simplify-cycle",
                "remaining_count": 1,
                "stop_reason": "needs_another_pass",
                "verification_status": "REVIEW_REQUIRED",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    safe_fail = subprocess.run(
        ["python3", str(CLI), "run", "safe-commit", "--dir", str(harness_dir)],
        capture_output=True,
        text=True,
        env=ENV,
        check=False,
    )
    assert safe_fail.returncode == 1
    safe_status = json.loads((status_dir / "safe-commit.json").read_text(encoding="utf-8"))
    events = [json.loads(line) for line in (harness_dir / "events.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    assert safe_status["safety_verdict"] == "UNSAFE"
    assert any(event["type"] == "safe_commit_completed" for event in events)

    (status_dir / "simplify-cycle.json").write_text(
        json.dumps(
            {
                "name": "simplify-cycle",
                "remaining_count": 0,
                "stop_reason": "converged_to_zero",
                "verification_status": "PASS",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    safe_pass = subprocess.run(
        ["python3", str(CLI), "run", "safe-commit", "--dir", str(harness_dir)],
        capture_output=True,
        text=True,
        env=ENV,
        check=False,
    )
    assert safe_pass.returncode == 0

    squash_pass = subprocess.run(
        ["python3", str(CLI), "run", "squash-check", "--dir", str(harness_dir)],
        capture_output=True,
        text=True,
        env=ENV,
        check=False,
    )
    assert squash_pass.returncode == 0
    squash_status = json.loads((status_dir / "squash-commit.json").read_text(encoding="utf-8"))
    events = [json.loads(line) for line in (harness_dir / "events.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    assert squash_status["ready"] is True
    assert any(event["type"] == "squash_check_completed" for event in events)


def test_run_status_reports_snapshot_summary(tmp_path: Path) -> None:
    harness_dir = tmp_path / ".ai-harness"
    status_dir = harness_dir / "status"
    status_dir.mkdir(parents=True)
    (status_dir / "simplify-cycle.json").write_text('{"remaining_count":0,"stop_reason":"converged_to_zero"}\n', encoding="utf-8")
    (status_dir / "safe-commit.json").write_text('{"safety_verdict":"SAFE","verification_status":"PASS"}\n', encoding="utf-8")
    (status_dir / "squash-commit.json").write_text('{"ready":true,"reason":"ready"}\n', encoding="utf-8")

    result = subprocess.run(
        ["python3", str(CLI), "run", "status", "--dir", str(harness_dir)],
        capture_output=True,
        text=True,
        env=ENV,
        check=False,
    )
    assert result.returncode == 0
    assert "simplify-cycle: remaining=0" in result.stdout
    assert "safe-commit: verdict=SAFE" in result.stdout
    assert "squash-commit: ready=True" in result.stdout
