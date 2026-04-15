from __future__ import annotations

from scripts.lib.platform_map import PLATFORM_CAPABILITIES, PROJECT_PATHS


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


def test_claude_paths_have_all_keys() -> None:
    paths = PROJECT_PATHS["claude"]
    expected = {
        "rules_dir",
        "skills_dir",
        "agents_dir",
        "hooks_dir",
        "shared_docs_dir",
        "shared_snippets_dir",
        "agents_path",
        "claude_md_path",
        "config_path",
    }
    assert expected.issubset(set(paths.keys()))


def test_codex_paths_exist() -> None:
    assert "codex" in PROJECT_PATHS
    paths = PROJECT_PATHS["codex"]
    assert "skills_dir" in paths
    assert str(paths["skills_dir"]) == ".agents/skills"
    assert paths.get("rules_dir") is None
    assert paths.get("hooks_dir") is None
    assert paths.get("agents_dir") is None
    assert paths.get("claude_md_path") is None


def test_codex_capabilities() -> None:
    assert "codex" in PLATFORM_CAPABILITIES
    caps = PLATFORM_CAPABILITIES["codex"]
    assert caps["rules"] is False
    assert caps["skills"] is True
    assert caps["agents"] is False
    assert caps["hooks"] is False


def test_claude_capabilities_all_true() -> None:
    caps = PLATFORM_CAPABILITIES["claude"]
    assert all(caps.values())
