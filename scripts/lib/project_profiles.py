from __future__ import annotations

import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
SKILL_CATALOG_PATH = ROOT_DIR / "templates" / "project" / ".ai-harness" / "skill-catalog.json"


def load_skill_catalog() -> dict[str, dict]:
    return _load_json(SKILL_CATALOG_PATH)


def detect_project_profiles(project_dir: Path) -> dict[str, object]:
    signals: list[str] = []
    profiles: list[str] = []
    has_workspace_config = False

    package_json = project_dir / "package.json"
    if package_json.exists():
        package_data = _load_json(package_json)
        deps = _package_deps(package_data)
        package_manager = str(package_data.get("packageManager", "")).lower()
        has_workspace_config = _has_workspace_config(package_data.get("workspaces"))
        if "turbo" in deps:
            signals.append("package.json:turborepo")
        if "nx" in deps:
            signals.append("package.json:nx")
        if "lerna" in deps:
            signals.append("package.json:lerna")
        if any(dep in deps for dep in {"next", "react", "vite", "@remix-run/react"}):
            profiles.append("frontend")
            if "next" in deps:
                profiles.append("next-app")
                signals.append("package.json:next")
            elif _is_react_library_package(package_data, deps):
                profiles.append("react-lib")
                profiles.append("js-package")
                signals.append("package.json:react-lib")
            elif "react" in deps:
                signals.append("package.json:react")
            elif "vite" in deps:
                signals.append("package.json:vite")
            else:
                signals.append("package.json:frontend-framework")
        if deps and not any(dep in deps for dep in {"next", "react", "vite", "@remix-run/react"}):
            profiles.append("js-package")
            signals.append("package.json:js-package")
        if package_manager.startswith("pnpm@") and (
            (project_dir / "pnpm-workspace.yaml").exists() or has_workspace_config
        ):
            signals.append("packageManager:pnpm")
        if package_manager.startswith("yarn@") and has_workspace_config:
            signals.append("packageManager:yarn")

    pyproject = project_dir / "pyproject.toml"
    if pyproject.exists():
        text = pyproject.read_text(encoding="utf-8").lower()
        if "[tool.poetry]" in text or "[tool.poetry.dependencies]" in text:
            signals.append("pyproject.toml:poetry")
        if "[tool.uv" in text:
            signals.append("pyproject.toml:uv")
        if "[tool.uv.workspace]" in text:
            profiles.append("monorepo")
            signals.append("pyproject.toml:uv-workspace")
        if "[tool.hatch" in text:
            signals.append("pyproject.toml:hatch")
        if any(token in text for token in {"fastapi", "django", "flask", "sqlalchemy", "uvicorn"}):
            profiles.append("backend")
            if "fastapi" in text:
                profiles.append("fastapi-service")
                signals.append("pyproject.toml:fastapi")
            elif "django" in text:
                profiles.append("django-service")
                signals.append("pyproject.toml:django")
            else:
                signals.append("pyproject.toml:backend-framework")
        profiles.append("python-package")
        signals.append("pyproject.toml:python-package")

    requirements = _read_first_existing(project_dir / "requirements.txt")
    if requirements:
        if "backend" not in profiles:
            profiles.append("backend")
            signals.append("requirements.txt:python-backend")
        if "fastapi" in requirements:
            profiles.append("fastapi-service")
            signals.append("requirements.txt:fastapi")
        elif "django" in requirements:
            profiles.append("django-service")
            signals.append("requirements.txt:django")
        elif any(token in requirements for token in {"flask", "sqlalchemy", "uvicorn"}):
            signals.append("requirements.txt:backend-framework")

    if (project_dir / "manage.py").exists():
        profiles.append("backend")
        profiles.append("django-service")
        signals.append("manage.py:django")

    if (project_dir / "go.mod").exists():
        profiles.append("backend")
        signals.append("go.mod:backend-service")

    if (project_dir / "Cargo.toml").exists():
        profiles.append("backend")
        signals.append("Cargo.toml:backend-service")

    if (project_dir / "apps").exists() and (project_dir / "packages").exists():
        profiles.append("monorepo")
        signals.append("workspace:apps+packages")

    if has_workspace_config:
        profiles.append("monorepo")
        signals.append("package.json:workspaces")

    if (project_dir / "pnpm-workspace.yaml").exists():
        profiles.append("monorepo")

    if (project_dir / "pnpm-workspace.yaml").exists() or "packageManager:pnpm" in signals:
        profiles.append("pnpm-monorepo")
        signals.append("workspace:pnpm")

    if "packageManager:yarn" in signals:
        profiles.append("yarn-monorepo")
        signals.append("workspace:yarn")

    if (project_dir / "app").exists() and any(
        (project_dir / "app" / name).exists() for name in ("page.tsx", "layout.tsx", "page.js", "layout.js")
    ):
        signals.append("next:app-router")

    vite_config = _read_first_existing(project_dir / "vite.config.ts", project_dir / "vite.config.js")
    if vite_config and "lib:" in vite_config:
        profiles.append("react-lib")
        profiles.append("js-package")
        signals.append("vite.config:lib-mode")

    profiles = _dedupe(profiles)
    signals = _dedupe(signals)
    recommendations = recommend_skill_plan(profiles, signals)
    return {
        "detected_profiles": profiles,
        "detection_signals": signals,
        **recommendations,
    }


def recommend_skills_for_profiles(profiles: list[str]) -> list[str]:
    return recommend_skill_plan(profiles, [])["recommended_skills"]


def recommend_skill_plan(
    profiles: list[str],
    signals: list[str],
    platforms: list[str] | None = None,
    enabled_optional_skills: list[str] | None = None,
) -> dict[str, object]:
    skill_catalog = load_skill_catalog()
    selected_platforms = _dedupe(platforms or ["claude", "codex"])
    selected_optional = _dedupe(enabled_optional_skills or [])
    policy_promoted = _policy_promoted_skills(profiles)
    enabled: list[str] = []
    recommended: list[str] = []
    optional: list[str] = []
    reasons: dict[str, list[str]] = {}

    for skill_name, meta in sorted(
        skill_catalog.items(), key=lambda item: (-int(item[1].get("priority", 0)), item[0])
    ):
        if not _is_skill_available_for_platforms(meta, selected_platforms):
            continue
        if not _matches_profiles(meta, profiles):
            continue
        if skill_name not in policy_promoted and not _matches_signals(meta, signals):
            continue

        rationale = _build_rationale(skill_name, meta, profiles, signals)
        if skill_name in policy_promoted:
            rationale.append(f"policy promotion: {policy_promoted[skill_name]}")
        reasons[skill_name] = rationale
        tier = str(meta.get("tier", "optional"))
        if tier == "core":
            enabled.append(skill_name)
            recommended.append(skill_name)
        elif tier == "recommended" or skill_name in policy_promoted:
            enabled.append(skill_name)
            recommended.append(skill_name)
        else:
            if skill_name in selected_optional:
                enabled.append(skill_name)
                recommended.append(skill_name)
            optional.append(skill_name)

    return {
        "enabled_skills": _dedupe(enabled),
        "recommended_skills": _dedupe(recommended),
        "optional_skills": _dedupe(optional),
        "policy_promoted_skills": policy_promoted,
        "skill_recommendations": {skill: reasons[skill] for skill in _dedupe(recommended + optional)},
    }


def resolve_preset(
    project_dir: Path,
    preset_name: str,
    base_preset: dict,
    platforms: list[str] | None = None,
    enabled_optional_skills: list[str] | None = None,
) -> dict:
    if preset_name != "auto":
        return dict(base_preset)
    detected = detect_project_profiles(project_dir)
    recommendations = recommend_skill_plan(
        detected["detected_profiles"],
        detected["detection_signals"],
        platforms=platforms,
        enabled_optional_skills=enabled_optional_skills,
    )
    resolved = dict(base_preset)
    resolved.update(detected)
    resolved.update(recommendations)
    resolved["enabled_optional_skills"] = _dedupe(enabled_optional_skills or [])
    return resolved


def _build_rationale(skill_name: str, meta: dict, profiles: list[str], signals: list[str]) -> list[str]:
    reasons = [str(meta.get("rationale", skill_name))]
    matched_profiles = [profile for profile in profiles if profile in meta.get("applies_to", [])]
    if matched_profiles:
        reasons.append(f"matched profiles: {', '.join(matched_profiles)}")
    matched_signals = [signal for signal in signals if signal in meta.get("signals_any", [])]
    if matched_signals:
        reasons.append(f"matched signals: {', '.join(matched_signals)}")
    workflow_tags = meta.get("workflow_tags", [])
    if workflow_tags:
        reasons.append(f"workflow tags: {', '.join(str(tag) for tag in workflow_tags)}")
    return reasons


def _is_skill_available_for_platforms(meta: dict, platforms: list[str]) -> bool:
    supported = set(str(platform) for platform in meta.get("platforms", []))
    return all(platform in supported for platform in platforms)


def _matches_profiles(meta: dict, profiles: list[str]) -> bool:
    applies_to = set(str(item) for item in meta.get("applies_to", []))
    if "*" in applies_to:
        return True
    return bool(applies_to.intersection(profiles))


def _matches_signals(meta: dict, signals: list[str]) -> bool:
    required_any = set(str(item) for item in meta.get("signals_any", []))
    if not required_any:
        return True
    return bool(required_any.intersection(signals))


def _policy_promoted_skills(profiles: list[str]) -> dict[str, str]:
    promoted: dict[str, str] = {}
    if "next-app" in profiles:
        promoted["specify"] = "next-app repos default to full specification workflow"
    if "react-lib" in profiles:
        promoted["specify"] = "react-lib repos benefit from explicit API/change planning"
    if "monorepo" in profiles or "pnpm-monorepo" in profiles:
        promoted["execute"] = "monorepo repos usually need longer coordinated execution chains"
        promoted["spec-validate"] = "monorepo repos benefit from stronger spec verification across packages"
    return promoted


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _read_first_existing(*paths: Path) -> str:
    for path in paths:
        try:
            if path.exists():
                return path.read_text(encoding="utf-8").lower()
        except OSError:
            continue
    return ""


def _package_deps(package_data: dict) -> set[str]:
    deps = set()
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        values = package_data.get(key, {})
        if isinstance(values, dict):
            deps.update(str(name) for name in values.keys())
    return deps


def _has_workspace_config(workspaces: object) -> bool:
    if isinstance(workspaces, list):
        return bool(workspaces)
    if isinstance(workspaces, dict):
        packages = workspaces.get("packages")
        return isinstance(packages, list) and bool(packages)
    return False


def _is_react_library_package(package_data: dict, deps: set[str]) -> bool:
    if "react" not in deps:
        return False
    if "next" in deps:
        return False
    exports = package_data.get("exports")
    has_library_entry = any(
        bool(package_data.get(key)) for key in ("main", "module", "types", "typesVersions", "bin")
    ) or isinstance(exports, (dict, str))
    return has_library_entry or any(dep in deps for dep in {"tsup", "rollup", "vite", "storybook"})


def _dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))
