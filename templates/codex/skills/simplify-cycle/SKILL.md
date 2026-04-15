---
name: simplify-cycle
description: Run repeated simplify passes until the remaining simplification count converges to zero, then report what changed and what still looks risky.
validate_prompt: |
  Output must include:
  - Pass count
  - Remaining simplification count
  - What changed in the final pass
  - Verification evidence
  - Stop reason
---

# simplify-cycle

큰 작업이 끝난 뒤 구조를 더 단순하게 만들 수 있는지 여러 번 압축 점검합니다.
Codex에서는 Claude의 slash command에 의존하지 않고 같은 루프를 자연어/명시 호출로 수행합니다.

## When to use

- 기능 구현은 끝났고 구조를 더 줄일 수 있는지 확인하고 싶을 때
- 중복, 불필요한 분기, 애매한 helper가 남아 있을 수 있을 때
- 최종 커밋 전에 diff를 더 가볍게 만들고 싶을 때

## Codex-friendly invocation

```text
$simplify-cycle
```

또는 아래처럼 직접 지시해도 됩니다.

```text
현재 diff를 한 번 더 단순화해. Code reuse, code quality, efficiency 세 관점으로 먼저 점검하고, 남은 simplification count를 숫자로 적어. 0이 아니면 다시 같은 pass를 반복해.
```

## Core loop

1. 현재 변경 범위와 검증 상태를 먼저 확인합니다.
2. simplify pass를 1회 실행합니다.
3. Claude의 `/simplify`에서 자주 보는 3개 lens를 Codex에서도 같은 기준으로 점검합니다.
   - Code Reuse Review
   - Code Quality Review
   - Efficiency Review
4. 각 lens에서 나온 actionable item을 반영하거나, 왜 유지하는지 짧게 남깁니다.
5. 이번 pass에서 줄어든 복잡도와 남은 단순화 후보를 숫자로 적습니다.
6. 관련 테스트/검증을 다시 실행합니다.
7. 남은 simplification count가 0이면 종료합니다.
8. 0이 아니면 같은 루프를 반복합니다.

## Convergence state

각 pass마다 최소 아래 상태를 남깁니다.

- `pass_index`
- `remaining_count`
- `lens_results.code_reuse`
- `lens_results.code_quality`
- `lens_results.efficiency`
- `actions_taken`
- `verification_commands`
- `stop_reason`

`remaining_count`는 최종 목표가 0입니다. 다만 아래 경우는 0이 아니어도 안전 종료 가능합니다.

- `no_safe_gain` — 더 줄이면 요구사항/가독성/디버깅성이 나빠짐
- `repeated_no_progress` — 같은 종류의 지적이 반복되고 diff 개선이 없음
- `blocked_by_requirement` — 요구사항 때문에 남겨야 함
- `circuit_breaker` — 2~3 pass 연속으로 실질 개선이 없거나 검증만 흔들림

## Simplification checklist

- 같은 의미의 로직이 여러 곳에 중복되지 않는가
- 조건문/branch 수를 줄일 수 있는가
- 이름만 복잡하고 가치가 작은 abstraction이 남아 있지 않은가
- 한 함수/파일이 지나치게 많은 책임을 갖지 않는가
- 테스트나 사용처를 깨지 않고 삭제 가능한 코드가 남아 있지 않은가
- 설명 없이 유지보수 비용만 늘리는 옵션/flag가 남아 있지 않은가

## Stop rules

다음 중 하나면 종료합니다.

- remaining simplification count = 0
- 더 줄이면 요구사항, 가독성, 검증 안정성을 해칠 때
- 같은 종류의 변경이 반복되고 실제 diff 개선이 없을 때

## Output format

```text
simplify-cycle result:
  Passes: <count>
  Remaining simplification count: <n>
  Lens results:
    - code_reuse: <n>
    - code_quality: <n>
    - efficiency: <n>
  Final pass changes:
    - ...
  Verification:
    - <command/result>
  Stop reason: converged_to_zero | no_safe_gain | blocked_by_requirement | repeated_no_progress | circuit_breaker
```

## Rules

1. 요구사항을 바꾸는 단순화는 금지합니다.
2. 매 pass 후 관련 검증을 다시 확인합니다.
3. count는 감으로 쓰지 말고 현재 diff 기준으로 설명 가능한 근거를 남깁니다.
4. count가 0이 아니면 완료라고 주장하지 않습니다.
5. Claude 전용 slash command를 전제로 설명하지 않습니다.
6. 삭제/축소가 유리해 보여도 추적성이나 디버깅성이 크게 나빠지면 멈춥니다.
7. `Code Reuse Review`, `Code Quality Review`, `Efficiency Review`는 pass별 first-class 결과로 남깁니다.
