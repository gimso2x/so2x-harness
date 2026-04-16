# so2x-harness

**Claude Code 중심**으로 시작했지만, 지금의 so2x-harness는 personal per-project harness입니다.

[![Version](https://img.shields.io/badge/Version-0.6.2-green)](./VERSION)

so2x-harness는 heavyweight install/distribution kit가 아니라, 프로젝트마다 같이 두고 쓰는 lightweight orchestration scaffold를 목표로 합니다.

핵심 메시지:
- so2x-harness는 personal per-project harness
- lightweight orchestration scaffold
- core files = `CLAUDE.md` / `spec.json` / `harness.json`
- orchestration은 harness가 담당
- model routing은 CCS가 담당
- intentionally small
- install/distribution kit가 기본 목표가 아님

## Thin core

thin core는 역할을 분리합니다.
- `spec.py`는 상태만 안다
- `runtime.py`는 실행만 안다
- `run.py`는 흐름만 안다
- `doctor.py`는 읽기만 한다

## Core files

### spec.json
상태 원천은 `spec.json` 하나입니다.

### harness.json
runner 설정은 `harness.json` 하나입니다.

예시:
```json
{
  "runners": {
    "planning": ["ccs", "run", "gpt54-plan"],
    "review": ["ccs", "run", "gpt54-review"],
    "dev": ["ccs", "run", "glm-dev"]
  }
}
```

### CLAUDE.md
프로젝트 규칙은 `CLAUDE.md` 하나입니다.

## CLI

지원 thin 명령:
```bash
so2x-cli init --goal "OAuth 로그인 추가"
so2x-cli status --file spec.json
so2x-cli next --file spec.json
so2x-cli set-status --file spec.json --task-id T1 --status done --summary "흐름 정리 완료"
so2x-cli validate --file spec.json
so2x-cli run --file spec.json --task T1
so2x-cli run --file spec.json --next
so2x-cli doctor --project .
```

호환 명령도 유지합니다.
```bash
so2x-cli spec set-task-status spec.json --task-id T1 --status blocked --summary "Waiting for approval from product owner"
so2x-cli run safe-commit --dir .ai-harness
so2x-cli run squash-check --dir .ai-harness
so2x-cli skills recommend --project .
```

## Doctor surface

doctor는 읽기 전용입니다.

예시:
```text
[WARN] execution_status: blocked on task T1
[WARN] execution_summary: latest summary: Waiting for approval from product owner
[OK] current_detected_profiles: frontend, next-app
[OK] current_enabled_skills: planning, implementation, review
[OK] current_enabled_optional_skills: execute
[OK] current_recommended_skills: simplify-cycle, squash-commit
```

## Existing workflow compatibility

thin core가 기본이지만, 기존 workflow surface도 유지합니다.
- `/review-cycle`
- `.review-artifacts/`
- auto profile signals:
  - `workspace:bun`
  - `package.json:workspaces`
  - `go.work:workspace`
  - `workspace:turborepo`

## Minimal bootstrap

새 프로젝트에 아래 3개 파일을 복사하면 시작할 수 있습니다.
- `templates/minimal/spec.json`
- `templates/minimal/harness.json`
- `templates/minimal/CLAUDE.md`

## Scope out

이번 thin core는 의도적으로 제외합니다.
- install/apply/update 중심 엔진 설명
- team rollout narrative
- heavy spec engine narrative
- learn subsystem을 중심으로 한 세계관
- full 6-layer spec engine 강제

KISS / YAGNI 우선으로 personal per-project thin harness bootstrap만 제공합니다.
