from __future__ import annotations

from pathlib import Path

import tomllib
import yaml

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
VERSION = (ROOT_DIR / "VERSION").read_text(encoding="utf-8").strip()
README = (ROOT_DIR / "README.md").read_text(encoding="utf-8")
PYPROJECT = tomllib.loads((ROOT_DIR / "pyproject.toml").read_text(encoding="utf-8"))
HARNESS = yaml.safe_load((ROOT_DIR / "harness.yaml").read_text(encoding="utf-8"))


def test_license_file_exists() -> None:
    assert (ROOT_DIR / "LICENSE").exists()


def test_readme_matches_thin_identity() -> None:
    assert "personal per-project harness" in README
    assert "lightweight orchestration scaffold" in README
    assert "core files = `CLAUDE.md` / `spec.json` / `harness.json`" in README
    assert "install/distribution kit가 기본 목표가 아님" in README
    assert "so2x run --file spec.json --next" in README


def test_repo_metadata_versions_are_aligned() -> None:
    assert PYPROJECT["project"]["name"] == "so2x-harness"
    assert PYPROJECT["project"]["version"] == VERSION
    assert HARNESS["version"] == VERSION
