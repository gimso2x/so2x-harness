from __future__ import annotations

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def test_install_ps1_handles_invoke_expression_without_script_path() -> None:
    script = (ROOT_DIR / "install.ps1").read_text(encoding="utf-8")

    assert "$scriptPath = $MyInvocation.MyCommand.Path" in script
    assert "if ($scriptPath) {" in script
    assert "$Root = Split-Path -Parent $scriptPath" in script
    assert "$Root = $null" in script
