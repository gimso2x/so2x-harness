# Preset Guide

so2x-harness의 프리셋 시스템을 설명합니다.

## 프리셋이란

프리셋은 프로젝트 유형에 따라 활성화할 rules와 skills를 정의하는 설정 파일입니다.

## 기본 제공 프리셋

### general

모든 프로젝트에 적용 가능한 기본 프리셋입니다.

```json
{
  "preset": "general",
  "platforms": ["claude"],
  "language": "ko",
  "comment_language": "en",
  "enabled_rules": ["language-policy", "scope-control", "file-size-limit", "testing-policy", "verification-policy"],
  "enabled_skills": ["planning", "implementation", "debugging", "review", "specify-lite", "check-harness", "spec-validate", "setup-context", "changelog", "safe-commit"]
}
```

### nextjs

Next.js 프로젝트용 프리셋입니다. general과 동일한 rules/skills에 추가 메타데이터를 포함합니다.

```json
{
  "preset": "nextjs",
  "platforms": ["claude"],
  "language": "ko",
  "comment_language": "en",
  "enabled_rules": ["language-policy", "scope-control", "file-size-limit", "testing-policy", "verification-policy"],
  "enabled_skills": ["planning", "implementation", "debugging", "review", "specify-lite", "check-harness", "spec-validate", "setup-context", "changelog", "safe-commit"],
  "notes": {
    "framework": "nextjs",
    "expected_dirs": ["src", "app", "components"],
    "verification_hint": "Check route-level UI behavior and build output for Next.js projects."
  }
}
```

## 커스텀 프리셋 작성

### 1. 프리셋 파일 생성

`templates/project/.ai-harness/presets/` 아래에 JSON 파일을 만듭니다.

```json
{
  "preset": "my-framework",
  "platforms": ["claude"],
  "language": "ko",
  "comment_language": "en",
  "enabled_rules": [
    "language-policy",
    "scope-control",
    "file-size-limit",
    "testing-policy",
    "verification-policy"
  ],
  "enabled_skills": [
    "planning",
    "implementation",
    "debugging",
    "review"
  ],
  "notes": {
    "framework": "my-framework",
    "expected_dirs": ["src"]
  }
}
```

### 2. 스키마 검증

```bash
python3 -c "
import json
from jsonschema import validate
schema = json.load(open('schemas/config.schema.json'))
preset = json.load(open('templates/project/.ai-harness/presets/my-framework.json'))
# 프리셋의 enabled_rules/skills만 검증
config = {'project_name': 'test', 'preset': preset['preset'], 'platforms': preset['platforms'], 'language': preset['language']}
validate(instance=config, schema=schema)
print('Valid')
"
```

### 3. 설치 테스트

```bash
python3 scripts/apply.py --project /tmp/test-project --preset my-framework
```

## 프리셋 구조

| 필드 | 필수 | 설명 |
|---|---|---|
| `preset` | O | 프리셋 이름 (파일명과 일치) |
| `platforms` | O | 지원 플랫폼 목록 |
| `language` | O | 기본 응답 언어 |
| `comment_language` | X | 코드 주석 언어 |
| `enabled_rules` | O | 활성화할 rule 파일 목록 |
| `enabled_skills` | O | 활성화할 skill 파일 목록 |
| `notes` | X | 프레임워크별 추가 정보 |

## 프리셋 추가 체크리스트

- [ ] `templates/project/.ai-harness/presets/<name>.json` 파일 생성
- [ ] `enabled_rules`에 존재하는 rule만 포함
- [ ] `enabled_skills`에 존재하는 skill만 포함
- [ ] `make test` 통과
- [ ] `python3 scripts/apply.py --preset <name>` 정상 동작
