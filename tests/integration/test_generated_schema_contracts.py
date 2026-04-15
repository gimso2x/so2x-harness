from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from scripts.lib.manifest import load_manifest

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_SCHEMA = json.loads((ROOT_DIR / "schemas/config.schema.json").read_text(encoding="utf-8"))
MANIFEST_SCHEMA = json.loads(
    (ROOT_DIR / "schemas/manifest.schema.json").read_text(encoding="utf-8")
)


def _apply(*args: str) -> Path:
    import subprocess
    import tempfile

    project = Path(tempfile.mkdtemp()) / "project"
    project.mkdir(parents=True)
    subprocess.run(
        [
            "python3",
            str(ROOT_DIR / "scripts/apply.py"),
            "--project",
            str(project),
            *args,
            "--preset",
            "general",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return project


def test_generated_codex_config_and_manifest_validate_against_schemas() -> None:
    project = _apply("--platform", "codex")
    config = json.loads((project / ".ai-harness" / "config.json").read_text(encoding="utf-8"))
    manifest = load_manifest(project)

    jsonschema.validate(config, CONFIG_SCHEMA)
    jsonschema.validate(manifest, MANIFEST_SCHEMA)


def test_generated_multi_platform_config_and_manifest_validate_against_schemas() -> None:
    project = _apply("--platform", "claude", "codex")
    config = json.loads((project / ".ai-harness" / "config.json").read_text(encoding="utf-8"))
    manifest = load_manifest(project)

    jsonschema.validate(config, CONFIG_SCHEMA)
    jsonschema.validate(manifest, MANIFEST_SCHEMA)
