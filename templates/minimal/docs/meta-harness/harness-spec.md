# Harness Spec: sample-task

## Goal
작업별 하네스가 자동화해야 하는 최종 결과를 한 문장으로 정의한다.

## Non-Goals
- 배포 자동화 제외
- 운영 장애 복구 제외

## Success Criteria
- 지정 산출물이 생성된다.
- required verification이 통과한다.
- 사용자 승인 지점은 명시된 단계에서만 발생한다.

## Fixed Criteria
- review lenses: code-reuse-review, code-quality-review, efficiency-review
- verification policy: smallest-relevant-check-first
- naming policy: thin-core

## Per-Run Variables
- target repository/path
- feature scope
- output destination

## Intervention Points
- conflicting design choice
- destructive operation
- final verdict sign-off

## Orchestration Class
simple

## Capability Assumptions
- delegation: true
- nested_delegation: false
- background_execution: true
- resume_persistence: true

## Required Artifacts
- outputs/<run-id>/interview/answers.json
- outputs/<run-id>/plan/plan.md
- outputs/<run-id>/execution/artifacts.json
- outputs/<run-id>/review/final-verdict.json
- outputs/<run-id>/final/summary.md

## Verification Strategy
- stage별 artifact schema 검증
- final completeness 검증
- 3개 review lens 분리 검증
