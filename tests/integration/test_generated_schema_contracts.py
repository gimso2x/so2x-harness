from __future__ import annotations

import json
from pathlib import Path

import jsonschema

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
SPEC_SCHEMA = json.loads((ROOT_DIR / "schemas/spec.schema.json").read_text(encoding="utf-8"))
MINIMAL_SPEC = json.loads((ROOT_DIR / "templates/minimal/spec.json").read_text(encoding="utf-8"))


def test_minimal_spec_template_validates_against_spec_schema() -> None:
    jsonschema.validate(MINIMAL_SPEC, SPEC_SCHEMA)


def test_spec_schema_is_lite_only() -> None:
    schema_text = (ROOT_DIR / "schemas/spec.schema.json").read_text(encoding="utf-8")
    assert "l0" not in schema_text
    assert "l1" not in schema_text
    assert "reviewer" not in schema_text
    assert "learning" not in schema_text
