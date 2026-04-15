## Codex / Claude parity bundle draft

This draft summarizes the follow-up parity work completed after the initial Codex platform support release.

### Scope
- #39 Codex parity: make config.json platforms reflect installed platforms
- #40 Codex parity: generate installed skill lists from enabled_skills
- #41 Codex parity: make Codex skills platform-neutral and remove Claude-specific invocation assumptions
- #42 Codex parity: add drift checks between config, manifest, and generated platform assets

### Why this bundle mattered
The harness could install Codex assets, but several surrounding outputs still behaved as if Claude were the default truth:
- generated config and schemas drifted from actual installed platforms
- installed skill lists drifted across presets, generated directories, and CLAUDE.md
- Codex skill templates still carried Claude-first slash and agent-chain assumptions
- doctor had no strong visibility into config/manifest/asset drift

### What changed

#### 1. Config and schema alignment
- `.ai-harness/config.json` now renders `platforms` from the actual installed platform set
- incremental apply/update flows keep config platforms synchronized with manifest platforms
- schema and example files now accept/show both `claude` and `codex`
- generated config + manifest outputs are covered by schema contract tests

#### 2. enabled_skills as the effective generation source
- `CLAUDE.md` Installed Skills is now rendered from preset `enabled_skills`
- generated `.claude/skills/*` and `.agents/skills/*` are filtered by `enabled_skills`
- update/apply resync config `enabled_skills` from the preset
- stale skill directories outside the enabled set are removed during apply/update

#### 3. Codex skill template neutrality
- Codex `specify` and `execute` templates no longer depend on Claude-style slash invocations
- Claude-specific agent-chain labels such as Interviewer / Planner / Reviewer were removed from Codex variants
- Codex templates now use more direct, Codex-friendly invocation examples like `$specify` and `$execute`
- regression tests now block reintroduction of Claude-first wording in Codex skill templates

#### 4. Drift diagnostics in doctor
- `doctor.py` now warns when config platforms diverge from manifest platforms
- `doctor.py` now warns when installed skill count drifts from `enabled_skills`
- dedicated integration tests cover config/manifest platform drift and missing declared assets

### User-visible effect
- multi-platform installs are now more internally consistent across config, manifest, generated skills, and docs
- Codex users see more natural skill guidance instead of Claude-first slash workflow assumptions
- drift is surfaced earlier by doctor instead of being silently tolerated

### Validation
- `make check`
- `make coverage`
- generated schema contract tests for codex-only and mixed installs
- enabled_skills generation tests for Claude and Codex outputs
- doctor drift integration tests

### Landed PRs
- #43 fix: sync config platforms with installed platforms
- #44 fix: derive installed skills from enabled_skills
- #45 fix: remove claude-first assumptions from codex skills
- #46 feat: add doctor drift diagnostics

### Suggested release note summary
Codex/Claude parity follow-up: config, schema, skill generation, Codex skill wording, and doctor drift checks were all tightened so multi-platform installs behave consistently and drift becomes visible earlier.
