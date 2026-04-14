---
name: spec-validate
description: Validate spec-lite documents for structure, completeness, and consistency
validate_prompt: |
  Output must include:
  - Overall status: PASS or FAIL
  - Checked sections list
  - Issues found (if any) with specific locations
---

# spec-validate

spec-lite 문서의 구조, 완결성, 일관성을 검증합니다.

## When to use

- 구현을 시작하기 전에 spec 문서가 충분한지 확인할 때
- 리뷰 요청 전에 spec 품질을 점검할 때
- 기존 spec이 여전히 유효한지 확인할 때

## Checklist

### Structure

- [ ] Goal 섹션이 존재하고 명확한가
- [ ] Key Decisions 섹션이 존재하는가
- [ ] Requirements 섹션이 존재하고 R1, R2... 번호가 매겨졌는가
- [ ] Risks / Unknowns 섹션이 존재하는가
- [ ] Implementation Steps 섹션이 존재하는가
- [ ] Verification 섹션이 존재하고 체크리스트 형태인가

### Completeness

- [ ] Goal이 측정 가능한 결과를 포함하는가
- [ ] 각 Requirement가 검증 가능한가
- [ ] Implementation Steps가 Requirement를 모두 커버하는가
- [ ] Verification 항목이 모든 Requirement에 대응하는가

### Consistency

- [ ] Requirements와 Implementation Steps가 모순되지 않는가
- [ ] Key Decisions이 Requirements에 반영되었는가
- [ ] Risks에 대한 대응이 Implementation Steps에 포함되었는가

## Output format

```
spec-validate result:
  File: <path>
  Status: PASS | FAIL
  Sections: <checked sections>
  Issues:
    - <issue description> (<location>)
```
