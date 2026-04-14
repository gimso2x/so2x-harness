#!/usr/bin/env bash
# spec-gate: Validate spec-lite document completeness
set -euo pipefail

SPEC_FILE="${1:-}"

if [ -z "$SPEC_FILE" ]; then
  # Try to find spec-lite documents
  SPEC_FILE=$(find . -name "*.md" -path "*/specs/*" -type f | head -1)
  if [ -z "$SPEC_FILE" ]; then
    echo "[spec-gate] INFO: no spec file found, skipping gate"
    exit 0
  fi
fi

if [ ! -f "$SPEC_FILE" ]; then
  echo "[spec-gate] ERROR: spec file not found: $SPEC_FILE"
  exit 1
fi

CONTENT=$(cat "$SPEC_FILE")
MISSING=()

# Check required sections
for SECTION in "Goal" "Requirements" "Implementation Steps" "Verification"; do
  if ! echo "$CONTENT" | grep -qi "## .*$SECTION"; then
    MISSING+=("$SECTION")
  fi
done

if [ ${#MISSING[@]} -gt 0 ]; then
  echo "[spec-gate] FAIL: missing required sections in $SPEC_FILE:"
  for S in "${MISSING[@]}"; do
    echo "  - $S"
  done
  exit 1
fi

echo "[spec-gate] PASS: $SPEC_FILE has all required sections"
