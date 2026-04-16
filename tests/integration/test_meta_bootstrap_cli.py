from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CLI = ROOT_DIR / "scripts/cli/main.py"
ENV = {**os.environ, "PYTHONPATH": str(ROOT_DIR / "scripts")}


def test_init_state_command_bootstraps_meta_state_file(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    result = subprocess.run(
        [
            "python3",
            str(CLI),
            "init-state",
            "--project",
            str(project),
            "--run-id",
            "run-42",
            "--harness-name",
            "oauth-login",
        ],
        capture_output=True,
        text=True,
        env=ENV,
        check=False,
    )

    assert result.returncode == 0
    state_path = project / "outputs" / "run-42" / "_state.json"
    assert state_path.exists()
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["run_id"] == "run-42"
    assert state["harness_name"] == "oauth-login"
    assert state["current_stage"] == "stage-0-interview"
    assert state["interview_answers_path"] == "outputs/run-42/interview/answers.json"
    assert "[meta-state] created" in result.stdout


def test_init_state_command_refuses_to_overwrite_without_force(tmp_path: Path) -> None:
    project = tmp_path / "project"
    state_dir = project / "outputs" / "run-42"
    state_dir.mkdir(parents=True)
    state_path = state_dir / "_state.json"
    state_path.write_text('{"run_id": "existing"}\n', encoding="utf-8")

    result = subprocess.run(
        [
            "python3",
            str(CLI),
            "init-state",
            "--project",
            str(project),
            "--run-id",
            "run-42",
        ],
        capture_output=True,
        text=True,
        env=ENV,
        check=False,
    )

    assert result.returncode == 1
    assert json.loads(state_path.read_text(encoding="utf-8"))["run_id"] == "existing"
    assert "already exists" in result.stderr
