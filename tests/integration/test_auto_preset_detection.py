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
