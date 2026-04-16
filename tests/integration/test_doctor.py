from __future__ import annotations

import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def test_doctor_on_minimal_project(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "CLAUDE.md").write_text("# Goal\n", encoding="utf-8")
    (project / "harness.json").write_text("{}\n", encoding="utf-8")
    (project / "spec.json").write_text(
        """
{
  "meta": {
    "id": "SPEC-1",
    "goal": "OAuth 로그인 추가",
    "created_at": "2026-04-16T00:00:00+00:00",
    "updated_at": "2026-04-16T00:00:00+00:00"
  },
  "tasks": [
    {
      "id": "T1",
      "role": "dev",
      "action": "OAuth callback 처리 구현",
      "status": "blocked",
      "summary": "redirect URI 확인 필요",
      "last_error": "",
      "depends_on": [],
      "artifacts": [],
      "updated_at": "2026-04-16T00:00:00+00:00"
    }
  ]
}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["python3", str(ROOT_DIR / "scripts/doctor.py"), "--project", str(project)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "[INFO] project:" in result.stdout
    assert "[OK] goal: OAuth 로그인 추가" in result.stdout
    assert "[WARN] next_task: none" in result.stdout
    assert "[WARN] execution_status: blocked on T1" in result.stdout
    assert "[OK] summary: redirect URI 확인 필요" in result.stdout
    assert "[OK] counts: pending=0 in_progress=0 blocked=1 error=0 done=0" in result.stdout
