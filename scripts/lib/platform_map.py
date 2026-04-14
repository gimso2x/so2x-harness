from __future__ import annotations

from pathlib import Path

PROJECT_PATHS = {
    "claude": {
        "rules_dir": Path(".claude/rules/so2x-harness"),
        "skills_dir": Path(".claude/skills"),
        "agents_dir": Path(".claude/agents/so2x-harness"),
        "hooks_dir": Path(".claude/hooks"),
        "plugin_dir": Path(".claude-plugin"),
        "shared_docs_dir": Path(".ai-harness/docs"),
        "shared_snippets_dir": Path(".ai-harness/snippets"),
        "agents_path": Path("AGENTS.md"),
        "claude_md_path": Path("CLAUDE.md"),
        "config_path": Path(".ai-harness/config.json"),
    }
}
