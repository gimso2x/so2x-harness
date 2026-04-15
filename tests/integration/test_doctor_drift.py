from __future__ import annotations

import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def _apply(*platforms: str) -> Path:
    import subprocess
    import tempfile

    project = Path(tempfile.mkdtemp()) / "project"
    project.mkdir(parents=True)
    subprocess.run(
        [
            "python3",
            str(ROOT_DIR / "scripts/apply.py"),
            "--project",
            str(project),
            "--platform",
            *platforms,
            "--preset",
            "general",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return project


def test_doctor_warns_when_config_platforms_drift_from_manifest() -> None:
    import subprocess

    project = _apply("claude", "codex")
    config_path = project / ".ai-harness" / "config.json"
    data = json.loads(config_path.read_text(encoding="utf-8"))
    data["platforms"] = ["codex"]
    config_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result = subprocess.run(
        ["python3", str(ROOT_DIR / "scripts/doctor.py"), "--project", str(project)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert "config_platforms" in result.stdout
    assert "manifest platforms" in result.stdout


def test_doctor_warns_when_declared_claude_assets_are_missing() -> None:
    import subprocess

    project = _apply("claude", "codex")
    claude_md = project / "CLAUDE.md"
    claude_md.unlink()

    result = subprocess.run(
        ["python3", str(ROOT_DIR / "scripts/doctor.py"), "--project", str(project)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert "claude.claude_md" in result.stdout
    assert "CLAUDE.md not found yet" in result.stdout


def test_doctor_warns_when_skill_count_drifts_from_enabled_skills() -> None:
    import subprocess

    project = _apply("claude")
    stale_dir = project / ".claude" / "skills" / "unexpected-skill"
    stale_dir.mkdir(parents=True)
    (stale_dir / "SKILL.md").write_text("stale", encoding="utf-8")

    result = subprocess.run(
        ["python3", str(ROOT_DIR / "scripts/doctor.py"), "--project", str(project)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert "skills_drift" in result.stdout
    assert "enabled skills" in result.stdout


def test_doctor_warns_when_workflow_status_files_are_missing() -> None:
    import subprocess

    project = _apply("claude")
    result = subprocess.run(
        ["python3", str(ROOT_DIR / "scripts/doctor.py"), "--project", str(project)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert "simplify_status" in result.stdout
    assert "missing simplify-cycle.json" in result.stdout
    assert "safe_commit_status" in result.stdout
    assert "squash_status" in result.stdout
    assert "feedback_events" in result.stdout
    assert "safe_commit_events" in result.stdout
    assert "squash_check_events" in result.stdout
