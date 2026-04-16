from __future__ import annotations

from cli.commands.spec import (
    create_initial_spec,
    get_next_task,
    set_task_status,
    summarize_spec,
)


def _spec() -> dict:
    spec = create_initial_spec("OAuth 로그인 추가", spec_id="SPEC-TEST-001")
    spec["tasks"] = [
        {
            "id": "T1",
            "role": "planning",
            "action": "흐름 정리",
            "status": "pending",
            "summary": "",
            "last_error": "",
            "depends_on": [],
            "artifacts": [],
            "updated_at": spec["meta"]["updated_at"],
        },
        {
            "id": "T2",
            "role": "dev",
            "action": "callback 구현",
            "status": "pending",
            "summary": "",
            "last_error": "",
            "depends_on": ["T1"],
            "artifacts": [],
            "updated_at": spec["meta"]["updated_at"],
        },
    ]
    return spec


def test_spec_init_generation() -> None:
    spec = create_initial_spec("OAuth 로그인 추가", spec_id="SPEC-OAUTH-001")
    assert spec["meta"]["goal"] == "OAuth 로그인 추가"
    assert spec["meta"]["id"] == "SPEC-OAUTH-001"
    assert spec["tasks"] == []


def test_next_runnable_task_selection() -> None:
    task = get_next_task(_spec())
    assert task is not None
    assert task["id"] == "T1"


def test_next_excludes_unsatisfied_dependency() -> None:
    spec = _spec()
    spec["tasks"][0]["status"] = "blocked"
    assert get_next_task(spec) is None


def test_set_status_updates_summary() -> None:
    spec = set_task_status(_spec(), "T1", "done", summary="계획 정리 완료")
    assert spec["tasks"][0]["status"] == "done"
    assert spec["tasks"][0]["summary"] == "계획 정리 완료"


def test_summarize_spec_counts() -> None:
    spec = _spec()
    spec = set_task_status(spec, "T1", "done", summary="done")
    summary = summarize_spec(spec)
    assert summary["counts"]["done"] == 1
    assert summary["counts"]["pending"] == 1
