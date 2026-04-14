---
name: review
description: Review changes against requirements, scope, risks, and verification quality.
validate_prompt: |
  Output must include:
  - Summary
  - Findings
  - Risks
  - Verification status
  - Recommended next step
---

# Review

Use this skill after implementation or before approval.
Its job is not to rewrite the feature. Its job is to judge whether the current change is acceptable.

## What to review

Review the change in four passes.

### 1. Requirement alignment
- Does the change actually satisfy the stated goal?
- Are important requirements covered?
- Is anything important still missing?

### 2. Scope control
- Did the change stay within the requested scope?
- Did it introduce unrelated refactors or behavior changes?
- Are assumptions called out clearly?

### 3. Risk check
- Could this break existing flows?
- Are edge cases or integration points easy to miss?
- Is there any part that looks under-verified?

### 4. Verification quality
- Is there evidence, not just claims?
- Were tests, checks, or manual verification steps shown?
- Is the reported verification actually relevant to the requested change?

## Output format

### Summary
One short paragraph: acceptable as-is, acceptable with caveats, or not ready.

### Findings
- Requirement alignment:
- Scope control:
- Risk check:
- Verification quality:

### Risks
- Risk 1
- Risk 2

### Verification status
- Verified
- Partially verified
- Not verified

### Recommended next step
- Approve
- Fix specific issue first
- Add verification first
- Clarify requirement first

## Quality bar
- Prefer evidence over opinion.
- Separate observed facts from guesses.
- Do not suggest unrelated cleanup unless it blocks approval.
- If you cannot verify something, say it is unverified.
