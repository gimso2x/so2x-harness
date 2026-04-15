from __future__ import annotations

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def _apply(project: Path) -> None:
    import subprocess

    subprocess.run(
        [
            "python3",
            str(ROOT_DIR / "scripts/apply.py"),
            "--project",
            str(project),
            "--platform",
            "claude",
            "--preset",
            "general",
        ],
        capture_output=True,
        text=True,
        check=True,
    )


def test_doctor_on_installed_project(tmp_project: Path) -> None:
    import subprocess

    _apply(tmp_project)
    result = subprocess.run(
        ["python3", str(ROOT_DIR / "scripts/doctor.py"), "--project", str(tmp_project)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "[OK]" in result.stdout
    assert "manifest" in result.stdout.lower()


def test_doctor_on_empty_project(tmp_path: Path) -> None:
    import subprocess

    empty = tmp_path / "empty-project"
    empty.mkdir()
    result = subprocess.run(
        ["python3", str(ROOT_DIR / "scripts/doctor.py"), "--project", str(empty)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "[WARN]" in result.stdout or "not found" in result.stdout


def test_doctor_detects_rules(tmp_project: Path) -> None:
    import subprocess

    _apply(tmp_project)
    result = subprocess.run(
        ["python3", str(ROOT_DIR / "scripts/doctor.py"), "--project", str(tmp_project)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert "rules_dir" in result.stdout
    assert "skills_dir" in result.stdout


def _apply_codex(project: Path) -> None:
    import subprocess

    subprocess.run(
        [
            "python3",
            str(ROOT_DIR / "scripts/apply.py"),
            "--project",
            str(project),
            "--platform",
            "codex",
            "--preset",
            "general",
        ],
        capture_output=True,
        text=True,
        check=True,
    )


def test_doctor_on_codex_project(tmp_project: Path) -> None:
    import subprocess

    _apply_codex(tmp_project)
    result = subprocess.run(
        ["python3", str(ROOT_DIR / "scripts/doctor.py"), "--project", str(tmp_project)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "[OK]" in result.stdout
    assert "skills" in result.stdout.lower()


def test_doctor_reports_workflow_status_surface(tmp_project: Path) -> None:
    import json
    import subprocess

    _apply(tmp_project)
    harness_dir = tmp_project / ".ai-harness"
    status_dir = harness_dir / "status"
    status_dir.mkdir(parents=True, exist_ok=True)
    (status_dir / "simplify-cycle.json").write_text(
        json.dumps({"remaining_count": 0, "stop_reason": "converged_to_zero"}, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )
    (status_dir / "safe-commit.json").write_text(
        json.dumps({"safety_verdict": "SAFE", "verification_status": "PASS"}, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )
    (status_dir / "squash-commit.json").write_text(
        json.dumps({"ready": True, "reason": "ready"}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (harness_dir / "promoted-rules.json").write_text(
        json.dumps(
            {
                "rules": [
                    {
                        "rule": "Keep simplify-cycle at zero",
                        "promoted_at": "2026-04-15T00:00:00+00:00",
                    },
                    {
                        "rule": "Honor repeated user feedback: 더 단순하게",
                        "promoted_at": "2026-04-16T00:00:00+00:00",
                    },
                ]
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    (harness_dir / "events.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {"type": "user_feedback_captured", "message": "더 단순하게"}, ensure_ascii=False
                ),
                json.dumps(
                    {"type": "safe_commit_completed", "reason": "ready_for_commit"},
                    ensure_ascii=False,
                ),
                json.dumps(
                    {"type": "squash_check_completed", "reason": "ready"}, ensure_ascii=False
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    config_path = harness_dir / "config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["policy_promoted_skills"] = {
        "specify": "next-app repos default to full specification workflow"
    }
    config["skill_recommendations"] = {
        "specify": [
            "Full spec workflow is optional unless the project asks for heavier planning.",
            "policy promotion: next-app repos default to full specification workflow",
        ]
    }
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result = subprocess.run(
        ["python3", str(ROOT_DIR / "scripts/doctor.py"), "--project", str(tmp_project)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "simplify_status" in result.stdout
    assert "safe_commit_status" in result.stdout
    assert "squash_status" in result.stdout
    assert "promoted_rules" in result.stdout
    assert "latest_promoted_rule" in result.stdout
    assert "Honor repeated user feedback: 더 단순하게" in result.stdout
    assert "policy_promoted_skills" in result.stdout
    assert "skill_recommendation.specify" in result.stdout
    assert "policy promotion: next-app repos default to full specification workflow" in result.stdout
    assert "feedback_events" in result.stdout
    assert "latest_feedback" in result.stdout
    assert "safe_commit_events" in result.stdout
    assert "squash_check_events" in result.stdout
