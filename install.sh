#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${1:-.}"
PLATFORM="${PLATFORM:-claude}"

info() {
  printf '[so2x-harness] %s\n' "$1"
}

fail() {
  printf '[so2x-harness] ERROR: %s\n' "$1" >&2
  exit 1
}

if ! command -v python3 >/dev/null 2>&1; then
  if command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    fail "python3 또는 python을 찾지 못했습니다. Python을 설치한 뒤 다시 실행해 주세요."
  fi
else
  PYTHON_BIN="python3"
fi

if [ ! -d "$PROJECT_DIR" ]; then
  fail "대상 프로젝트 디렉터리가 없습니다: $PROJECT_DIR"
fi

case "$PLATFORM" in
  claude)
    ;;
  *)
    fail "현재 지원하지 않는 platform입니다: $PLATFORM (지원: claude)"
    ;;
esac

PROJECT_DIR_ABS="$(cd "$PROJECT_DIR" && pwd)"

info "project=$PROJECT_DIR_ABS"
info "platform=$PLATFORM"
info "python=$PYTHON_BIN"

"$PYTHON_BIN" "$ROOT_DIR/scripts/apply.py" --project "$PROJECT_DIR_ABS" --platform "$PLATFORM"

info "설치가 끝났습니다. 확인하려면 아래를 실행하세요:"
info "  $PYTHON_BIN $ROOT_DIR/scripts/doctor.py --project $PROJECT_DIR_ABS"
