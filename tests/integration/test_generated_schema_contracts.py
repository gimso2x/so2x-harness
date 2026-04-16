from __future__ import annotations

import json
from pathlib import Path

import jsonschema

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
SPEC_SCHEMA = json.loads((ROOT_DIR / "schemas/spec.schema.json").read_text(encoding="utf-8"))
STATE_SCHEMA = json.loads((ROOT_DIR / "schemas/state.schema.json").read_text(encoding="utf-8"))
MINIMAL_SPEC = json.loads((ROOT_DIR / "templates/minimal/spec.json").read_text(encoding="utf-8"))
META_HARNESS_STATE = json.loads((ROOT_DIR / "docs/meta-harness/_state.json").read_text(encoding="utf-8"))
MINIMAL_META_HARNESS_STATE = json.loads(
    (ROOT_DIR / "templates/minimal/docs/meta-harness/_state.json").read_text(encoding="utf-8")
)


def test_minimal_spec_template_validates_against_spec_schema() -> None:
    jsonschema.validate(MINIMAL_SPEC, SPEC_SCHEMA)


def test_meta_harness_state_example_validates_against_state_schema() -> None:
    jsonschema.validate(META_HARNESS_STATE, STATE_SCHEMA)


def test_minimal_meta_harness_state_template_validates_against_state_schema() -> None:
    jsonschema.validate(MINIMAL_META_HARNESS_STATE, STATE_SCHEMA)


def test_state_schema_stays_meta_harness_focused() -> None:
    schema_text = (ROOT_DIR / "schemas/state.schema.json").read_text(encoding="utf-8")
    assert "conversation_history" not in schema_text
    assert "transcript" not in schema_text
    assert "chat_log" not in schema_text


def test_spec_schema_is_lite_only() -> None:
    schema_text = (ROOT_DIR / "schemas/spec.schema.json").read_text(encoding="utf-8")
    assert "l0" not in schema_text
    assert "l1" not in schema_text
    assert "reviewer" not in schema_text
    assert "learning" not in schema_text
