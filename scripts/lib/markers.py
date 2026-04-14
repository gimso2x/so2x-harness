from __future__ import annotations

import re


def extract_marker_block(text: str, marker: str) -> str:
    pattern = re.compile(
        rf"<!-- {re.escape(marker)}:BEGIN -->.*?<!-- {re.escape(marker)}:END -->",
        re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        raise ValueError(f"marker block not found for {marker}")
    return match.group(0)


def upsert_marker_block(existing_text: str, marker_block: str, marker: str) -> str:
    pattern = re.compile(
        rf"<!-- {re.escape(marker)}:BEGIN -->.*?<!-- {re.escape(marker)}:END -->",
        re.DOTALL,
    )
    if pattern.search(existing_text):
        return pattern.sub(marker_block, existing_text, count=1)

    base = existing_text.rstrip()
    if base:
        return base + "\n\n" + marker_block + "\n"
    return marker_block + "\n"
