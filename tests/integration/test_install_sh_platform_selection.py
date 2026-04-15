from __future__ import annotations

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def test_install_sh_supports_explicit_multi_platform_tokens() -> None:
    script = (ROOT_DIR / "install.sh").read_text(encoding="utf-8")

    assert "normalize_platform_selection()" in script
    assert '3|claude,codex|codex,claude|"claude codex"|"codex claude"|"둘 다"|"둘다")' in script
    assert "printf '  Enter) 감지 결과 그대로 설치\\n'" in script


def test_install_sh_defaults_empty_selection_to_detected_platforms() -> None:
    script = (ROOT_DIR / "install.sh").read_text(encoding="utf-8")

    assert '") printf \'%s\\n\' "$2" ;;' in script
    assert 'info "입력이 없어서 감지된 플랫폼 그대로 설치합니다."' in script


def test_install_sh_passes_multi_platforms_after_single_flag() -> None:
    script = (ROOT_DIR / "install.sh").read_text(encoding="utf-8")

    assert 'set -- "$PYTHON_BIN" "$ROOT_DIR/scripts/apply.py"' in script
    assert 'set -- "$@" --platform' in script
    assert 'for p in $PLATFORM; do' in script
