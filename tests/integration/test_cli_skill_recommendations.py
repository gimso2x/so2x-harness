from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CLI = ROOT_DIR / "scripts/cli/main.py"
APPLY = ROOT_DIR / "scripts/apply.py"
ENV = {**os.environ, "PYTHONPATH": str(ROOT_DIR / "scripts")}


def test_cli_skills_recommend_shows_optional_and_reasons(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "package.json").write_text(
        json.dumps({"dependencies": {"next": "15.0.0", "react": "19.0.0"}}) + "\n",
        encoding="utf-8",
    )

    apply = subprocess.run(
        [
            "python3",
            str(APPLY),
            "--project",
            str(project),
            "--platform",
            "claude",
            "codex",
            "--preset",
            "auto",
        ],
        capture_output=True,
        text=True,
        env=ENV,
        check=False,
    )
    assert apply.returncode == 0

    result = subprocess.run(
        ["python3", str(CLI), "skills", "recommend", "--project", str(project)],
        capture_output=True,
        text=True,
        env=ENV,
        check=False,
    )

    assert result.returncode == 0
    assert "enabled_skills:" in result.stdout
    assert "enabled_optional_skills:" in result.stdout
    assert "optional_skills:" in result.stdout
    assert "policy_promoted_skills:" in result.stdout
    assert "execute" in result.stdout
    assert "enabled_optional_skills: none" in result.stdout
    assert "specify: next-app repos default to full specification workflow" in result.stdout
    assert "workflow tags: code-reuse-review, code-quality-review, efficiency-review" in result.stdout


def test_cli_skills_enable_promotes_optional_skill_into_installed_set(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "package.json").write_text(
        json.dumps({"dependencies": {"next": "15.0.0", "react": "19.0.0"}}) + "\n",
        encoding="utf-8",
    )

    apply = subprocess.run(
        [
            "python3",
            str(APPLY),
            "--project",
            str(project),
            "--platform",
            "claude",
            "codex",
            "--preset",
            "auto",
        ],
        capture_output=True,
        text=True,
        env=ENV,
        check=False,
    )
    assert apply.returncode == 0

    result = subprocess.run(
        [
            "python3",
            str(CLI),
            "skills",
            "enable",
            "execute",
            "--project",
            str(project),
        ],
        capture_output=True,
        text=True,
        env=ENV,
        check=False,
    )

    assert result.returncode == 0
    config = json.loads((project / ".ai-harness" / "config.json").read_text(encoding="utf-8"))
    assert config["enabled_optional_skills"] == ["execute"]
    assert "execute" in config["enabled_skills"]
    assert "specify" in config["enabled_skills"]
    assert (project / ".claude" / "skills" / "execute" / "SKILL.md").exists()
    assert (project / ".claude" / "skills" / "specify" / "SKILL.md").exists()
    assert (project / ".agents" / "skills" / "execute" / "SKILL.md").exists()
    assert (project / ".agents" / "skills" / "specify" / "SKILL.md").exists()

    doctor = subprocess.run(
        ["python3", str(ROOT_DIR / "scripts/doctor.py"), "--project", str(project)],
        capture_output=True,
        text=True,
        env=ENV,
        check=False,
    )
    assert doctor.returncode == 0
    assert "enabled_optional_skills" in doctor.stdout
    assert "current_enabled_optional_skills" in doctor.stdout
    assert "execute" in doctor.stdout
