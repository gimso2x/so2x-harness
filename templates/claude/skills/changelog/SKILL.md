---
name: changelog
description: Record structured change history with decisions, alternatives, and rationale
validate_prompt: |
  Output must include:
  - Change type (added/changed/fixed/deprecated/removed)
  - Summary
  - Decision rationale (if applicable)
---

# changelog

변경 이력을 구조화된 형식으로 기록합니다.

## When to use

- 의미 있는 변경을 완료했을 때
- 중요한 결정을 내렸을 때
- 대안을 검토했을 때

## Change types

| Type | Description |
|---|---|
| `added` | 새로운 기능 |
| `changed` | 기존 기능의 변경 |
| `fixed` | 버그 수정 |
| `deprecated` | 곧 제거될 기능 |
| `removed` | 제거된 기능 |

## Format

```markdown
## [version] - YYYY-MM-DD

### added
- 기능 설명
  - **Why**: 왜 추가했는가
  - **Decision**: 어떤 결정을 내렸는가
  - **Alternatives**: 고려했던 다른 방법 (있다면)

### changed
- 변경 설명
  - **Why**: 왜 변경했는가

### fixed
- 수정 설명
  - **Root cause**: 근본 원인
```

## Notes

- `CHANGELOG.md`에 Keep a Changelog 형식으로 기록
- 커밋 메시지에 결정 사항 포함
- spec-lite가 있다면 참조 링크 포함
