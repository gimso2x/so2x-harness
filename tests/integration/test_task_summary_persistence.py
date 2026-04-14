from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CLI = ROOT_DIR / "scripts/cli/main.py"
ENV = {**os.environ, "PYTHONPATH": str(ROOT_DIR / "scripts")}


def _write_spec(path: Path) -> None:
    spec = {
        "meta": {
            "id": "SPEC-SUMMARY-001",
            "goal": "Persist task summary",
            "status": "draft",
            "mode": "standard",
            "created_at": "2026-04-15T00:00:00+00:00",
            "updated_at": "2026-04-15T00:00:00+00:00",
        },
        "chain": {
            "l0_goal": "Persist task summary",
            "l4_tasks": [
                {
                    "id": "T1",
                    "action": "Wait for approval",
                    "requirement_refs": ["R1"],
                    "status": "pending",
                }
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


def test_spec_set_task_status_persists_summary_for_blocked(tmp_path: Path) -> None:
    spec_file = tmp_path / "spec.json"
    _write_spec(spec_file)

    result = subprocess.run(
        [
            "python3",
            str(CLI),
            "spec",
            "set-task-status",
            str(spec_file),
            "--task-id",
            "T1",
            "--status",
            "blocked",
            "--summary",
            "Waiting for user approval",
        ],
        capture_output=True,
        text=True,
        check=False,
        env=ENV,
    )

    assert result.returncode == 0
    saved = json.loads(spec_file.read_text(encoding="utf-8"))
    task = saved["chain"]["l4_tasks"][0]
    assert task["status"] == "blocked"
    assert task["summary"] == "Waiting for user approval"


def test_spec_set_task_status_overwrites_existing_summary(tmp_path: Path) -> None:
    spec_file = tmp_path / "spec.json"
    _write_spec(spec_file)

    first = subprocess.run(
        [
            "python3",
            str(CLI),
            "spec",
            "set-task-status",
            str(spec_file),
            "--task-id",
            "T1",
            "--status",
            "blocked",
            "--summary",
            "Waiting for user approval",
        ],
        capture_output=True,
        text=True,
        check=False,
        env=ENV,
    )
    assert first.returncode == 0

    second = subprocess.run(
        [
            "python3",
            str(CLI),
            "spec",
            "set-task-status",
            str(spec_file),
            "--task-id",
            "T1",
            "--status",
            "done",
            "--summary",
            "Approved and completed",
        ],
        capture_output=True,
        text=True,
        check=False,
        env=ENV,
    )

    assert second.returncode == 0
    saved = json.loads(spec_file.read_text(encoding="utf-8"))
    task = saved["chain"]["l4_tasks"][0]
    assert task["status"] == "done"
    assert task["summary"] == "Approved and completed"
