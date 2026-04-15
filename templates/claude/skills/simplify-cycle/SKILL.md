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
Claude Code에서 `/simplify`를 자주 반복해 쓰는 흐름을 기준으로 만든 마무리 스킬입니다.

## When to use

- 기능 구현은 끝났고 구조를 더 줄일 수 있는지 확인하고 싶을 때
- 중복, 불필요한 분기, 애매한 helper가 남아 있을 수 있을 때
- 최종 커밋 전에 diff를 더 가볍게 만들고 싶을 때

## Core loop

1. 현재 변경 범위와 검증 상태를 먼저 확인합니다.
2. `/simplify` 또는 같은 의도의 simplify pass를 1회 실행합니다.
3. Claude가 sub-agent 결과를 보여주면 최소 아래 3개 lens를 확인합니다.
   - Code Reuse Review
   - Code Quality Review
   - Efficiency Review
4. 각 lens에서 나온 actionable item을 반영하거나, 왜 유지하는지 짧게 남깁니다.
5. 이번 pass에서 줄어든 복잡도와 남은 단순화 후보를 숫자로 적습니다.
6. 관련 테스트/검증을 다시 실행합니다.
7. 남은 simplification count가 0이면 종료합니다.
8. 0이 아니면 같은 루프를 반복합니다.

## How to run in Claude Code

```text
/simplify
```

권장 루프는 아래처럼 해석합니다.

- pass마다 반드시 "remaining simplification count: N" 형태로 남깁니다.
- `3 agents finished (ctrl+o to expand)` 같은 출력이 보이면 expand해서 각 review lens 결과를 확인합니다.
- Code Reuse Review, Code Quality Review, Efficiency Review 셋 중 하나라도 미반영 이슈가 남으면 count를 0으로 두지 않습니다.
- N > 0 이면 다음 `/simplify`를 다시 실행합니다.
- N = 0 이면 종료하고 결과를 요약합니다.

`/simplify`가 현재 세션에 없으면 같은 목표를 자연어로 수행합니다.
예: "현재 diff를 더 단순하게 만들어. Code reuse, code quality, efficiency 3가지 관점으로 먼저 점검하고, 남은 simplification count를 숫자로 답해."

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
  Final pass changes:
    - ...
  Verification:
    - <command/result>
  Stop reason: converged_to_zero | no_safe_gain | blocked_by_requirement
```

## Rules

1. 요구사항을 바꾸는 단순화는 금지합니다.
2. 매 pass 후 관련 검증을 다시 확인합니다.
3. count는 감으로 쓰지 말고 현재 diff 기준으로 설명 가능한 근거를 남깁니다.
4. count가 0이 아니면 완료라고 주장하지 않습니다.
5. 삭제/축소가 유리해 보여도 추적성이나 디버깅성이 크게 나빠지면 멈춥니다.
