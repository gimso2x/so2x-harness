---
name: specify-lite
description: Turn a goal into lightweight requirements, key decisions, implementation steps, and verification criteria before coding.
validate_prompt: |
  Output must include:
  - Goal
  - Key Decisions
  - Requirements
  - Risks / Unknowns
  - Implementation Steps
  - Verification
---

# Specify Lite

Use this skill before non-trivial work.

This is a lightweight requirements-first skill.
It does not try to create a full spec system.
Its job is to make the work clear enough that implementation can start without hidden assumptions.

## When to use
- the user request is bigger than a tiny edit
- there are obvious product or technical choices hidden in the request
- multiple files or steps will probably be involved
- you need a shared implementation frame before coding

## How to think
1. Restate the goal in plain language.
2. Surface key decisions that affect implementation.
3. Turn the goal into concrete requirements.
4. Separate confirmed facts from unknowns.
5. Propose a small implementation sequence.
6. Define what evidence would count as done.

## Output format

### Goal
One short paragraph describing the target outcome.

### Key Decisions
List the decisions that materially affect implementation.
For each item, include:
- decision
- chosen direction
- reason

### Requirements
Write short concrete requirements.
Prefer statements that can later be verified.

Good examples:
- User can toggle dark mode from settings.
- Theme preference persists across refresh.
- Existing light mode behavior remains unchanged.

### Risks / Unknowns
List anything that is unclear, risky, or needs confirmation.
Do not silently invent missing decisions.

### Implementation Steps
Write a short ordered sequence.
Keep steps concrete and small enough to execute.

### Verification
Describe how completion will be checked.
Include tests, manual checks, or visible outcomes when relevant.

## Quality bar
- Do not jump straight to code structure if product behavior is still vague.
- Do not invent missing decisions unless the user explicitly allows defaults.
- Keep it lightweight: enough structure to reduce ambiguity, not a giant spec.
- Prefer requirements that can later be reviewed against actual changes.

## Minimal example

### Goal
Add a dark mode toggle in settings so the user can switch themes manually.

### Key Decisions
- Decision: toggle location
  - Chosen direction: settings page
  - Reason: clear and discoverable
- Decision: persistence
  - Chosen direction: save in local storage
  - Reason: keep preference across refresh

### Requirements
- User can switch between light and dark mode from settings.
- The chosen theme persists after refresh.
- Existing pages remain readable in both themes.

### Risks / Unknowns
- Whether system theme sync is needed later.
- Whether charts or images need separate dark variants.

### Implementation Steps
1. Add theme toggle UI in settings.
2. Store selected theme locally.
3. Apply theme on app load.
4. Verify key screens in both themes.

### Verification
- Toggle changes theme immediately.
- Refresh keeps selected theme.
- Settings and home screen remain readable in both themes.
