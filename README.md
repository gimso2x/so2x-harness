# so2x-harness

**여러 프로젝트에 공통 AI harness를 설치해서 쓰는 가벼운 GitHub-managed kit.**

[![CI](https://github.com/gimso2x/so2x-harness/actions/workflows/ci.yml/badge.svg)](https://github.com/gimso2x/so2x-harness/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform: Claude Code](https://img.shields.io/badge/Platform-Claude_Code-blueviolet)](https://docs.anthropic.com/en/docs/claude-code)
[![Version](https://img.shields.io/badge/Version-0.1.1-green)](https://github.com/gimso2x/so2x-harness/blob/main/VERSION)

Quick Start · Why · What's Inside · Install · Update · Presets · Docs

---

> _하나의 repo에서 공통 규칙을 관리하고, 여러 프로젝트에 안전하게 설치하고, 필요할 때 갱신한다._

## Quick Start

```bash
# macOS / Linux
curl -sSfL https://raw.githubusercontent.com/gimso2x/so2x-harness/main/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://raw.githubusercontent.com/gimso2x/so2x-harness/main/install.ps1 | iex"
```

기본값은 `claude + general preset`으로 현재 디렉터리에 설치입니다.

```bash
# 다른 프로젝트에 다른 preset으로 설치
python3 scripts/apply.py --project /path/to/my-project --preset nextjs
```

설치 후 프로젝트 구조:

```
my-project/
├── CLAUDE.md                  # harness 구간이 관리됨
├── AGENTS.md
├── .claude/
│   ├── rules/so2x-harness/    # 5개 규칙
│   ├── skills/so2x-harness/   # 10개 스킬
│   └── hooks/                 # 5개 hook
├── .claude-plugin/
└── .ai-harness/
    ├── config.json            # 프로젝트 설정
    └── manifest.json          # 설치 추적
```

---

## Why This Exists

AI 코딩 도구를 여러 프로젝트에서 쓸 때 같은 문제가 반복됩니다.

| 문제 | so2x-harness의 접근 |
|---|---|
| 프로젝트마다 같은 규칙을 복사 | GitHub repo 하나에서 중앙 관리 |
| 규칙을 업데이트하려면 일일이 수정 | manifest 기반 안전한 업데이트 |
| 로컬 수정과 공통 규칙이 충돌 | marker 구간으로 로컬/공통 분리 |
| 검증 없이 "다 했다"고 넘어감 | validate_prompt + hook으로 검증 |

### 무겁지 않습니다

full orchestration framework가 아닙니다. 설치 가능한 harness kit입니다.

- Python 3.10+ 만 있으면 됨
- Go binary, npm package 불필요
- 프로젝트에 Python 런타임도 불필요 (markdown + shell만 설치됨)
- CI/CD 포함, 테스트 포함, 스키마 검증 포함

---

## What's Inside

### 10 Skills

| Skill | When |
|---|---|
| `planning` | 큰 작업 전 계획 구조화 |
| `implementation` | 범위 제한, 작은 단위 구현 |
| `debugging` | root cause 중심 디버깅 |
| `review` | 요구사항/위험/검증 기준 기반 리뷰 |
| `specify-lite` | 요구 → 결정 → 구현 순서 정리 |
| `check-harness` | harness 성숙도 점검 |
| `spec-validate` | spec-lite 문서 완결성 검증 |
| `setup-context` | 프로젝트 분석 → 컨텍스트 문서 생성 |
| `changelog` | 변경 이력 구조화 기록 |
| `safe-commit` | 커밋 전 검증 (시크릿, 크기, 범위) |

### 5 Rules

| Rule | Purpose |
|---|---|
| `language-policy` | 응답은 한국어, 주석은 영어 |
| `scope-control` | 관련 없는 변경 방지 |
| `file-size-limit` | 파일 300줄 이하 권장 |
| `testing-policy` | 검증 후 완료 판단 |
| `verification-policy` | 변경 내용, 증거, 위험 명시 |

### 5 Hooks

| Hook | Trigger |
|---|---|
| `validate-output` | skill/task 실행 후 출력 검증 |
| `pre-apply-check` | 설치 전 프로젝트 상태 확인 |
| `post-apply-verify` | 설치 후 결과 검증 |
| `pre-commit-check` | 커밋 전 시크릿/크기/범위 검사 |
| `spec-gate` | spec-lite 완결성 게이트 |

---

## Install

### Bootstrap (권장)

```bash
# macOS / Linux
curl -sSfL https://raw.githubusercontent.com/gimso2x/so2x-harness/main/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://raw.githubusercontent.com/gimso2x/so2x-harness/main/install.ps1 | iex"
```

### Local Clone

```bash
git clone https://github.com/gimso2x/so2x-harness.git
cd so2x-harness

# 특정 프로젝트에 설치
python3 scripts/apply.py --project /path/to/project --platform claude --preset general

# 상태 점검
python3 scripts/doctor.py --project /path/to/project
```

---

## Update

설치 후 공통 관리 부분만 갱신합니다. 프로젝트별 수정은 보존됩니다.

```bash
python3 /path/to/so2x-harness/scripts/update.py --project .
```

동작:

| 정책 | 동작 |
|---|---|
| `overwrite` | 템플릿으로 항상 교체 (rules, skills, hooks) |
| `marker` | `SO2X-HARNESS:BEGIN`~`END` 구간만 교체 (CLAUDE.md) |
| `skip_if_exists` | 이미 있으면 유지 (config, AGENTS.md) |

---

## Presets

| Preset | Description |
|---|---|
| `general` | 모든 프로젝트용 기본 preset |
| `nextjs` | Next.js 프로젝트용 preset |

커스텀 preset 작성 → [docs/preset-guide.md](docs/preset-guide.md)

---

## Project Config

각 프로젝트는 `.ai-harness/config.json`으로 로컬 옵션을 가집니다.

```json
{
  "project_name": "my-project",
  "preset": "general",
  "platforms": ["claude"],
  "language": "ko",
  "comment_language": "en",
  "enabled_rules": ["language-policy", "scope-control", "testing-policy"],
  "enabled_skills": ["planning", "implementation", "debugging", "review"]
}
```

---

## Spec Lite

full schema 기반 spec engine 대신 가벼운 markdown 문서를 사용합니다.

```markdown
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

`spec-validate` 스킬로 구조와 완결성을 검증합니다.

---

## Docs

| Document | Description |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | 시스템 구조, 모듈, 데이터 흐름 |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 기여 가이드, 개발 환경, PR 프로세스 |
| [CHANGELOG.md](CHANGELOG.md) | 버전별 변경 이력 |
| [docs/cli-reference.md](docs/cli-reference.md) | 전체 명령 참조 |
| [docs/preset-guide.md](docs/preset-guide.md) | 프리셋 작성 가이드 |

---

## Roadmap

### v0.1 (현재)
Claude Code 지원, 설치/업데이트/doctor, 10 스킬, 5 규칙, CI/CD

### v0.2
- Codex 지원
- project-type presets 확장
- hook coverage 강화

### v0.3
- spec-lite 자동 검증
- review report template
- optional QA skill pack

### v1.0
- stable install/update workflow
- versioned releases
- team-wide repeatable rollout

---

## Principles

| 원칙 | 의미 |
|---|---|
| **Keep it installable** | 배포 가능한 kit, 실험장이 아님 |
| **Keep it small** | framework 욕심보다 유지 가능한 크기 |
| **Keep local edits safe** | 프로젝트별 수정은 최대한 보존 |
| **Keep requirements visible** | 구현 전에 요구와 검증 기준을 드러냄 |
| **Keep done verifiable** | 완료는 주장이 아닌 증거로 판단 |

## License

MIT
