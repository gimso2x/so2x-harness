---
name: execute
description: Implement work from an approved spec or task breakdown and verify completion against explicit checks.
validate_prompt: |
  Output must include:
  - Tasks completed count
  - Verification results
  - Remaining risks or blockers
  - Overall verdict: ship or needs_fixes
---

# execute

정리된 요구사항이나 spec를 바탕으로 실제 구현과 검증을 진행합니다.

## When to use

- 요구사항/태스크가 이미 정리된 뒤
- 승인된 spec, task list, 또는 구현 체크리스트가 있을 때
- 작업 단위를 순서대로 구현하고 검증해야 할 때

## Codex-friendly invocation

```text
$execute
```

또는 현재 문맥에 있는 spec/task list를 기준으로 “이제 구현해”라고 직접 요청할 수 있습니다.

## Expected workflow

1. 입력으로 받은 spec 또는 task list 확인
2. pending 또는 미완료 작업부터 순서대로 구현
3. 각 작업 후 관련 검증 수행
4. 실패한 검증이 있으면 원인과 보완점 기록
5. 모든 작업 완료 후 최종 verdict 제시

## Recommended output shape

```markdown
### Source
- spec/task reference: ...

### Tasks completed
1. ...
2. ...

### Verification
- test/manual check: pass | fail
- ...

### Remaining risks
- ...

### Verdict
ship | needs_fixes
```

## Rules

1. 정리되지 않은 요구사항을 임의로 확정하지 않습니다.
2. 현재 spec/task 범위를 벗어나는 구현은 분리해서 제안합니다.
3. 구현만 하지 말고 관련 검증 결과를 함께 남깁니다.
4. Claude 전용 slash command, hook, agent orchestration을 전제로 설명하지 않습니다.
5. 이 문서만 읽어도 Codex 사용자가 바로 실행할 수 있어야 합니다.

## Example

```markdown
### Source
- spec/task reference: OAuth 로그인 spec v1

### Tasks completed
1. Google OAuth 시작 endpoint 추가
2. GitHub OAuth callback 처리 추가
3. 신규 사용자 생성 로직 연결

### Verification
- Google 로그인 성공: pass
- GitHub 로그인 성공: pass
- 이메일 충돌 자동 병합 방지: pass

### Remaining risks
- provider 설정값 누락 시 배포 환경에서 실패할 수 있음

### Verdict
ship
```
