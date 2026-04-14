from __future__ import annotations

from pathlib import Path
import sys

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT_DIR / "scripts"
TEMPLATES_DIR = ROOT_DIR / "templates"

sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))


@pytest.fixture()
def tmp_project(tmp_path: Path) -> Path:
    project = tmp_path / "test-project"
    project.mkdir()
    (project / "package.json").write_text('{"name": "test-project"}', encoding="utf-8")
    return project


@pytest.fixture()
def templates_dir() -> Path:
    return TEMPLATES_DIR


@pytest.fixture()
def sample_manifest() -> dict:
    return {
        "name": "so2x-harness",
        "version": "0.1.0",
        "platforms": ["claude"],
        "installed_at": "2026-04-14T10:30:00+00:00",
        "files": {
            "CLAUDE.md": {
                "mode": "marker",
                "marker": "SO2X-HARNESS",
                "checksum": "sha256:abc123",
            },
            ".claude/rules/so2x-harness/language-policy.md": {
                "mode": "overwrite",
                "checksum": "sha256:def456",
            },
        },
    }
