---
name: specify
description: Derive requirements from intent through 6-layer chain with gated validation
validate_prompt: |
  Output must include:
  - spec.json path created/updated
  - Derivation status per layer (L0-L5)
  - Gate results (pass/fail per gate)
  - Issues found (if any)
---

# specify

spec.json 파생 체인을 통해 의도를 검증된 구현 계획으로 변환합니다.

## When to use

- 새로운 기능이나 변경을 시작하기 전
- "add dark mode", "implement OAuth" 같은 요청을 받았을 때
- `/specify "목표 설명"` 형태로 호출

## Pipeline

```
L0: Goal          ← Interviewer가 질문으로 명확화
 │  게이트: so2x-cli spec check --gate l0_to_l1
 ↓
L1: Context       ← Code Explorer가 프로젝트 분석
 │  게이트: so2x-cli spec check --gate l1_to_l2
 ↓
L2: Decisions     ← Interviewer + 분석으로 결정 도출
 │  게이트: so2x-cli spec check --gate l2_to_l3
 ↓
L3: Requirements  ← Spec Writer가 검증 가능한 요구사항 작성
 │  게이트: so2x-cli spec check --gate l3_to_l3
 ↓
L4: Tasks         ← Planner가 태스크 분해
 │  게이트: so2x-cli spec check --gate l4_to_l5
 ↓
L5: Review        ← Reviewer가 최종 검토
    게이트: so2x-cli spec validate
```

## How to use

```
/specify "OAuth2 Google/GitHub 로그인 추가"
```

1. `so2x-cli spec init "목표"`로 spec.json 생성
2. Interviewer 에이전트가 L0 명확화 질문
3. Code Explorer가 L1 컨텍스트 분석
4. Interviewer가 L2 결정 도출
5. Spec Writer가 L3 요구사항 작성
6. Planner가 L4 태스크 분해
7. Reviewer가 L5 최종 검토
8. 각 단계마다 `so2x-cli spec check --gate` 실행

## Rules

1. **spec.json만 수정** — 다른 파일 변경하지 않음
2. **게이트 통과해야 다음 단계** — 실패 시 현재 단계 보완
3. **append-only** — 기존 항목 수정하지 않고 추가만
4. **각 에이전트는 독립적** — 한 에이전트의 출력이 다음 에이전트의 입력

## Output

```
specify result:
  Spec: spec.json
  Status: approved | draft (with pending gates)
  Layers:
    L0: defined
    L1: 3 assumptions, 2 constraints
    L2: 2 decisions
    L3: 3 requirements, 7 scenarios
    L4: 4 tasks
    L5: pass
  Gates: all passed | X failed
```
