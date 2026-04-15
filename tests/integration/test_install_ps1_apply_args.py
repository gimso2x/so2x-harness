from __future__ import annotations

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def test_install_ps1_passes_multi_platforms_in_single_apply_invocation() -> None:
    script = (ROOT_DIR / "install.ps1").read_text(encoding="utf-8")

    expected_prefix = (
        '$applyArgs = @("$ResolvedRoot/scripts/apply.py", '
        '"--project", $projectAbs, "--preset", $Preset)'
    )
    assert expected_prefix in script
    assert "if ($Platform.Count -gt 0) {" in script
    assert '$applyArgs += "--platform"' in script
    assert "$applyArgs += $Platform" in script
    assert "foreach ($p in $Platform)" not in script
