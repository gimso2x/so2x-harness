---
name: specify
description: Turn a goal into requirements, decisions, tasks, and verification-ready output before implementation.
validate_prompt: |
  Output must include:
  - Goal
  - Current context summary
  - Key decisions
  - Requirements
  - Tasks
  - Verification plan
---

# specify

목표를 바로 구현하지 말고, 구현 가능한 요구사항과 작업 순서로 먼저 정리합니다.

## When to use

- 새로운 기능이나 큰 변경을 시작하기 전
- 여러 파일이나 단계가 함께 바뀔 가능성이 있을 때
- 구현 전에 결정해야 할 정책, 예외, 상태 변화가 있을 때
- 코딩 전에 검증 기준을 먼저 세우고 싶을 때

## Codex-friendly invocation

```text
$specify OAuth2 Google/GitHub 로그인 추가
```

또는 자연어로 직접 요청해도 되지만, Codex에서는 `$specify`처럼 명시적으로 부르는 예시를 우선 사용합니다.

## What this skill should produce

1. Goal
   - 무엇을 바꾸는지 한두 문장으로 정리
2. Current context
   - 현재 코드/화면/흐름에서 관련된 지점 요약
3. Key decisions
   - 구현 전에 정해야 하는 선택과 이유
4. Requirements
   - 검증 가능한 요구사항 목록
5. Tasks
   - 작은 구현 단계 순서
6. Verification
   - 완료 여부를 확인할 테스트/시나리오

## Recommended output shape

```markdown
### Goal
...

### Current context
...

### Key decisions
- Decision: ...
  - Chosen direction: ...
  - Reason: ...

### Requirements
- ...
- ...

### Tasks
1. ...
2. ...
3. ...

### Verification
- ...
- ...
```

## Rules

1. 코드부터 쓰지 말고 먼저 요구사항과 결정사항을 정리합니다.
2. 숨은 가정이 보이면 명시적으로 드러냅니다.
3. 검증 불가능한 추상 표현보다 테스트 가능한 요구사항을 우선합니다.
4. Claude 전용 slash command, hook, sub-agent chain을 전제로 설명하지 않습니다.
5. 이 문서만 읽어도 Codex 사용자가 바로 실행할 수 있어야 합니다.

## Example

```markdown
### Goal
OAuth2 Google/GitHub 로그인을 추가해 사용자가 외부 계정으로 로그인할 수 있게 한다.

### Current context
현재 로그인은 이메일/비밀번호만 지원하고, 계정 연결 정책은 아직 없다.

### Key decisions
- Decision: 신규 계정 자동 생성 여부
  - Chosen direction: 첫 로그인 시 자동 생성
  - Reason: 가입 장벽을 낮추기 위해
- Decision: 동일 이메일 계정 병합 정책
  - Chosen direction: 명시 확인 전까지 자동 병합하지 않음
  - Reason: 잘못된 계정 연결 위험 방지

### Requirements
- 사용자는 Google 또는 GitHub 버튼으로 로그인할 수 있어야 한다.
- 첫 OAuth 로그인 시 계정이 없으면 새 계정을 만든다.
- 동일 이메일의 기존 로컬 계정은 자동 병합하지 않는다.

### Tasks
1. OAuth provider 설정 지점 정리
2. 로그인 시작/콜백 처리 추가
3. 계정 생성/연결 정책 구현
4. 성공/실패 시나리오 검증

### Verification
- Google 로그인 성공
- GitHub 로그인 성공
- 기존 로컬 계정과 이메일 충돌 시 자동 병합되지 않음
```
