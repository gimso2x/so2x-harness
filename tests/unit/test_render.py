from __future__ import annotations

import tempfile
from pathlib import Path

from scripts.lib.render import render_template


def _write_template(content: str) -> Path:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".tmpl", delete=False, encoding="utf-8")
    f.write(content)
    f.flush()
    f.close()
    return Path(f.name)


def test_render_simple_replacement() -> None:
    path = _write_template("Hello {{ name }}!")
    try:
        result = render_template(path, {"name": "World"})
        assert result == "Hello World!"
    finally:
        path.unlink()


def test_render_multiple_vars() -> None:
    path = _write_template("{{ a }} and {{ b }}")
    try:
        result = render_template(path, {"a": "foo", "b": "bar"})
        assert result == "foo and bar"
    finally:
        path.unlink()


def test_render_no_vars() -> None:
    path = _write_template("no placeholders here")
    try:
        result = render_template(path, {})
        assert result == "no placeholders here"
    finally:
        path.unlink()


def test_render_missing_key_left_as_is() -> None:
    path = _write_template("Hello {{ name }}!")
    try:
        result = render_template(path, {})
        assert "{{ name }}" in result
    finally:
        path.unlink()


def test_render_json_value() -> None:
    import json

    path = _write_template('{"items": {{ items }}}')
    try:
        items = json.dumps(["a", "b"])
        result = render_template(path, {"items": items})
        assert '"a"' in result
    finally:
        path.unlink()
