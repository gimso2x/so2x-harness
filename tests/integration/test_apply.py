from __future__ import annotations

import json
from pathlib import Path

from scripts.lib.manifest import load_manifest, manifest_path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def test_apply_creates_manifest(tmp_project: Path) -> None:
    import subprocess

    result = subprocess.run(
        [
            "python3",
            str(ROOT_DIR / "scripts/apply.py"),
            "--project",
            str(tmp_project),
            "--platform",
            "claude",
            "--preset",
            "general",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert manifest_path(tmp_project).exists()


def test_apply_creates_claude_md(tmp_project: Path) -> None:
    import subprocess

    subprocess.run(
        [
            "python3",
            str(ROOT_DIR / "scripts/apply.py"),
            "--project",
            str(tmp_project),
            "--platform",
            "claude",
            "--preset",
            "general",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    claude_md = tmp_project / "CLAUDE.md"
    assert claude_md.exists()
    content = claude_md.read_text(encoding="utf-8")
    assert "SO2X-HARNESS:BEGIN" in content


def test_apply_creates_rules(tmp_project: Path) -> None:
    import subprocess

    subprocess.run(
        [
            "python3",
            str(ROOT_DIR / "scripts/apply.py"),
            "--project",
            str(tmp_project),
            "--platform",
            "claude",
            "--preset",
            "general",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    rules_dir = tmp_project / ".claude" / "rules" / "so2x-harness"
    assert rules_dir.exists()
    rules = list(rules_dir.glob("*.md"))
    assert len(rules) >= 5


def test_apply_creates_skills(tmp_project: Path) -> None:
    import subprocess

    subprocess.run(
        [
            "python3",
            str(ROOT_DIR / "scripts/apply.py"),
            "--project",
            str(tmp_project),
            "--platform",
            "claude",
            "--preset",
            "general",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    skills_dir = tmp_project / ".claude" / "skills" / "so2x-harness"
    assert skills_dir.exists()
    skills = list(skills_dir.glob("*.md"))
    assert len(skills) >= 6


def test_apply_creates_config(tmp_project: Path) -> None:
    import subprocess

    subprocess.run(
        [
            "python3",
            str(ROOT_DIR / "scripts/apply.py"),
            "--project",
            str(tmp_project),
            "--platform",
            "claude",
            "--preset",
            "general",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    config = tmp_project / ".ai-harness" / "config.json"
    assert config.exists()
    data = json.loads(config.read_text(encoding="utf-8"))
    assert data["preset"] == "general"
    assert data["project_name"] == "test-project"


def test_apply_manifest_has_files(tmp_project: Path) -> None:
    import subprocess

    subprocess.run(
        [
            "python3",
            str(ROOT_DIR / "scripts/apply.py"),
            "--project",
            str(tmp_project),
            "--platform",
            "claude",
            "--preset",
            "general",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    manifest = load_manifest(tmp_project)
    assert "files" in manifest
    assert len(manifest["files"]) >= 10


def test_apply_unsupported_platform(tmp_project: Path) -> None:
    import subprocess

    result = subprocess.run(
        [
            "python3",
            str(ROOT_DIR / "scripts/apply.py"),
            "--project",
            str(tmp_project),
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


def test_apply_nextjs_preset(tmp_project: Path) -> None:
    import subprocess

    result = subprocess.run(
        [
            "python3",
            str(ROOT_DIR / "scripts/apply.py"),
            "--project",
            str(tmp_project),
            "--platform",
            "claude",
            "--preset",
            "nextjs",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    config = tmp_project / ".ai-harness" / "config.json"
    data = json.loads(config.read_text(encoding="utf-8"))
    assert data["preset"] == "nextjs"
