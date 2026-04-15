from __future__ import annotations

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def test_install_sh_declares_with_cli_env_toggle() -> None:
    script = (ROOT_DIR / "install.sh").read_text(encoding="utf-8")

    assert 'WITH_CLI="${WITH_CLI:-}"' in script


def test_install_sh_includes_cli_install_helper_and_messages() -> None:
    script = (ROOT_DIR / "install.sh").read_text(encoding="utf-8")

    assert "install_so2x_cli()" in script
    assert 'info "so2x-cli 설치를 진행합니다."' in script
    assert 'info "so2x-cli 설치를 건너뜁니다. 필요하면 repo에서 pip install -e . 하세요."' in script


def test_install_sh_supports_with_cli_prompt_choice() -> None:
    script = (ROOT_DIR / "install.sh").read_text(encoding="utf-8")

    assert "so2x-cli도 설치할까요? [y/N]: " in script
    assert 'case "$reply" in' in script
    assert 'y|Y|yes|YES) WITH_CLI="1" ;;' in script
