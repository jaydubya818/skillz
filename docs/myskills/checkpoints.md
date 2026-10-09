# Implementation checkpoints

## A: inventory and manifest

Baseline: public skillz main 4942dde4b2a442df3ee45879bb22734c658426df,
including PR #5. Branch: codex/myskills-platform.

- 92 skills inventoried, 92 generated manifests, zero parse failures.
- All 92 remain UNTRUSTED / NOT_EVALUATED. Zero deep-qualified skills.
- Manifest contract, deterministic package export/digest, exact read interfaces,
  owner-filtered search, pinned dependency validation and cycle rejection implemented.
- Seven Addy Osmani adaptations retain upstream revision and MIT license references.
- Existing SKILL.md files, plugins, installers and license material are unchanged.
- Portable suite: 101 passing tests, including 18 new governance tests.
- Negative coverage: tampering, symlink rejection, unknown metadata, bad versions,
  undeclared effects, private lookup denial, dependency cycles/missing/revoked state.
- Independent review identified five findings; fixes and regressions added.
- Public diff reviewed for private content and credentials; only public catalog
  data and synthetic owners are included.
- Recorder suite remains outside portable qualification due to its known local
  FFmpeg/sandbox prerequisites. PR #5 Greploop timed out and is not a review PASS.

Remote verification, fresh-checkout results and hosted CI are recorded in the PR
and task evidence after the checkpoint commit exists. This checkpoint is not the
completed MySkills release. B through H remain required.

Production integration: NOT_RUN. Production mutations: 0. Paid model operations: 0.
MyEve source modified: NO. MyFactory source modified: NO. Relay source modified: NO.
External-alpha impact: NONE. Marketplace activation: NOT_RUN.

## B: governed registry

Implements immutable version registration, separate lifecycle decisions, idempotent
revocation, publisher/dependency revocation, exact update discovery and security
permission diffs. Scoped qualification remains required for promotion. Six focused
regressions cover history, revocation, mutation denial and update review.

Checkpoint A remote SHA verified: c2aef38f832d0b4d6e20573e83dfdc58d42864d1.
Fresh clone: 101 portable tests PASS and 92 catalog entries validated.
Independent checkpoint A review: PASS for offline foundation code; five findings
fixed. This does not establish Greploop approval or skill behavioral qualification.

Hosted CI for checkpoint A: package-contract PASS on c2aef38, 21 seconds.

## C: owner isolation and installations

Authenticated-owner reference sessions implement install, enable, disable, uninstall,
exact reviewed update and monotonic revisions. Concurrent duplicate installs converge.
Four owner-state tests cover cross-owner installation denial, stale decisions,
revocation racing update review, explicit update and historical identity retention.
Independent B and C reviews PASS within the offline authenticated-session scope.
The decision digest does not replace authentication or owner authorization.

Checkpoint B remote SHA verified: d21578a624878d649856825784fd942f5e534b78.

## D: resolver

Nine deterministic tests cover exact selection, no match, ambiguity, unqualified
catalog matches, revocation, excessive effects, disabled/missing child installations,
private resolution freeze and external dependency denial. A ten-request corpus uses
the actual library, including all seven curated capability areas; every request
returns NO_ELIGIBLE_SKILL because these entries remain NOT_EVALUATED. No bodies load.
Synthetic qualified fixtures exercise the positive path without elevating real skills.
Independent review found three dependency bypasses; all fixed and re-reviewed PASS.

Checkpoint C remote SHA verified: e0abd4993c127c90477fb415bc5de475c31b7f49.

## E: qualification and private builder

Eight focused tests cover the private lifecycle, isolation of body/evidence/install,
exact runtime/policy/corpus scope, reviewer authority, static effect ceilings, wrong
and re-sealed evidence, owner-private evaluations of public skills, revoked replay,
version mutation and malicious draft patterns. Independent review found four issues;
all fixed and re-reviewed PASS within the static-package-only scope.

Deep-qualified actual catalog skills: 0. No real Skill gained platform trust.
Checkpoint D remote SHA verified: 59341b1352a76113f6a1fe4c3724cee8bf1eba6e.

## F: inactive platform compatibility

The read-only canonical-source probe confirms MyEve routing ownership/no fallback,
executes the actual MyFactory cloud parser against a synthetic valid request and an
invalid Skill extension, and confirms Relay's strict registration boundary. No
compatibility source changed. Exact source revisions remain in private task evidence.

Three reference-contract tests bind the complete proposed Work fixture to independent
authority, reject altered identities/owners/expiry, preserve privacy in advertisement,
and enforce zero-operation limits. Independent F review PASS within the inactive
fixture scope. Actual integration: NOT_RUN. This is not live protocol compatibility.
See the separate [change-impact proposal](integration-proposal.md).

Checkpoint E remote SHA verified: 0cde4b71f02cd1a108481aa5919eba6806251b0a.

## G: local UI and shared action API

The loopback-only prototype supports discovery, exact details, install/enable/disable,
private draft/validate/qualify/accept, and reviewed updates. All actions share the
authenticated Application service. Session, cross-origin and administrator denials
are covered. Four application tests and 21 browser checks pass, including four
automated accessibility scans, stale-response protection, errors/retry and layout.
Portable suite: 135 tests PASS. Four reviewed screenshot comparisons also pass.
Recorder limitations remain unchanged.

Independent UI review identified exact-version control, stale-response and historical
evidence display issues; each has a fix and regression coverage. Nested provenance
diffs are human-readable; private card state reflects the current exact installation
after updates and uninstall. Browser screenshots and reports remain in task/CI artifacts.
This is an ephemeral reference UI, not production multi-tenant custody.
Independent re-review: PASS for this scope; no outstanding G findings.

Checkpoint F remote SHA verified: 27b0d08031711f8c85ce195d37a8657b2b2cdb4d.
