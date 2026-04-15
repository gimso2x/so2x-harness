---
name: check-harness
description: Check whether the current project has the minimum harness structure, workflow guardrails, and verification habits.
validate_prompt: |
  Output must include:
  - Overall score (0-10) or level (red/yellow/green)
  - Findings by category
  - Missing items
  - Recommended next steps
---

# Check Harness

Use this skill to diagnose whether a project is ready for reliable AI-assisted work.

## What to inspect

Check the project in five categories.

### 1. Entry points
- `CLAUDE.md` or equivalent root guidance exists
- shared managed section is present
- project-specific notes can coexist with shared guidance

### 2. Shared context
- shared rules are installed
- shared skills are installed
- there is a clear place for local notes and project-specific decisions

### 3. Execution habits
- non-trivial work usually starts with a short plan
- large changes are broken into smaller steps
- scope drift is actively avoided

### 4. Verification
- there is a clear expectation to verify before claiming completion
- test or check commands are known for the project
- reviews mention evidence, not just opinions

### 5. Maintainability
- the harness can be updated without destroying local notes
- managed vs project-owned files are distinguishable
- missing guardrails are easy to identify

## Scoring guide
- 0-3: red — basic harness structure is missing
- 4-7: yellow — partially usable, but important guardrails are weak
- 8-10: green — ready for day-to-day AI-assisted work

## Output format

### Overall
- Score: X/10
- Level: red | yellow | green
- One-line summary

### Findings by category
- Entry points:
- Shared context:
- Execution habits:
- Verification:
- Maintainability:

### Missing items
- Missing item 1
- Missing item 2

### Recommended next steps
1. Highest priority fix
2. Next improvement
3. Nice-to-have improvement

## Review rules
- Prefer direct inspection over assumptions.
- Distinguish what exists from what is only implied.
- If a check cannot be verified, mark it as unverified.
- Keep recommendations practical and small.
