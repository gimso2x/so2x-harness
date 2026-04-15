## Codex / Claude parity 변경 묶음 초안

이 문서는 초기 Codex 플랫폼 지원 이후에 진행한 parity 후속 작업(#39 ~ #42)을 한 번에 정리한 release note 초안입니다.

### 범위
- #39 Codex parity: make config.json platforms reflect installed platforms
- #40 Codex parity: generate installed skill lists from enabled_skills
- #41 Codex parity: make Codex skills platform-neutral and remove Claude-specific invocation assumptions
- #42 Codex parity: add drift checks between config, manifest, and generated platform assets

### 왜 이 작업 묶음이 필요했나
하니스는 이미 Codex 자산을 설치할 수 있었지만, 주변 출력물과 문서, 검증 흐름은 여전히 Claude를 기본 전제로 보는 부분이 남아 있었습니다.

주요 문제는 다음과 같았습니다.
- 생성된 config와 schema가 실제 설치 플랫폼 상태와 어긋남
- preset, 생성된 skill 디렉터리, CLAUDE.md의 Installed Skills 목록이 서로 드리프트함
- Codex skill 템플릿에 Claude식 slash command와 agent-chain 전제가 남아 있었음
- config / manifest / generated asset 사이의 드리프트를 doctor가 충분히 드러내지 못했음

### 무엇이 바뀌었나

#### 1. config / schema 정렬
- `.ai-harness/config.json`의 `platforms`를 실제 설치 플랫폼 기준으로 생성하도록 변경
- incremental apply/update 이후에도 config의 platform 정보가 manifest와 맞도록 동기화
- schema와 example 파일이 `claude`, `codex` 둘 다를 허용/표현하도록 수정
- generated config + manifest 출력이 schema를 통과하는지 계약 테스트 추가

#### 2. enabled_skills를 실질적인 생성 기준으로 정렬
- `CLAUDE.md`의 Installed Skills 목록을 preset의 `enabled_skills`에서 렌더하도록 변경
- `.claude/skills/*`, `.agents/skills/*` 생성 대상을 `enabled_skills` 기준으로 제한
- update/apply 시 config의 `enabled_skills`도 preset 기준으로 다시 맞춤
- enabled set 밖에 남아 있던 stale skill 디렉터리는 apply/update 시 정리

#### 3. Codex skill 템플릿 중립화
- Codex `specify`, `execute` 템플릿에서 Claude식 slash invocation 전제 제거
- Interviewer / Planner / Reviewer 같은 Claude 전용 agent-chain 표현 제거
- Codex 쪽은 `$specify`, `$execute` 같은 explicit invocation 예시 중심으로 정리
- Codex skill 템플릿에 Claude-first 문구가 다시 들어오지 않도록 회귀 테스트 추가

#### 4. doctor drift 진단 강화
- `doctor.py`가 config platforms와 manifest platforms가 다를 때 경고하도록 추가
- `doctor.py`가 installed skill count와 `enabled_skills`가 다를 때 경고하도록 추가
- config/manifest drift, 선언된 자산 누락, skill drift를 다루는 integration test 추가

### 사용자 입장에서 달라진 점
- multi-platform 설치 결과가 config, manifest, generated skills, 문서 사이에서 더 일관되게 맞습니다.
- Codex 사용자는 Claude-first slash workflow 대신 더 자연스러운 Codex 친화 문서를 보게 됩니다.
- 드리프트가 조용히 묻히지 않고 doctor에서 더 빨리 드러납니다.

### 검증
- `make check`
- `make coverage`
- codex-only / multi-platform schema contract 테스트
- Claude / Codex skill generation parity 테스트
- doctor drift integration 테스트

### 반영된 PR
- #43 fix: sync config platforms with installed platforms
- #44 fix: derive installed skills from enabled_skills
- #45 fix: remove claude-first assumptions from codex skills
- #46 feat: add doctor drift diagnostics

### release note 한 줄 요약안
Codex/Claude parity 후속 작업으로 config, schema, skill generation, Codex skill wording, doctor drift diagnostics를 정리해 multi-platform 설치 일관성과 드리프트 가시성을 높였습니다.
