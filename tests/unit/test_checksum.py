from __future__ import annotations

from scripts.lib.checksum import sha256_file, sha256_text


def test_sha256_text_deterministic() -> None:
    result1 = sha256_text("hello world")
    result2 = sha256_text("hello world")
    assert result1 == result2


def test_sha256_text_different_inputs() -> None:
    assert sha256_text("aaa") != sha256_text("bbb")


def test_sha256_text_empty() -> None:
    result = sha256_text("")
    assert result.startswith("sha256:")
    assert len(result.split(":")[1]) == 64


def test_sha256_text_format() -> None:
    result = sha256_text("test")
    assert result.startswith("sha256:")
    hash_part = result.split(":")[1]
    assert all(c in "0123456789abcdef" for c in hash_part)


def test_sha256_file(tmp_path: object) -> None:
    tmp = tmp_path  # type: ignore[assignment]
    f = tmp / "test.txt"  # type: ignore[operator]
    f.write_text("hello world", encoding="utf-8")
    result = sha256_file(f)
    assert result == sha256_text("hello world")


def test_sha256_file_vs_text_same_content() -> None:
    import tempfile
    from pathlib import Path

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("identical content")
        f.flush()
        path = Path(f.name)
    try:
        assert sha256_file(path) == sha256_text("identical content")
    finally:
        path.unlink()
