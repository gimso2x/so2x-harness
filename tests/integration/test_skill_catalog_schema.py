from __future__ import annotations

import json
from pathlib import Path

import jsonschema

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CATALOG_SCHEMA = json.loads(
    (ROOT_DIR / "schemas" / "skill-catalog.schema.json").read_text(encoding="utf-8")
)
SKILL_CATALOG = json.loads(
    (ROOT_DIR / "templates" / "project" / ".ai-harness" / "skill-catalog.json").read_text(
        encoding="utf-8"
    )
)


def test_skill_catalog_validates_against_schema() -> None:
    jsonschema.validate(SKILL_CATALOG, CATALOG_SCHEMA)


def test_skill_catalog_keeps_core_simplify_and_squash_entries() -> None:
    assert SKILL_CATALOG["simplify-cycle"]["tier"] == "core"
    assert SKILL_CATALOG["squash-commit"]["tier"] == "core"
    assert SKILL_CATALOG["safe-commit"]["tier"] == "core"
    assert SKILL_CATALOG["simplify-cycle"]["workflow_tags"] == [
        "code-reuse-review",
        "code-quality-review",
        "efficiency-review",
    ]
