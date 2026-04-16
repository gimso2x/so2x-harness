from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[3]
TEMPLATE_PATH = ROOT_DIR / "templates/minimal/docs/meta-harness/_state.json"


def _now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def render_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def _slugify_harness_name(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "sample-task"


def _rewrite_run_paths(value: Any, run_id: str) -> Any:
    if isinstance(value, str):
        return value.replace("2026-04-16T10-36-00Z-example", run_id)
    if isinstance(value, dict):
        return {key: _rewrite_run_paths(item, run_id) for key, item in value.items()}
    if isinstance(value, list):
        return [_rewrite_run_paths(item, run_id) for item in value]
    return value


def create_meta_harness_state(run_id: str, harness_name: str) -> dict[str, Any]:
    template = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    state = _rewrite_run_paths(template, run_id)
    state["run_id"] = run_id
    state["harness_name"] = _slugify_harness_name(harness_name)
    state["status"] = "running"
    state["current_stage"] = "stage-0-interview"
    state["last_completed_stage"] = None
    state["awaiting_input"] = False
    state["awaiting_input_schema"] = None
    state["updated_at"] = _now_z()
    return state


def write_meta_harness_state_bootstrap(
    project_dir: str | Path,
    run_id: str,
    harness_name: str,
    force: bool = False,
) -> Path:
    root = Path(project_dir)
    output_dir = root / "outputs" / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    state_path = output_dir / "_state.json"
    if state_path.exists() and not force:
        raise SystemExit(f"meta state already exists: {state_path}")
    state = create_meta_harness_state(run_id=run_id, harness_name=harness_name)
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return state_path


def cmd_init_state(args: argparse.Namespace) -> None:
    project_dir = Path(getattr(args, "project", ".")).resolve()
    run_id = getattr(args, "run_id", None) or render_run_id()
    harness_name = getattr(args, "harness_name", None) or project_dir.name
    try:
        state_path = write_meta_harness_state_bootstrap(
            project_dir=project_dir,
            run_id=run_id,
            harness_name=harness_name,
            force=bool(getattr(args, "force", False)),
        )
    except SystemExit as exc:
        raise SystemExit(str(exc)) from exc
    print(f"[meta-state] created {state_path}")
