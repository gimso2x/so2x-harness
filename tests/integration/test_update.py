from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.lib.manifest import load_manifest, manifest_path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def _apply(project: Path, preset: str = "general") -> None:
    import subprocess

    subprocess.run(
        ["python3", str(ROOT_DIR / "scripts/apply.py"), "--project", str(project), "--platform", "claude", "--preset", preset],
        capture_output=True,
        text=True,
        check=True,
    )


def _update(project: Path) -> None:
    import subprocess

    subprocess.run(
        ["python3", str(ROOT_DIR / "scripts/update.py"), "--project", str(project)],
        capture_output=True,
        text=True,
        check=True,
    )


def test_update_after_apply(tmp_project: Path) -> None:
    _apply(tmp_project)
    _update(tmp_project)
    manifest = load_manifest(tmp_project)
    assert "files" in manifest
    assert len(manifest["files"]) >= 10


def test_update_preserves_local_edits(tmp_project: Path) -> None:
    _apply(tmp_project)
    claude_md = tmp_project / "CLAUDE.md"
    original = claude_md.read_text(encoding="utf-8")
    # Add local content before marker
    local_note = "\n## Local Notes\n\nThis is my project note.\n"
    modified = local_note + original
    claude_md.write_text(modified, encoding="utf-8")

    _update(tmp_project)

    updated = claude_md.read_text(encoding="utf-8")
    assert "Local Notes" in updated
    assert "This is my project note." in updated


def test_update_without_manifest_fails(tmp_project: Path) -> None:
    import subprocess

    result = subprocess.run(
        ["python3", str(ROOT_DIR / "scripts/update.py"), "--project", str(tmp_project)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0


def test_update_overwrite_files_refreshed(tmp_project: Path) -> None:
    _apply(tmp_project)
    rules_dir = tmp_project / ".claude" / "rules" / "so2x-harness"
    rule_file = rules_dir / "language-policy.md"
    rule_file.write_text("tampered content", encoding="utf-8")

    _update(tmp_project)
    # After update, overwrite files should be restored
    restored = rule_file.read_text(encoding="utf-8")
    assert restored != "tampered content"
