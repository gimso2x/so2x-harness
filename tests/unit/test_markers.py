from __future__ import annotations

import pytest

from scripts.lib.markers import extract_marker_block, upsert_marker_block


def test_extract_marker_block_basic() -> None:
    text = "before\n<!-- SO2X:BEGIN -->\nhello\n<!-- SO2X:END -->\nafter"
    result = extract_marker_block(text, "SO2X")
    assert "<!-- SO2X:BEGIN -->" in result
    assert "hello" in result
    assert "<!-- SO2X:END -->" in result


def test_extract_marker_block_multiline() -> None:
    text = "<!-- SO2X:BEGIN -->\nline1\nline2\nline3\n<!-- SO2X:END -->"
    result = extract_marker_block(text, "SO2X")
    assert "line1" in result
    assert "line2" in result
    assert "line3" in result


def test_extract_marker_block_not_found_raises() -> None:
    text = "no markers here"
    with pytest.raises(ValueError, match="marker block not found"):
        extract_marker_block(text, "SO2X")


def test_upsert_marker_block_replace() -> None:
    existing = "before\n<!-- SO2X:BEGIN -->\nold\n<!-- SO2X:END -->\nafter"
    new_block = "<!-- SO2X:BEGIN -->\nupdated\n<!-- SO2X:END -->"
    result = upsert_marker_block(existing, new_block, "SO2X")
    assert "updated" in result
    assert "old" not in result
    assert "before" in result
    assert "after" in result


def test_upsert_marker_block_insert_appends() -> None:
    existing = "existing content"
    block = "<!-- SO2X:BEGIN -->\nnew block\n<!-- SO2X:END -->"
    result = upsert_marker_block(existing, block, "SO2X")
    assert "existing content" in result
    assert "new block" in result


def test_upsert_marker_preserves_surrounding() -> None:
    existing = (
        "# Header\n\nSome text\n\n<!-- SO2X:BEGIN -->\nold\n<!-- SO2X:END -->\n\nFooter"
    )
    new_block = "<!-- SO2X:BEGIN -->\nnew\n<!-- SO2X:END -->"
    result = upsert_marker_block(existing, new_block, "SO2X")
    assert result.startswith("# Header")
    assert "Footer" in result
