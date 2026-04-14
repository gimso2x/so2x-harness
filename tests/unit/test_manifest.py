from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.lib.manifest import load_manifest, manifest_path, write_manifest


def test_manifest_path(tmp_project: Path) -> None:
    result = manifest_path(tmp_project)
    assert str(result).endswith(".ai-harness/manifest.json")


def test_write_and_load_manifest(tmp_project: Path, sample_manifest: dict) -> None:
    write_manifest(tmp_project, sample_manifest)
    loaded = load_manifest(tmp_project)
    assert loaded["name"] == "so2x-harness"
    assert loaded["version"] == "0.1.0"
    assert "CLAUDE.md" in loaded["files"]


def test_write_manifest_creates_directory(tmp_path: Path) -> None:
    project = tmp_path / "nested" / "project"
    project.mkdir(parents=True)
    write_manifest(project, {"name": "test", "version": "0.1.0", "files": {}})
    assert manifest_path(project).exists()


def test_load_manifest_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_manifest(tmp_path)


def test_manifest_json_valid(tmp_project: Path, sample_manifest: dict) -> None:
    write_manifest(tmp_project, sample_manifest)
    raw = manifest_path(tmp_project).read_text(encoding="utf-8")
    parsed = json.loads(raw)
    assert parsed == sample_manifest
