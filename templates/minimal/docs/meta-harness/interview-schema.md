# Deep Interview Schema: sample-task

## Purpose
고정 규칙을 다시 묻지 않고, 이번 실행에서 필요한 per-run variables만 수집한다.

## Inputs
- docs/meta-harness/harness-spec.md
- CLAUDE.md
- prior _state.json(optional)

## Output Artifacts
- outputs/<run-id>/interview/answers.json
- outputs/<run-id>/interview/summary.md

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
- run_goal은 비어 있으면 안 된다.
- target_scope.repo 또는 target_scope.paths 중 최소 하나는 필요하다.
- approval_policy는 boolean으로 정규화한다.
- deliverables는 이름과 경로를 가져야 한다.
