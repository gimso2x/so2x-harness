# so2x-harness

**Claude Code 중심으로 여러 프로젝트에 공통 AI harness를 설치해서 쓰는 가벼운 GitHub-managed kit.**

[![CI](https://github.com/gimso2x/so2x-harness/actions/workflows/ci.yml/badge.svg)](https://github.com/gimso2x/so2x-harness/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform: Claude + Codex](https://img.shields.io/badge/Platform-Claude%20%2B%20Codex-blueviolet)](#install)
[![Version](https://img.shields.io/badge/Version-0.6.2-green)](https://github.com/gimso2x/so2x-harness/blob/main/VERSION)

[Quick Start](#quick-start) · [Usage](#usage) · [Spec Engine](#spec-engine) · [Agents](#agents) · [Skills](#skills) · [CLI](#cli) · [Install](#install) · [Docs](#docs)

---

> _하나의 repo에서 공통 규칙을 관리하고, 여러 프로젝트에 안전하게 설치하고, 필요할 때 갱신한다._

## Quick Start

현재 설치 엔진이 공식 지원하는 대상 플랫폼은 Claude Code와 Codex CLI입니다. `--platform claude`, `--platform codex`, 또는 `--platform claude codex`로 다중 플랫폼 동시 설치가 가능합니다.

```bash
# macOS / Linux — 대화형 설치
curl -sSfL https://raw.githubusercontent.com/gimso2x/so2x-harness/main/install.sh | sh

# macOS / Linux — bootstrap + CLI 설치까지 같이 하려면
curl -sSfL https://raw.githubusercontent.com/gimso2x/so2x-harness/main/install.sh | WITH_CLI=1 sh
```

```bash
# macOS / Linux — 둘 다 확실히 설치하려면
REPO_DIR="$(mktemp -d)"
git clone https://github.com/gimso2x/so2x-harness.git "$REPO_DIR"
python3 "$REPO_DIR/scripts/apply.py" --project . --platform claude codex --preset auto
```

```powershell
# Windows (PowerShell) — 대화형 설치
powershell -c "irm https://raw.githubusercontent.com/gimso2x/so2x-harness/main/install.ps1 | iex"

# Windows (PowerShell) — bootstrap + CLI 설치까지 같이 하려면
powershell -c "& ([scriptblock]::Create((irm https://raw.githubusercontent.com/gimso2x/so2x-harness/main/install.ps1))) -WithCli"
```

```powershell
# Windows (PowerShell) — 둘 다 확실히 설치하려면
$repo = Join-Path $env:TEMP "so2x-harness"
if (Test-Path $repo) { Remove-Item -Recurse -Force $repo }
git clone https://github.com/gimso2x/so2x-harness.git $repo
python "$repo\scripts\apply.py" --project . --platform claude codex --preset auto
```

---

### 설치 후 바로 확인하기

harness bootstrap 설치는 프로젝트에 규칙/skills/hooks를 배포하는 용도입니다. 이 단계만으로 `so2x-cli`가 전역 설치되지는 않습니다.

즉, 아래처럼 보이면 bootstrap은 실패가 아니라 정상일 수 있습니다.

```bash
so2x-cli not found
```

먼저 프로젝트에 플랫폼 자산이 들어왔는지 확인하세요.

```bash
cat .ai-harness/manifest.json
test -d .claude && echo ".claude ok"
test -d .agents && echo ".agents ok"
```

```powershell
Get-Content .ai-harness\manifest.json
Test-Path .claude
Test-Path .agents
```

- Claude를 같이 설치했다면 manifest `platforms`에 `claude`가 보여야 합니다.
- Codex를 같이 설치했다면 manifest `platforms`에 `codex`가 보여야 합니다.
- 둘 다 설치했다면 `.claude`와 `.agents`가 둘 다 있어야 합니다.

`so2x-cli`가 필요한 경우는 spec engine/CLI 명령을 직접 쓰고 싶을 때입니다. 설치 스크립트에 CLI까지 맡기고 싶으면 Linux/macOS에서는 `WITH_CLI=1 sh`, Windows에서는 `-WithCli`를 사용할 수 있습니다.

```bash
git clone https://github.com/gimso2x/so2x-harness.git
cd so2x-harness && pip install -e .
so2x-cli --version
```

`--preset auto`는 프로젝트 파일 시그널(`package.json`, `pyproject.toml`, `apps/`, `packages/` 등)을 보고 `detected_profiles`, `detection_signals`, `enabled_skills`, `recommended_skills`, `optional_skills`, `skill_recommendations`를 계산해서 더 맞는 skill 조합을 적용합니다. 강제로 고정 skill 셋을 쓰고 싶으면 `--preset general`을 사용하면 됩니다. `doctor.py`는 저장된 config surface와 함께 현재 파일 상태에서 다시 계산한 `current_detected_profiles`, `current_detection_signals`, `current_enabled_skills`, `current_recommended_skills`, `current_optional_skills`, `current_policy_promoted_skills`, `current_skill_recommendation.*`도 같이 보여줘서 auto preset drift와 현재 추천 근거를 한눈에 확인할 수 있습니다.

auto 추천 기준은 메타데이터 기반입니다.

catalog 원본은 `templates/project/.ai-harness/skill-catalog.json`에 있고, 스키마는 `schemas/skill-catalog.schema.json`입니다.

- `enabled_skills`: 실제로 설치되는 core/recommended 스킬
- `recommended_skills`: 현재 프로젝트에 맞다고 판단된 전체 추천 스킬
- `optional_skills`: 당장 설치하지는 않지만 후보로 남기는 스킬
- `enabled_optional_skills`: optional 중 사용자가 설치 승격한 스킬
- `skill_recommendations`: 왜 추천됐는지 남기는 이유 목록

기본 원칙은 다음과 같습니다.

- `simplify-cycle`, `squash-commit`, `safe-commit`은 공통 core로 유지
- `simplify-cycle`은 항상 3개 review lens를 우선 반영
  - Code Reuse Review
  - Code Quality Review
  - Efficiency Review
- frontend/backend/monorepo/package profile은 파일 시그널로 감지
- 세부 profile도 같이 잡습니다
  - next-app
  - react-lib
  - fastapi-service
  - django-service
  - pnpm-monorepo
  - uv workspace monorepo (`[tool.uv.workspace]`)
- signal도 더 세분화해서 잡습니다
  - turborepo / nx / lerna workspace
  - poetry / uv / hatch python toolchain
  - django manage.py
  - next app router
  - vite lib mode
- profile policy도 같이 적용합니다
  - next-app / react-lib: `specify`를 기본 추천에서 승격
  - monorepo / pnpm-monorepo: `execute`, `spec-validate`를 기본 추천에서 승격
- Claude/Codex는 같은 추천 로직을 공유하고, 플랫폼 미지원 스킬만 제외

optional 후보를 실제 설치로 올리고 싶으면 다음처럼 사용할 수 있습니다.

```bash
so2x-cli skills recommend --project ./my-app
so2x-cli skills enable execute specify --project ./my-app
```

---

## Usage

harness를 설치하면 Claude Code에서 slash 명령으로 바로 사용할 수 있습니다.

### 언제 `/specify`를 쓰고, 언제 바로 작업하나

핵심 기준은 단순합니다.

- 구현 전에 요구사항, 정책, 시나리오를 먼저 굳혀야 하면 `/specify`
- 이미 범위가 작고 해야 할 일이 분명하면 바로 작업
- 둘 사이가 애매하면 `/specify-lite`로 짧게 정리한 뒤 진행

| 작업 종류 | 추천 흐름 | 예시 |
|---|---|---|
| 새 기능, 큰 기능 변경 | `/specify` → `/execute` | 로그인 방식 추가, 결제 흐름 변경, 관리자 화면 신설 |
| 정책/상태/예외가 많은 작업 | `/specify` → `/execute` | 권한 정책 변경, 멀티스텝 폼, 복잡한 API 연동 |
| 애매하지만 큰 spec까지는 아닌 작업 | `/specify-lite` → 필요 시 바로 구현 | 작은 UX 개선, 경계 조건 정리, 구현 전 빠른 결정 필요 작업 |
| 단순 버그 수정 | 바로 작업 또는 `/debugging` | null 처리, 잘못된 분기 수정, 에러 재현 후 원인 분석 |
| 문구 수정, 작은 refactor, 명백한 수정 | 바로 작업 | copy 수정, import 정리, 작은 조건문 수정 |
| 변경 검토/마무리 | `/review`, `/review-cycle`, `/simplify-cycle`, `/safe-commit`, `/squash-commit` | 구현 후 리뷰, 3개 lens 기반 반복 단순화, 커밋 전 검증, 최종 squash 정리 |

### 추천 판단법

- 아래 중 하나라도 맞으면 `/specify` 쪽이 안전합니다.
  - 화면/흐름이 2개 이상 함께 바뀜
  - 구현 전에 결정해야 할 정책이 있음
  - acceptance criteria를 먼저 써야 안 헷갈림
  - 구현 뒤 verifier가 볼 시나리오를 먼저 정리하는 게 좋음
- 아래에 가까우면 바로 작업해도 됩니다.
  - 수정 범위가 파일 1~2개 수준임
  - 기대 결과가 이미 분명함
  - 정책 결정 없이 바로 고칠 수 있음

### 예시 흐름

#### 1) 새 기능 추가

```
/specify "OAuth2 Google/GitHub 로그인 추가"
/execute
```

#### 2) 일반 버그 수정

```
/debugging
# 원인 파악 후 바로 수정
```

또는 정말 단순한 수정이면 바로 작업하고 마지막에 검증합니다.

```
/review
/simplify-cycle
/safe-commit
/squash-commit
```

#### 3) 애매한 작업

```
/specify-lite
```

짧게 결정과 구현 순서를 정리한 뒤, 그대로 바로 구현하거나 필요하면 `/specify`로 올립니다.

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
/simplify-cycle        # Code Reuse / Quality / Efficiency lens로 반복 단순화 pass를 0까지 수렴
/safe-commit           # 커밋 전 검증
/squash-commit         # simplify/safe-commit 이후 단일 squash 커밋 정리
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
| 반복 단순화 | `/simplify-cycle` |
| 검증 후 squash 커밋 | `/squash-commit` |
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

# feedback도 쌓고 반복되면 promoted-rules로 승격됨
python3 scripts/cli/main.py learn feedback "이건 별로고 다음엔 더 단순하게 해" --phase simplify --dir .ai-harness

# doctor는 사람이 읽기 쉬운 top-level surface를 보여줌
python3 scripts/doctor.py --project .
# [WARN] execution_status: blocked on task T1
# [WARN] execution_summary: latest summary: Waiting for approval from product owner
# [OK] pending_tasks: 1 task(s) still pending
# [WARN] simplify_status: missing simplify-cycle.json
# [WARN] safe_commit_status: missing safe-commit.json
# [WARN] squash_status: missing squash-commit.json
# [WARN] feedback_events: no feedback events captured yet
# [WARN] safe_commit_events: no safe-commit events recorded yet
# [WARN] squash_check_events: no squash-check events recorded yet
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
| `simplify-cycle` | 반복 simplify pass를 남은 count 0까지 수렴 |
| `squash-commit` | 검증 완료 후 단일 squash 커밋으로 정리 |
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
`run execute`는 task summary와 review finding을 읽어 `.ai-harness/learnings.jsonl`에 자동 학습 항목을 추가합니다.

```bash
# 학습 기록
so2x-cli learn add \
  --problem "OAuth callback이 배포마다 다름" \
  --cause "환경 변수 없이 하드코딩" \
  --rule "callback URL은 항상 환경 변수로 설정" \
  --category anti-pattern \
  --tags "oauth,config"

# 자동 주입 확인
so2x-cli run specify "OAuth 로그인 추가"
# Relevant learnings:
# - [anti-pattern] OAuth callback이 배포마다 다름
#   Rule: callback URL은 항상 환경 변수로 설정

# 검색
so2x-cli learn search "oauth"
# [LRN-E27F72] [anti-pattern] OAuth callback이 배포마다 다름
#   Rule: callback URL은 항상 환경 변수로 설정
```

저장 위치: `my-project/.ai-harness/learnings.jsonl`

---

## Install

현재 설치 엔진은 Claude Code 및 Codex CLI용 하네스 배포를 기준으로 동작합니다. `scripts/apply.py`의 공식 지원 플랫폼은 `claude`와 `codex`이며, 다중 플랫폼 동시 설치도 지원합니다.

```bash
# Bootstrap (macOS / Linux)
curl -sSfL https://raw.githubusercontent.com/gimso2x/so2x-harness/main/install.sh | sh

# CLI 설치 (spec engine 사용 시)
git clone https://github.com/gimso2x/so2x-harness.git
cd so2x-harness && pip install -e .

# 수동 설치
python3 scripts/apply.py --project /path/to/project --platform claude --preset general
```

설치 후 프로젝트 구조 (claude + codex):

```
my-project/
├── CLAUDE.md                    # Claude Code용 (claude 플랫폼 시)
├── AGENTS.md
├── .claude/
│   ├── rules/so2x-harness/     # 5개 규칙
│   ├── skills/                  # 15개 스킬 폴더 (각각 SKILL.md)
│   ├── agents/so2x-harness/    # 6개 에이전트
│   └── hooks/                  # 5개 hook
├── codex/
│   └── skills/                  # 15개 스킬 폴더 (각각 SKILL.md)
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

### v0.4
Spec engine, 6 agents, CLI, knowledge system, orchestration pipeline

### v0.5 (현재)
- Codex CLI 지원 (멀티플랫폼)
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
