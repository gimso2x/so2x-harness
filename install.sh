#!/bin/sh
set -eu

PROJECT_DIR="${1:-.}"
PLATFORM="${PLATFORM:-claude}"
PRESET="${PRESET:-general}"
REPO_URL="${SO2X_REPO_URL:-https://github.com/gimso2x/so2x-harness.git}"
REPO_REF="${SO2X_REPO_REF:-main}"
TEMP_ROOT=""

info() {
  printf '[so2x-harness] %s\n' "$1"
}

cleanup() {
  if [ -n "$TEMP_ROOT" ] && [ -d "$TEMP_ROOT" ]; then
    rm -rf "$TEMP_ROOT"
  fi
}

fail() {
  printf '[so2x-harness] ERROR: %s\n' "$1" >&2
  cleanup
  exit 1
}

trap cleanup EXIT INT TERM

resolve_root_dir() {
  candidate=""
  if [ -n "${SO2X_LOCAL_ROOT:-}" ] && [ -f "${SO2X_LOCAL_ROOT}/scripts/apply.py" ]; then
    printf '%s\n' "$SO2X_LOCAL_ROOT"
    return 0
  fi

  script_path="${0:-}"
  case "$script_path" in
    /*|./*|../*)
      candidate="$(cd "$(dirname "$script_path")" && pwd)"
      if [ -f "$candidate/scripts/apply.py" ]; then
        printf '%s\n' "$candidate"
        return 0
      fi
      ;;
  esac

  command -v git >/dev/null 2>&1 || fail "raw 설치에는 git이 필요합니다. git을 설치하거나 repo를 clone한 뒤 로컬 install.sh를 실행해 주세요."
  TEMP_ROOT="$(mktemp -d)"
  printf '[so2x-harness] %s\n' "bootstrap source를 임시 디렉터리에 내려받습니다." >&2
  git clone --depth 1 --branch "$REPO_REF" "$REPO_URL" "$TEMP_ROOT/repo" >/dev/null 2>&1 || fail "repo를 내려받지 못했습니다: $REPO_URL@$REPO_REF"
  printf '%s\n' "$TEMP_ROOT/repo"
}

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  fail "python3 또는 python을 찾지 못했습니다. Python을 설치한 뒤 다시 실행해 주세요."
fi

if [ ! -d "$PROJECT_DIR" ]; then
  fail "대상 프로젝트 디렉터리가 없습니다: $PROJECT_DIR"
fi

case "$PLATFORM" in
  claude) ;;
  *) fail "현재 지원하지 않는 platform입니다: $PLATFORM (지원: claude)" ;;
esac

case "$PRESET" in
  general) ;;
  *) fail "현재 지원하지 않는 preset입니다: $PRESET (지원: general)" ;;
esac

ROOT_DIR="$(resolve_root_dir)"
PROJECT_DIR_ABS="$(cd "$PROJECT_DIR" && pwd)"

info "project=$PROJECT_DIR_ABS"
info "platform=$PLATFORM"
info "preset=$PRESET"
info "python=$PYTHON_BIN"
info "source=$ROOT_DIR"

"$PYTHON_BIN" "$ROOT_DIR/scripts/apply.py" --project "$PROJECT_DIR_ABS" --platform "$PLATFORM" --preset "$PRESET"

info "설치가 끝났습니다. 확인하려면 아래를 실행하세요:"
info "  $PYTHON_BIN $ROOT_DIR/scripts/doctor.py --project $PROJECT_DIR_ABS"
