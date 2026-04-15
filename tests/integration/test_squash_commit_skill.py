from __future__ import annotations

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def test_claude_and_codex_squash_commit_require_simplify_and_safe_commit() -> None:
    claude = (ROOT_DIR / "templates/claude/skills/squash-commit/SKILL.md").read_text(encoding="utf-8")
    codex = (ROOT_DIR / "templates/codex/skills/squash-commit/SKILL.md").read_text(encoding="utf-8")

    for content in (claude, codex):
        assert "safe-commit" in content
        assert "simplify-cycle" in content
        assert "remaining_count == 0" in content
        assert "Safety verdict" in content or "safety verdict" in content
        assert "상태/이벤트" in content
