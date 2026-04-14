from __future__ import annotations

import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def test_license_file_exists() -> None:
    assert (ROOT_DIR / "LICENSE").exists()


def test_readme_mentions_claude_code_scope() -> None:
    readme = (ROOT_DIR / "README.md").read_text(encoding="utf-8")
    assert "Claude Code 중심" in readme


def test_readme_documents_blocked_task_and_doctor_examples() -> None:
    readme = (ROOT_DIR / "README.md").read_text(encoding="utf-8")
    assert "set-task-status" in readme
    assert "blocked on task T1" in readme
    assert "latest summary: Waiting for approval from product owner" in readme


def test_readme_documents_review_cycle_artifacts() -> None:
    readme = (ROOT_DIR / "README.md").read_text(encoding="utf-8")
    assert "/review-cycle" in readme
    assert ".review-artifacts/" in readme


def test_architecture_documents_spec_and_doctor_status_surface() -> None:
    architecture = (ROOT_DIR / "ARCHITECTURE.md").read_text(encoding="utf-8")
    assert "spec.json이 canonical execution state" in architecture
    assert "execution_status" in architecture
    assert "blocked on task" in architecture


def test_apply_unsupported_platform_message_lists_supported_platforms(tmp_path: Path) -> None:
    project = tmp_path / "project"
    result = subprocess.run(
        [
            "python3",
            str(ROOT_DIR / "scripts/apply.py"),
            "--project",
            str(project),
            "--platform",
            "codex",
            "--preset",
            "general",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "currently supported: claude" in result.stderr
