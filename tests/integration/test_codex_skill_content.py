from __future__ import annotations

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CODEX_SKILLS_DIR = ROOT_DIR / "templates" / "codex" / "skills"
FORBIDDEN_STRINGS = [
    "/specify",
    "/execute",
    "Interviewer",
    "Code Explorer",
    "Spec Writer",
    "Planner",
    "Reviewer",
    "Verifier",
]


def test_codex_skills_do_not_reference_claude_slash_or_agent_chain_terms() -> None:
    for skill_file in CODEX_SKILLS_DIR.glob("*/SKILL.md"):
        content = skill_file.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_STRINGS:
            assert forbidden not in content, f"{skill_file} still references {forbidden}"


def test_codex_specify_skill_uses_codex_friendly_invoke_examples() -> None:
    content = (CODEX_SKILLS_DIR / "specify" / "SKILL.md").read_text(encoding="utf-8")
    assert "$specify" in content


def test_codex_execute_skill_uses_codex_friendly_invoke_examples() -> None:
    content = (CODEX_SKILLS_DIR / "execute" / "SKILL.md").read_text(encoding="utf-8")
    assert "$execute" in content
