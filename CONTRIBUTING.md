# Contributing Guide

so2x-harness에 기여하는 방법을 안내합니다.

## 개발 환경 설정

### 요구사항

- Python 3.10+
- Git

### 설정

```bash
git clone https://github.com/gimso2x/so2x-harness.git
cd so2x-harness

# 테스트 의존성 설치
pip install pytest pytest-cov ruff
```

### 확인

```bash
make test      # 테스트 실행
make lint      # 린트 검사
make coverage  # 커버리지 리포트
```

## 코드 스타일

### 포맷팅

- ruff를 사용하여 코드 포맷팅
- `make format`으로 자동 수정

### 언어 규칙

- 코드 식별자: 영어
- 주석: 영어
- 문서, 커밋 메시지: 한국어
- 사용자 대면 메시지: 한국어

### 파일 크기

- 모든 Python 파일 300줄 이하 권장
- 파일이 너무 커지면 모듈 분리

## PR 프로세스

1. main 브랜치에서 feature 브랜치 생성
2. 변경 사항 구현
3. 테스트 작성
4. `make check` 통과 확인
5. PR 생성

### CI 검증

PR 생성 시 자동으로 실행됩니다.

- Python 3.10/3.11/3.12 매트릭스 테스트
- ruff 린트
- VERSION 형식 검증
- harness.yaml 형식 검증

## 테스트 작성

### 단위 테스트

lib 모듈의 순수 함수를 테스트합니다.

```python
# tests/unit/test_checksum.py
from scripts.lib.checksum import sha256_text

def test_sha256_text_deterministic():
    assert sha256_text("hello") == sha256_text("hello")
```

### 통합 테스트

apply/update/doctor를 서브프로세스로 실행합니다.

```python
# tests/integration/test_apply.py
import subprocess

def test_apply_creates_manifest(tmp_project):
    result = subprocess.run(
        ["python3", "scripts/apply.py", "--project", str(tmp_project)],
        capture_output=True, text=True, check=True,
    )
    assert (tmp_project / ".ai-harness" / "manifest.json").exists()
```

### Fixtures

`conftest.py`에서 제공하는 fixtures:

- `tmp_project`: 임시 프로젝트 디렉터리 (package.json 포함)
- `templates_dir`: 템플릿 디렉터리 경로
- `sample_manifest`: 샘플 manifest 딕셔너리

## 템플릿 추가

새로운 rule이나 skill을 추가할 때:

### 1. 템플릿 파일 작성

```
templates/claude/skills/my-skill.md
```

frontmatter 필수:

```markdown
---
name: my-skill
description: 무엇을 하는 스킬인지 한 줄 설명
validate_prompt: |
  Output must include:
  - 항목 1
  - 항목 2
---

# my-skill

상세 설명...
```

### 2. 프리셋 업데이트

`templates/project/.ai-harness/presets/general.json`의 `enabled_skills`에 추가.

### 3. harness.yaml 업데이트

`default_skills`에 추가.

### 4. 테스트

```bash
make test
python3 scripts/apply.py --project /tmp/test --preset general
```

## 커밋 메시지

형식:

```
한국어 간결한 설명

상세 내용 (필요시)
```

예시:

```
spec-validate 스킬 추가

spec-lite 문서의 구조, 완결성, 일관성을
검증하는 신규 스킬 템플릿 작성
```
