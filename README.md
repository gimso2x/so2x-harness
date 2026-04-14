# so2x-harness

Installable AI harness kit for multi-project development.

여러 프로젝트에 공통 AI harness를 설치해서 쓰기 위한 가벼운 GitHub-managed kit입니다.

목표는 하나입니다.

- 프로젝트마다 같은 AI 작업 규칙을 재사용하고
- GitHub repo 하나에서 중앙 관리하고
- 필요할 때 안전하게 update하고
- 무거운 framework나 binary 없이도 실전에서 바로 쓰는 것

이 repo는 full orchestration framework가 아닙니다.
대신 다음에 집중합니다.

- installable harness
- shared rules and skills
- project-safe update
- requirements-first workflow
- lightweight validation

## Why this exists

기존 AI harness/framework는 크게 두 갈래가 있습니다.

1. 아주 강한 framework
- 장점: 체계적이고 강력함
- 단점: 무겁고 도입 비용이 큼

2. 아주 가벼운 prompt/skill 모음
- 장점: 단순하고 빠름
- 단점: 설치, update, 검증 체계가 약함

`so2x-harness`는 그 중간을 목표로 합니다.

- starter kit처럼 가볍게 시작
- requirements-first와 verification 원칙은 유지
- install/update/manifest는 최소한 갖춤

## Design goals

### 1. GitHub 하나로 중앙 관리
공통 규칙과 skill은 이 repo에서 관리합니다.

### 2. 여러 프로젝트에 설치 가능
각 프로젝트에 필요한 파일만 복사하거나 marker 구간만 삽입합니다.

### 3. 로컬 커스터마이징 허용
프로젝트별 메모와 설정은 남기고, 공통 관리 구간만 update합니다.

### 4. 가벼운 구현
초기 버전은 shell + Python으로 구현합니다.
Go binary, 복잡한 CLI, orchestration engine은 포함하지 않습니다.

### 5. requirements-first
큰 구현 전에는 요구, 결정, 검증 기준을 먼저 정리합니다.

### 6. validate-before-done
완료 주장 전에는 최소 검증 형식을 요구합니다.

## Non-goals

현재 버전에서 하지 않는 것:

- multi-model orchestration
- full spec.json schema engine
- autonomous worker fleet
- project architecture auto-generation
- heavy merge engine
- cross-platform binary distribution

## Repo structure

```text
so2x-harness/
├─ README.md
├─ VERSION
├─ harness.yaml
├─ install.sh
├─ install.ps1
├─ scripts/
│  ├─ apply.py
│  ├─ update.py
│  ├─ doctor.py
│  └─ lib/
│     ├─ manifest.py
│     ├─ markers.py
│     ├─ checksum.py
│     ├─ render.py
│     └─ platform_map.py
├─ templates/
│  ├─ shared/
│  │  ├─ AGENTS.md
│  │  ├─ docs/
│  │  │  ├─ harness-philosophy.md
│  │  │  ├─ workflow.md
│  │  │  └─ review-checklist.md
│  │  └─ snippets/
│  │     └─ validate-prompt.md
│  ├─ claude/
│  │  ├─ CLAUDE.md
│  │  ├─ rules/
│  │  │  ├─ language-policy.md
│  │  │  ├─ scope-control.md
│  │  │  ├─ file-size-limit.md
│  │  │  ├─ testing-policy.md
│  │  │  └─ verification-policy.md
│  │  ├─ skills/
│  │  │  ├─ planning.md
│  │  │  ├─ implementation.md
│  │  │  ├─ debugging.md
│  │  │  ├─ review.md
│  │  │  ├─ specify-lite.md
│  │  │  └─ check-harness.md
│  │  ├─ hooks/
│  │  │  ├─ hooks.json
│  │  │  └─ validate-output.sh
│  │  └─ plugin/
│  │     └─ plugin.json
│  └─ project/
│     └─ .ai-harness/
│        ├─ config.json.tmpl
│        └─ manifest.json.tmpl
├─ materials/
│  ├─ checklist.md
│  └─ examples/
│     ├─ nextjs-example.md
│     └─ api-example.md
└─ examples/
   ├─ project-config.general.json
   └─ project-config.nextjs.json
```

## What comes from where

이 repo는 세 가지 계열의 장점을 섞습니다.

### From lightweight starter-style harnesses
- 단순한 plugin/skill 중심 구조
- 작은 repo 크기
- 빠른 도입
- 교육/공유에 쉬운 형태

### From requirements-first systems
- requirements-first planning
- planning과 execution 분리
- validate prompt 개념
- hook-based guardrails
- traceable review mindset

### From installable framework systems
- install/update scripts
- manifest and checksums
- overwrite / marker / skip 정책
- shared vs platform vs project template 분리

## Supported platforms

v0.1 목표:

- Claude Code only

향후 확장 가능:

- Codex
- Gemini
- other AI coding tools

초기에는 하나만 잘 지원하는 것이 우선입니다.

## Core concepts

### 1. Shared templates
공통 규칙과 skill 원본은 이 repo의 `templates/` 아래에 있습니다.

### 2. Project installation
설치 시 각 프로젝트 안에 실제 사용 파일이 생성됩니다.

예:

```text
my-project/
├─ CLAUDE.md
├─ .claude/
│  ├─ rules/so2x-harness/
│  └─ skills/so2x-harness/
└─ .ai-harness/
   ├─ config.json
   └─ manifest.json
```

### 3. Marker-managed files
일부 파일은 전체를 덮어쓰지 않고 특정 구간만 관리합니다.

예: `CLAUDE.md`

```md
<!-- SO2X-HARNESS:BEGIN -->
공통 관리 영역
<!-- SO2X-HARNESS:END -->
```

이 방식으로 프로젝트별 메모는 남기고 공통 구간만 update할 수 있습니다.

### 4. Manifest-managed updates
설치된 파일 상태는 `.ai-harness/manifest.json`에 기록합니다.

이 파일은 다음을 추적합니다.

- 설치 버전
- 설치 플랫폼
- 파일별 checksum
- 파일별 update 정책
- marker 정보

## File update policies

세 가지 정책만 지원합니다.

### `overwrite`
공통 원본이 항상 우선인 파일

예:
- rules
- shared skills
- hook script

### `marker`
파일 일부 구간만 공통 관리하는 파일

예:
- `CLAUDE.md`
- `AGENTS.md`

### `skip_if_exists`
이미 프로젝트에서 관리 중이면 건드리지 않는 파일

예:
- `.claude/settings.json`
- 로컬 설정 파일
- 팀별 메모 파일

## Installed skill set (v0.1)

v0.1에서는 아래 skill만 기본 제공합니다.

### `planning`
큰 작업 시작 전 계획 구조화

### `implementation`
범위 제한, 작은 단위 구현, 검증 우선

### `debugging`
root cause 중심 디버깅

### `review`
요구사항/위험/검증 기준 기반 리뷰

### `specify-lite`
요구 → 결정 → 구현 순서 → 검증 기준 정리

### `check-harness`
현재 프로젝트의 harness 성숙도 점검

## Spec Lite

이 repo는 full schema 기반 spec engine을 사용하지 않습니다.
대신 가벼운 `spec-lite` 문서를 사용합니다.

기본 형식:

```md
# Spec Lite

## Goal
무엇을 만들거나 바꾸는가

## Key Decisions
중요한 결정과 이유

## Requirements
반드시 만족해야 하는 요구

## Risks / Unknowns
아직 불확실한 점

## Implementation Steps
구현 순서

## Verification
완료 판단 기준
```

목적:
- 큰 작업 전 생각 정리
- 요구사항 누락 줄이기
- 구현/리뷰 기준 만들기

## Validation model

이 repo는 “완료했다”보다 “검증했다”를 더 중요하게 봅니다.

가능하면 skill이나 agent 문서에 `validate_prompt`를 둡니다.

예:

```yaml
---
name: review
description: Review changes against requirements and risks
validate_prompt: |
  Output must include:
  - Summary
  - Findings
  - Risks
  - Verification status
---
```

hook는 완료 후 이 형식을 다시 상기시켜
검토 없이 넘어가는 걸 줄입니다.

## Quick start

로컬 clone 기준 가장 단순한 시작 방법입니다.

```bash
git clone https://github.com/gimso2x/so2x-harness.git
cd so2x-harness

# 임의의 프로젝트에 설치
python3 scripts/apply.py --project /path/to/my-project --platform claude
```

설치가 끝나면 프로젝트 안에 대략 아래 구조가 생깁니다.

```text
my-project/
├─ CLAUDE.md
├─ AGENTS.md
├─ .claude/
│  ├─ rules/so2x-harness/
│  ├─ skills/so2x-harness/
│  └─ hooks/
├─ .claude-plugin/
└─ .ai-harness/
   ├─ config.json
   ├─ manifest.json
   ├─ docs/
   └─ snippets/
```

## Installation

### Recommended
프로젝트 루트에서 직접 적용:

```bash
python3 /path/to/so2x-harness/scripts/apply.py --project . --platform claude
```

### Tested example
실제 테스트는 아래 샘플 프로젝트로 확인했습니다.

- harness repo: `/home/sgkim/ssuk/so2x-harness`
- sample project: `/home/sgkim/ssuk/so2x-sandbox`

실행 예:

```bash
python3 /home/sgkim/ssuk/so2x-harness/scripts/apply.py \
  --project /home/sgkim/ssuk/so2x-sandbox \
  --platform claude
```

예상 결과:
- `CLAUDE.md` 생성 또는 marker 구간 삽입
- `.claude/rules/so2x-harness/` 생성
- `.claude/skills/so2x-harness/` 생성
- `.ai-harness/config.json` 생성
- `.ai-harness/manifest.json` 생성

### Future convenience install
향후 지원 예정:

```bash
curl -fsSL https://raw.githubusercontent.com/<org>/so2x-harness/main/install.sh | sh
```

## Update

설치 후 공통 관리 부분만 갱신합니다.

```bash
python3 /path/to/so2x-harness/scripts/update.py --project .
```

동작:
- manifest 읽기
- 새 template checksum 계산
- `overwrite` 파일 교체
- `marker` 파일은 marker 구간만 교체
- `skip_if_exists` 파일은 유지
- 새 manifest 저장

## Project config

각 프로젝트는 `.ai-harness/config.json`로 local 옵션을 가질 수 있습니다.

예:

```json
{
  "project_name": "my-project",
  "platforms": ["claude"],
  "language": "ko",
  "comment_language": "en",
  "enabled_rules": [
    "language-policy",
    "scope-control",
    "testing-policy"
  ],
  "enabled_skills": [
    "planning",
    "implementation",
    "debugging",
    "review",
    "specify-lite",
    "check-harness"
  ]
}
```

## Manifest example

```json
{
  "name": "so2x-harness",
  "version": "0.1.0",
  "platforms": ["claude"],
  "installed_at": "2026-04-14T10:30:00Z",
  "files": {
    "CLAUDE.md": {
      "mode": "marker",
      "marker": "SO2X-HARNESS",
      "checksum": "sha256:..."
    },
    ".claude/rules/so2x-harness/language-policy.md": {
      "mode": "overwrite",
      "checksum": "sha256:..."
    },
    ".claude/skills/so2x-harness/planning.md": {
      "mode": "overwrite",
      "checksum": "sha256:..."
    }
  }
}
```

## v0.1 scope

반드시 포함:

- Claude-only support
- install script entrypoints
- Python apply/update scripts
- marker-managed `CLAUDE.md`
- manifest recording
- 6 base skills
- 5 base rules
- check-harness
- specify-lite
- validate-output hook

포함하지 않음:

- Codex support
- full plugin marketplace flow
- full spec schema engine
- orchestration engine
- multi-model review engine
- architecture auto-generation
- advanced merge system

## Roadmap

### v0.1
가볍게 설치해서 쓰는 첫 버전

### v0.2
- Codex support
- project-type presets
- stronger hook coverage
- richer check-harness checklist

### v0.3
- spec-lite validation
- review report templates
- project profile presets
- optional QA skill pack

### v1.0
- stable install/update workflow
- versioned releases
- team-wide repeatable rollout

## Principles

### Keep it installable
이 repo는 실험장이 아니라 배포 가능한 kit여야 합니다.

### Keep it small
framework 욕심보다 유지 가능한 크기를 우선합니다.

### Keep local edits safe
프로젝트별 수정은 최대한 보존합니다.

### Keep requirements visible
구현 전에 요구와 검증 기준을 드러냅니다.

### Keep done verifiable
완료는 주장보다 증거로 판단합니다.

## License

TBD
