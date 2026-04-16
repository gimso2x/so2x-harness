# so2x-harness

[![Version](https://img.shields.io/badge/Version-0.6.2-green)](./VERSION)

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

- 기존 `so2x-cli` 중심 흐름은 제거되었습니다.
- 이제 공식 엔트리포인트는 `so2x`입니다.
- legacy install/apply/update/manifest/preset/learning surface는 유지하지 않습니다.
- 기존 프로젝트는 `CLAUDE.md`, `spec.json`, `harness.json` 3개 core file 기준으로 옮기면 됩니다.

## Minimal bootstrap

새 프로젝트에 아래 3개 파일을 복사하면 시작할 수 있습니다.
- `templates/minimal/spec.json`
- `templates/minimal/harness.json`
- `templates/minimal/CLAUDE.md`

## Scope

의도적으로 넣지 않습니다.
- install/apply/update/manifest/preset engine
- heavy templates/distribution kit
- learn subsystem
- multi-platform rollout narrative
- full 6-layer spec engine

KISS / YAGNI 우선으로 personal per-project thin harness bootstrap만 제공합니다.
