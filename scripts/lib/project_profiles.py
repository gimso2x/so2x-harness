from __future__ import annotations

import json
from pathlib import Path


SKILL_CATALOG = {
    "planning": {
        "tier": "core",
        "applies_to": ["*"],
        "platforms": ["claude", "codex"],
        "priority": 100,
        "rationale": "All projects need a shared planning entry point.",
    },
    "implementation": {
        "tier": "core",
        "applies_to": ["*"],
        "platforms": ["claude", "codex"],
        "priority": 100,
        "rationale": "All projects need a default implementation workflow.",
    },
    "debugging": {
        "tier": "core",
        "applies_to": ["*"],
        "platforms": ["claude", "codex"],
        "priority": 100,
        "rationale": "Every repo needs a default debugging path.",
    },
    "review": {
        "tier": "core",
        "applies_to": ["*"],
        "platforms": ["claude", "codex"],
        "priority": 100,
        "rationale": "Baseline review skill for any change set.",
    },
    "setup-context": {
        "tier": "core",
        "applies_to": ["*"],
        "platforms": ["claude", "codex"],
        "priority": 100,
        "rationale": "All projects need environment/context bootstrap.",
    },
    "check-harness": {
        "tier": "core",
        "applies_to": ["*"],
        "platforms": ["claude", "codex"],
        "priority": 100,
        "rationale": "All projects should verify harness health before work.",
    },
    "safe-commit": {
        "tier": "core",
        "applies_to": ["*"],
        "platforms": ["claude", "codex"],
        "priority": 110,
        "rationale": "Commit safety checks are required across all repos.",
    },
    "simplify-cycle": {
        "tier": "core",
        "applies_to": ["*"],
        "platforms": ["claude", "codex"],
        "priority": 120,
        "rationale": "User-preferred convergence workflow; keep installed everywhere.",
        "workflow_tags": ["code-reuse-review", "code-quality-review", "efficiency-review"],
    },
    "squash-commit": {
        "tier": "core",
        "applies_to": ["*"],
        "platforms": ["claude", "codex"],
        "priority": 115,
        "rationale": "User-preferred post-simplify squash workflow; keep installed everywhere.",
    },
    "review-cycle": {
        "tier": "recommended",
        "applies_to": ["frontend", "backend", "monorepo"],
        "platforms": ["claude", "codex"],
        "priority": 90,
        "signals_any": [
            "package.json:next",
            "package.json:react",
            "package.json:vite",
            "package.json:frontend-framework",
            "pyproject.toml:fastapi",
            "pyproject.toml:django",
            "pyproject.toml:backend-framework",
            "requirements.txt:python-backend",
            "go.mod:backend-service",
            "Cargo.toml:backend-service",
            "workspace:apps+packages",
        ],
        "rationale": "Multi-step review loops help app/service repos converge safely.",
    },
    "specify-lite": {
        "tier": "recommended",
        "applies_to": ["frontend", "backend"],
        "platforms": ["claude", "codex"],
        "priority": 80,
        "signals_any": [
            "package.json:next",
            "package.json:react",
            "package.json:vite",
            "package.json:frontend-framework",
            "pyproject.toml:fastapi",
            "pyproject.toml:django",
            "pyproject.toml:backend-framework",
            "requirements.txt:python-backend",
            "go.mod:backend-service",
            "Cargo.toml:backend-service",
        ],
        "rationale": "Service/UI repos benefit from lighter spec capture before implementation.",
    },
    "spec-validate": {
        "tier": "recommended",
        "applies_to": ["backend", "python-package", "monorepo"],
        "platforms": ["claude", "codex"],
        "priority": 85,
        "signals_any": [
            "pyproject.toml:fastapi",
            "pyproject.toml:django",
            "pyproject.toml:backend-framework",
            "pyproject.toml:python-package",
            "requirements.txt:python-backend",
            "go.mod:backend-service",
            "Cargo.toml:backend-service",
            "workspace:apps+packages",
        ],
        "rationale": "Backends, Python packages, and monorepos benefit from spec verification.",
    },
    "changelog": {
        "tier": "recommended",
        "applies_to": ["python-package", "js-package"],
        "platforms": ["claude", "codex"],
        "priority": 70,
        "signals_any": ["pyproject.toml:python-package", "package.json:js-package"],
        "rationale": "Package repos benefit from release-note discipline.",
    },
    "execute": {
        "tier": "optional",
        "applies_to": ["frontend", "backend", "python-package", "js-package", "monorepo"],
        "platforms": ["claude", "codex"],
        "priority": 40,
        "rationale": "Useful when the repo needs longer execution chains, but not installed by default.",
    },
    "specify": {
        "tier": "optional",
        "applies_to": ["frontend", "backend", "python-package", "js-package", "monorepo"],
        "platforms": ["claude", "codex"],
        "priority": 35,
        "rationale": "Full spec workflow is optional unless the project asks for heavier planning.",
    },
}


def detect_project_profiles(project_dir: Path) -> dict[str, object]:
    signals: list[str] = []
    profiles: list[str] = []

    package_json = project_dir / "package.json"
    if package_json.exists():
        package_data = _load_json(package_json)
        deps = _package_deps(package_data)
        if any(dep in deps for dep in {"next", "react", "vite", "@remix-run/react"}):
            profiles.append("frontend")
            if "next" in deps:
                signals.append("package.json:next")
            elif "react" in deps:
                signals.append("package.json:react")
            elif "vite" in deps:
                signals.append("package.json:vite")
            else:
                signals.append("package.json:frontend-framework")
        if deps and not any(dep in deps for dep in {"next", "react", "vite", "@remix-run/react"}):
            profiles.append("js-package")
            signals.append("package.json:js-package")

    pyproject = project_dir / "pyproject.toml"
    if pyproject.exists():
        text = pyproject.read_text(encoding="utf-8").lower()
        if any(token in text for token in {"fastapi", "django", "flask", "sqlalchemy", "uvicorn"}):
            profiles.append("backend")
            if "fastapi" in text:
                signals.append("pyproject.toml:fastapi")
            elif "django" in text:
                signals.append("pyproject.toml:django")
            else:
                signals.append("pyproject.toml:backend-framework")
        profiles.append("python-package")
        signals.append("pyproject.toml:python-package")

    if (project_dir / "requirements.txt").exists() and "backend" not in profiles:
        profiles.append("backend")
        signals.append("requirements.txt:python-backend")

    if (project_dir / "go.mod").exists():
        profiles.append("backend")
        signals.append("go.mod:backend-service")

    if (project_dir / "Cargo.toml").exists():
        profiles.append("backend")
        signals.append("Cargo.toml:backend-service")

    if (project_dir / "apps").exists() and (project_dir / "packages").exists():
        profiles.append("monorepo")
        signals.append("workspace:apps+packages")

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
) -> dict[str, object]:
    selected_platforms = _dedupe(platforms or ["claude", "codex"])
    enabled: list[str] = []
    recommended: list[str] = []
    optional: list[str] = []
    reasons: dict[str, list[str]] = {}

    for skill_name, meta in sorted(
        SKILL_CATALOG.items(), key=lambda item: (-int(item[1].get("priority", 0)), item[0])
    ):
        if not _is_skill_available_for_platforms(meta, selected_platforms):
            continue
        if not _matches_profiles(meta, profiles):
            continue
        if not _matches_signals(meta, signals):
            continue

        rationale = _build_rationale(skill_name, meta, profiles, signals)
        reasons[skill_name] = rationale
        tier = str(meta.get("tier", "optional"))
        if tier == "core":
            enabled.append(skill_name)
            recommended.append(skill_name)
        elif tier == "recommended":
            enabled.append(skill_name)
            recommended.append(skill_name)
        else:
            optional.append(skill_name)

    return {
        "enabled_skills": _dedupe(enabled),
        "recommended_skills": _dedupe(recommended),
        "optional_skills": _dedupe(optional),
        "skill_recommendations": {skill: reasons[skill] for skill in _dedupe(recommended + optional)},
    }


def resolve_preset(
    project_dir: Path,
    preset_name: str,
    base_preset: dict,
    platforms: list[str] | None = None,
) -> dict:
    if preset_name != "auto":
        return dict(base_preset)
    detected = detect_project_profiles(project_dir)
    recommendations = recommend_skill_plan(
        detected["detected_profiles"],
        detected["detection_signals"],
        platforms=platforms,
    )
    resolved = dict(base_preset)
    resolved.update(detected)
    resolved.update(recommendations)
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


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _package_deps(package_data: dict) -> set[str]:
    deps = set()
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        values = package_data.get(key, {})
        if isinstance(values, dict):
            deps.update(str(name) for name in values.keys())
    return deps


def _dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))