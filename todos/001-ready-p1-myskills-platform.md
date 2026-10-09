---
status: ready
priority: p1
issue_id: "001"
tags: [myskills, governance, security]
dependencies: []
---
# MySkills foundation

## Problem statement
The portable collection needs explicit package identity, eligibility, owner isolation,
and evidence without changing existing runtimes or granting execution authority.

## Findings
Canonical baseline 4942dde includes the seven PR #5 adaptations. No re-import.
The library and installer use Python. Preserve the skill tree and license material.

## Proposed solutions
Use an additive Python reference library and generated JSON catalog. Production
persistence and integration remain separate releases. No new production database.

## Recommended action
Implement the authorized checkpoints in order, with negative tests, independent
review, disclosure checks, commits, pushes, and exact remote verification.

## Acceptance criteria
- [x] A: inventory, strict manifest, digest, provenance and safe default metadata
- [x] B: registry, exact dependency graph, lifecycle, update/revocation
- [x] C: isolated owner state, install/enable, private records
- [x] D: deterministic resolver and routing corpus
- [x] E: qualification evidence, tamper checks, controlled promotion, private builder
- [x] F: inactive platform compatibility contracts against current source
- [x] G: functional local UI, shared agent API, browser/accessibility qualification
- [ ] H: composed deterministic journey, fresh clone, CI, final independent review

## Work log
### 2026-10-08
Created task-owned worktree from current canonical main. All production integration,
paid qualification, deployment, tester grants and marketplace activation remain off.
Recorder tests retain their known local FFmpeg/sandbox limitation. Greploop review
of PR #5 timed out; that review is not a PASS.
