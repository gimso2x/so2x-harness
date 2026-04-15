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
    skills_dir = tmp_project / ".claude" / "skills"
    assert skills_dir.exists()
    skills = list(skills_dir.glob("*/SKILL.md"))
    assert len(skills) >= 6


def test_apply_installs_review_cycle_skill(tmp_project: Path) -> None:
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
    skill = tmp_project / ".claude" / "skills" / "review-cycle" / "SKILL.md"
    assert skill.exists()
    content = skill.read_text(encoding="utf-8")
    assert ".review-artifacts/{branch-name}/" in content


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
            "gemini",
            "--preset",
            "general",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0


def test_apply_codex_creates_agents_skills(tmp_project: Path) -> None:
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
    assert result.returncode == 0, result.stderr
    skills_dir = tmp_project / ".agents" / "skills"
    assert skills_dir.exists()
    assert len(list(skills_dir.glob("*/SKILL.md"))) >= 6


def test_apply_codex_agents_md_has_rules(tmp_project: Path) -> None:
    import subprocess

    subprocess.run(
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
        check=True,
    )
    agents_md = tmp_project / "AGENTS.md"
    assert agents_md.exists()
    content = agents_md.read_text(encoding="utf-8")
    assert "SO2X-HARNESS:BEGIN" in content
    assert "## Rules" in content


def test_apply_multi_platform(tmp_project: Path) -> None:
    import subprocess

    result = subprocess.run(
        [
            "python3",
            str(ROOT_DIR / "scripts/apply.py"),
            "--project",
            str(tmp_project),
            "--platform",
            "claude",
            "codex",
            "--preset",
            "general",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert (tmp_project / "CLAUDE.md").exists()
    assert (tmp_project / ".agents" / "skills").exists()
    assert (tmp_project / ".claude" / "skills").exists()
    manifest = load_manifest(tmp_project)
    assert "claude" in manifest["platforms"]
    assert "codex" in manifest["platforms"]

    config = json.loads((tmp_project / ".ai-harness" / "config.json").read_text(encoding="utf-8"))
    assert "claude" in config["platforms"]
    assert "codex" in config["platforms"]


def test_apply_dedup_platforms(tmp_project: Path) -> None:
    import subprocess

    result = subprocess.run(
        [
            "python3",
            str(ROOT_DIR / "scripts/apply.py"),
            "--project",
            str(tmp_project),
            "--platform",
            "codex",
            "codex",
            "--preset",
            "general",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    manifest = load_manifest(tmp_project)
    assert manifest["platforms"].count("codex") == 1

    config = json.loads((tmp_project / ".ai-harness" / "config.json").read_text(encoding="utf-8"))
    assert config["platforms"] == ["codex"]


def test_apply_upgrade_claude_to_multi(tmp_project: Path) -> None:
    import subprocess

    # First install claude only
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
    assert manifest["platforms"] == ["claude"]

    config = json.loads((tmp_project / ".ai-harness" / "config.json").read_text(encoding="utf-8"))
    assert config["platforms"] == ["claude"]

    # Then add codex
    subprocess.run(
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
        check=True,
    )
    manifest = load_manifest(tmp_project)
    assert "claude" in manifest["platforms"]
    assert "codex" in manifest["platforms"]
    assert (tmp_project / ".agents" / "skills").exists()

    config = json.loads((tmp_project / ".ai-harness" / "config.json").read_text(encoding="utf-8"))
    assert "claude" in config["platforms"]
    assert "codex" in config["platforms"]
