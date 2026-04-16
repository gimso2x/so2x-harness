from __future__ import annotations

import json
from pathlib import Path

from cli.commands.meta import create_meta_harness_state, render_run_id


def test_render_run_id_is_file_safe() -> None:
    run_id = render_run_id()
    assert ":" not in run_id
    assert "/" not in run_id
    assert run_id.endswith("Z")


def test_create_meta_harness_state_rewrites_paths_for_run_id() -> None:
    state = create_meta_harness_state(run_id="2026-04-16T11-10-00Z", harness_name="oauth-login")

    assert state["run_id"] == "2026-04-16T11-10-00Z"
    assert state["harness_name"] == "oauth-login"
    assert state["current_stage"] == "stage-0-interview"
    assert state["last_completed_stage"] is None
    assert state["interview_answers_path"] == "outputs/2026-04-16T11-10-00Z/interview/answers.json"
    assert state["artifacts"]["plan"] == "outputs/2026-04-16T11-10-00Z/plan/plan.md"
    assert state["updated_at"].endswith("Z")


def test_create_meta_harness_state_matches_schema_shape(tmp_path: Path) -> None:
    state = create_meta_harness_state(run_id="run-1", harness_name="sample-task")
    path = tmp_path / "_state.json"
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["status"] == "running"
    assert loaded["orchestration_class"] == "simple"
    assert loaded["capability_snapshot"]["resume_persistence"] is True
