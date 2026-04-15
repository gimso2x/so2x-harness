from __future__ import annotations

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def test_claude_simplify_cycle_mentions_three_review_lenses() -> None:
    content = (ROOT_DIR / "templates/claude/skills/simplify-cycle/SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "Code Reuse Review" in content
    assert "Code Quality Review" in content
    assert "Efficiency Review" in content
    assert "3 agents finished" in content
    assert "Convergence state" in content
    assert "repeated_no_progress" in content
    assert "circuit_breaker" in content


def test_codex_simplify_cycle_mentions_three_review_lenses() -> None:
    content = (ROOT_DIR / "templates/codex/skills/simplify-cycle/SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "Code Reuse Review" in content
    assert "Code Quality Review" in content
    assert "Efficiency Review" in content
    assert "Convergence state" in content
    assert "repeated_no_progress" in content
    assert "circuit_breaker" in content
