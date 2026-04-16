from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from cli.commands.run import parse_runner_output
from doctor import render_doctor_lines

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
    lines = render_doctor_lines(project, {"CLAUDE.md": True, "spec.json": True, "harness.json": True}, spec)
    output = "\n".join(lines)
    assert "project=" in output
    assert "goal: OAuth 로그인 추가" in output
    assert "next_task: none" in output
    assert "execution_status: blocked on T1" in output
    assert "latest summary: redirect URI 확인 필요" in output


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
