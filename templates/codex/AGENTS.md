# AGENTS

<!-- SO2X-HARNESS:BEGIN -->
# AGENTS

Shared harness guidance for AI agents.

## Core workflow
1. Clarify requirements before implementation.
2. Prefer a small explicit plan for non-trivial work.
3. Keep scope tight.
4. Verify before claiming completion.

## Rules

### file-size-limit

# File size limit

- Prefer files under 300 lines.
- Split by concern when a file grows too large.

### language-policy

# Language policy

- AI responses: Korean
- Code comments: English
- Commit messages: Korean

### scope-control

# Scope control

- Do not refactor unrelated code.
- Keep changes limited to the requested goal.
- Call out assumptions explicitly.

### testing-policy

# Testing policy

- Verify changed behavior before claiming completion.
- Prefer targeted tests first, broader checks second.

### verification-policy

# Verification policy

- Final output should include what changed, evidence, and remaining risks.

<!-- SO2X-HARNESS:END -->
