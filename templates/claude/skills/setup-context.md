---
name: setup-context
description: Analyze project structure and generate context documents for AI agents
validate_prompt: |
  Output must include:
  - Project structure summary
  - Key patterns identified
  - Files analyzed count
  - Generated context file paths
---

# setup-context

프로젝트를 분석하여 AI 에이전트가 즉시 이해할 수 있는 컨텍스트 문서를 생성합니다.

## When to use

- 새 프로젝트에 harness를 설치한 직후
- 프로젝트 구조가 크게 변경되었을 때
- AI 에이전트가 프로젝트를 더 잘 이해해야 할 때

## What it generates

분석 결과를 `.ai-harness/docs/` 아래에 저장합니다.

### `project-overview.md`

- 프로젝트 이름과 목적
- 기술 스택 (언어, 프레임워크, 빌드 도구)
- 핵심 패턴 (디렉터리 구조, 네이밍 컨벤션)

### `key-patterns.md`

- 주요 아키텍처 패턴
- 코딩 컨벤션
- 테스트 전략
- 빌드/배포 흐름

## How to use

1. 프로젝트 루트에서 실행
2. `.ai-harness/docs/` 생성 확인
3. CLAUDE.md에 컨텍스트 참조 추가 여부 확인

## Notes

- 기존 컨텍스트 문서가 있으면 덮어쓰지 않고 업데이트 권장
- 생성된 문서는 `overwrite` 정책으로 관리되지 않음 (프로젝트별 소유)
