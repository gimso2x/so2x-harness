# CLI Reference

so2x-harness의 모든 명령을 설명합니다.

## apply.py

프로젝트에 harness를 설치합니다.

```bash
python3 scripts/apply.py --project <경로> [--platform claude] [--preset general]
```

### 옵션

| 옵션 | 필수 | 기본값 | 설명 |
|---|---|---|---|
| `--project` | O | - | 대상 프로젝트 경로 |
| `--platform` | X | `claude` | 설치 플랫폼 (현재 `claude`만 지원) |
| `--preset` | X | `general` | 프리셋 (`general`) |

### 동작

1. 대상 프로젝트 디렉터리 생성 (없으면)
2. CLAUDE.md에 마커 구간 삽입
3. AGENTS.md 복사 (기존 파일이 없으면)
4. rules, skills, hooks, plugin 파일 복사
5. config.json 생성
6. manifest.json 기록

### 예시

```bash
# 기본 설치
python3 scripts/apply.py --project /path/to/my-project
```

## update.py

설치된 harness를 최신 템플릿으로 업데이트합니다.

```bash
python3 scripts/update.py --project <경로>
```

### 옵션

| 옵션 | 필수 | 기본값 | 설명 |
|---|---|---|---|
| `--project` | O | - | 대상 프로젝트 경로 |

### 동작

1. 기존 manifest.json 읽기
2. 템플릿 파일과 체크섬 비교
3. `overwrite` 파일: 전체 교체
4. `marker` 파일: 마커 구간만 교체
5. `skip_if_exists` 파일: 유지
6. 새 manifest.json 기록

### 예시

```bash
python3 scripts/update.py --project .
```

## doctor.py

프로젝트의 harness 설치 상태를 진단합니다.

```bash
python3 scripts/doctor.py --project <경로>
```

### 옵션

| 옵션 | 필수 | 기본값 | 설명 |
|---|---|---|---|
| `--project` | X | `.` | 대상 프로젝트 경로 |

### 진단 항목

- Python 설치 여부
- 프로젝트 디렉터리 존재 여부
- CLAUDE.md 존재 여부
- AGENTS.md 존재 여부
- manifest.json 존재 및 파싱
- config.json 존재 및 파싱
- rules 디렉터리 및 파일 수
- skills 디렉터리 및 파일 수
- hooks 디렉터리 및 파일 수
- plugin 디렉터리

### 출력 레벨

| 레벨 | 의미 |
|---|---|
| `[OK]` | 정상 |
| `[WARN]` | 권장 사항 |
| `[ERROR]` | 반드시 수정 필요 |

### 예시

```bash
python3 scripts/doctor.py --project /path/to/my-project
```

## Makefile 타겟

| 명령 | 설명 |
|---|---|
| `make test` | pytest 테스트 실행 |
| `make lint` | ruff 린트 검사 |
| `make format` | ruff 자동 포맷팅 |
| `make coverage` | 커버리지 리포트 생성 |
| `make doctor` | 프로젝트 상태 진단 |
| `make check` | lint + test 실행 |
| `make clean` | 캐시 정리 |
| `make install` | 현재 디렉터리에 harness 설치 |
