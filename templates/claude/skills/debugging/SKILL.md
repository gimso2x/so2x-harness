---
name: debugging
description: Reproduce the problem, identify the root cause, and separate confirmed facts from proposed fixes.
validate_prompt: |
  Output must include:
  - Reproduction
  - Root cause
  - Evidence
  - Next action
---

# Debugging

Use this skill when behavior is wrong, failing, confusing, or inconsistent.
The first goal is not to fix. The first goal is to understand.

## Debugging sequence
1. Reproduce the problem if possible.
2. Record the exact symptom.
3. Trace backward to the likely cause.
4. Distinguish confirmed evidence from hypotheses.
5. Only then suggest the next action.

## What good debugging looks like

### Reproduction
- exact step
- command or action
- observed output or behavior

### Root cause
A short statement of what is actually causing the issue.
Not just where it appears.

### Evidence
- file or code path inspected
- command output
- relevant log or error text
- reason alternative explanations were rejected

### Next action
One of:
- fix candidate
- extra check needed
- missing context to retrieve

## Output format

### Reproduction
How the issue was reproduced, or why reproduction was not possible.

### Symptom
What visibly failed.

### Root cause
Most likely underlying cause, labeled as confirmed or probable.

### Evidence
Concrete evidence for the claim.

### Next action
Smallest sensible next move.

## Quality bar
- Reproduce before theorizing when possible.
- Do not confuse symptom with cause.
- If the cause is only probable, label it clearly.
- Prefer direct evidence over intuition.
