from __future__ import annotations

from pathlib import Path

from scripts.lib.project_profiles import (
    detect_project_profiles,
    recommend_skill_plan,
    recommend_skills_for_profiles,
)


def test_detect_project_profiles_for_next_monorepo(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "package.json").write_text(
        '{"dependencies":{"next":"15.0.0","react":"19.0.0"}}\n',
        encoding="utf-8",
    )
    (project / "apps").mkdir()
    (project / "packages").mkdir()

    detected = detect_project_profiles(project)

    assert "frontend" in detected["detected_profiles"]
    assert "monorepo" in detected["detected_profiles"]
    assert "package.json:next" in detected["detection_signals"]
    assert "workspace:apps+packages" in detected["detection_signals"]
    assert "review-cycle" in detected["recommended_skills"]
    assert "specify-lite" in detected["recommended_skills"]
    assert "execute" in detected["optional_skills"]
    assert "simplify-cycle" in detected["enabled_skills"]
    assert "workflow tags: code-reuse-review, code-quality-review, efficiency-review" in detected[
        "skill_recommendations"
    ]["simplify-cycle"]


def test_detect_project_profiles_for_fastapi_package(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "pyproject.toml").write_text(
        '[project]\nname = "svc"\ndependencies = ["fastapi", "uvicorn"]\n',
        encoding="utf-8",
    )

    detected = detect_project_profiles(project)

    assert "backend" in detected["detected_profiles"]
    assert "python-package" in detected["detected_profiles"]
    assert "pyproject.toml:fastapi" in detected["detection_signals"]
    assert "spec-validate" in detected["recommended_skills"]
    assert "changelog" in detected["recommended_skills"]
    assert "specify" in detected["optional_skills"]


def test_recommend_skills_for_empty_profiles_returns_core() -> None:
    recommended = recommend_skills_for_profiles([])

    assert recommended == [
        "simplify-cycle",
        "squash-commit",
        "safe-commit",
        "check-harness",
        "debugging",
        "implementation",
        "planning",
        "review",
        "setup-context",
    ]


def test_recommend_skill_plan_keeps_enabled_and_optional_separate() -> None:
    plan = recommend_skill_plan(["frontend"], ["package.json:next"], platforms=["claude", "codex"])

    assert "review-cycle" in plan["enabled_skills"]
    assert "specify-lite" in plan["enabled_skills"]
    assert "execute" in plan["optional_skills"]
    assert "specify" in plan["optional_skills"]
    assert "execute" not in plan["enabled_skills"]
