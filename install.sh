#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${1:-.}"
PLATFORM="${PLATFORM:-claude}"

python3 "$ROOT_DIR/scripts/apply.py" --project "$PROJECT_DIR" --platform "$PLATFORM"
