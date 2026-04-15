# Architecture

so2x-harness의 시스템 구조를 설명합니다.

## 시스템 개요

so2x-harness는 여러 프로젝트에 공통 AI 작업 규칙을 설치/관리하는 가벼운 키트입니다. Shell + Python으로 구현되며, GitHub repo 하나로 중앙 관리합니다.

현재 설치 엔진이 공식 지원하는 대상 플랫폼은 Claude Code와 Codex CLI입니다. 두 플랫폼은 invocation만 다르고, review/simplify/safe-commit/squash-commit의 의미 계약은 같게 유지합니다.

```
┌─────────────────────────────────────────────┐
│                 so2x-harness repo            │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐ │
│  │templates │  │ scripts  │  │ schemas   │ │
│  │(원본)    │→ │(설치엔진)│→ │(검증)     │ │
│  └──────────┘  └──────────┘  └───────────┘ │
└──────────────────────┬──────────────────────┘
                       │ apply / update
                       ▼
┌─────────────────────────────────────────────┐
│              target project                 │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐ │
│  │ CLAUDE.md│  │ .claude/ │  │.ai-harness│ │
│  │(marker)  │  │rules/    │  │config.json│ │
│  │          │  │skills/   │  │manifest   │ │
│  │          │  │hooks/    │  │events.jsonl│ │
│  │          │  │.agents/  │  │status/     │ │
│  └──────────┘  └──────────┘  └───────────┘ │
└─────────────────────────────────────────────┘
```

## 모듈 구조

### scripts/apply.py — 설치 엔진

프로젝트에 harness를 설치합니다.

1. 대상 프로젝트 디렉터리 준비
2. 프리셋 로드 (`presets/<name>.json`)
3. CLAUDE.md에 마커 구간 삽입 (marker 정책)
4. rules, skills, hooks, plugin 파일 복사 (overwrite 정책)
5. AGENTS.md, config.json 복사 (skip_if_exists 정책)
6. manifest.json 기록

### scripts/update.py — 업데이트 엔진

설치된 harness를 최신 템플릿으로 갱신합니다.

1. 기존 manifest.json 읽기
2. 템플릿 체크섬과 비교
3. 정책에 따라 파일 업데이트
4. 새 manifest.json 기록

### scripts/doctor.py — 상태 진단

프로젝트의 harness 설치 상태를 점검합니다. 설치 여부만 찍는 도구로 끝내지 않고, spec.json이 canonical execution state 라는 전제에서 현재 작업 흐름도 top-level surface로 보여줍니다.

예를 들어 `spec.json`에 blocked task와 summary가 있으면 `doctor.py`는 아래처럼 바로 읽히는 문구를 출력합니다.

```
[WARN] execution_status: blocked on task T1
[WARN] execution_summary: latest summary: Waiting for approval from product owner
[OK] pending_tasks: 1 task(s) still pending
```

그리고 `.ai-harness/status/`와 학습 파일이 있으면 마무리 상태도 같이 보여줍니다.

```
[OK] simplify_status: remaining=0, stop_reason=converged_to_zero
[OK] safe_commit_status: verdict=SAFE, verification=PASS
[OK] squash_status: ready=True, reason=ready
[OK] promoted_rules: 3 promoted rule(s)
[OK] latest_promoted_rule: Honor repeated user feedback: 더 단순하게
[OK] feedback_events: 2 feedback event(s) captured
[OK] latest_feedback: 더 단순하게
[OK] safe_commit_events: 4 safe-commit event(s) recorded
[OK] squash_check_events: 3 squash-check event(s) recorded
```

즉 source of truth는 여전히 `spec.json`이고, `doctor.py`는 그걸 사람이 한 줄씩 빠르게 훑을 수 있게 요약해서 보여주는 표면입니다. auto preset 프로젝트에서는 저장된 추천 surface와 현재 재계산한 surface를 모두 출력하고, 빈 profile/signal/optional/policy 항목도 `none`으로 명시해서 "숨겨진 것"과 "정말 비어 있는 것"을 구분합니다.

### scripts/lib/ — 공유 라이브러리

| 모듈 | 책임 |
|---|---|
| `manifest.py` | manifest.json 읽기/쓰기/경로 |
| `markers.py` | HTML 마커 파싱/삽입/치환 |
| `checksum.py` | SHA256 체크섬 계산 |
| `render.py` | `{{ key }}` 템플릿 렌더링 |
| `platform_map.py` | 플랫폼별 파일 경로 매핑 |

## 데이터 흐름

### 설치 흐름

```
apply.py --project ./my-app --preset auto
  │
  ├── load_preset("auto")
  │     → templates/project/.ai-harness/presets/auto.json
  │
  ├── detect_project_profiles()
  │     → detected_profiles / detection_signals
  │     → enabled_skills / recommended_skills / optional_skills / enabled_optional_skills / skill_recommendations
  │
  ├── for each template file:
  │     ├── marker 파일: extract_marker_block → upsert_marker_block
  │     ├── overwrite 파일: 직접 복사
  │     └── skip_if_exists: 파일이 없으면 복사
  │
  ├── install_project_config()
  │     → config.json.tmpl → render_template → config.json
  │
  └── write_manifest()
        → manifest.json (파일별 mode, checksum 기록)
```

`project_profiles.py`는 단순 profile bundle이 아니라 외부 skill metadata catalog(`templates/project/.ai-harness/skill-catalog.json`)를 사용합니다. catalog 구조는 `schemas/skill-catalog.schema.json`으로 검증합니다. `doctor.py`는 저장된 `detected_profiles`/`recommended_skills`뿐 아니라 현재 working tree 기준으로 다시 계산한 `current_detected_profiles`, `current_detection_signals`, `current_enabled_skills`, `current_enabled_optional_skills`, `current_recommended_skills`, `current_optional_skills`, `current_policy_promoted_skills`, `current_skill_recommendation.*`를 함께 보여줘서 install 시점과 현재 상태의 차이뿐 아니라 live 추천 근거까지 바로 확인하게 합니다. 또한 설치된 skill 디렉터리와 config의 `enabled_skills`를 이름 기준으로 비교해 `skills_drift`, `missing_enabled_skills`, `unexpected_installed_skills`를 따로 surface해서 단순 개수 mismatch보다 바로 복구 가능한 상태 정보를 제공합니다. `pnpm-workspace.yaml`이 있는 저장소는 `apps/` + `packages/` 디렉터리가 없어도 coarse `monorepo`와 fine-grained `pnpm-monorepo`를 함께 유지해서 catalog 정책과 doctor surface가 일관되게 동작합니다. npm workspaces도 `packageManager:npm` + `workspace:npm` signal을 통해 `npm-monorepo`로 승격되어 yarn/pnpm과 동일한 doctor visibility를 가집니다. bun workspaces도 `packageManager:bun` + `workspace:bun` signal을 통해 `bun-monorepo`로 승격되어 같은 path를 공유합니다. Node backend repos도 `express`/`fastify`/`koa`/`hono`/`nestjs` dependency를 읽어 `package.json:backend-framework` signal과 함께 `backend` + `js-package`로 승격되므로 auto preset과 doctor가 JS service repos를 frontend package로 오분류하지 않습니다. `go.work`가 있는 저장소도 `go.work:workspace` signal을 통해 shared `monorepo` policy path로 승격되어 Go workspace 루트에서 review/spec validation rationale을 잃지 않습니다. Cargo workspace root도 `[workspace]` 선언을 읽어 `Cargo.toml:workspace` signal과 함께 같은 `monorepo` policy path로 승격되어 Rust workspace 루트에서도 doctor/recommendation visibility를 유지합니다. `review-cycle` catalog rule은 `package.json:workspaces`, `workspace:pnpm|yarn|npm|bun`, `pyproject.toml:uv-workspace`, `go.work:workspace`, `Cargo.toml:workspace`를 직접 signal로 받아 workspace-only monorepo에서도 framework dependency 없이 rationale/doctor surface를 유지합니다. 이제 `specify-lite`도 같은 workspace-root signal 집합을 공유해 workspace-only monorepo에서 구현 전에 lightweight spec capture를 잃지 않습니다. 또한 config-only orchestrator signal인 `workspace:turborepo`, `workspace:nx`, `workspace:lerna`도 catalog `signals_any`에 포함되어 workspace root recommendation rationale과 doctor output에 실제 orchestrator 근거를 남깁니다.

- tier: `core` / `recommended` / `optional`
- applies_to: 어떤 project profile에 붙는지
  - coarse: `frontend`, `backend`, `monorepo`, `python-package`, `js-package`
  - fine-grained: `next-app`, `react-lib`, `fastapi-service`, `django-service`, `pnpm-monorepo`
  - workspace-aware Python: `pyproject.toml:uv-workspace` signal promotes the repo into the shared `monorepo` policy path
- platforms: Claude/Codex parity 확인용
- signals_any: 어떤 파일 시그널에서 활성화되는지
  - 예: Next app router는 `app/` 뿐 아니라 `src/app/`도 `next:app-router`로 감지
- rationale: config와 doctor에 남길 추천 이유
- workflow_tags: 반복 simplify 흐름 같은 우선 워크플로 태그

사용자가 optional skill을 직접 승격하면 `enabled_optional_skills`에 저장되고,
다음 `update.py` 실행에서도 설치 집합에 다시 합쳐집니다.

현재는 `simplify-cycle`, `squash-commit`, `safe-commit`이 공통 core이며,
`simplify-cycle`에는 아래 3개 lens를 first-class tag로 둡니다.

- Code Reuse Review
- Code Quality Review
- Efficiency Review

### 업데이트 흐름

```
update.py --project ./my-app
  │
  ├── load_manifest()
  │     → 기존 설치 정보 로드
  │
  ├── for each file in manifest:
  │     ├── overwrite: 새 템플릿으로 교체
  │     ├── marker: 마커 구간만 교체
  │     └── skip_if_exists: 변경 없음
  │
  └── write_manifest()
        → 업데이트된 manifest.json
```

## 파일 업데이트 정책

### overwrite

템플릿 원본이 항상 우선입니다.

- 대상: rules, skills, hooks, plugin, shared docs/snippets
- 동작: 기존 파일을 무시하고 템플릿으로 교체

### marker

파일의 특정 구간만 공통 관리합니다.

- 대상: CLAUDE.md
- 동작: `<!-- SO2X-HARNESS:BEGIN -->` ~ `<!-- SO2X-HARNESS:END -->` 구간만 교체
- 나머지 내용은 프로젝트 로컬 소유

### skip_if_exists

이미 파일이 있으면 건드리지 않습니다.

- 대상: AGENTS.md, config.json, settings.json
- 동작: 파일이 없으면 템플릿에서 복사, 있으면 유지

## 템플릿 시스템

### templates/shared/

모든 플랫폼에 공통으로 적용되는 파일입니다.

- `AGENTS.md` — 에이전트 가이드
- `docs/` — harness-philosophy, workflow, review-checklist
- `snippets/` — validate-prompt 등 공통 스니펫

### templates/claude/

Claude Code 전용 파일입니다.

- `CLAUDE.md` — 프로젝트 노트 (마커 관리)
- `rules/` — 5개 기본 규칙
- `skills/` — 13개 일반 스킬 + review-cycle 파이프라인 + 마무리용 simplify/squash 스킬
- `run specify` — 관련 learning + promoted rule 자동 주입
- `run execute` — task summary / review finding + simplify/safe/squash 상태 기반 auto-learning 축적
- `hooks/` — 검증 훅 스크립트
- `plugin/` — 플러그인 메타데이터

### templates/project/

프로젝트 설정 템플릿입니다.

- `config.json.tmpl` — 프로젝트 설정 템플릿
- `manifest.json.tmpl` — 매니페스트 템플릿

## Learning / event persistence

`run execute`는 구현 단계의 task summary와 review finding만 저장하지 않고, 마무리 단계에서 다시 주입 가능한 운영 상태도 같이 남깁니다.

- `.ai-harness/events.jsonl` — raw event 로그
- `.ai-harness/learnings.jsonl` — dedupe된 actionable learning
- `.ai-harness/promoted-rules.json` — 반복 출현 규칙 승격본
- `.ai-harness/status/simplify-cycle.json` — simplify convergence 상태

특히 `user_feedback_captured` 이벤트가 같은 메시지로 반복되면 feedback-frequency 승격 규칙이 생성되어 이후 `run specify`에 바로 다시 주입됩니다.

이 구조는 stable-loop의 feedback/audit 흐름과 autopus-adk의 telemetry/auto-learning wiring 아이디어를 섞은 것입니다.

## 테스트 전략

```
tests/
├── unit/           # lib 모듈 단위 테스트 (격리된 함수 테스트)
├── integration/    # 스크립트 통합 테스트 (서브프로세스 실행)
└── conftest.py     # 공통 fixtures (tmp_project, sample_manifest)
```

- 단위 테스트: lib 모듈의 순수 함수를 직접 호출
- 통합 테스트: apply/update/doctor를 subprocess로 실행하여 E2E 검증
- tmp_path fixture로 격리된 임시 디렉터리에서 실행
