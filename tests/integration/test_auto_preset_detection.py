from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def test_apply_auto_preset_detects_frontend_monorepo_and_surfaces_in_doctor(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "package.json").write_text(
        json.dumps({"packageManager": "pnpm@9.0.0", "dependencies": {"next": "15.0.0", "react": "19.0.0"}}) + "\n",
        encoding="utf-8",
    )
    (project / "pnpm-workspace.yaml").write_text("packages:\n  - apps/*\n  - packages/*\n", encoding="utf-8")
    (project / "apps").mkdir()
    (project / "packages").mkdir()
    app_dir = project / "app"
    app_dir.mkdir()
    (app_dir / "page.tsx").write_text("export default function Page() { return null }\n", encoding="utf-8")

    apply = subprocess.run(
        [
            "python3",
            str(ROOT_DIR / "scripts/apply.py"),
            "--project",
            str(project),
            "--platform",
            "claude",
            "codex",
            "--preset",
            "auto",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert apply.returncode == 0
    assert "detected_profiles=frontend,next-app,monorepo,pnpm-monorepo" in apply.stdout
    assert "recommended_skills=" in apply.stdout
    assert "optional_skills=" in apply.stdout

    config = json.loads((project / ".ai-harness" / "config.json").read_text(encoding="utf-8"))
    assert config["preset"] == "auto"
    assert config["detected_profiles"] == ["frontend", "next-app", "monorepo", "pnpm-monorepo"]
    assert "package.json:next" in config["detection_signals"]
    assert "next:app-router" in config["detection_signals"]
    assert "workspace:apps+packages" in config["detection_signals"]
    assert "workspace:pnpm" in config["detection_signals"]
    assert "review-cycle" in config["enabled_skills"]
    assert "specify-lite" in config["enabled_skills"]
    assert "specify" in config["enabled_skills"]
    assert "execute" in config["enabled_skills"]
    assert "spec-validate" in config["enabled_skills"]
    assert "simplify-cycle" in config["recommended_skills"]
    assert config["policy_promoted_skills"] == {
        "specify": "next-app repos default to full specification workflow",
        "execute": "monorepo repos usually need longer coordinated execution chains",
        "spec-validate": "monorepo repos benefit from stronger spec verification across packages",
    }
    assert "workflow tags: code-reuse-review, code-quality-review, efficiency-review" in config[
        "skill_recommendations"
    ]["simplify-cycle"]

    doctor = subprocess.run(
        ["python3", str(ROOT_DIR / "scripts/doctor.py"), "--project", str(project)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert doctor.returncode == 0
    assert "detected_profiles" in doctor.stdout
    assert "frontend, next-app, monorepo, pnpm-monorepo" in doctor.stdout
    assert "detection_signals" in doctor.stdout
    assert "recommended_skills" in doctor.stdout
    assert "specify" in doctor.stdout
    assert "execute" in doctor.stdout
    assert "current_detected_profiles" in doctor.stdout
    assert "current_enabled_skills" in doctor.stdout
    assert "current_recommended_skills" in doctor.stdout
    assert "current_skill_recommendation.specify" in doctor.stdout
    assert "current_skill_recommendation.simplify-cycle" in doctor.stdout
    assert "policy promotion: next-app repos default to full specification workflow" in doctor.stdout
    assert "review-cycle" in doctor.stdout


def test_apply_auto_preset_detects_workspace_only_monorepo(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "package.json").write_text(
        json.dumps({"workspaces": ["apps/*", "packages/*"], "dependencies": {"react": "19.0.0"}}) + "\n",
        encoding="utf-8",
    )

    apply = subprocess.run(
        [
            "python3",
            str(ROOT_DIR / "scripts/apply.py"),
            "--project",
            str(project),
            "--platform",
            "claude",
            "codex",
            "--preset",
            "auto",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert apply.returncode == 0

    config = json.loads((project / ".ai-harness" / "config.json").read_text(encoding="utf-8"))
    assert config["detected_profiles"] == ["frontend", "monorepo"]
    assert "package.json:workspaces" in config["detection_signals"]
    assert "review-cycle" in config["enabled_skills"]
    assert "specify-lite" in config["enabled_skills"]
    assert "execute" in config["enabled_skills"]
    assert "spec-validate" in config["enabled_skills"]

    doctor = subprocess.run(
        ["python3", str(ROOT_DIR / "scripts/doctor.py"), "--project", str(project)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert doctor.returncode == 0
    assert "frontend, monorepo" in doctor.stdout
    assert "package.json:workspaces" in doctor.stdout
    assert "review-cycle" in doctor.stdout
    assert "specify-lite" in doctor.stdout


def test_apply_auto_preset_detects_object_workspaces_monorepo(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "package.json").write_text(
        json.dumps(
            {
                "packageManager": "pnpm@9.0.0",
                "workspaces": {"packages": ["apps/*", "packages/*"]},
                "dependencies": {"react": "19.0.0"},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    apply = subprocess.run(
        [
            "python3",
            str(ROOT_DIR / "scripts/apply.py"),
            "--project",
            str(project),
            "--platform",
            "claude",
            "codex",
            "--preset",
            "auto",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert apply.returncode == 0
    assert "detected_profiles=frontend,monorepo,pnpm-monorepo" in apply.stdout

    config = json.loads((project / ".ai-harness" / "config.json").read_text(encoding="utf-8"))
    assert config["detected_profiles"] == ["frontend", "monorepo", "pnpm-monorepo"]
    assert "package.json:workspaces" in config["detection_signals"]
    assert "packageManager:pnpm" in config["detection_signals"]
    assert "workspace:pnpm" in config["detection_signals"]
    assert "review-cycle" in config["enabled_skills"]
    assert "specify-lite" in config["enabled_skills"]
    assert "execute" in config["enabled_skills"]
    assert "spec-validate" in config["enabled_skills"]

    doctor = subprocess.run(
        ["python3", str(ROOT_DIR / "scripts/doctor.py"), "--project", str(project)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert doctor.returncode == 0
    assert "frontend, monorepo, pnpm-monorepo" in doctor.stdout
    assert "package.json:workspaces" in doctor.stdout
    assert "packageManager:pnpm" in doctor.stdout
    assert "workspace:pnpm" in doctor.stdout


def test_apply_auto_preset_detects_yarn_workspace_monorepo(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "package.json").write_text(
        json.dumps(
            {
                "packageManager": "yarn@4.1.0",
                "workspaces": ["apps/*", "packages/*"],
                "dependencies": {"react": "19.0.0"},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    apply = subprocess.run(
        [
            "python3",
            str(ROOT_DIR / "scripts/apply.py"),
            "--project",
            str(project),
            "--platform",
            "claude",
            "codex",
            "--preset",
            "auto",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert apply.returncode == 0
    assert "detected_profiles=frontend,monorepo,yarn-monorepo" in apply.stdout

    config = json.loads((project / ".ai-harness" / "config.json").read_text(encoding="utf-8"))
    assert config["detected_profiles"] == ["frontend", "monorepo", "yarn-monorepo"]
    assert "package.json:workspaces" in config["detection_signals"]
    assert "packageManager:yarn" in config["detection_signals"]
    assert "workspace:yarn" in config["detection_signals"]
    assert "review-cycle" in config["enabled_skills"]
    assert "specify-lite" in config["enabled_skills"]
    assert "execute" in config["enabled_skills"]
    assert "spec-validate" in config["enabled_skills"]

    doctor = subprocess.run(
        ["python3", str(ROOT_DIR / "scripts/doctor.py"), "--project", str(project)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert doctor.returncode == 0
    assert "frontend, monorepo, yarn-monorepo" in doctor.stdout
    assert "packageManager:yarn" in doctor.stdout
    assert "workspace:yarn" in doctor.stdout


def test_apply_auto_preset_detects_npm_workspace_monorepo(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "package.json").write_text(
        json.dumps(
            {
                "packageManager": "npm@10.8.2",
                "workspaces": ["apps/*", "packages/*"],
                "dependencies": {"react": "19.0.0"},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    apply = subprocess.run(
        [
            "python3",
            str(ROOT_DIR / "scripts/apply.py"),
            "--project",
            str(project),
            "--platform",
            "claude",
            "codex",
            "--preset",
            "auto",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert apply.returncode == 0
    assert "detected_profiles=frontend,monorepo,npm-monorepo" in apply.stdout

    config = json.loads((project / ".ai-harness" / "config.json").read_text(encoding="utf-8"))
    assert config["detected_profiles"] == ["frontend", "monorepo", "npm-monorepo"]
    assert "package.json:workspaces" in config["detection_signals"]
    assert "packageManager:npm" in config["detection_signals"]
    assert "workspace:npm" in config["detection_signals"]
    assert "review-cycle" in config["enabled_skills"]
    assert "specify-lite" in config["enabled_skills"]
    assert "execute" in config["enabled_skills"]
    assert "spec-validate" in config["enabled_skills"]

    doctor = subprocess.run(
        ["python3", str(ROOT_DIR / "scripts/doctor.py"), "--project", str(project)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert doctor.returncode == 0
    assert "frontend, monorepo, npm-monorepo" in doctor.stdout
    assert "packageManager:npm" in doctor.stdout
    assert "workspace:npm" in doctor.stdout


def test_apply_auto_preset_detects_pnpm_workspace_yaml_only_monorepo(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "package.json").write_text(
        json.dumps({"packageManager": "pnpm@9.0.0", "dependencies": {"react": "19.0.0"}}) + "\n",
        encoding="utf-8",
    )
    (project / "pnpm-workspace.yaml").write_text("packages:\n  - packages/*\n", encoding="utf-8")

    apply = subprocess.run(
        [
            "python3",
            str(ROOT_DIR / "scripts/apply.py"),
            "--project",
            str(project),
            "--platform",
            "claude",
            "codex",
            "--preset",
            "auto",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert apply.returncode == 0
    assert "detected_profiles=frontend,monorepo,pnpm-monorepo" in apply.stdout

    config = json.loads((project / ".ai-harness" / "config.json").read_text(encoding="utf-8"))
    assert config["detected_profiles"] == ["frontend", "monorepo", "pnpm-monorepo"]
    assert "packageManager:pnpm" in config["detection_signals"]
    assert "workspace:pnpm" in config["detection_signals"]
    assert "review-cycle" in config["enabled_skills"]
    assert "execute" in config["enabled_skills"]
    assert "spec-validate" in config["enabled_skills"]

    doctor = subprocess.run(
        ["python3", str(ROOT_DIR / "scripts/doctor.py"), "--project", str(project)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert doctor.returncode == 0
    assert "frontend, monorepo, pnpm-monorepo" in doctor.stdout
    assert "packageManager:pnpm" in doctor.stdout
    assert "workspace:pnpm" in doctor.stdout
    assert "review-cycle" in doctor.stdout


def test_apply_auto_preset_detects_bun_workspace_monorepo(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "package.json").write_text(
        json.dumps(
            {
                "packageManager": "bun@1.1.17",
                "workspaces": ["apps/*", "packages/*"],
                "dependencies": {"react": "19.0.0"},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    apply = subprocess.run(
        [
            "python3",
            str(ROOT_DIR / "scripts/apply.py"),
            "--project",
            str(project),
            "--platform",
            "claude",
            "codex",
            "--preset",
            "auto",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert apply.returncode == 0
    assert "detected_profiles=frontend,monorepo,bun-monorepo" in apply.stdout

    config = json.loads((project / ".ai-harness" / "config.json").read_text(encoding="utf-8"))
    assert config["detected_profiles"] == ["frontend", "monorepo", "bun-monorepo"]
    assert "package.json:workspaces" in config["detection_signals"]
    assert "packageManager:bun" in config["detection_signals"]
    assert "workspace:bun" in config["detection_signals"]
    assert "review-cycle" in config["enabled_skills"]
    assert "execute" in config["enabled_skills"]
    assert "spec-validate" in config["enabled_skills"]

    doctor = subprocess.run(
        ["python3", str(ROOT_DIR / "scripts/doctor.py"), "--project", str(project)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert doctor.returncode == 0
    assert "frontend, monorepo, bun-monorepo" in doctor.stdout
    assert "packageManager:bun" in doctor.stdout
    assert "workspace:bun" in doctor.stdout
    assert "review-cycle" in doctor.stdout


def test_apply_auto_preset_detects_workspace_only_bun_monorepo(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "package.json").write_text(
        json.dumps({"packageManager": "bun@1.1.17", "workspaces": ["apps/*", "packages/*"]}) + "\n",
        encoding="utf-8",
    )

    apply = subprocess.run(
        [
            "python3",
            str(ROOT_DIR / "scripts/apply.py"),
            "--project",
            str(project),
            "--platform",
            "claude",
            "codex",
            "--preset",
            "auto",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert apply.returncode == 0
    assert "detected_profiles=monorepo,bun-monorepo" in apply.stdout

    config = json.loads((project / ".ai-harness" / "config.json").read_text(encoding="utf-8"))
    assert config["detected_profiles"] == ["monorepo", "bun-monorepo"]
    assert "package.json:workspaces" in config["detection_signals"]
    assert "packageManager:bun" in config["detection_signals"]
    assert "workspace:bun" in config["detection_signals"]
    assert "review-cycle" in config["enabled_skills"]
    assert "execute" in config["enabled_skills"]
    assert "spec-validate" in config["enabled_skills"]

    doctor = subprocess.run(
        ["python3", str(ROOT_DIR / "scripts/doctor.py"), "--project", str(project)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert doctor.returncode == 0
    assert "monorepo, bun-monorepo" in doctor.stdout
    assert "package.json:workspaces" in doctor.stdout
    assert "workspace:bun" in doctor.stdout
    assert "review-cycle" in doctor.stdout


def test_apply_auto_preset_detects_uv_workspace_monorepo(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "pyproject.toml").write_text(
        '[project]\nname = "workspace-root"\nversion = "0.1.0"\n[tool.uv.workspace]\nmembers = ["apps/api", "packages/shared"]\n',
        encoding="utf-8",
    )

    apply = subprocess.run(
        [
            "python3",
            str(ROOT_DIR / "scripts/apply.py"),
            "--project",
            str(project),
            "--platform",
            "claude",
            "codex",
            "--preset",
            "auto",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert apply.returncode == 0
    assert "detected_profiles=" in apply.stdout
    assert "monorepo" in apply.stdout
    assert "python-package" in apply.stdout

    config = json.loads((project / ".ai-harness" / "config.json").read_text(encoding="utf-8"))
    assert config["detected_profiles"] == ["monorepo", "python-package"]
    assert "pyproject.toml:uv" in config["detection_signals"]
    assert "pyproject.toml:uv-workspace" in config["detection_signals"]
    assert "execute" in config["enabled_skills"]
    assert "spec-validate" in config["enabled_skills"]

    doctor = subprocess.run(
        ["python3", str(ROOT_DIR / "scripts/doctor.py"), "--project", str(project)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert doctor.returncode == 0
    assert "monorepo, python-package" in doctor.stdout
    assert "pyproject.toml:uv-workspace" in doctor.stdout
    assert "execute" in doctor.stdout
    assert "spec-validate" in doctor.stdout


def test_apply_auto_preset_detects_requirements_backend_framework_project(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "requirements.txt").write_text("flask>=3.0\nsqlalchemy>=2.0\n", encoding="utf-8")

    apply = subprocess.run(
        [
            "python3",
            str(ROOT_DIR / "scripts/apply.py"),
            "--project",
            str(project),
            "--platform",
            "claude",
            "codex",
            "--preset",
            "auto",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert apply.returncode == 0
    assert "detected_profiles=backend" in apply.stdout

    config = json.loads((project / ".ai-harness" / "config.json").read_text(encoding="utf-8"))
    assert config["detected_profiles"] == ["backend"]
    assert "requirements.txt:python-backend" in config["detection_signals"]
    assert "requirements.txt:backend-framework" in config["detection_signals"]
    assert "review-cycle" in config["enabled_skills"]
    assert "specify-lite" in config["enabled_skills"]
    assert "spec-validate" in config["enabled_skills"]

    doctor = subprocess.run(
        ["python3", str(ROOT_DIR / "scripts/doctor.py"), "--project", str(project)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert doctor.returncode == 0
    assert "requirements.txt:backend-framework" in doctor.stdout
    assert "review-cycle" in doctor.stdout
    assert "specify-lite" in doctor.stdout
    assert "spec-validate" in doctor.stdout
