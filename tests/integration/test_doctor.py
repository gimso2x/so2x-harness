from __future__ import annotations

import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def test_doctor_on_minimal_project(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "CLAUDE.md").write_text("# Goal\n", encoding="utf-8")
    (project / "harness.json").write_text("{}\n", encoding="utf-8")
    (project / "spec.json").write_text(
        """
{
  "meta": {
    "id": "SPEC-1",
    "goal": "OAuth 로그인 추가",
    "created_at": "2026-04-16T00:00:00+00:00",
    "updated_at": "2026-04-16T00:00:00+00:00"
  },
  "tasks": [
    {
      "id": "T1",
      "role": "dev",
      "action": "OAuth callback 처리 구현",
      "status": "blocked",
      "summary": "redirect URI 확인 필요",
      "last_error": "",
      "depends_on": [],
      "artifacts": [],
      "updated_at": "2026-04-16T00:00:00+00:00"
    }
  ]
}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["python3", str(ROOT_DIR / "scripts/doctor.py"), "--project", str(project)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "[INFO] project:" in result.stdout
    assert "[OK] goal: OAuth 로그인 추가" in result.stdout
    assert "[WARN] next_task: none" in result.stdout
    assert "[WARN] execution_status: blocked on T1" in result.stdout
    assert "[OK] summary: redirect URI 확인 필요" in result.stdout
    assert "[OK] counts: pending=0 in_progress=0 blocked=1 error=0 done=0" in result.stdout


def test_doctor_surfaces_meta_harness_state(tmp_path: Path) -> None:
    project = tmp_path / "project"
    state_dir = project / "outputs" / "run-1"
    state_dir.mkdir(parents=True)
    (project / "CLAUDE.md").write_text("# Goal\n", encoding="utf-8")
    (project / "harness.json").write_text("{}\n", encoding="utf-8")
    (project / "spec.json").write_text(
        """
{
  "meta": {
    "id": "SPEC-1",
    "goal": "Meta harness 상태 노출",
    "created_at": "2026-04-16T00:00:00+00:00",
    "updated_at": "2026-04-16T00:00:00+00:00"
  },
  "tasks": []
}
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (state_dir / "_state.json").write_text(
        """
{
  "version": 1,
  "run_id": "run-1",
  "harness_name": "sample-task",
  "status": "awaiting_input",
  "orchestration_class": "simple",
  "current_stage": "stage-3-review",
  "last_completed_stage": "stage-2-execute",
  "awaiting_input": true,
  "awaiting_input_schema": null,
  "interview_answers_path": "outputs/run-1/interview/answers.json",
  "artifacts": {
    "plan": "outputs/run-1/plan/plan.md"
  },
  "intervention_points": [],
  "capability_snapshot": {
    "delegation": true,
    "nested_delegation": false,
    "background_execution": true,
    "resume_persistence": true,
    "structured_artifact_validation": true
  },
  "notes": [],
  "updated_at": "2026-04-16T00:00:00+00:00"
}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["python3", str(ROOT_DIR / "scripts/doctor.py"), "--project", str(project)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "[OK] meta_harness_status: awaiting_input" in result.stdout
    assert "[OK] meta_harness_stage: stage-3-review" in result.stdout
    assert "[OK] meta_harness_run: run-1" in result.stdout


def test_doctor_honors_explicit_run_id(tmp_path: Path) -> None:
    project = tmp_path / "project"
    run_old = project / "outputs" / "run-old"
    run_new = project / "outputs" / "run-new"
    run_old.mkdir(parents=True)
    run_new.mkdir(parents=True)
    (project / "CLAUDE.md").write_text("# Goal\n", encoding="utf-8")
    (project / "harness.json").write_text("{}\n", encoding="utf-8")
    (project / "spec.json").write_text('{"meta":{"id":"SPEC-1","goal":"Meta harness 상태 노출","created_at":"2026-04-16T00:00:00+00:00","updated_at":"2026-04-16T00:00:00+00:00"},"tasks":[]}\n', encoding="utf-8")
    (run_old / "_state.json").write_text('{"version":1,"run_id":"run-old","harness_name":"sample-task","status":"running","orchestration_class":"simple","current_stage":"stage-1-plan","last_completed_stage":"stage-0-interview","awaiting_input":false,"awaiting_input_schema":null,"interview_answers_path":"outputs/run-old/interview/answers.json","artifacts":{},"intervention_points":[],"capability_snapshot":{"delegation":true,"nested_delegation":false,"background_execution":true,"resume_persistence":true,"structured_artifact_validation":true},"notes":[],"updated_at":"2026-04-16T00:00:00+00:00"}\n', encoding="utf-8")
    (run_new / "_state.json").write_text('{"version":1,"run_id":"run-new","harness_name":"sample-task","status":"awaiting_input","orchestration_class":"simple","current_stage":"stage-3-review","last_completed_stage":"stage-2-execute","awaiting_input":true,"awaiting_input_schema":null,"interview_answers_path":"outputs/run-new/interview/answers.json","artifacts":{},"intervention_points":[],"capability_snapshot":{"delegation":true,"nested_delegation":false,"background_execution":true,"resume_persistence":true,"structured_artifact_validation":true},"notes":[],"updated_at":"2026-04-17T00:00:00+00:00"}\n', encoding="utf-8")

    result = subprocess.run(
        ["python3", str(ROOT_DIR / "scripts/doctor.py"), "--project", str(project), "--run-id", "run-old"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "[OK] meta_harness_run: run-old" in result.stdout
    assert "[OK] meta_harness_stage: stage-1-plan" in result.stdout
