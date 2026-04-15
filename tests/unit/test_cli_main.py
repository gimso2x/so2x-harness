from __future__ import annotations

from importlib import metadata
from pathlib import Path

from cli.main import get_version

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
VERSION = (ROOT_DIR / "VERSION").read_text(encoding="utf-8").strip()


def test_get_version_reads_repo_version_file() -> None:
    assert get_version() == VERSION


def test_get_version_prefers_installed_package_metadata_when_version_file_missing(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(metadata, "version", lambda _: "9.9.9")

    assert get_version(tmp_path) == "9.9.9"
