from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CLI = ROOT_DIR / "scripts/cli/main.py"
APPLY = ROOT_DIR / "scripts/apply.py"
DOCTOR = ROOT_DIR / "scripts/doctor.py"
ENV = {**os.environ, "PYTHONPATH": str(ROOT_DIR / "scripts")}


def test_multi_platform_apply_and_workflow_smoke(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "package.json").write_text('{"name":"smoke-project"}\n', encoding="utf-8")

    apply = subprocess.run(
        [
            "python3",
            str(APPLY),
            "--project",
            str(project),
            "--platform",
            "claude",
            "codex",
            "--preset",
            "general",
        ],
        capture_output=True,
        text=True,
        env=ENV,
        check=False,
    )
    assert apply.returncode == 0

    assert (project / "CLAUDE.md").exists()
    assert (project / "AGENTS.md").exists()
    assert (project / ".claude" / "skills").exists()
    assert (project / ".agents" / "skills").exists()
    manifest = json.loads((project / ".ai-harness" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["platforms"] == ["claude", "codex"]

    status_dir = project / ".ai-harness" / "status"
    status_dir.mkdir(parents=True, exist_ok=True)
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

    safe_commit = subprocess.run(
        ["python3", str(CLI), "run", "safe-commit", "--dir", str(project / ".ai-harness")],
        capture_output=True,
        text=True,
        env=ENV,
        check=False,
    )
    squash_check = subprocess.run(
        ["python3", str(CLI), "run", "squash-check", "--dir", str(project / ".ai-harness")],
        capture_output=True,
        text=True,
        env=ENV,
        check=False,
    )
    feedback_a = subprocess.run(
        [
            "python3",
            str(CLI),
            "learn",
            "feedback",
            "더 단순하게 해",
            "--phase",
            "simplify",
            "--dir",
            str(project / ".ai-harness"),
        ],
        capture_output=True,
        text=True,
        env=ENV,
        check=False,
    )
    feedback_b = subprocess.run(
        [
            "python3",
            str(CLI),
            "learn",
            "feedback",
            "좀 더 단순하게 해줘",
            "--phase",
            "simplify",
            "--dir",
            str(project / ".ai-harness"),
        ],
        capture_output=True,
        text=True,
        env=ENV,
        check=False,
    )
    doctor = subprocess.run(
        ["python3", str(DOCTOR), "--project", str(project)],
        capture_output=True,
        text=True,
        env=ENV,
        check=False,
    )

    assert safe_commit.returncode == 0
    assert squash_check.returncode == 0
    assert feedback_a.returncode == 0
    assert feedback_b.returncode == 0
    assert doctor.returncode == 0

    promoted = json.loads(
        (project / ".ai-harness" / "promoted-rules.json").read_text(encoding="utf-8")
    )
    assert any(rule.get("promotion_source") == "feedback-frequency" for rule in promoted["rules"])

    doctor_output = doctor.stdout
    assert "claude.skills_dir" in doctor_output
    assert "codex.skills_dir" in doctor_output
    assert "safe_commit_status" in doctor_output
    assert "squash_status" in doctor_output
    assert "latest_promoted_rule" in doctor_output
    assert "Honor repeated user feedback: 더 단순하게" in doctor_output
