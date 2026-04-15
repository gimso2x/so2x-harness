---
name: execute
description: Execute spec-driven implementation with verification
validate_prompt: |
  Output must include:
  - Tasks completed count
  - Scenarios verified count (pass/fail)
  - Gate results
  - Overall verdict: ship or needs_fixes
---

# execute

spec.json에 정의된 태스크를 구현하고 시나리오별로 검증합니다.

## When to use

- `/specify`로 spec.json이 작성된 후
- `/execute`로 구현 시작
- 태스크 단위로 구현 → 검증 반복

## Pipeline

```
1. Load spec.json
   → l4_tasks에서 pending 태스크 확인

2. For each pending task:
   ├── Implement (작은 범위, 300줄 이하)
   ├── Verify scenarios for related requirements
   │   └── so2x-cli spec check --gate l3_to_l4
   └── Update task status to "done"

3. Final verification
   ├── Verifier 에이전트가 모든 시나리오 독립 검증
   └── so2x-cli spec validate

4. Result
   ├── all pass → ship
   └── any fail → needs_fixes (어떤 시나리오가 실패했는지 보고)
```

## How to use

```
/execute
```

1. 프로젝트의 `.ai-harness/specs/*/spec.json` 탐색
2. status가 "approved"인 spec 선택
3. l4_tasks를 순서대로 구현
4. 각 태스크 완료 후 관련 시나리오 검증
5. 모든 태스크 완료 후 전체 검증

## Rules

1. **spec.json의 태스크만 구현** — 범위를 벗어나지 않음
2. **태스크당 300줄 이하** — 크면 분해
3. **시나리오 검증 필수** — 구현만 하고 검증 건너뛰지 않음
4. **spec.json gates 섹션에 결과 기록**
5. **append-only** — 새 태스크 추가 가능하지만 기존 태스크 수정 불가

## Output

```
execute result:
  Spec: SPEC-AUTH-001
  Tasks: 4/4 done
  Scenarios: 3/3 passed
  Gates: all passed
  Verdict: ship
```
