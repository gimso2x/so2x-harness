from __future__ import annotations

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def test_install_ps1_supports_explicit_multi_platform_tokens() -> None:
    script = (ROOT_DIR / "install.ps1").read_text(encoding="utf-8")

    assert "function Resolve-PlatformSelection" in script
    assert '"claude,codex" { return @("claude", "codex") }' in script
    assert '"codex,claude" { return @("claude", "codex") }' in script
    assert '"둘 다" { return @("claude", "codex") }' in script


def test_install_ps1_prompt_documents_detected_default_choice() -> None:
    script = (ROOT_DIR / "install.ps1").read_text(encoding="utf-8")

    assert 'Write-Host "  Enter) 감지 결과 그대로 설치"' in script
    assert 'Info "입력이 없어서 감지된 플랫폼 그대로 설치합니다."' in script
