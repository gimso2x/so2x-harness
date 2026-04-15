# Changelog

All notable changes to so2x-harness will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.0] - 2026-04-16

### added
- `run specify`에 목표 기반 관련 learning 자동 주입
- `run execute`에 task summary / review finding 기반 auto-learning 축적
- 신규 helper/test: learning_tools, run learning integration coverage
- 신규 스킬: `simplify-cycle`, `squash-commit` (Claude/Codex 공통 배포)
- `general` preset에 반복 simplify → safe-commit → squash-commit 마무리 흐름 추가
- `.ai-harness/events.jsonl`, `.ai-harness/learnings.jsonl`, `.ai-harness/promoted-rules.json`, `.ai-harness/status/*.json` 기반 학습/상태 표면 추가
- `learn feedback`, `run safe-commit`, `run squash-check`, `run status` CLI 추가
- 멀티 플랫폼 end-to-end smoke test 추가 (`claude` + `codex` 동시 apply + workflow 검증)

### changed
- `doctor.py`가 simplify/safe-commit/squash/promoted-rules/latest promoted rule/latest feedback/event counts를 surface하도록 확장
- 반복된 `user_feedback_captured` 이벤트를 feedback-frequency 규칙으로 승격하고 이후 `run specify`에 다시 주입하도록 연결
- `simplify-cycle` / `squash-commit` 스킬을 3 review lens(Code Reuse, Code Quality, Efficiency)와 convergence/precondition 규약 기준으로 강화
- README / ARCHITECTURE를 Claude/Codex parity 및 learning surface 흐름 기준으로 갱신

## [0.5.0] - 2026-04-15

### added
- Codex CLI 플랫폼 지원 (`--platform codex`)
- 다중 플랫폼 동시 설치 지원 (`--platform claude codex`)
- `install.sh` / `install.ps1` 인터랙티브 플랫폼 선택 (자동 감지 + 프롬프트)
- `templates/codex/` 템플릿 (AGENTS.md + skills)
- `platform_map.py`에 codex 경로 매핑 및 `PLATFORM_CAPABILITIES`
- `doctor.py` codex 플랫폼 진단

### changed
- `apply.py`: `--platform` 다중 선택 지원, 중복 제거, manifest platforms add-only 병합
- `update.py`: manifest platforms 기반 다중 플랫폼 업데이트
- `doctor.py`: 설치된 플랫폼별 진단 분기

## [0.4.0] - 2026-04-14

### added
- `review-cycle` skill for artifact-first code review using `.review-artifacts/{branch-name}/`
- Agent orchestration pipeline runner (so2x-cli run specify/execute)
- Sequential pipeline: Interviewer → Code Explorer → Spec Writer → Planner → Reviewer → Verifier
- Gate checks between each pipeline stage
- Agent template auto-loading with instruction generation
- Task status tracking (pending/in_progress/done)

### changed
- `review` skill now points broad or risky changes to `/review-cycle`
- `review` now checks `design-intent.md`, `code-quality-guide.md`, and explicit side effects/tradeoffs when present
- README, CLAUDE template, preset, and architecture docs now document the review-cycle flow
- integration tests now verify review-cycle installation and documentation coverage
- preset 구조를 단순화하고 `general` 단일 preset으로 정리
- plugin 배포를 쓰지 않도록 `plugin.json`과 `.claude-plugin` 설치/점검 경로 제거

## [0.3.0] - 2026-04-14

### added
- Knowledge accumulation system (JSONL-based learning storage)
- so2x-cli learn add/search/sync/summary commands
- Cross-project learning sharing (local + central)
- 4 learning categories: pattern, anti-pattern, edge-case, decision
- /specify auto-injects related learnings during derivation

## [0.2.0] - 2026-04-14

### added
- spec.json JSON Schema (6-layer derivation chain: L0~L5)
- so2x-cli Python CLI: spec init, check --gate, validate, status, guide
- 6 core agent templates: Interviewer, Code Explorer, Spec Writer, Planner, Reviewer, Verifier
- /specify skill: automated derivation pipeline with gated validation
- /execute skill: spec-driven implementation with scenario verification
- pyproject.toml for pip install -e .
- agents directory in platform_map and apply/update scripts

## [0.1.1] - 2026-04-14

### added
- pytest 기반 단위/통합 테스트 인프라 (41개 테스트)
- Makefile (test, lint, coverage, doctor 타겟)
- GitHub Actions CI/CD 파이프라인 (ci.yml, release.yml)
- JSON 스키마 (config.schema.json, manifest.schema.json)
- 신규 스킬: spec-validate, setup-context, changelog, safe-commit
- 신규 hook: pre-apply-check, post-apply-verify, pre-commit-check, spec-gate
- 설계 문서 (docs/superpowers/specs/)

## [0.1.0] - 2026-04-14

### added
- 초기 so2x-harness 골격
- apply.py 설치 엔진
- update.py 업데이트 엔진
- doctor.py 상태 진단
- marker 기반 CLAUDE.md 관리
- manifest 기반 파일 추적
- 6개 기본 스킬 (planning, implementation, debugging, review, specify-lite, check-harness)
- 5개 기본 규칙 (language-policy, scope-control, file-size-limit, testing-policy, verification-policy)
- general / nextjs 프리셋
- install.sh / install.ps1 부트스트랩 스크립트
