from __future__ import annotations

from pathlib import Path

PROJECT_PATHS = {
    "claude": {
        "rules_dir": Path(".claude/rules/so2x-harness"),
        "skills_dir": Path(".claude/skills"),
        "agents_dir": Path(".claude/agents/so2x-harness"),
        "hooks_dir": Path(".claude/hooks"),
        "shared_docs_dir": Path(".ai-harness/docs"),
        "shared_snippets_dir": Path(".ai-harness/snippets"),
        "agents_path": Path("AGENTS.md"),
        "claude_md_path": Path("CLAUDE.md"),
        "config_path": Path(".ai-harness/config.json"),
    },
    "codex": {
        "skills_dir": Path(".agents/skills"),
        "shared_docs_dir": Path(".ai-harness/docs"),
        "shared_snippets_dir": Path(".ai-harness/snippets"),
        "agents_path": Path("AGENTS.md"),
        "config_path": Path(".ai-harness/config.json"),
    },
}

PLATFORM_CAPABILITIES = {
    "claude": {"rules": True, "skills": True, "agents": True, "hooks": True},
    "codex": {"rules": False, "skills": True, "agents": False, "hooks": False},
}
