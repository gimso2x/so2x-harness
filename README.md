# so2x-harness

**여러 프로젝트에 공통 AI harness를 설치해서 쓰는 가벼운 GitHub-managed kit.**

[![CI](https://github.com/gimso2x/so2x-harness/actions/workflows/ci.yml/badge.svg)](https://github.com/gimso2x/so2x-harness/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform: Claude Code](https://img.shields.io/badge/Platform-Claude_Code-blueviolet)](https://docs.anthropic.com/en/docs/claude-code)
[![Version](https://img.shields.io/badge/Version-0.4.0-green)](https://github.com/gimso2x/so2x-harness/blob/main/VERSION)

Quick Start · Why · Spec Engine · Agents · CLI · Install · Docs

---

> _하나의 repo에서 공통 규칙을 관리하고, 여러 프로젝트에 안전하게 설치하고, 필요할 때 갱신한다._

## Quick Start

```bash
# macOS / Linux
curl -sSfL https://raw.githubusercontent.com/gimso2x/so2x-harness/main/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://raw.githubusercontent.com/gimso2x/so2x-harness/main/install.ps1 | iex"
```

```bash
# CLI 설치 (spec engine 사용 시)
git clone https://github.com/gimso2x/so2x-harness.git
cd so2x-harness && pip install -e .

# spec 생성
so2x-cli spec init "다크모드 토글 추가"

# 에이전트 파이프라인 실행
so2x-cli run specify "OAuth2 로그인 추가"
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

## 6 Agents

| Agent | Role | Phase |
|---|---|---|
| **Interviewer** | 질문으로 가정 노출, 결정 강제 | L0, L2 |
| **Code Explorer** | 코드 분석, 패턴 파악 | L1 |
| **Spec Writer** | 검증 가능한 요구사항 + 시나리오 작성 | L3 |
| **Planner** | 요구사항 → 태스크 분해, 순서 배치 | L4 |
| **Reviewer** | 품질/일관성/위험 검토 | L5 |
| **Verifier** | 시나리오별 독립 검증 | 실행 후 |

에이전트는 `so2x-cli run`으로 순차 파이프라인에서 자동 실행됩니다.

```bash
so2x-cli run specify "기능 설명"   # Interviewer → Explorer → Writer → Planner → Reviewer
so2x-cli run execute --file spec.json  # Task별 구현 → Verifier 검증
```

---

## CLI (so2x-cli)

```bash
# Spec 관리
so2x-cli spec init "목표"              # spec.json 생성
so2x-cli spec check spec.json --gate all # 게이트 검증
so2x-cli spec validate spec.json        # 전체 구조 검증
so2x-cli spec status spec.json          # 파생 상태 조회
so2x-cli spec guide l3_requirements     # 레이어 필드 안내

# 학습 관리
so2x-cli learn add --problem "..." --rule "..."   # 학습 기록
so2x-cli learn search "키워드"                      # 검색
so2x-cli learn summary                              # 요약

# 파이프라인 실행
so2x-cli run specify "목표"       # 지정 파이프라인
so2x-cli run execute --file spec.json  # 실행 파이프라인
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

```bash
# Bootstrap
curl -sSfL https://raw.githubusercontent.com/gimso2x/so2x-harness/main/install.sh | sh

# Local Clone + CLI
git clone https://github.com/gimso2x/so2x-harness.git
cd so2x-harness && pip install -e .

# 프로젝트에 설치
python3 scripts/apply.py --project /path/to/project --preset general

# 상태 점검
python3 scripts/doctor.py --project /path/to/project

# 업데이트
python3 scripts/update.py --project /path/to/project
```

설치 후 프로젝트 구조:

```
my-project/
├── CLAUDE.md
├── AGENTS.md
├── .claude/
│   ├── rules/so2x-harness/     # 5개 규칙
│   ├── skills/so2x-harness/    # 12개 스킬
│   ├── agents/so2x-harness/    # 6개 에이전트
│   └── hooks/                  # 5개 hook
├── .claude-plugin/
└── .ai-harness/
    ├── config.json
    ├── manifest.json
    ├── learnings.jsonl
    └── specs/
```

---

## 12 Skills

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
| **`specify`** | **6단계 파생 체인 + 게이트 검증** |
| **`execute`** | **spec 기반 구현 + 시나리오 검증** |

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

MIT
