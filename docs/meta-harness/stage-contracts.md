# Stage Artifact Contracts

so2x-harness의 meta-harness는 stage를 대화 순서가 아니라 artifact handoff 규약으로 정의한다.
각 stage는 이전 stage의 출력물만으로 재현 가능해야 한다.

## Global Rules
- 각 stage는 명시적 input artifact만 읽는다.
- conversation history는 필수 의존성이 아니어야 한다.
- stage 출력물은 다음 stage의 유일한 handoff surface가 된다.
- 검증 실패는 stage 내부 실패로 남기고, 다음 stage로 넘기지 않는다.

## Stage 0: Deep Interview

### Objective
이번 실행에서 필요한 per-run variables와 승인 정책을 수집한다.

### Inputs
- `docs/meta-harness/harness-spec.md`
- `docs/meta-harness/interview-schema.md`
- `CLAUDE.md`
- prior `_state.json`(optional)

### Outputs
- `outputs/<run-id>/interview/answers.json`
- `outputs/<run-id>/interview/summary.md`

### Validation
- required answer fields present
- approval policy normalized
- deliverable paths non-empty

### Resume Boundary
`answers.json`이 유효하면 Stage 0은 완료로 간주한다.

## Stage 1: Plan

### Objective
인터뷰 결과를 기반으로 실행 계획과 routing 결정을 만든다.

### Inputs
- interview answers
- harness spec
- current `spec.json`
- current `harness.json`

### Outputs
- `outputs/<run-id>/plan/plan.md`
- `outputs/<run-id>/plan/routing-decision.json`
- `outputs/<run-id>/plan/task-map.json`

### Validation
- task breakdown complete
- stage ordering explicit
- routing choice justified by capability snapshot
- expected artifacts declared

### Resume Boundary
`plan.md`와 `routing-decision.json`이 둘 다 유효하면 다음 stage로 진행 가능하다.

## Stage 2: Execute

### Objective
계획된 task를 실제로 수행하고 실행 산출물을 남긴다.

### Inputs
- plan outputs
- relevant project files
- current `spec.json`

### Outputs
- `outputs/<run-id>/execution/artifacts.json`
- `outputs/<run-id>/execution/log.md`
- task별 concrete artifact files

### Validation
- required artifacts all produced
- command/test evidence captured
- failed task remains localized in execution log

### Resume Boundary
`artifacts.json`을 기준으로 완료/미완료 task를 판별한다.

## Stage 3: Review

### Objective
실행 결과를 so2x의 필수 3개 렌즈로 분리 검토한다.

### Inputs
- execution artifacts
- execution log
- plan outputs

### Outputs
- `outputs/<run-id>/review/code-reuse.md`
- `outputs/<run-id>/review/code-quality.md`
- `outputs/<run-id>/review/efficiency.md`
- `outputs/<run-id>/review/final-verdict.json`

### Validation
- 세 개 리뷰 문서가 모두 존재한다.
- 각 리뷰는 pass|needs_changes|blocked 중 하나의 verdict를 가진다.
- `final-verdict.json`은 stage별 후속 액션을 명시한다.

### Review Lens Rules
- Code Reuse Review: 중복/기존 자산 활용 여부
- Code Quality Review: 명확성, 일관성, 안정성, 검증 충족 여부
- Efficiency Review: 과설계, 불필요 작업, 실행 비용 관점

### Resume Boundary
세 렌즈와 final verdict가 모두 있으면 Review stage 완료다.

## Stage 4: Finalize

### Objective
최종 보고서와 resume state를 갱신한다.

### Inputs
- review verdict
- approved artifacts
- prior `_state.json`

### Outputs
- `outputs/<run-id>/final/summary.md`
- `outputs/<run-id>/_state.json`

### Validation
- summary가 concrete artifacts를 참조한다.
- state가 `completed`, `awaiting_input`, `blocked`, `failed` 중 하나로 닫힌다.

## Handoff Invariants
- Stage 1은 Stage 0 output 없이 시작하지 않는다.
- Stage 2는 plan artifact 없이 시작하지 않는다.
- Stage 3은 execution evidence 없이 시작하지 않는다.
- Stage 4는 review verdict 없이 시작하지 않는다.

## Failure Handling Boundary
실패 처리/재시도는 본 규약의 핵심 목표가 아니다.
다만 so2x-harness에서는 최소한 아래는 표면화한다.
- 어떤 stage에서 멈췄는지
- 어떤 artifact가 유효한지
- 다음 재개 시 어디서부터 다시 시작할지

## Mapping To Thin Core Runtime
- `spec.json`은 high-level task state를 유지한다.
- `harness.json`은 role runner/timeout/retry를 유지한다.
- `_state.json`은 run-local orchestration state를 유지한다.
- stage artifact는 `outputs/<run-id>/...` 아래에 위치한다.
