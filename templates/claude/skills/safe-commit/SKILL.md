---
name: safe-commit
description: Pre-commit validation for secrets, file size, scope, and verification status
validate_prompt: |
  Output must include:
  - Files checked count
  - Issues found (if any)
  - Commit safety verdict: SAFE or UNSAFE
---

# safe-commit

커밋 전에 보안, 범위, 검증 상태를 확인합니다.

## When to use

- 변경 사항을 커밋하기 전
- PR을 생성하기 전
- 민감 정보가 포함될 수 있는 작업 후

## Checks

### 1. Secret detection

다음 패턴을 스캔합니다.

- `.env` 파일 내용
- API key 패턴 (`sk-`, `ghp_`, `AKIA`, `AIza` 등)
- 비밀번호/토큰 패턴
- private key 블록

### 2. File size check

- 단일 파일 300줄 초과 여부
- 과도하게 큰 파일이 새로 추가되었는지

### 3. Scope check

- 변경 파일이 작업 범위와 일치하는지
- 관련 없는 파일이 포함되었는지
- 예상치 못한 대량 변경 여부 (10개 파일 초과 시 경고)

### 4. Verification status

- 관련 테스트가 통과했는지
- lint가 통과했는지
- build가 성공했는지 (해당 시)

## Output format

```
safe-commit result:
  Files: <count> checked
  Secrets: CLEAN | FOUND (<count>)
  Size: OK | WARN (<file>: <lines> lines)
  Scope: OK | WARN (<reason>)
  Verification: PASS | FAIL (<reason>)
  Verdict: SAFE | UNSAFE
```

## Notes

- UNSAFE인 경우 커밋을 중단하고 이슈를 해결해야 함
- WARN인 경우 사용자 판단에 맡김
