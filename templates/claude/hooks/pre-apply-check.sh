#!/usr/bin/env bash
# pre-apply-check: Validate target project state before harness installation
set -euo pipefail

PROJECT_DIR="${1:-.}"

if [ ! -d "$PROJECT_DIR" ]; then
  echo "[pre-apply-check] ERROR: project directory does not exist: $PROJECT_DIR"
  exit 1
fi

MANIFEST="$PROJECT_DIR/.ai-harness/manifest.json"
if [ -f "$MANIFEST" ]; then
  echo "[pre-apply-check] WARN: existing harness installation found"
  echo "[pre-apply-check] INFO: update mode will be used for existing files"
fi

# Check for write permission
if [ ! -w "$PROJECT_DIR" ]; then
  echo "[pre-apply-check] ERROR: no write permission for: $PROJECT_DIR"
  exit 1
fi

echo "[pre-apply-check] OK: project directory ready for installation"
