from __future__ import annotations

import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def test_license_file_exists() -> None:
    assert (ROOT_DIR / "LICENSE").exists()


def test_readme_mentions_claude_code_scope() -> None:
    readme = (ROOT_DIR / "README.md").read_text(encoding="utf-8")
    assert "Claude Code 중심" in readme


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
