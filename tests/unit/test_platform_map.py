from __future__ import annotations

from scripts.lib.platform_map import PROJECT_PATHS


def test_claude_platform_exists() -> None:
    assert "claude" in PROJECT_PATHS


def test_claude_has_required_paths() -> None:
    paths = PROJECT_PATHS["claude"]
    required_keys = [
        "claude_md_path",
        "agents_path",
        "rules_dir",
        "skills_dir",
        "hooks_dir",
        "plugin_dir",
        "config_path",
        "shared_docs_dir",
        "shared_snippets_dir",
    ]
    for key in required_keys:
        assert key in paths, f"missing key: {key}"


def test_claude_paths_are_pathlib() -> None:
    from pathlib import Path

    paths = PROJECT_PATHS["claude"]
    for key, value in paths.items():
        assert isinstance(value, Path), f"{key} is not a Path: {type(value)}"


def test_only_claude_supported() -> None:
    assert list(PROJECT_PATHS.keys()) == ["claude"]
