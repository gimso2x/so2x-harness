from __future__ import annotations

import subprocess
from pathlib import Path

import tomllib
import yaml

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
VERSION = (ROOT_DIR / "VERSION").read_text(encoding="utf-8").strip()
README = (ROOT_DIR / "README.md").read_text(encoding="utf-8")
PYPROJECT = tomllib.loads((ROOT_DIR / "pyproject.toml").read_text(encoding="utf-8"))
HARNESS = yaml.safe_load((ROOT_DIR / "harness.yaml").read_text(encoding="utf-8"))


def test_repo_metadata_versions_are_aligned() -> None:
    assert PYPROJECT["project"]["version"] == VERSION
    assert HARNESS["version"] == VERSION
    assert f"Version-{VERSION}-green" in README


def test_cli_version_matches_repo_version() -> None:
    result = subprocess.run(
        ["python3", str(ROOT_DIR / "scripts/cli/main.py"), "--version"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == f"so2x-cli {VERSION}"
