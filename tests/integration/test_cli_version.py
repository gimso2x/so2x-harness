from __future__ import annotations

import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CLI = ROOT_DIR / "scripts/cli/main.py"
VERSION = (ROOT_DIR / "VERSION").read_text(encoding="utf-8").strip()


def test_cli_version_matches_repo_version() -> None:
    result = subprocess.run(
        ["python3", str(CLI), "--version"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == f"so2x {VERSION}"
