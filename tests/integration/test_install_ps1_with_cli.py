from __future__ import annotations

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def test_install_ps1_declares_with_cli_parameter() -> None:
    script = (ROOT_DIR / "install.ps1").read_text(encoding="utf-8")

    assert "[switch]$WithCli" in script


def test_install_ps1_includes_cli_install_helper_and_messages() -> None:
    script = (ROOT_DIR / "install.ps1").read_text(encoding="utf-8")

    assert "function Install-So2xCli" in script
    assert 'Info "so2x-cli 설치를 진행합니다."' in script
    assert 'Info "so2x-cli 설치를 건너뜁니다. 필요하면 repo에서 pip install -e . 하세요."' in script


def test_install_ps1_supports_with_cli_prompt_choice() -> None:
    script = (ROOT_DIR / "install.ps1").read_text(encoding="utf-8")

    assert 'Read-Host "so2x-cli도 설치할까요? [y/N]"' in script
    assert 'if ($reply -match "^(y|yes)$") {' in script
