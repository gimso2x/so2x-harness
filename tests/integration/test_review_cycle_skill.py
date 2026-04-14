from __future__ import annotations

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def test_review_cycle_skill_exists() -> None:
    skill = ROOT_DIR / "templates/claude/skills/review-cycle/SKILL.md"
    assert skill.exists()
    content = skill.read_text(encoding="utf-8")
    assert ".review-artifacts/{branch-name}/" in content
    assert "[p1]" in content
    assert "side effect" in content
