from __future__ import annotations

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def test_codex_skills_match_claude() -> None:
    claude_skills = ROOT_DIR / "templates/claude/skills"
    codex_skills = ROOT_DIR / "templates/codex/skills"
    claude_names = sorted(d.name for d in claude_skills.iterdir() if d.is_dir())
    codex_names = sorted(d.name for d in codex_skills.iterdir() if d.is_dir())
    assert claude_names == codex_names, f"Skill mismatch: claude={claude_names} codex={codex_names}"
