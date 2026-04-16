# Goal

Keep this project moving with a thin per-project harness.

# Do

- follow the current task in spec.json
- keep summaries short and concrete
- return STATUS/SUMMARY markers
- verify changed code or explain blockers

# Don't

- do not rewrite unrelated areas
- do not mutate spec.json directly from the runner
- do not invent hidden requirements

# Verification

- run the smallest relevant check
- mention what was verified in SUMMARY

# Summary Rule

Always print:
- STATUS: done|blocked|error
- SUMMARY: one short sentence
- ERROR: only when status is error
