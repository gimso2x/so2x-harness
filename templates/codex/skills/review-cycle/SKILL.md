---
name: review-cycle
description: Build review artifacts first, then run evidence-based code review with explicit severity and side effects.
validate_prompt: |
  Output must include:
  - Artifact status
  - Review findings with severity
  - Side effects or tradeoffs
  - Verification result
  - Recommended next step
---

# review-cycle

큰 변경이나 위험한 변경은 그냥 `/review` 한 번 치고 끝내면 허술해집니다.
이 스킬은 리뷰 전에 근거 문서를 만들고, 그 문서에 묶여서 리뷰하게 만드는 artifact-first 코드리뷰 파이프라인입니다.

## When to use

- PR 설명이 빈약한데 변경 규모가 큰 경우
- 설계 의도와 실제 코드가 어긋났는지 봐야 하는 경우
- 팀 기준을 취향이 아니라 문서 근거로 묶고 싶은 경우
- 리뷰 코멘트에 side effect와 tradeoff까지 남겨야 하는 경우

## Artifact directory

모든 산출물은 현재 브랜치 기준으로 아래에 저장합니다.

```
.review-artifacts/{branch-name}/
```

기본 파일:

- `design-intent.md` — 왜 이렇게 설계했는지
- `code-quality-guide.md` — 이번 변경에 실제 적용할 리뷰 기준
- `pr-body.md` — 변경 요약, 범위, 위험, 검증
- `review-comments.md` — 최종 리뷰 결과

## Pipeline

### 1. 상태 점검
- `git branch --show-current`로 브랜치 확인
- `git diff main...HEAD --stat` 또는 실제 base branch 대비 diff 범위 확인
- `.review-artifacts/{branch-name}/` 디렉터리 생성

### 2. 설계 의도 정리
- 이번 변경의 목표, 비목표, 의도적 tradeoff를 `design-intent.md`에 적습니다.
- 애매한 선택지는 숨기지 말고 남깁니다.

### 3. 리뷰 기준 정리
- 팀 규칙, 요구사항, 리스크를 바탕으로 `code-quality-guide.md`를 작성합니다.
- 이번 변경과 무관한 일반론은 버리고, 실제로 리뷰할 기준만 남깁니다.

### 4. PR 본문 초안 작성
- `pr-body.md`에 변경 이유, 사용자 영향, 검증 방식, 남은 위험을 요약합니다.

### 5. 근거 기반 리뷰 실행
- 코드 diff, `design-intent.md`, `code-quality-guide.md`, `pr-body.md`를 함께 읽고 리뷰합니다.
- 취향 코멘트는 금지. 근거가 없으면 코멘트도 없습니다.

### 6. 리뷰 반영 + QA
- 각 코멘트에 대해 accept/reject를 명시합니다.
- 수정 후 테스트/빌드/수동 검증을 다시 돌립니다.

## Review comment rules

코멘트는 아래 우선순위를 씁니다.

- `[p1]` 반드시 수정해야 하는 문제
- `[p2]` 강하게 권장되는 수정
- `[p3]` 개선 권장
- `[p4]` 사소한 개선

각 코멘트에는 아래를 남깁니다.

- 근거
- 문제 설명
- 제안
- side effect 또는 tradeoff
- 왜 그래도 이 제안을 하는지

## Output format

```markdown
# Code Review

## Artifact status
- design-intent.md: ready
- code-quality-guide.md: ready
- pr-body.md: ready

## Summary
변경이 승인 가능한지 한 단락으로 요약

## Findings

### [p1] path/to/file.py:42
- 근거: requirement / code-quality-guide 항목
- 내용: ...
- 제안: ...
- side effect: ...
- 제안 이유: ...

## Verification
- 테스트: pass/fail
- 수동 검증: pass/fail

## Recommended next step
- approve / fix first / clarify first
```

## Rules

1. 리뷰 전에 artifact부터 만든다.
2. 설계 의도와 실제 코드가 충돌하면 그걸 제일 먼저 잡는다.
3. 근거 없는 취향 리뷰는 남기지 않는다.
4. side effect를 숨기지 않는다.
5. 검증을 안 했으면 안 했다고 쓴다.
