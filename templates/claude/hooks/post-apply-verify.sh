#!/usr/bin/env bash
# post-apply-verify: Verify harness installation result
set -euo pipefail

PROJECT_DIR="${1:-.}"

ERRORS=0

MANIFEST="$PROJECT_DIR/.ai-harness/manifest.json"
if [ ! -f "$MANIFEST" ]; then
  echo "[post-apply-verify] ERROR: manifest.json not found"
  ERRORS=$((ERRORS + 1))
else
  echo "[post-apply-verify] OK: manifest.json exists"
fi

CONFIG="$PROJECT_DIR/.ai-harness/config.json"
if [ ! -f "$CONFIG" ]; then
  echo "[post-apply-verify] ERROR: config.json not found"
  ERRORS=$((ERRORS + 1))
else
  echo "[post-apply-verify] OK: config.json exists"
fi

CLAUDE_MD="$PROJECT_DIR/CLAUDE.md"
if [ ! -f "$CLAUDE_MD" ]; then
  echo "[post-apply-verify] WARN: CLAUDE.md not found"
else
  if grep -q "SO2X-HARNESS:BEGIN" "$CLAUDE_MD"; then
    echo "[post-apply-verify] OK: CLAUDE.md has harness marker"
  else
    echo "[post-apply-verify] ERROR: CLAUDE.md missing harness marker"
    ERRORS=$((ERRORS + 1))
  fi
fi

RULES_DIR="$PROJECT_DIR/.claude/rules/so2x-harness"
if [ -d "$RULES_DIR" ]; then
  COUNT=$(find "$RULES_DIR" -name "*.md" | wc -l)
  echo "[post-apply-verify] OK: $COUNT rule files installed"
else
  echo "[post-apply-verify] ERROR: rules directory missing"
  ERRORS=$((ERRORS + 1))
fi

SKILLS_DIR="$PROJECT_DIR/.claude/skills/so2x-harness"
if [ -d "$SKILLS_DIR" ]; then
  COUNT=$(find "$SKILLS_DIR" -name "*.md" | wc -l)
  echo "[post-apply-verify] OK: $COUNT skill files installed"
else
  echo "[post-apply-verify] ERROR: skills directory missing"
  ERRORS=$((ERRORS + 1))
fi

if [ "$ERRORS" -gt 0 ]; then
  echo "[post-apply-verify] FAIL: $ERRORS error(s) found"
  exit 1
fi

echo "[post-apply-verify] PASS: installation verified"
