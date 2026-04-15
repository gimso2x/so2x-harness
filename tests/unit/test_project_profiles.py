from __future__ import annotations

from pathlib import Path

from scripts.lib.project_profiles import (
    SKILL_CATALOG_PATH,
    detect_project_profiles,
    load_skill_catalog,
    recommend_skill_plan,
    recommend_skills_for_profiles,
)


def test_detect_project_profiles_for_next_monorepo(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "package.json").write_text(
        '{"packageManager":"pnpm@9.0.0","dependencies":{"next":"15.0.0","react":"19.0.0"}}\n',
        encoding="utf-8",
    )
    (project / "pnpm-workspace.yaml").write_text("packages:\n  - apps/*\n  - packages/*\n", encoding="utf-8")
    (project / "apps").mkdir()
    (project / "packages").mkdir()

    detected = detect_project_profiles(project)

    assert "frontend" in detected["detected_profiles"]
    assert "next-app" in detected["detected_profiles"]
    assert "monorepo" in detected["detected_profiles"]
    assert "pnpm-monorepo" in detected["detected_profiles"]
    assert "package.json:next" in detected["detection_signals"]
    assert "workspace:apps+packages" in detected["detection_signals"]
    assert "workspace:pnpm" in detected["detection_signals"]
    assert "review-cycle" in detected["recommended_skills"]
    assert "specify-lite" in detected["recommended_skills"]
    assert "execute" in detected["enabled_skills"]
    assert "specify" in detected["enabled_skills"]
    assert "spec-validate" in detected["enabled_skills"]
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
    assert "fastapi-service" in detected["detected_profiles"]
    assert "python-package" in detected["detected_profiles"]
    assert "pyproject.toml:fastapi" in detected["detection_signals"]
    assert "spec-validate" in detected["recommended_skills"]
    assert "changelog" in detected["recommended_skills"]
    assert "specify" in detected["optional_skills"]


def test_detect_project_profiles_for_django_service(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "pyproject.toml").write_text(
        '[project]\nname = "svc"\ndependencies = ["django"]\n',
        encoding="utf-8",
    )

    detected = detect_project_profiles(project)

    assert "backend" in detected["detected_profiles"]
    assert "django-service" in detected["detected_profiles"]
    assert "pyproject.toml:django" in detected["detection_signals"]


def test_detect_project_profiles_for_react_library(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "package.json").write_text(
        '{"peerDependencies":{"react":"^19.0.0"},"devDependencies":{"tsup":"^8.0.0"},"exports":{".":"./dist/index.js"}}\n',
        encoding="utf-8",
    )

    detected = detect_project_profiles(project)

    assert "frontend" in detected["detected_profiles"]
    assert "react-lib" in detected["detected_profiles"]
    assert "js-package" in detected["detected_profiles"]
    assert "package.json:react-lib" in detected["detection_signals"]
    assert "changelog" in detected["recommended_skills"]


def test_detect_project_profiles_for_turborepo_workspace(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "package.json").write_text(
        '{"packageManager":"pnpm@9.0.0","workspaces":["apps/*","packages/*"],"devDependencies":{"turbo":"^2.0.0"}}\n',
        encoding="utf-8",
    )

    detected = detect_project_profiles(project)

    assert "pnpm-monorepo" in detected["detected_profiles"]
    assert "package.json:turborepo" in detected["detection_signals"]
    assert "workspace:pnpm" in detected["detection_signals"]


def test_detect_project_profiles_for_pnpm_workspace_yaml_only_monorepo(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "package.json").write_text(
        '{"packageManager":"pnpm@9.0.0","dependencies":{"react":"19.0.0"}}\n',
        encoding="utf-8",
    )
    (project / "pnpm-workspace.yaml").write_text("packages:\n  - packages/*\n", encoding="utf-8")

    detected = detect_project_profiles(project)

    assert "frontend" in detected["detected_profiles"]
    assert "monorepo" in detected["detected_profiles"]
    assert "pnpm-monorepo" in detected["detected_profiles"]
    assert "packageManager:pnpm" in detected["detection_signals"]
    assert "workspace:pnpm" in detected["detection_signals"]
    assert "review-cycle" in detected["recommended_skills"]
    assert "execute" in detected["enabled_skills"]


def test_detect_project_profiles_for_plain_workspace_monorepo_recommends_review_cycle(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "package.json").write_text(
        '{"workspaces":["apps/*","packages/*"],"dependencies":{"react":"19.0.0"}}\n',
        encoding="utf-8",
    )

    detected = detect_project_profiles(project)

    assert "frontend" in detected["detected_profiles"]
    assert "monorepo" in detected["detected_profiles"]
    assert "package.json:workspaces" in detected["detection_signals"]
    assert "review-cycle" in detected["recommended_skills"]
    assert "specify-lite" in detected["recommended_skills"]
    assert "execute" in detected["enabled_skills"]
    assert "spec-validate" in detected["enabled_skills"]


def test_detect_project_profiles_for_nx_workspace(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "package.json").write_text(
        '{"workspaces":["apps/*","packages/*"],"devDependencies":{"nx":"^19.0.0"}}\n',
        encoding="utf-8",
    )

    detected = detect_project_profiles(project)

    assert "monorepo" in detected["detected_profiles"]
    assert "package.json:nx" in detected["detection_signals"]


def test_detect_project_profiles_for_yarn_workspace_monorepo(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "package.json").write_text(
        '{"packageManager":"yarn@4.1.0","workspaces":["apps/*","packages/*"],"dependencies":{"react":"19.0.0"}}\n',
        encoding="utf-8",
    )

    detected = detect_project_profiles(project)

    assert "frontend" in detected["detected_profiles"]
    assert "monorepo" in detected["detected_profiles"]
    assert "yarn-monorepo" in detected["detected_profiles"]
    assert "packageManager:yarn" in detected["detection_signals"]
    assert "workspace:yarn" in detected["detection_signals"]
    assert "review-cycle" in detected["recommended_skills"]
    assert "execute" in detected["enabled_skills"]
    assert "spec-validate" in detected["enabled_skills"]


def test_detect_project_profiles_for_object_workspaces_monorepo(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "package.json").write_text(
        '{"workspaces":{"packages":["apps/*","packages/*"]},"dependencies":{"react":"19.0.0"}}\n',
        encoding="utf-8",
    )

    detected = detect_project_profiles(project)

    assert "frontend" in detected["detected_profiles"]
    assert "monorepo" in detected["detected_profiles"]
    assert "package.json:workspaces" in detected["detection_signals"]
    assert "review-cycle" in detected["recommended_skills"]
    assert "specify-lite" in detected["recommended_skills"]


def test_detect_project_profiles_for_object_pnpm_workspaces_monorepo(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "package.json").write_text(
        '{"packageManager":"pnpm@9.0.0","workspaces":{"packages":["apps/*","packages/*"]},"dependencies":{"react":"19.0.0"}}\n',
        encoding="utf-8",
    )

    detected = detect_project_profiles(project)

    assert "frontend" in detected["detected_profiles"]
    assert "monorepo" in detected["detected_profiles"]
    assert "pnpm-monorepo" in detected["detected_profiles"]
    assert "packageManager:pnpm" in detected["detection_signals"]
    assert "workspace:pnpm" in detected["detection_signals"]


def test_detect_project_profiles_for_poetry_backend(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "pyproject.toml").write_text(
        '[tool.poetry]\nname = "svc"\nversion = "0.1.0"\n[tool.poetry.dependencies]\npython = "^3.12"\nfastapi = "^0.115.0"\n',
        encoding="utf-8",
    )

    detected = detect_project_profiles(project)

    assert "backend" in detected["detected_profiles"]
    assert "fastapi-service" in detected["detected_profiles"]
    assert "pyproject.toml:poetry" in detected["detection_signals"]


def test_detect_project_profiles_for_uv_workspace_monorepo(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "pyproject.toml").write_text(
        '[project]\nname = "workspace-root"\nversion = "0.1.0"\n[tool.uv.workspace]\nmembers = ["apps/api", "packages/shared"]\n',
        encoding="utf-8",
    )

    detected = detect_project_profiles(project)

    assert "python-package" in detected["detected_profiles"]
    assert "monorepo" in detected["detected_profiles"]
    assert "pyproject.toml:uv" in detected["detection_signals"]
    assert "pyproject.toml:uv-workspace" in detected["detection_signals"]
    assert "execute" in detected["enabled_skills"]
    assert "spec-validate" in detected["enabled_skills"]


def test_detect_project_profiles_for_django_manage_py_project(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "manage.py").write_text("print('manage')\n", encoding="utf-8")
    (project / "requirements.txt").write_text("django>=5\n", encoding="utf-8")

    detected = detect_project_profiles(project)

    assert "backend" in detected["detected_profiles"]
    assert "django-service" in detected["detected_profiles"]
    assert "manage.py:django" in detected["detection_signals"]


def test_detect_project_profiles_for_fastapi_requirements_project(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "requirements.txt").write_text("fastapi>=0.115\nuvicorn>=0.30\n", encoding="utf-8")

    detected = detect_project_profiles(project)

    assert "backend" in detected["detected_profiles"]
    assert "fastapi-service" in detected["detected_profiles"]
    assert "requirements.txt:fastapi" in detected["detection_signals"]
    assert "review-cycle" in detected["recommended_skills"]
    assert "specify-lite" in detected["recommended_skills"]


def test_detect_project_profiles_for_flask_requirements_project(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "requirements.txt").write_text("flask>=3.0\nsqlalchemy>=2.0\n", encoding="utf-8")

    detected = detect_project_profiles(project)

    assert "backend" in detected["detected_profiles"]
    assert "requirements.txt:backend-framework" in detected["detection_signals"]
    assert "review-cycle" in detected["recommended_skills"]
    assert "specify-lite" in detected["recommended_skills"]
    assert "spec-validate" in detected["recommended_skills"]


def test_detect_project_profiles_for_next_app_router_project(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "package.json").write_text(
        '{"dependencies":{"next":"15.0.0","react":"19.0.0"}}\n',
        encoding="utf-8",
    )
    app_dir = project / "app"
    app_dir.mkdir()
    (app_dir / "page.tsx").write_text("export default function Page() { return null }\n", encoding="utf-8")

    detected = detect_project_profiles(project)

    assert "next-app" in detected["detected_profiles"]
    assert "next:app-router" in detected["detection_signals"]


def test_detect_project_profiles_for_vite_library_mode(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "package.json").write_text(
        '{"dependencies":{"react":"^19.0.0"},"devDependencies":{"vite":"^5.0.0"}}\n',
        encoding="utf-8",
    )
    (project / "vite.config.ts").write_text(
        'import { defineConfig } from "vite"\nexport default defineConfig({ build: { lib: { entry: "src/index.ts" } } })\n',
        encoding="utf-8",
    )

    detected = detect_project_profiles(project)

    assert "react-lib" in detected["detected_profiles"]
    assert "vite.config:lib-mode" in detected["detection_signals"]


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


def test_recommend_skill_plan_promotes_specify_for_next_app() -> None:
    plan = recommend_skill_plan(
        ["frontend", "next-app"],
        ["package.json:next", "next:app-router"],
        platforms=["claude", "codex"],
    )

    assert "specify" in plan["enabled_skills"]
    assert "specify" in plan["recommended_skills"]
    assert "execute" in plan["optional_skills"]
    assert any("policy" in reason for reason in plan["skill_recommendations"]["specify"])
    assert plan["policy_promoted_skills"] == {
        "specify": "next-app repos default to full specification workflow"
    }


def test_recommend_skill_plan_promotes_execute_and_spec_validate_for_monorepo() -> None:
    plan = recommend_skill_plan(
        ["monorepo", "pnpm-monorepo"],
        ["package.json:turborepo", "workspace:pnpm"],
        platforms=["claude", "codex"],
    )

    assert "execute" in plan["enabled_skills"]
    assert "execute" in plan["recommended_skills"]
    assert "spec-validate" in plan["enabled_skills"]
    assert any("policy" in reason for reason in plan["skill_recommendations"]["execute"])


def test_load_skill_catalog_reads_external_catalog_file() -> None:
    catalog = load_skill_catalog()

    assert SKILL_CATALOG_PATH.exists()
    assert "planning" in catalog
    assert catalog["simplify-cycle"]["tier"] == "core"
    assert catalog["execute"]["tier"] == "optional"
