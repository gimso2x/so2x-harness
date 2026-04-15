from __future__ import annotations

import json
from pathlib import Path

from scripts.lib.manifest import load_manifest

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def _apply(project: Path, preset: str = "general") -> None:
    import subprocess

    subprocess.run(
        [
            "python3",
            str(ROOT_DIR / "scripts/apply.py"),
            "--project",
            str(project),
            "--platform",
            "claude",
            "--preset",
            preset,
        ],
        capture_output=True,
        text=True,
        check=True,
    )


def _apply_codex(project: Path) -> None:
    import subprocess

    subprocess.run(
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
    local_note = "\n## Local Notes\n\nThis is my project note.\n"
    claude_md.write_text(local_note + original, encoding="utf-8")

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
    rule_file = tmp_project / ".claude" / "rules" / "so2x-harness" / "language-policy.md"
    rule_file.write_text("tampered content", encoding="utf-8")

    _update(tmp_project)

    restored = rule_file.read_text(encoding="utf-8")
    assert restored != "tampered content"


def test_update_after_codex_apply(tmp_project: Path) -> None:
    _apply_codex(tmp_project)
    _update(tmp_project)

    manifest = load_manifest(tmp_project)
    assert manifest["platforms"] == ["codex"]
    assert (tmp_project / ".agents" / "skills").exists()


def test_update_recreates_valid_config_with_platforms(tmp_project: Path) -> None:
    _apply_codex(tmp_project)
    config = tmp_project / ".ai-harness" / "config.json"
    config.unlink()

    _update(tmp_project)

    data = json.loads(config.read_text(encoding="utf-8"))
    assert data["preset"] == "general"
    assert data["platforms"] == ["codex"]


def test_update_resyncs_enabled_skills_from_preset(tmp_project: Path) -> None:
    _apply(tmp_project)
    config = tmp_project / ".ai-harness" / "config.json"
    data = json.loads(config.read_text(encoding="utf-8"))
    data["enabled_skills"] = ["execute"]
    config.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    _update(tmp_project)

    updated = json.loads(config.read_text(encoding="utf-8"))
    assert "planning" in updated["enabled_skills"]
    assert "execute" not in updated["enabled_skills"]


def test_update_removes_stale_skill_directories(tmp_project: Path) -> None:
    _apply(tmp_project)
    stale_dir = tmp_project / ".claude" / "skills" / "execute"
    stale_dir.mkdir(parents=True)
    (stale_dir / "SKILL.md").write_text("stale", encoding="utf-8")

    _update(tmp_project)

    assert not stale_dir.exists()
