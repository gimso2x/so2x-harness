from __future__ import annotations

import json
from pathlib import Path

from meta_state import load_meta_harness_state, resolve_meta_harness_state_path


def test_resolve_meta_harness_state_path_honors_explicit_run_id(tmp_path: Path) -> None:
    project = tmp_path / "project"
    state_dir = project / "outputs" / "run-1"
    state_dir.mkdir(parents=True)
    state_path = state_dir / "_state.json"
    state_path.write_text('{"run_id": "run-1"}\n', encoding="utf-8")

    resolved = resolve_meta_harness_state_path(project, run_id="run-1")

    assert resolved == state_path


def test_load_meta_harness_state_uses_harness_active_run_id_when_present(tmp_path: Path) -> None:
    project = tmp_path / "project"
    run_old = project / "outputs" / "run-old"
    run_new = project / "outputs" / "run-new"
    run_old.mkdir(parents=True)
    run_new.mkdir(parents=True)
    (project / "harness.json").write_text('{"active_run_id": "run-old"}\n', encoding="utf-8")
    (run_old / "_state.json").write_text(json.dumps({"run_id": "run-old", "current_stage": "stage-1-plan"}) + "\n", encoding="utf-8")
    (run_new / "_state.json").write_text(json.dumps({"run_id": "run-new", "current_stage": "stage-3-review"}) + "\n", encoding="utf-8")

    state = load_meta_harness_state(project)

    assert state is not None
    assert state["run_id"] == "run-old"
    assert state["current_stage"] == "stage-1-plan"


def test_load_meta_harness_state_falls_back_when_active_run_is_missing(tmp_path: Path) -> None:
    project = tmp_path / "project"
    run_new = project / "outputs" / "run-new"
    run_new.mkdir(parents=True)
    (project / "harness.json").write_text('{"active_run_id": "run-missing"}\n', encoding="utf-8")
    (run_new / "_state.json").write_text(
        json.dumps({"run_id": "run-new", "current_stage": "stage-3-review"}) + "\n",
        encoding="utf-8",
    )

    state = load_meta_harness_state(project)

    assert state is not None
    assert state["run_id"] == "run-new"
