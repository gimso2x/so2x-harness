from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CLI = ROOT_DIR / "scripts/cli/main.py"
DOCTOR = ROOT_DIR / "scripts/doctor.py"
ENV = {**os.environ, "PYTHONPATH": str(ROOT_DIR / "scripts")}


def _write_spec(path: Path) -> None:
    spec = {
        "meta": {
            "id": "SPEC-TEST-001",
            "goal": "Test blocked execution state",
            "status": "draft",
            "mode": "standard",
            "created_at": "2026-04-15T00:00:00+00:00",
            "updated_at": "2026-04-15T00:00:00+00:00",
        },
        "chain": {
            "l0_goal": "Test blocked execution state",
            "l4_tasks": [
                {
                    "id": "T1",
                    "action": "Wait for approval",
                    "requirement_refs": ["R1"],
                    "status": "blocked",
                    "summary": "Waiting for user approval",
                },
                {
                    "id": "T2",
                    "action": "Finish implementation",
                    "requirement_refs": ["R1"],
                    "status": "pending",
                },
            ],
        },
        "gates": {
            "l0_to_l1": {"status": "pending"},
            "l1_to_l2": {"status": "pending"},
            "l2_to_l3": {"status": "pending"},
            "l3_to_l4": {"status": "pending"},
            "l4_to_l5": {"status": "pending"},
        },
    }
    path.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def test_spec_status_shows_blocked_task_and_summary(tmp_path: Path) -> None:
    spec_file = tmp_path / "spec.json"
    _write_spec(spec_file)

    result = subprocess.run(
        ["python3", str(CLI), "spec", "status", str(spec_file)],
        capture_output=True,
        text=True,
        check=False,
        env=ENV,
    )

    assert result.returncode == 0
    assert "T1" in result.stdout
    assert "blocked" in result.stdout
    assert "Waiting for user approval" in result.stdout


def test_doctor_surfaces_blocked_execution_summary(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "package.json").write_text('{"name": "test-project"}', encoding="utf-8")
    spec_file = project / "spec.json"
    _write_spec(spec_file)

    result = subprocess.run(
        ["python3", str(DOCTOR), "--project", str(project)],
        capture_output=True,
        text=True,
        check=False,
        env=ENV,
    )

    assert result.returncode == 0
    assert "execution_status" in result.stdout
    assert "blocked" in result.stdout
    assert "Waiting for user approval" in result.stdout
    assert "pending_tasks" in result.stdout
