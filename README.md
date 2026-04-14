# so2x-harness

**Claude Code 중심으로 여러 프로젝트에 공통 AI harness를 설치해서 쓰는 가벼운 GitHub-managed kit.**

[![CI](https://github.com/gimso2x/so2x-harness/actions/workflows/ci.yml/badge.svg)](https://github.com/gimso2x/so2x-harness/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform: Claude Code](https://img.shields.io/badge/Platform-Claude_Code-blueviolet)](https://docs.anthropic.com/en/docs/claude-code)
[![Version](https://img.shields.io/badge/Version-0.4.0-green)](https://github.com/gimso2x/so2x-harness/blob/main/VERSION)

[Quick Start](#quick-start) · [Usage](#usage) · [Spec Engine](#spec-engine) · [Agents](#agents) · [Skills](#skills) · [CLI](#cli) · [Install](#install) · [Docs](#docs)

---

> _하나의 repo에서 공통 규칙을 관리하고, 여러 프로젝트에 안전하게 설치하고, 필요할 때 갱신한다._

## Quick Start

현재 설치 엔진이 공식 지원하는 대상 플랫폼은 Claude Code입니다. 멀티플랫폼 확장은 열어 두고 있지만, 지금 리포에서 바로 검증된 설치 경로는 `claude` 하나입니다.

```bash
# macOS / Linux
curl -sSfL https://raw.githubusercontent.com/gimso2x/so2x-harness/main/install.sh | sh
```

```powershell
# Windows (PowerShell)
powershell -c "irm https://raw.githubusercontent.com/gimso2x/so2x-harness/main/install.ps1 | iex"
```

---

## Usage

harness를 설치하면 Claude Code에서 slash 명령으로 바로 사용할 수 있습니다.

### 새 기능 추가

```
/specify "OAuth2 Google/GitHub 로그인 추가"
```

에이전트가 6단계로 요구사항을 파생합니다:

```
L0: Goal        ← Interviewer가 숨겨진 가정 질문
L1: Context     ← Code Explorer가 코드 분석
L2: Decisions   ← 결정 도출 (선택지와 이유)
L3: Requirements ← 검증 가능한 요구사항 + 시나리오
L4: Tasks       ← 구현 단계 분해
L5: Review      ← 계획 검증
```

spec이 완성되면:

```
/execute
```

태스크별로 구현 → 시나리오 검증 → 완료.

### 일상 작업

```
/planning              # 작업 전 계획
/debugging             # 버그 원인 분석
/review                # 변경 리뷰
/review-cycle          # artifact-first 코드리뷰 파이프라인
/safe-commit           # 커밋 전 검증
/specify-lite          # 요구사항 가볍게 정리
/spec-validate         # 누락 없는지 확인
```

### 빠른 참조

| 하고 싶은 것 | 명령 |
|---|---|
| 새 기능 계획 | `/specify "기능 설명"` |
| 계획 실행 | `/execute` |
| 버그 수정 | `/debugging` 후 설명 |
| 커밋 전 검증 | `/safe-commit` |
| 큰 변경 리뷰 | `/review-cycle` |
| 요구사항 정리 | `/specify-lite` |
| 변경 리뷰 | `/review` |
| 작업 계획 | `/planning` |
| harness 상태 | `doctor.py` |

### 상태 확인 및 업데이트

```bash
# 프로젝트 상태 점검
python3 scripts/doctor.py --project .

# harness 업데이트
python3 scripts/update.py --project .
```

spec 기반 실행 상태까지 같이 관리할 때는 task status와 summary를 바로 기록할 수 있습니다.

```bash
# blocked 상태와 최신 요약 기록
so2x-cli spec set-task-status spec.json \
  --task-id T1 \
  --status blocked \
  --summary "Waiting for approval from product owner"

# doctor는 사람이 읽기 쉬운 top-level surface를 보여줌
python3 scripts/doctor.py --project .
# [WARN] execution_status: blocked on task T1
# [WARN] execution_summary: latest summary: Waiting for approval from product owner
# [OK] pending_tasks: 1 task(s) still pending
```

---

## Why This Exists

| 문제 | 해결 |
|---|---|
| 프로젝트마다 같은 규칙 복사 | GitHub repo 하나로 중앙 관리 |
| 구현 전 요구사항 정리 안 됨 | spec.json 6단계 파생 체인 |
| 검증 없이 "다 했다" | 게이트 기반 검증 + 독립 Verifier |
| 같은 실수 반복 | 학습 축적 시스템 (learnings.jsonl) |

---

## Spec Engine

spec.json을 단일 소스 오브 트루스로, Goal에서 Tasks까지 6단계로 파생합니다.

```
L0: Goal          "무엇을 만들 것인가"
 ↓  게이트
L1: Context       "현재 상태는 어떤가"
 ↓  게이트
L2: Decisions     "어떤 선택을 했는가"
 ↓  게이트
L3: Requirements  "무엇을 만족해야 하는가 (시나리오 + 검증 포함)"
 ↓  게이트
L4: Tasks         "어떤 순서로 구현할 것인가"
 ↓  게이트
L5: Review        "계획이 검증되었는가"
```

각 게이트는 CLI 구조 검증 + 에이전트 품질 검증을 모두 통과해야 다음 단계로 넘어갑니다.

```bash
so2x-cli spec init "OAuth2 추가" --id SPEC-AUTH-001
so2x-cli spec check spec.json --gate all
so2x-cli spec validate spec.json
so2x-cli spec status spec.json
```

---

## Agents

에이전트는 `so2x-cli run`으로 순차 파이프라인에서 자동 실행됩니다.

| Agent | Role | Phase |
|---|---|---|
| **Interviewer** | 질문으로 가정 노출, 결정 강제 | L0, L2 |
| **Code Explorer** | 코드 분석, 패턴 파악 | L1 |
| **Spec Writer** | 검증 가능한 요구사항 + 시나리오 작성 | L3 |
| **Planner** | 요구사항 → 태스크 분해, 순서 배치 | L4 |
| **Reviewer** | 품질/일관성/위험 검토 | L5 |
| **Verifier** | 시나리오별 독립 검증 | 실행 후 |

```bash
so2x-cli run specify "기능 설명"        # Interviewer → Explorer → Writer → Planner → Reviewer
so2x-cli run execute --file spec.json   # Task별 구현 → Verifier 검증
```

---

## Skills

| Skill | When |
|---|---|
| `planning` | 큰 작업 전 계획 구조화 |
| `implementation` | 범위 제한, 작은 단위 구현 |
| `debugging` | root cause 중심 디버깅 |
| `review` | 요구사항/위험/검증 기준 기반 리뷰 |
| `review-cycle` | `.review-artifacts` 기반 근거 문서 + 코드리뷰 파이프라인 |
| `specify-lite` | 요구 → 결정 → 구현 순서 정리 |
| `check-harness` | harness 성숙도 점검 |
| `spec-validate` | spec-lite 문서 완결성 검증 |
| `setup-context` | 프로젝트 분석 → 컨텍스트 문서 생성 |
| `changelog` | 변경 이력 구조화 기록 |
| `safe-commit` | 커밋 전 검증 (시크릿, 크기, 범위) |
| **`specify`** | **6단계 파생 체인 + 게이트 검증** |
| **`execute`** | **spec 기반 구현 + 시나리오 검증** |

---

## CLI (so2x-cli)

```bash
# Spec 관리
so2x-cli spec init "목표"               # spec.json 생성
so2x-cli spec check spec.json --gate all # 게이트 검증
so2x-cli spec validate spec.json         # 전체 구조 검증
so2x-cli spec status spec.json           # 파생 상태 조회
so2x-cli spec guide l3_requirements      # 레이어 필드 안내

# 학습 관리
so2x-cli learn add --problem "..." --rule "..."   # 학습 기록
so2x-cli learn search "키워드"                      # 검색
so2x-cli learn summary                              # 요약

# 파이프라인 실행
so2x-cli run specify "목표"              # 지정 파이프라인
so2x-cli run execute --file spec.json    # 실행 파이프라인
```

---

## Knowledge System

각 프로젝트에 학습이 축적됩니다. `/specify` 실행 시 관련 학습이 자동으로 주입됩니다.

```bash
# 학습 기록
so2x-cli learn add \
  --problem "OAuth callback이 배포마다 다름" \
  --cause "환경 변수 없이 하드코딩" \
  --rule "callback URL은 항상 환경 변수로 설정" \
  --category anti-pattern \
  --tags "oauth,config"

# 검색
so2x-cli learn search "oauth"
# [LRN-E27F72] [anti-pattern] OAuth callback이 배포마다 다름
#   Rule: callback URL은 항상 환경 변수로 설정
```

저장 위치: `my-project/.ai-harness/learnings.jsonl`

---

## Install

현재 설치 엔진은 Claude Code용 하네스 배포를 기준으로 동작합니다. `scripts/apply.py`의 공식 지원 플랫폼도 `claude` 하나이며, 다른 플랫폼 이름을 넘기면 에러를 반환합니다.

```bash
# Bootstrap (macOS / Linux)
curl -sSfL https://raw.githubusercontent.com/gimso2x/so2x-harness/main/install.sh | sh

# CLI 설치 (spec engine 사용 시)
git clone https://github.com/gimso2x/so2x-harness.git
cd so2x-harness && pip install -e .

# 수동 설치
python3 scripts/apply.py --project /path/to/project --platform claude --preset general
```

설치 후 프로젝트 구조:

```
my-project/
├── CLAUDE.md
├── AGENTS.md
├── .claude/
│   ├── rules/so2x-harness/     # 5개 규칙
│   ├── skills/                  # 13개 스킬 폴더 (각각 SKILL.md)
│   ├── agents/so2x-harness/    # 6개 에이전트
│   └── hooks/                  # 5개 hook
└── .ai-harness/
    ├── config.json
    ├── manifest.json
    ├── learnings.jsonl
    └── specs/

.review-artifacts/
└── feature-branch/
    ├── design-intent.md
    ├── code-quality-guide.md
    ├── pr-body.md
    └── review-comments.md
```

---

## Docs

| Document | Description |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | 시스템 구조, 모듈, 데이터 흐름 |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 기여 가이드, 개발 환경, PR 프로세스 |
| [CHANGELOG.md](CHANGELOG.md) | 버전별 변경 이력 |
| [docs/cli-reference.md](docs/cli-reference.md) | 전체 명령 참조 |

---

## Roadmap

### v0.4 (현재)
Spec engine, 6 agents, CLI, knowledge system, orchestration pipeline

### v0.5
- Codex, Gemini 지원 (멀티플랫폼)
- 병렬 에이전트 실행 옵션

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

This repository is licensed under the [MIT License](./LICENSE).
