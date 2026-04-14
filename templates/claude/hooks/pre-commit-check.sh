#!/usr/bin/env bash
# pre-commit-check: Validate changes before commit
set -euo pipefail

STAGED_FILES=$(git diff --cached --name-only 2>/dev/null || true)

if [ -z "$STAGED_FILES" ]; then
  echo "[pre-commit-check] INFO: no staged files"
  exit 0
fi

ISSUES=0

# Secret detection patterns
SECRET_PATTERNS=(
  'sk-[a-zA-Z0-9]{20,}'
  'ghp_[a-zA-Z0-9]{36}'
  'AKIA[0-9A-Z]{16}'
  'AIza[0-9A-Za-z_-]{35}'
  '-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----'
)

for FILE in $STAGED_FILES; do
  if [ ! -f "$FILE" ]; then
    continue
  fi

  # Check for secrets
  for PATTERN in "${SECRET_PATTERNS[@]}"; do
    if grep -qE "$PATTERN" "$FILE" 2>/dev/null; then
      echo "[pre-commit-check] ERROR: potential secret in $FILE (pattern: $PATTERN)"
      ISSUES=$((ISSUES + 1))
    fi
  done

  # Check file size (warn if > 300 lines)
  LINES=$(wc -l < "$FILE" 2>/dev/null || echo 0)
  if [ "$LINES" -gt 300 ]; then
    echo "[pre-commit-check] WARN: $FILE has $LINES lines (recommended max: 300)"
  fi
done

# Check total number of staged files
FILE_COUNT=$(echo "$STAGED_FILES" | wc -l)
if [ "$FILE_COUNT" -gt 10 ]; then
  echo "[pre-commit-check] WARN: $FILE_COUNT files staged — consider splitting into smaller commits"
fi

if [ "$ISSUES" -gt 0 ]; then
  echo "[pre-commit-check] FAIL: $ISSUES issue(s) found — review before committing"
  exit 1
fi

echo "[pre-commit-check] PASS: $FILE_COUNT files checked, no issues found"
