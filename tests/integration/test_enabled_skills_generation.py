from __future__ import annotations

import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
PRESET = json.loads(
    (ROOT_DIR / "templates/project/.ai-harness/presets/general.json").read_text(encoding="utf-8")
)
EXPECTED_SKILLS = PRESET["enabled_skills"]


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


def _extract_installed_skills(claude_md: str) -> list[str]:
    section = claude_md.split("## Installed Skills\n", 1)[1]
    lines = []
    for line in section.splitlines():
        if line.startswith("<!-- SO2X-HARNESS:END -->"):
            break
        if line.startswith("- "):
            lines.append(line[2:])
    return lines


def test_claude_installed_skills_match_enabled_skills() -> None:
    project = _apply("claude")
    claude_md = (project / "CLAUDE.md").read_text(encoding="utf-8")

    assert _extract_installed_skills(claude_md) == EXPECTED_SKILLS


def test_generated_claude_skill_dirs_match_enabled_skills() -> None:
    project = _apply("claude")
    generated = sorted(d.name for d in (project / ".claude" / "skills").iterdir() if d.is_dir())

    assert generated == sorted(EXPECTED_SKILLS)


def test_generated_codex_skill_dirs_match_enabled_skills() -> None:
    project = _apply("codex")
    generated = sorted(d.name for d in (project / ".agents" / "skills").iterdir() if d.is_dir())

    assert generated == sorted(EXPECTED_SKILLS)
