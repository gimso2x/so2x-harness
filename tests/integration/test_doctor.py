from __future__ import annotations

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def _apply(project: Path) -> None:
    import subprocess

    subprocess.run(
        [
            "python3",
            str(ROOT_DIR / "scripts/apply.py"),
            "--project",
            str(project),
            "--platform",
            "claude",
            "--preset",
            "general",
        ],
        capture_output=True,
        text=True,
        check=True,
    )


def test_doctor_on_installed_project(tmp_project: Path) -> None:
    import subprocess

    _apply(tmp_project)
    result = subprocess.run(
        ["python3", str(ROOT_DIR / "scripts/doctor.py"), "--project", str(tmp_project)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "[OK]" in result.stdout
    assert "manifest" in result.stdout.lower()


def test_doctor_on_empty_project(tmp_path: Path) -> None:
    import subprocess

    empty = tmp_path / "empty-project"
    empty.mkdir()
    result = subprocess.run(
        ["python3", str(ROOT_DIR / "scripts/doctor.py"), "--project", str(empty)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "[WARN]" in result.stdout or "not found" in result.stdout


def test_doctor_detects_rules(tmp_project: Path) -> None:
    import subprocess

    _apply(tmp_project)
    result = subprocess.run(
        ["python3", str(ROOT_DIR / "scripts/doctor.py"), "--project", str(tmp_project)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert "rules_dir" in result.stdout
    assert "skills_dir" in result.stdout


def _apply_codex(project: Path) -> None:
    import subprocess

    subprocess.run(
        [
            "python3",
            str(ROOT_DIR / "scripts/apply.py"),
            "--project",
            str(project),
            "--platform",
            "codex",
            "--preset",
            "general",
        ],
        capture_output=True,
        text=True,
        check=True,
    )


def test_doctor_on_codex_project(tmp_project: Path) -> None:
    import subprocess

    _apply_codex(tmp_project)
    result = subprocess.run(
        ["python3", str(ROOT_DIR / "scripts/doctor.py"), "--project", str(tmp_project)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "[OK]" in result.stdout
    assert "skills" in result.stdout.lower()
