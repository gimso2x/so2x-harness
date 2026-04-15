from __future__ import annotations

import pytest
from pathlib import Path
from lib.install import (
    Capability,
    SUPPORTED_PLATFORMS,
    DEFAULT_PLATFORM,
    write_text,
    install_copy_file,
    keep_existing_file,
)


def test_capability_constants():
    assert Capability.RULES == "rules"
    assert Capability.SKILLS == "skills"
    assert Capability.AGENTS == "agents"
    assert Capability.HOOKS == "hooks"


def test_supported_platforms():
    assert "claude" in SUPPORTED_PLATFORMS
    assert "codex" in SUPPORTED_PLATFORMS


def test_default_platform():
    assert DEFAULT_PLATFORM == "claude"


def test_write_text(tmp_path: Path) -> None:
    target = tmp_path / "sub" / "test.txt"
    write_text(target, "hello")
    assert target.read_text() == "hello"


def test_install_copy_file(tmp_path: Path) -> None:
    src = tmp_path / "src.txt"
    src.write_text("content", encoding="utf-8")
    dst = tmp_path / "dst.txt"
    checksum = install_copy_file(src, dst)
    assert dst.read_text() == "content"
    assert checksum.startswith("sha256:")


def test_keep_existing_file(tmp_path: Path) -> None:
    existing = tmp_path / "existing.txt"
    existing.write_text("data", encoding="utf-8")
    checksum = keep_existing_file(existing)
    assert checksum.startswith("sha256:")
