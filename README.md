# so2x-harness

[![Version](https://img.shields.io/badge/Version-0.7.0-green)](./VERSION)

so2x-harness는 personal per-project harness입니다.

이 저장소는 heavyweight install/distribution kit가 아니라,
프로젝트마다 같이 두고 쓰는 lightweight orchestration scaffold만 남깁니다.

핵심 메시지
- so2x-harness는 personal per-project harness
- lightweight orchestration scaffold
- core files = `CLAUDE.md` / `spec.json` / `harness.json`
- orchestration은 harness가 담당
- model routing은 CCS가 담당
- intentionally small
- install/distribution kit가 기본 목표가 아님

## Thin core principles

- `scripts/cli/commands/spec.py`는 상태만 안다
- `scripts/runtime.py`는 실행만 안다
- `scripts/cli/commands/run.py`는 흐름만 안다
- `scripts/doctor.py`는 읽기만 한다

상태 원천은 `spec.json` 하나입니다.
runner 설정은 `harness.json` 하나입니다.
프로젝트 규칙은 `CLAUDE.md` 하나입니다.

## Core files

### `spec.json`
작업 상태와 task 목록을 담는 단일 상태 원천입니다.

### `harness.json`
role별 runner command, timeout, retry 정책을 담습니다.

예시:
```json
{
  "version": 1,
  "rule_file": "CLAUDE.md",
  "spec_file": "spec.json",
  "runners": {
    "planning": ["ccs", "run", "gpt54-plan"],
    "review": ["ccs", "run", "gpt54-review"],
    "dev": ["ccs", "run", "glm-dev"]
  },
  "timeout_sec": {
    "default": 1800,
    "planning": 900,
    "review": 900,
    "dev": 1800
  },
  "max_retries": {
    "planning": 1,
    "review": 1,
    "dev": 3
  },
  "prompt": {
    "include_rule_file": true,
    "include_completed_summaries": true,
    "include_last_error": true
  }
}
```

### `CLAUDE.md`
프로젝트 규칙과 verification/summarization 규칙을 담습니다.

## CLI

thin surface만 지원합니다.

```bash
so2x init --goal "OAuth 로그인 추가"
so2x status --file spec.json
so2x next --file spec.json
so2x set-status --file spec.json --task-id T1 --status done --summary "흐름 정리 완료"
so2x validate --file spec.json
so2x run --file spec.json --task T1
so2x run --file spec.json --next
so2x doctor --project .
```

## Migration note

- 공식 entrypoint는 `so2x` 하나만 둡니다.
- legacy install/apply/update/manifest/preset/learning surface는 유지하지 않습니다.
- 기존 프로젝트는 `CLAUDE.md`, `spec.json`, `harness.json` 3개 core file 기준으로 옮기면 됩니다.

## Minimal bootstrap

새 프로젝트에 아래 파일들을 복사하면 시작할 수 있습니다.
- `templates/minimal/spec.json`
- `templates/minimal/harness.json`
- `templates/minimal/CLAUDE.md`
- `templates/minimal/docs/meta-harness/harness-spec.md`
- `templates/minimal/docs/meta-harness/interview-schema.md`
- `templates/minimal/docs/meta-harness/stage-contracts.md`
- `templates/minimal/docs/meta-harness/_state.json`

## Quickstart

가장 빠른 시작 예시입니다.

```bash
cp templates/minimal/spec.json ./spec.json
cp templates/minimal/harness.json ./harness.json
cp templates/minimal/CLAUDE.md ./CLAUDE.md
mkdir -p docs/meta-harness outputs/<run-id>
cp templates/minimal/docs/meta-harness/harness-spec.md ./docs/meta-harness/harness-spec.md
cp templates/minimal/docs/meta-harness/interview-schema.md ./docs/meta-harness/interview-schema.md
cp templates/minimal/docs/meta-harness/stage-contracts.md ./docs/meta-harness/stage-contracts.md
cp templates/minimal/docs/meta-harness/_state.json ./outputs/<run-id>/_state.json
```

그 다음 최소 확인 순서:

```bash
so2x init-state --project .
so2x doctor --project .
so2x validate --file spec.json
so2x status --file spec.json
so2x run --file spec.json --next
```

권장 초기 수정 포인트:
- `spec.json`: goal / tasks / depends_on
- `harness.json`: role별 runner command / timeout / retry
- `CLAUDE.md`: 프로젝트 규칙 / verification / summary format
- `outputs/<run-id>/_state.json`: 현재 run의 stage / artifact path / resume 상태

추가 helper:
- `so2x init-state --project .`: `outputs/<run-id>/_state.json` 생성 helper
- `so2x init-state --project . --run-id run-42 --harness-name oauth-login`: run-id / harness-name 명시 초기화
- `so2x init-state --project . --run-id run-42 --activate`: 생성 후 `harness.json.active_run_id`까지 갱신
- `so2x doctor --project . --run-id run-42`: 특정 run 상태만 확인
- `so2x run --file spec.json --next --run-id run-42`: 특정 run의 resume state만 읽고 갱신
- `--run-id`를 생략하면 `harness.json.active_run_id`를 먼저 보고, 없으면 최신 `_state.json`을 사용
- 이미 같은 경로에 `_state.json`이 있으면 덮어쓰지 않음. 필요하면 `--force`

## Meta-harness adoption guide

meta-harness는 실행기 구현이 아니라 설계 규약 레이어입니다.
so2x-harness에는 아래처럼 얹습니다.

1. `harness-spec.md`에서 fixed criteria / per-run variables / intervention points를 먼저 고정
2. `interview-schema.md`에서 deep-interview 질문만 분리
3. `stage-contracts.md`에서 stage를 대화가 아니라 artifact chain으로 정의
4. `outputs/<run-id>/_state.json`으로 중단/재개 상태를 파일로 관리
5. `doctor`와 `run`은 최신 `_state.json`을 읽어 현재 stage와 resume context를 반영

실무 해석:
- 그대로 가져올 것은 코드보다 규약
- 특히 가져갈 것은 암묵지 분류 체계 / stage artifact contract / resume state schema / deep-interview 선행 구조
- 그대로 이식하면 안 되는 것은 Claude Code 전용 경로, 명명 규칙, subagent 전제

현재 thin core 기준에서의 역할 분리:
- `CLAUDE.md`: fixed criteria와 verification policy
- `spec.json`: task surface와 dependency
- `harness.json`: runner routing / timeout / retry
- `docs/meta-harness/*.md`: 설계 계약
- `outputs/<run-id>/_state.json`: resume truth source

## Scope

의도적으로 넣지 않습니다.
- install/apply/update/manifest/preset engine
- heavy templates/distribution kit
- learn subsystem
- multi-platform rollout narrative
- full 6-layer spec engine

KISS / YAGNI 우선으로 personal per-project thin harness bootstrap만 제공합니다.
