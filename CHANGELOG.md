# Changelog

All notable changes to so2x-harness will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-04-14

### added
- Agent orchestration pipeline runner (so2x-cli run specify/execute)
- Sequential pipeline: Interviewer → Code Explorer → Spec Writer → Planner → Reviewer → Verifier
- Gate checks between each pipeline stage
- Agent template auto-loading with instruction generation
- Task status tracking (pending/in_progress/done)

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
