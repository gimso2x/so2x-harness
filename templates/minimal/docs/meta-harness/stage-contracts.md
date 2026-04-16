# Stage Artifact Contracts: sample-task

## Global Rules
- 각 stage는 명시적 input artifact만 읽는다.
- conversation history는 필수 의존성이 아니어야 한다.
- stage 출력물은 다음 stage의 유일한 handoff surface가 된다.

## Stage 0: Deep Interview
Inputs:
- docs/meta-harness/harness-spec.md
- docs/meta-harness/interview-schema.md
- CLAUDE.md

Outputs:
- outputs/<run-id>/interview/answers.json
- outputs/<run-id>/interview/summary.md

## Stage 1: Plan
Inputs:
- interview answers
- harness spec
- spec.json
- harness.json

Outputs:
- outputs/<run-id>/plan/plan.md
- outputs/<run-id>/plan/routing-decision.json
- outputs/<run-id>/plan/task-map.json

## Stage 2: Execute
Inputs:
- plan outputs
- relevant project files
- spec.json

Outputs:
- outputs/<run-id>/execution/artifacts.json
- outputs/<run-id>/execution/log.md

## Stage 3: Review
Inputs:
- execution artifacts
- execution log
- plan outputs

Outputs:
- outputs/<run-id>/review/code-reuse.md
- outputs/<run-id>/review/code-quality.md
- outputs/<run-id>/review/efficiency.md
- outputs/<run-id>/review/final-verdict.json

## Stage 4: Finalize
Inputs:
- review verdict
- approved artifacts
- prior _state.json

Outputs:
- outputs/<run-id>/final/summary.md
- outputs/<run-id>/_state.json
