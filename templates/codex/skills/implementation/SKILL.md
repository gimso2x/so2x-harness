---
name: implementation
description: Implement requested changes in tight scope, keep assumptions visible, and verify before done.
validate_prompt: |
  Output must include:
  - What changed
  - Files changed
  - Evidence
  - Risks / follow-ups
---

# Implementation

Use this skill when the requested work is clear enough to build.
The job is to make the smallest sufficient change, then show evidence.

## Working rules
- Stay within the requested scope.
- Prefer small, direct changes over broad rewrites.
- Avoid unrelated refactors unless they are required to complete the task safely.
- If a decision is unclear, do not silently invent it unless the user explicitly allows defaults.

## Execution sequence
1. Restate the target outcome briefly.
2. Identify the smallest file set likely needed.
3. Make the change in the tightest possible scope.
4. Run the most relevant verification available.
5. Report what changed and what is still uncertain.

## Verification expectations
Use the strongest realistic evidence available.
Examples:
- targeted test output
- build or lint result
- manual verification steps
- before/after behavior summary

## Output format

### What changed
Short summary of the implementation.

### Files changed
- file 1
- file 2

### Evidence
- command run
- result
- relevant visible outcome

### Risks / follow-ups
- remaining risk
- follow-up suggestion if needed

## Quality bar
- Do not claim success without evidence.
- Do not hide uncertainty.
- Keep the change understandable and reviewable.
- Prefer a small finished change over a large half-verified one.
