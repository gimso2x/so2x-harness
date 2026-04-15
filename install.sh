#!/bin/sh
set -eu

PROJECT_DIR="${1:-.}"
PLATFORM="${PLATFORM:-}"
WITH_CLI="${WITH_CLI:-}"
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

install_so2x_cli() {
  root_dir="$1"
  info "so2x-cli 설치를 진행합니다."
  if command -v pip3 >/dev/null 2>&1; then
    pip3 install "$root_dir"
  elif command -v pip >/dev/null 2>&1; then
    pip install "$root_dir"
  else
    "$PYTHON_BIN" -m pip install "$root_dir"
  fi
}

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

detect_platforms() {
  found=""
  command -v claude >/dev/null 2>&1 && found="claude"
  command -v codex >/dev/null 2>&1 && found="$found codex"
  printf '%s\n' "$(echo "$found" | xargs)"
}

normalize_platform_selection() {
  choice="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | xargs)"
  case "$choice" in
    "") printf '%s\n' "$2" ;;
    1|claude) printf 'claude\n' ;;
    2|codex) printf 'codex\n' ;;
    3|claude,codex|codex,claude|"claude codex"|"codex claude"|"둘 다"|"둘다") printf 'claude codex\n' ;;
    *)
      case "$choice" in
        *claude*codex*|*codex*claude*) printf 'claude codex\n' ;;
        *codex*) printf 'codex\n' ;;
        *) printf 'claude\n' ;;
      esac
      ;;
  esac
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

# Platform detection + interactive selection
if [ -z "$PLATFORM" ]; then
  DETECTED=$(detect_platforms)
  if [ -z "$DETECTED" ]; then
    DETECTED="claude"
  fi
  printf '[so2x-harness] 감지된 플랫폼: %s\n' "$DETECTED"
  if [ -t 0 ]; then
    printf '설치할 플랫폼을 선택하세요:\n'
    printf '  1) claude\n'
    printf '  2) codex\n'
    printf '  3) 둘 다\n'
    printf '  Enter) 감지 결과 그대로 설치\n'
    printf '  직접 입력도 가능: claude / codex / claude,codex\n'
    printf '선택 [Enter/1/2/3]: '
    read -r choice
    PLATFORM="$(normalize_platform_selection "$choice" "$DETECTED")"
    if [ -z "$(printf '%s' "$choice" | xargs)" ]; then
      info "입력이 없어서 감지된 플랫폼 그대로 설치합니다."
    fi
  else
    PLATFORM="$DETECTED"
  fi
fi

if [ -z "$WITH_CLI" ] && [ -t 0 ]; then
  printf 'so2x-cli도 설치할까요? [y/N]: '
  read -r reply
  case "$reply" in
    y|Y|yes|YES) WITH_CLI="1" ;;
    *) WITH_CLI="" ;;
  esac
fi

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

set -- "$PYTHON_BIN" "$ROOT_DIR/scripts/apply.py" \
  --project "$PROJECT_DIR_ABS" \
  --preset "$PRESET"
set -- "$@" --platform
for p in $PLATFORM; do
  set -- "$@" "$p"
done
"$@"

if [ -n "$WITH_CLI" ]; then
  install_so2x_cli "$ROOT_DIR"
else
  info "so2x-cli 설치를 건너뜁니다. 필요하면 repo에서 pip install -e . 하세요."
fi

info "설치가 끝났습니다. 확인하려면 아래를 실행하세요:"
info "  $PYTHON_BIN $ROOT_DIR/scripts/doctor.py --project $PROJECT_DIR_ABS"
