# Deep Interview Schema

so2x-harness의 deep-interview는 고정 규칙을 다시 묻는 단계가 아니다.
이 단계는 오직 per-run variables를 수집하고, unsafe action 관련 승인 범위를 정규화한다.

## Purpose
- fixed criteria를 재확인하지 않는다.
- run-specific inputs만 수집한다.
- intervention points에 필요한 승인 정책을 정규화한다.
- 이후 stage가 conversation history 없이도 재현되도록 answers artifact를 만든다.

## Inputs
- `harness-spec.md`
- `CLAUDE.md`
- prior run state(optional)
- 기존 artifact snapshot(optional)

## Output Artifacts
- `outputs/<run-id>/interview/answers.json`
- `outputs/<run-id>/interview/summary.md`

## Question Design Rules
- 질문은 실행 변수만 대상으로 한다.
- 이미 fixed criteria에 있는 것은 다시 묻지 않는다.
- 답이 없으면 unsafe action을 기본 허용하지 않는다.
- answer는 후속 stage가 기계적으로 읽을 수 있게 구조화한다.

## Recommended Question Set
1. 이번 실행의 최종 목표 산출물은 무엇인가?
2. 변경 가능한 대상 repo/path는 어디인가?
3. 변경 범위에서 제외해야 할 영역은 무엇인가?
4. 중간 승인 없이 진행 가능한 범위는 어디까지인가?
5. destructive action이 필요한 경우 어떻게 처리해야 하는가?
6. 결과물을 어떤 형식과 위치에 남겨야 하는가?

## Answer Contract
```json
{
  "run_goal": "string",
  "target_scope": {
    "repo": "string",
    "paths": ["string"],
    "excluded_paths": ["string"]
  },
  "constraints": ["string"],
  "approval_policy": {
    "allow_autonomous_non_destructive": true,
    "requires_confirmation_for_destructive": true,
    "requires_confirmation_for_design_override": true
  },
  "deliverables": [
    {
      "name": "string",
      "path": "string",
      "format": "md|json|txt|other"
    }
  ]
}
```

## Validation Rules
- `run_goal`은 비어 있으면 안 된다.
- `target_scope.repo` 또는 `target_scope.paths` 중 최소 하나는 필요하다.
- `approval_policy`는 boolean으로 정규화한다.
- `deliverables`는 이름과 경로를 가져야 한다.
- 값이 누락되면 safe default를 쓰되 destructive action 승인값은 default 허용 금지.

## Summary Artifact Rules
`summary.md`는 아래만 짧게 기록한다.
- run goal
- target scope
- excluded scope
- approval policy
- deliverables

요약은 사람이 읽기 쉽게 쓰되, 실제 후속 실행 기준은 `answers.json`이다.

## Resume Rules
- `answers.json`이 유효하면 deep-interview는 재실행하지 않는다.
- 단, 사용자가 run scope를 바꾸면 새 run으로 간주한다.
- 기존 `_state.json`이 `awaiting_input` 상태면 요청했던 input schema와 answers를 함께 검증한다.

## Escalation Rules
아래 상황이면 interview stage에서 바로 `awaiting_input` 또는 `blocked`로 넘길 수 있다.
- 대상 path 불명확
- 변경 금지 영역과 작업 목표가 충돌
- destructive action 허용 여부 미정
- deliverable path가 서로 충돌

## Anti-Patterns
- fixed knowledge를 다시 질문하기
- 자유서술만 받고 구조화하지 않기
- approval policy를 텍스트로만 남기기
- 요약만 저장하고 machine-readable answer를 남기지 않기
