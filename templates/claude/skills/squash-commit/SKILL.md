---
name: squash-commit
description: Collapse the current branch changes into a single verified commit after review, simplify-cycle, and safe-commit checks.
validate_prompt: |
  Output must include:
  - Base branch used
  - Verification summary
  - Files included
  - Final commit message
  - Safety verdict
---

# squash-commit

작업이 끝난 뒤 현재 브랜치의 의미 있는 변경을 한 개의 커밋으로 압축합니다.

## When to use

- 여러 개의 중간 커밋을 정리하고 싶을 때
- `safe-commit`과 `simplify-cycle`을 통과한 뒤 최종 이력을 깔끔하게 남기고 싶을 때
- PR 전 히스토리를 한 번에 정리하고 싶을 때

## Recommended order

1. 변경 구현 완료
2. `review` 또는 `review-cycle`
3. `simplify-cycle`로 remaining simplification count를 0까지 수렴
4. `safe-commit`
5. `git diff <base>...HEAD --stat`로 포함 범위 재확인
6. squash commit 실행

## How to run in Claude Code

Claude Code에서는 아래 의도로 실행합니다.

```text
현재 브랜치의 변경을 검증 후 single squash commit으로 정리해.
base branch를 먼저 확인하고, 커밋 메시지는 한국어로 간결하게 써.
```

실제 git 조작은 아래 원칙을 따릅니다.

- base branch를 먼저 확인합니다. 기본은 `main`이고 저장소 관례가 다르면 실제 base를 사용합니다.
- 최신 `simplify-cycle` 결과가 있고, `remaining_count == 0` 또는 허용된 종료 사유인지 먼저 확인합니다.
- 최신 `safe-commit` verdict가 `SAFE`인지 확인합니다.
- 최종 diff 범위를 확인한 뒤 `git reset --soft <base>` 또는 동등한 방법으로 staged 상태를 만듭니다.
- 전체 변경이 의도 범위와 일치하는지 다시 확인합니다.
- 한국어 단일 커밋 메시지로 커밋합니다.

## Safety rules

- 검증 실패 상태에서는 squash commit 금지
- `simplify-cycle` 없이 바로 squash 금지
- unrelated change가 섞여 있으면 먼저 분리
- force-push가 필요한 상황이면 그 사실을 명시
- 민감 정보나 생성 산출물이 섞였는지 `safe-commit` 결과를 다시 확인

## Output format

```text
squash-commit result:
  Base branch: <base>
  Verification: PASS | FAIL
  Files included: <count>
  Commit message: <message>
  Safety verdict: SAFE | UNSAFE
```

## Rules

1. squash 전에 포함 범위를 말로 다시 확인합니다.
2. 한 개 커밋으로 묶을 가치가 없는 독립 변경이 있으면 분리 제안합니다.
3. 커밋 메시지는 한국어로, 범위를 드러내는 짧은 문장으로 작성합니다.
4. 검증 근거 없이 바로 squash하지 않습니다.
5. 이미 공유된 브랜치 히스토리를 다시 쓰는 경우 side effect를 명시합니다.
6. squash 결과는 base branch, verification, safety verdict를 상태/이벤트로 남깁니다.
