from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from cli.commands.run import parse_runner_output
from doctor import render_doctor_lines
from runtime import build_prompt, load_latest_meta_harness_state

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CLI = ROOT_DIR / "scripts/cli/main.py"
ENV = {**os.environ, "PYTHONPATH": str(ROOT_DIR / "scripts")}


def test_parse_runner_output_markers() -> None:
    parsed = parse_runner_output(
        "STATUS: blocked\nSUMMARY: redirect URI 확인 필요\n",
        "",
    )
    assert parsed["status"] == "blocked"
    assert parsed["summary"] == "redirect URI 확인 필요"


def test_doctor_output_core_lines(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "CLAUDE.md").write_text("# rules\n", encoding="utf-8")
    (project / "harness.json").write_text("{}\n", encoding="utf-8")
    spec = {
        "meta": {
            "id": "SPEC-1",
            "goal": "OAuth 로그인 추가",
            "created_at": "2026-04-16T00:00:00+00:00",
            "updated_at": "2026-04-16T00:00:00+00:00",
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
                "updated_at": "2026-04-16T00:00:00+00:00",
            }
        ],
    }
    lines = render_doctor_lines(
        project,
        {"CLAUDE.md": True, "spec.json": True, "harness.json": True},
        spec,
    )
    output = "\n".join(lines)
    assert "project:" in output
    assert "goal: OAuth 로그인 추가" in output
    assert "next_task: none" in output
    assert "execution_status: blocked on T1" in output
    assert "summary: redirect URI 확인 필요" in output


def test_load_latest_meta_harness_state_prefers_most_recent_file(tmp_path: Path) -> None:
    project = tmp_path / "project"
    old_dir = project / "outputs" / "run-old"
    new_dir = project / "outputs" / "run-new"
    old_dir.mkdir(parents=True)
    new_dir.mkdir(parents=True)
    (old_dir / "_state.json").write_text('{"run_id": "run-old", "status": "running"}\n', encoding="utf-8")
    newest = new_dir / "_state.json"
    newest.write_text('{"run_id": "run-new", "status": "awaiting_input", "current_stage": "stage-2"}\n', encoding="utf-8")

    state = load_latest_meta_harness_state(project)

    assert state is not None
    assert state["run_id"] == "run-new"
    assert state["status"] == "awaiting_input"


def test_load_latest_meta_harness_state_honors_explicit_run_id(tmp_path: Path) -> None:
    project = tmp_path / "project"
    old_dir = project / "outputs" / "run-old"
    new_dir = project / "outputs" / "run-new"
    old_dir.mkdir(parents=True)
    new_dir.mkdir(parents=True)
    (old_dir / "_state.json").write_text('{"run_id": "run-old", "status": "running", "current_stage": "stage-1-plan"}\n', encoding="utf-8")
    (new_dir / "_state.json").write_text('{"run_id": "run-new", "status": "awaiting_input", "current_stage": "stage-3-review"}\n', encoding="utf-8")

    state = load_latest_meta_harness_state(project, run_id="run-old")

    assert state is not None
    assert state["run_id"] == "run-old"
    assert state["current_stage"] == "stage-1-plan"


def test_build_prompt_includes_meta_harness_resume_context() -> None:
    spec = {
        "meta": {"goal": "OAuth 로그인 추가"},
        "tasks": [],
    }
    task = {"id": "T2", "role": "dev", "action": "callback 구현", "depends_on": []}

    prompt = build_prompt(
        spec,
        task,
        rule_text="# rules",
        summaries=["이전 요약"],
        dependency_summaries=["T1: 흐름 정리 완료"],
        last_error="tests failed",
        meta_state={
            "run_id": "run-1",
            "status": "awaiting_input",
            "current_stage": "stage-3-review",
            "last_completed_stage": "stage-2-execute",
            "notes": ["final verdict requires sign-off"],
        },
    )

    assert "Meta harness state:" in prompt
    assert "RUN_ID: run-1" in prompt
    assert "STATUS: awaiting_input" in prompt
    assert "CURRENT_STAGE: stage-3-review" in prompt
    assert "LAST_COMPLETED_STAGE: stage-2-execute" in prompt
    assert "NOTES:" in prompt
    assert "- final verdict requires sign-off" in prompt


def test_run_command_applies_done_status(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "CLAUDE.md").write_text("# Goal\n", encoding="utf-8")
    runner = project / "runner.py"
    runner.write_text(
        "import sys\n"
        "sys.stdin.read()\n"
        "print('STATUS: done')\n"
        "print('SUMMARY: 로그인 버튼과 진입 흐름을 정리함')\n",
        encoding="utf-8",
    )
    (project / "harness.json").write_text(
        json.dumps(
            {
                "rule_file": "CLAUDE.md",
                "spec_file": "spec.json",
                "runners": {
                    "planning": ["python3", "runner.py"],
                    "review": ["python3", "runner.py"],
                    "dev": ["python3", "runner.py"],
                },
                "timeout_sec": {"default": 30},
                "max_retries": {"planning": 1, "review": 1, "dev": 3},
                "prompt": {
                    "include_rule_file": True,
                    "include_completed_summaries": True,
                    "include_last_error": True,
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (project / "spec.json").write_text(
        json.dumps(
            {
                "meta": {
                    "id": "SPEC-1",
                    "goal": "OAuth 로그인 추가",
                    "created_at": "2026-04-16T00:00:00+00:00",
                    "updated_at": "2026-04-16T00:00:00+00:00",
                },
                "tasks": [
                    {
                        "id": "T1",
                        "role": "dev",
                        "action": "callback 구현",
                        "status": "pending",
                        "summary": "",
                        "last_error": "",
                        "depends_on": [],
                        "artifacts": [],
                        "updated_at": "2026-04-16T00:00:00+00:00",
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["python3", str(CLI), "run", "--file", str(project / "spec.json"), "--next"],
        capture_output=True,
        text=True,
        env=ENV,
        check=False,
    )
    assert result.returncode == 0
    updated = json.loads((project / "spec.json").read_text(encoding="utf-8"))
    assert updated["tasks"][0]["status"] == "done"
    assert updated["tasks"][0]["summary"] == "로그인 버튼과 진입 흐름을 정리함"


def test_run_command_includes_meta_harness_state_in_runner_prompt(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "CLAUDE.md").write_text("# Goal\n", encoding="utf-8")
    (project / "outputs" / "run-1").mkdir(parents=True)
    (project / "outputs" / "run-1" / "_state.json").write_text(
        json.dumps(
            {
                "run_id": "run-1",
                "status": "awaiting_input",
                "current_stage": "stage-3-review",
                "last_completed_stage": "stage-2-execute",
                "notes": ["final verdict requires sign-off"],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    runner = project / "runner.py"
    prompt_capture = project / "prompt.txt"
    runner.write_text(
        "from pathlib import Path\n"
        "import sys\n"
        f"Path({str(prompt_capture)!r}).write_text(sys.stdin.read(), encoding='utf-8')\n"
        "print('STATUS: done')\n"
        "print('SUMMARY: meta harness prompt 확인')\n",
        encoding="utf-8",
    )
    (project / "harness.json").write_text(
        json.dumps(
            {
                "rule_file": "CLAUDE.md",
                "spec_file": "spec.json",
                "runners": {
                    "planning": ["python3", "runner.py"],
                    "review": ["python3", "runner.py"],
                    "dev": ["python3", "runner.py"],
                },
                "timeout_sec": {"default": 30},
                "max_retries": {"planning": 1, "review": 1, "dev": 1},
                "prompt": {
                    "include_rule_file": True,
                    "include_completed_summaries": True,
                    "include_last_error": True,
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (project / "spec.json").write_text(
        json.dumps(
            {
                "meta": {
                    "id": "SPEC-1",
                    "goal": "OAuth 로그인 추가",
                    "created_at": "2026-04-16T00:00:00+00:00",
                    "updated_at": "2026-04-16T00:00:00+00:00",
                },
                "tasks": [
                    {
                        "id": "T1",
                        "role": "dev",
                        "action": "callback 구현",
                        "status": "pending",
                        "summary": "",
                        "last_error": "",
                        "depends_on": [],
                        "artifacts": [],
                        "updated_at": "2026-04-16T00:00:00+00:00",
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["python3", str(CLI), "run", "--file", str(project / "spec.json"), "--next"],
        capture_output=True,
        text=True,
        env=ENV,
        check=False,
    )

    assert result.returncode == 0
    prompt_text = prompt_capture.read_text(encoding="utf-8")
    assert "Meta harness state:" in prompt_text
    assert "RUN_ID: run-1" in prompt_text
    assert "STATUS: awaiting_input" in prompt_text
    assert "CURRENT_STAGE: stage-3-review" in prompt_text


def test_run_command_honors_explicit_run_id_for_prompt_and_write(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "CLAUDE.md").write_text("# Goal\n", encoding="utf-8")
    old_dir = project / "outputs" / "run-old"
    new_dir = project / "outputs" / "run-new"
    old_dir.mkdir(parents=True)
    new_dir.mkdir(parents=True)
    old_state_path = old_dir / "_state.json"
    new_state_path = new_dir / "_state.json"
    old_state_path.write_text(
        json.dumps(
            {
                "version": 1,
                "run_id": "run-old",
                "harness_name": "sample-task",
                "status": "running",
                "orchestration_class": "simple",
                "current_stage": "stage-1-plan",
                "last_completed_stage": "stage-0-interview",
                "awaiting_input": False,
                "awaiting_input_schema": None,
                "interview_answers_path": "outputs/run-old/interview/answers.json",
                "artifacts": {},
                "intervention_points": [],
                "capability_snapshot": {
                    "delegation": True,
                    "nested_delegation": False,
                    "background_execution": True,
                    "resume_persistence": True,
                    "structured_artifact_validation": True,
                },
                "notes": [],
                "updated_at": "2026-04-16T00:00:00+00:00",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    new_state_path.write_text(
        json.dumps(
            {
                "version": 1,
                "run_id": "run-new",
                "harness_name": "sample-task",
                "status": "awaiting_input",
                "orchestration_class": "simple",
                "current_stage": "stage-3-review",
                "last_completed_stage": "stage-2-execute",
                "awaiting_input": True,
                "awaiting_input_schema": None,
                "interview_answers_path": "outputs/run-new/interview/answers.json",
                "artifacts": {},
                "intervention_points": [],
                "capability_snapshot": {
                    "delegation": True,
                    "nested_delegation": False,
                    "background_execution": True,
                    "resume_persistence": True,
                    "structured_artifact_validation": True,
                },
                "notes": [],
                "updated_at": "2026-04-17T00:00:00+00:00",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    runner = project / "runner.py"
    prompt_capture = project / "prompt.txt"
    runner.write_text(
        "from pathlib import Path\n"
        "import sys\n"
        f"Path({str(prompt_capture)!r}).write_text(sys.stdin.read(), encoding='utf-8')\n"
        "print('STATUS: blocked')\n"
        "print('SUMMARY: old run needs input')\n",
        encoding="utf-8",
    )
    (project / "harness.json").write_text(
        json.dumps(
            {
                "rule_file": "CLAUDE.md",
                "spec_file": "spec.json",
                "runners": {
                    "planning": ["python3", "runner.py"],
                    "review": ["python3", "runner.py"],
                    "dev": ["python3", "runner.py"],
                },
                "timeout_sec": {"default": 30},
                "max_retries": {"planning": 0, "review": 0, "dev": 0},
                "prompt": {
                    "include_rule_file": True,
                    "include_completed_summaries": True,
                    "include_last_error": True,
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (project / "spec.json").write_text(
        json.dumps(
            {
                "meta": {
                    "id": "SPEC-1",
                    "goal": "OAuth 로그인 추가",
                    "created_at": "2026-04-16T00:00:00+00:00",
                    "updated_at": "2026-04-16T00:00:00+00:00",
                },
                "tasks": [
                    {
                        "id": "T1",
                        "role": "dev",
                        "action": "callback 구현",
                        "status": "pending",
                        "summary": "",
                        "last_error": "",
                        "depends_on": [],
                        "artifacts": [],
                        "updated_at": "2026-04-16T00:00:00+00:00",
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["python3", str(CLI), "run", "--file", str(project / "spec.json"), "--next", "--run-id", "run-old"],
        capture_output=True,
        text=True,
        env=ENV,
        check=False,
    )

    assert result.returncode == 0
    prompt_text = prompt_capture.read_text(encoding="utf-8")
    assert "RUN_ID: run-old" in prompt_text
    updated_old = json.loads(old_state_path.read_text(encoding="utf-8"))
    updated_new = json.loads(new_state_path.read_text(encoding="utf-8"))
    assert updated_old["status"] == "awaiting_input"
    assert any("T1 blocked: old run needs input" in note for note in updated_old["notes"])
    assert updated_new["run_id"] == "run-new"
    assert updated_new["current_stage"] == "stage-3-review"


def test_run_command_updates_meta_harness_state_file(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "CLAUDE.md").write_text("# Goal\n", encoding="utf-8")
    state_dir = project / "outputs" / "run-1"
    state_dir.mkdir(parents=True)
    state_path = state_dir / "_state.json"
    state_path.write_text(
        json.dumps(
            {
                "version": 1,
                "run_id": "run-1",
                "harness_name": "sample-task",
                "status": "running",
                "orchestration_class": "simple",
                "current_stage": "stage-2-execute",
                "last_completed_stage": "stage-1-plan",
                "awaiting_input": False,
                "awaiting_input_schema": None,
                "interview_answers_path": "outputs/run-1/interview/answers.json",
                "artifacts": {"plan": "outputs/run-1/plan/plan.md"},
                "intervention_points": [],
                "capability_snapshot": {
                    "delegation": True,
                    "nested_delegation": False,
                    "background_execution": True,
                    "resume_persistence": True,
                    "structured_artifact_validation": True
                },
                "notes": [],
                "updated_at": "2026-04-16T00:00:00+00:00"
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    runner = project / "runner.py"
    runner.write_text(
        "import sys\n"
        "sys.stdin.read()\n"
        "print('STATUS: blocked')\n"
        "print('SUMMARY: 사용자 입력 필요')\n",
        encoding="utf-8",
    )
    (project / "harness.json").write_text(
        json.dumps(
            {
                "rule_file": "CLAUDE.md",
                "spec_file": "spec.json",
                "runners": {
                    "planning": ["python3", "runner.py"],
                    "review": ["python3", "runner.py"],
                    "dev": ["python3", "runner.py"],
                },
                "timeout_sec": {"default": 30},
                "max_retries": {"planning": 0, "review": 0, "dev": 0},
                "prompt": {
                    "include_rule_file": True,
                    "include_completed_summaries": True,
                    "include_last_error": True,
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (project / "spec.json").write_text(
        json.dumps(
            {
                "meta": {
                    "id": "SPEC-1",
                    "goal": "OAuth 로그인 추가",
                    "created_at": "2026-04-16T00:00:00+00:00",
                    "updated_at": "2026-04-16T00:00:00+00:00",
                },
                "tasks": [
                    {
                        "id": "T1",
                        "role": "dev",
                        "action": "callback 구현",
                        "status": "pending",
                        "summary": "",
                        "last_error": "",
                        "depends_on": [],
                        "artifacts": [],
                        "updated_at": "2026-04-16T00:00:00+00:00",
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["python3", str(CLI), "run", "--file", str(project / "spec.json"), "--next"],
        capture_output=True,
        text=True,
        env=ENV,
        check=False,
    )

    assert result.returncode == 0
    updated_state = json.loads(state_path.read_text(encoding="utf-8"))
    assert updated_state["status"] == "awaiting_input"
    assert updated_state["awaiting_input"] is True
    assert updated_state["current_stage"] == "stage-2-execute"
    assert updated_state["last_completed_stage"] == "stage-1-plan"
    assert any("T1 blocked: 사용자 입력 필요" in note for note in updated_state["notes"])


def test_run_command_advances_meta_harness_stage_on_done(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "CLAUDE.md").write_text("# Goal\n", encoding="utf-8")
    state_dir = project / "outputs" / "run-1"
    state_dir.mkdir(parents=True)
    state_path = state_dir / "_state.json"
    state_path.write_text(
        json.dumps(
            {
                "version": 1,
                "run_id": "run-1",
                "harness_name": "sample-task",
                "status": "running",
                "orchestration_class": "simple",
                "current_stage": "stage-2-execute",
                "last_completed_stage": "stage-1-plan",
                "awaiting_input": False,
                "awaiting_input_schema": None,
                "interview_answers_path": "outputs/run-1/interview/answers.json",
                "artifacts": {"plan": "outputs/run-1/plan/plan.md"},
                "intervention_points": [],
                "capability_snapshot": {
                    "delegation": True,
                    "nested_delegation": False,
                    "background_execution": True,
                    "resume_persistence": True,
                    "structured_artifact_validation": True
                },
                "notes": [],
                "updated_at": "2026-04-16T00:00:00+00:00"
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    runner = project / "runner.py"
    runner.write_text(
        "import sys\n"
        "sys.stdin.read()\n"
        "print('STATUS: done')\n"
        "print('SUMMARY: 실행 완료')\n",
        encoding="utf-8",
    )
    (project / "harness.json").write_text(
        json.dumps(
            {
                "rule_file": "CLAUDE.md",
                "spec_file": "spec.json",
                "runners": {
                    "planning": ["python3", "runner.py"],
                    "review": ["python3", "runner.py"],
                    "dev": ["python3", "runner.py"],
                },
                "timeout_sec": {"default": 30},
                "max_retries": {"planning": 0, "review": 0, "dev": 0},
                "prompt": {
                    "include_rule_file": True,
                    "include_completed_summaries": True,
                    "include_last_error": True,
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (project / "spec.json").write_text(
        json.dumps(
            {
                "meta": {
                    "id": "SPEC-1",
                    "goal": "OAuth 로그인 추가",
                    "created_at": "2026-04-16T00:00:00+00:00",
                    "updated_at": "2026-04-16T00:00:00+00:00",
                },
                "tasks": [
                    {
                        "id": "T1",
                        "role": "dev",
                        "action": "callback 구현",
                        "status": "pending",
                        "summary": "",
                        "last_error": "",
                        "depends_on": [],
                        "artifacts": [],
                        "updated_at": "2026-04-16T00:00:00+00:00",
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["python3", str(CLI), "run", "--file", str(project / "spec.json"), "--next"],
        capture_output=True,
        text=True,
        env=ENV,
        check=False,
    )

    assert result.returncode == 0
    updated_state = json.loads(state_path.read_text(encoding="utf-8"))
    assert updated_state["status"] == "running"
    assert updated_state["awaiting_input"] is False
    assert updated_state["awaiting_input_schema"] is None
    assert updated_state["last_completed_stage"] == "stage-2-execute"
    assert updated_state["current_stage"] == "stage-3-review"
    assert any("T1 done: 실행 완료" in note for note in updated_state["notes"])


def test_run_command_marks_meta_harness_completed_on_finalize_done(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "CLAUDE.md").write_text("# Goal\n", encoding="utf-8")
    state_dir = project / "outputs" / "run-1"
    state_dir.mkdir(parents=True)
    state_path = state_dir / "_state.json"
    state_path.write_text(
        json.dumps(
            {
                "version": 1,
                "run_id": "run-1",
                "harness_name": "sample-task",
                "status": "running",
                "orchestration_class": "simple",
                "current_stage": "stage-4-finalize",
                "last_completed_stage": "stage-3-review",
                "awaiting_input": False,
                "awaiting_input_schema": None,
                "interview_answers_path": "outputs/run-1/interview/answers.json",
                "artifacts": {},
                "intervention_points": [],
                "capability_snapshot": {
                    "delegation": True,
                    "nested_delegation": False,
                    "background_execution": True,
                    "resume_persistence": True,
                    "structured_artifact_validation": True
                },
                "notes": [],
                "updated_at": "2026-04-16T00:00:00+00:00"
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    runner = project / "runner.py"
    runner.write_text(
        "import sys\n"
        "sys.stdin.read()\n"
        "print('STATUS: done')\n"
        "print('SUMMARY: 최종 정리 완료')\n",
        encoding="utf-8",
    )
    (project / "harness.json").write_text(
        json.dumps(
            {
                "rule_file": "CLAUDE.md",
                "spec_file": "spec.json",
                "runners": {
                    "planning": ["python3", "runner.py"],
                    "review": ["python3", "runner.py"],
                    "dev": ["python3", "runner.py"],
                },
                "timeout_sec": {"default": 30},
                "max_retries": {"planning": 0, "review": 0, "dev": 0},
                "prompt": {
                    "include_rule_file": True,
                    "include_completed_summaries": True,
                    "include_last_error": True,
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (project / "spec.json").write_text(
        json.dumps(
            {
                "meta": {
                    "id": "SPEC-1",
                    "goal": "OAuth 로그인 추가",
                    "created_at": "2026-04-16T00:00:00+00:00",
                    "updated_at": "2026-04-16T00:00:00+00:00",
                },
                "tasks": [
                    {
                        "id": "T1",
                        "role": "dev",
                        "action": "callback 구현",
                        "status": "pending",
                        "summary": "",
                        "last_error": "",
                        "depends_on": [],
                        "artifacts": [],
                        "updated_at": "2026-04-16T00:00:00+00:00",
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["python3", str(CLI), "run", "--file", str(project / "spec.json"), "--next"],
        capture_output=True,
        text=True,
        env=ENV,
        check=False,
    )

    assert result.returncode == 0
    updated_state = json.loads(state_path.read_text(encoding="utf-8"))
    assert updated_state["status"] == "completed"
    assert updated_state["awaiting_input"] is False
    assert updated_state["awaiting_input_schema"] is None
    assert updated_state["last_completed_stage"] == "stage-4-finalize"
    assert updated_state["current_stage"] == "stage-4-finalize"


def test_run_command_applies_blocked_and_error_statuses(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "CLAUDE.md").write_text("# Goal\n", encoding="utf-8")
    blocked_runner = project / "blocked_runner.py"
    blocked_runner.write_text(
        "import sys\n"
        "sys.stdin.read()\n"
        "print('STATUS: blocked')\n"
        "print('SUMMARY: redirect URI 확인 필요')\n",
        encoding="utf-8",
    )
    error_runner = project / "error_runner.py"
    error_runner.write_text(
        "import sys\n"
        "sys.stdin.read()\n"
        "print('STATUS: error')\n"
        "print('ERROR: tests failed in auth callback flow')\n",
        encoding="utf-8",
    )

    def write_project(runner_name: str) -> None:
        (project / "harness.json").write_text(
            json.dumps(
                {
                    "rule_file": "CLAUDE.md",
                    "spec_file": "spec.json",
                    "runners": {
                        "planning": ["python3", runner_name],
                        "review": ["python3", runner_name],
                        "dev": ["python3", runner_name],
                    },
                    "timeout_sec": {"default": 30},
                    "max_retries": {"planning": 0, "review": 0, "dev": 0},
                    "prompt": {
                        "include_rule_file": True,
                        "include_completed_summaries": True,
                        "include_last_error": True,
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (project / "spec.json").write_text(
            json.dumps(
                {
                    "meta": {
                        "id": "SPEC-1",
                        "goal": "OAuth 로그인 추가",
                        "created_at": "2026-04-16T00:00:00+00:00",
                        "updated_at": "2026-04-16T00:00:00+00:00",
                    },
                    "tasks": [
                        {
                            "id": "T1",
                            "role": "dev",
                            "action": "callback 구현",
                            "status": "pending",
                            "summary": "",
                            "last_error": "",
                            "depends_on": [],
                            "artifacts": [],
                            "updated_at": "2026-04-16T00:00:00+00:00",
                        }
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    write_project("blocked_runner.py")
    blocked = subprocess.run(
        ["python3", str(CLI), "run", "--file", str(project / "spec.json"), "--next"],
        capture_output=True,
        text=True,
        env=ENV,
        check=False,
    )
    assert blocked.returncode == 0
    updated = json.loads((project / "spec.json").read_text(encoding="utf-8"))
    assert updated["tasks"][0]["status"] == "blocked"
    assert updated["tasks"][0]["summary"] == "redirect URI 확인 필요"

    write_project("error_runner.py")
    errored = subprocess.run(
        ["python3", str(CLI), "run", "--file", str(project / "spec.json"), "--next"],
        capture_output=True,
        text=True,
        env=ENV,
        check=False,
    )
    assert errored.returncode == 1
    updated = json.loads((project / "spec.json").read_text(encoding="utf-8"))
    assert updated["tasks"][0]["status"] == "error"
    assert updated["tasks"][0]["last_error"] == "tests failed in auth callback flow"
