from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python <3.11
    import tomli as tomllib
import yaml

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
VERSION = (ROOT_DIR / "VERSION").read_text(encoding="utf-8").strip()
README = (ROOT_DIR / "README.md").read_text(encoding="utf-8")
PYPROJECT = tomllib.loads((ROOT_DIR / "pyproject.toml").read_text(encoding="utf-8"))
HARNESS = yaml.safe_load((ROOT_DIR / "harness.yaml").read_text(encoding="utf-8"))


def test_license_file_exists() -> None:
    assert (ROOT_DIR / "LICENSE").exists()


def test_readme_matches_thin_identity() -> None:
    assert "personal per-project harness" in README
    assert "lightweight orchestration scaffold" in README
    assert "core files = `CLAUDE.md` / `spec.json` / `harness.json`" in README
    assert "install/distribution kit가 기본 목표가 아님" in README
    assert "so2x run --file spec.json --next" in README
    assert "공식 entrypoint는 `so2x` 하나만 둡니다." in README
    assert "## Quickstart" in README
    assert "cp templates/minimal/spec.json ./spec.json" in README
    assert "so2x doctor --project ." in README
    assert "outputs/<run-id>/_state.json" in README
    assert "## Meta-harness adoption guide" in README


def test_repo_metadata_versions_are_aligned() -> None:
    assert PYPROJECT["project"]["name"] == "so2x-harness"
    assert PYPROJECT["project"]["version"] == VERSION
    assert HARNESS["version"] == VERSION


def test_minimal_template_includes_meta_harness_docs() -> None:
    template_dir = ROOT_DIR / "templates/minimal/docs/meta-harness"
    assert (template_dir / "harness-spec.md").exists()
    assert (template_dir / "interview-schema.md").exists()
    assert (template_dir / "stage-contracts.md").exists()
    assert (template_dir / "_state.json").exists()


def test_readme_mentions_meta_state_bootstrap_helper() -> None:
    assert "so2x init-state --project ." in README
    assert "`outputs/<run-id>/_state.json` 생성 helper" in README
