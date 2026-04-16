# Harness Spec Contract

so2x-harness에서 작업별 하네스를 설계할 때 사용하는 상위 규약이다.
핵심 목표는 실행 흐름을 대화 맥락이 아니라 명시적 artifact contract로 고정하는 것이다.

## Design Goals
- 작업별 하네스의 범위와 성공 조건을 고정한다.
- fixed criteria / per-run variables / intervention points를 분리한다.
- orchestration 복잡도를 build-time에 고정한다.
- 런타임 agent 차이는 경로나 명령이 아니라 capability snapshot으로 흡수한다.

## Required Sections

### 1. Goal
이 하네스가 자동화해야 하는 최종 결과를 한 문장으로 정의한다.

질문 예시:
- 무엇을 끝내면 이 실행을 성공으로 볼 것인가?
- 최종 사용자가 받는 산출물은 무엇인가?

### 2. Non-Goals
이번 하네스가 의도적으로 하지 않는 것을 명시한다.

예시:
- 배포 자동화 제외
- 운영 장애 복구 제외
- destructive cleanup 제외

### 3. Success Criteria
하네스 완료를 판정하는 객관 조건.

예시:
- 지정 산출물이 생성됨
- required verification이 통과함
- 사용자 승인 지점이 명시된 단계에서만 발생함

### 4. Fixed Criteria
매 실행에서 바뀌지 않는 기준.
실행 전에 설계에 박아두고 deep-interview에서 다시 묻지 않는다.

예시:
- coding standards
- review lenses
- naming policy
- required verification depth
- summary/reporting format

권장 형식:
```json
{
  "review_lenses": [
    "code-reuse-review",
    "code-quality-review",
    "efficiency-review"
  ],
  "naming_policy": "thin-core",
  "verification_policy": "smallest-relevant-check-first"
}
```

### 5. Per-Run Variables
실행마다 달라질 수 있어 deep-interview에서 수집해야 하는 값.

예시:
- target repository
- target path
- feature scope
- allowed change surface
- output destination

### 6. Intervention Points
자동 진행을 멈추고 사용자 판단이 필요한 지점.
"중간에 필요하면 묻기"가 아니라 설계 시점에 고정한다.

예시:
- conflicting design choice
- destructive operation
- review verdict override
- delivery format sign-off

### 7. Orchestration Class
하네스 구조를 `simple` 또는 `complex`로 build-time에 분류한다.
실행 중 바꾸지 않는다.

#### simple
- 선형 stage 흐름
- 조건 분기 없음
- loop/back-edge 없음
- fan-out 없음

#### complex
아래 중 하나라도 있으면 complex다.
- 조건 분기
- 병렬 stage
- loop/back-edge
- 동적 stage fan-out
- stage 수가 run-time에 달라짐

### 8. Capability Assumptions
하네스를 실행할 agent/runtime의 능력을 명시한다.
Claude/Codex/Hermes 전용 경로 대신 capability로 표현한다.

권장 필드:
```json
{
  "delegation": true,
  "nested_delegation": false,
  "background_execution": true,
  "resume_persistence": true,
  "structured_artifact_validation": true
}
```

### 9. Required Artifacts
각 stage가 남겨야 할 최소 산출물 목록.
artifact path는 resume와 review의 기준이 된다.

예시:
- `outputs/<run-id>/interview/answers.json`
- `outputs/<run-id>/plan/plan.md`
- `outputs/<run-id>/execution/artifacts.json`
- `outputs/<run-id>/review/final-verdict.json`
- `outputs/<run-id>/final/summary.md`

### 10. Verification Strategy
어떤 검증을 언제 통과해야 하는지 정의한다.

권장 원칙:
- stage별 artifact schema 검증
- 최종 산출물 completeness 검증
- so2x 3개 리뷰 렌즈를 항상 분리
  - Code Reuse Review
  - Code Quality Review
  - Efficiency Review

## Recommended Template

```md
# Harness Spec: <task-name>

## Goal
<one sentence>

## Non-Goals
- <item>

## Success Criteria
- <item>

## Fixed Criteria
- <item>

## Per-Run Variables
- <item>

## Intervention Points
- <item>

## Orchestration Class
simple | complex

## Capability Assumptions
- delegation: true|false
- nested_delegation: true|false
- background_execution: true|false
- resume_persistence: true|false

## Required Artifacts
- <artifact-path>

## Verification Strategy
- <check>
```

## Mapping To Thin Core
현재 thin core는 `CLAUDE.md` / `spec.json` / `harness.json` 3개 core file을 사용한다.
meta-harness 규약은 이 thin core 위에 추가되는 설계 레이어로 취급한다.

- `CLAUDE.md`: fixed criteria와 요약 규칙 반영
- `spec.json`: 실행 task surface 반영
- `harness.json`: role runner / timeout / retry 반영
- meta-harness docs: interview/stage/resume contract 반영

## Adoption Rules
- fixed knowledge는 인터뷰에서 다시 묻지 않는다.
- stage는 conversation chain이 아니라 artifact chain으로 정의한다.
- resume는 session memory가 아니라 state file로 판정한다.
- orchestration class는 설계 시점에 고정한다.
