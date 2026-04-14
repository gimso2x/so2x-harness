# Architecture

so2x-harness의 시스템 구조를 설명합니다.

## 시스템 개요

so2x-harness는 여러 프로젝트에 공통 AI 작업 규칙을 설치/관리하는 가벼운 키트입니다. Shell + Python으로 구현되며, GitHub repo 하나로 중앙 관리합니다.

현재 공식 설치 엔진 범위는 Claude Code입니다. 구조를 보면 나중에 다른 플랫폼으로 확장할 자리는 있지만, 지금 코드와 테스트가 실제로 보장하는 설치 경로는 `claude` 하나입니다.

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
│  │          │  │hooks/    │  │           │ │
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

프로젝트의 harness 설치 상태를 점검합니다.

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
apply.py --project ./my-app --preset general
  │
  ├── load_preset("general")
  │     → templates/project/.ai-harness/presets/general.json
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
- `skills/` — 10개 스킬
- `hooks/` — 검증 훅 스크립트
- `plugin/` — 플러그인 메타데이터

### templates/project/

프로젝트 설정 템플릿입니다.

- `config.json.tmpl` — 프로젝트 설정 템플릿
- `manifest.json.tmpl` — 매니페스트 템플릿

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
