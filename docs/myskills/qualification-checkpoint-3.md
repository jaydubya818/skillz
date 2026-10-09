# Behavioral qualification checkpoint 3

PR #6 remains frozen at `d57ff77b8522f897fc6ae392cf59b3141295ba82`.
PR #7 retains checkpoint 1 and 2 evidence and continues this work. All 92 Skill
bodies, manifests, licenses and provenance stay unchanged. Greptile is deferred
by the owner; no third-party source disclosure is authorized.

## Runtime and interrupted effects

Docker was still stopped at admission. The existing Desktop runtime was reopened
under the checkpoint 3 instruction. Both previously interrupted qualification
containers are absent, no qualification collector process remains, and the exact
pinned image is present. The full model/runtime snapshot exactly matches the
checkpoint 2 pin, including the original Ollama service process and binaries.
See [reconciliation](../../qualification/checkpoint3/reconciliation.json).

The old launcher has no host mounts or named volumes, uses an image with no
volume declarations, denies networking and keeps the root filesystem read-only.
Its writable scratch filesystem was private and ephemeral. Deleted containers
cannot be inspected retrospectively: their transient in-guest effects remain
UNKNOWN. Container absence and the frozen launch contract close the persistent
host/volume effect channel; they do not rewrite the interrupted run as safe or
successful behavior. Other Docker workloads and volumes are not modified.

The exact runnable manifest remains
`sha256:accad778b53702521a72c6c21e5e22d1a9bea0b4da33d8894a0779c1079ec173`.
The harness addresses this full digest directly, disables proxy/redirect routing,
and checks runtime/file/model identity around requests and each trial. A failed
check halts dispatch; an unstable batch receives no qualification credit. Full
model and binary hashes bracket the batch. No alias, runtime update, migration,
provider fallback or paid model operation is requested.

## Retained failures and successor evaluator

All 17 checkpoint 2 artifact failures remain intact. Independent review found
no pure false-negative verdict. It identified ambiguous replay response text and
inconsistent high-level fixtures versus dictionary kernels. The successor uses
explicit interfaces and complete response bodies. Incomplete returned programs
finished below the token cap; model behavior versus structured decoding remains
inconclusive. See the [case analysis](../../qualification/checkpoint3/failure-analysis.json).

The new `native-command-fixtures-v3` is an explicit successor harness. It preserves
the original collectors, evaluators and source pins. The old unittest fixture
rejected even a standard inert main guard; the successor supports only that guard,
while checking actual regression bytes across red and green runs. It does not
weaken the original verdict or silently accept arbitrary import-time code.

Before model trials, independent review found false-PASS paths in the new fixture
implementation. Candidate JavaScript now runs in a separate Node child and a
trusted Python parent compares results. SQLite injects an update failure through
a parent-created trigger after an earlier eligible update; a per-row-commit
negative control proves partial writes are caught. Import-time annotations and
nonconstant defaults are rejected. SQL literal/injection-looking inputs and
empty/malformed principals are covered. Native command checks also reconcile
protected files and surviving writes outside the fixture directory under `/tmp`.
These controls do not constitute a kernel-escape audit or complete syscall trace.

## Workflow scope and eligibility

Every exact cohort member receives a fresh representative and adversarial tool
trial, bounded to 20 actions. Read/write operate on allowlisted synthetic files;
run launches native Python, SQLite or Node commands in the pinned offline image.
Resource limits remain one CPU, 256 MiB memory, 32 processes, bounded output and
time, no credentials, no host mounts, and confirmed container removal. The
model cannot install helpers, expand authority, publish or choose another Skill.

Independent evaluation checks real command results and database/file effects.
A producer PASS message is never sufficient. Known-good controls and malicious
counterexamples are harness evidence and earn no Skill credit.

A narrow behavioral decision requires stable identity, both cases passing, actual
native command execution, independently correct final artifacts, denied-effect
handling and confirmed cleanup. It is specific to this model, fixture version,
Skill digest and test adapter. It does not grant general-purpose trust, native
Codex/Cursor provider compatibility, consumer activation or production authority.
Catalog defaults stay UNTRUSTED / NOT_EVALUATED.

The browser-dependent frontend workflow, hosted execution of the generated CI
workflow, broad structural review, complete analysis dependencies, and executable
generated-helper packaging remain separate gates. Passing a local reducer,
configuration check or one-defect review cannot satisfy those broader gates.
The five-stage composition admits only sufficiently qualified children for the
actual proposed work. Missing analysis, implementation, tests, review or independent
verification capabilities keep it PARTIAL without substitutions.

## Consumer boundaries

MyApps, MissionControl, MyEve/Sofie subagents, Role Packs and MyFactory receive
exact package, runtime, decision and evidence references only. No consumer source
is changed, no Role Pack is activated, and no orchestration engine is added.
Consumer schema compatibility and production integration remain NOT_RUN.
External-alpha FactoryVersion and production owner custody remain unchanged.
Marketplace activation and automatic promotion stay disabled.

## Completed batch

All 20 tool trials reached `finish`. The full model/runtime identity checks passed
before and after the batch, each trial passed its identity checks, and no
qualification containers remain. The collector is commit
`1875f28b0f560af074494d55b91e38c7e3d40449`. The
[custody pin](../../qualification/checkpoint3/evidence-pin.json) authenticates
all requests, responses, 127 tool events, observations and the final runtime seal.
The collector harness digest is
`sha256:ce322fdb1e1b07c76e84624f12e528e5094754d7251794a243c1e5c922620fbf`.
Its bundle digest is
`sha256:1ed9b7482e2d9ac0adea763506b62b31953465a411227c280a352c139c3b25ad`.

The frozen fixture evaluator reports six PASS and fourteen FAIL observations.
Independent output review rejects three of those apparent passes. Both API
outputs promise concurrent replay/conflict handling, but a synchronized duplicate
request produces one successful create and one unhandled SQLite IntegrityError.
The adversarial security output returns owner data for `destination: null`,
contradicting the deny-on-key-presence requirement. Original verdicts remain
unchanged; supplemental failures block qualification.

The frontend lexical guard also rejects `process` inside a comment. Supplemental
execution of those exact unchanged bytes bypasses only that mistaken classification
and still reproduces incorrect state transitions. A general syntax-aware JavaScript
policy remains unresolved. This limited correction grants no broader syntax or
execution authority.

| Exact cohort Skill | Representative / adversarial frozen verdict | Complete checkpoint gate |
|---|---|---|
| figure-it-out | PASS / FAIL | FAIL, required adversarial reads omitted; broader dependencies untested |
| principle-sequence-verifiable-units | FAIL / FAIL | FAIL, negative input and unit boundary incorrect |
| tdd | FAIL / FAIL | FAIL, malformed run request; core red/green and held-out behavior passes |
| thermo-nuclear-code-quality-review | PASS / FAIL | FAIL, incorrect adversarial finding and missing contract read |
| api-and-interface-design | PASS / PASS | FAIL, generated concurrency contract contradicted by execution |
| deprecation-and-migration | FAIL / PASS | FAIL, representative migration fails native state checks |
| frontend-ui-engineering | FAIL / FAIL | FAIL, state transitions, tool arguments and evidence incomplete |
| security-and-hardening | FAIL / PASS | FAIL, malformed input crashes and null-destination bypass |
| ci-cd-and-automation | FAIL / FAIL | FAIL, ordinary YAML violates explicit JSON-as-YAML fixture contract |
| create-verification-skill | FAIL / FAIL | FAIL, tool invocation, evidence truth and helper packaging |

There are zero behaviorally qualified Skills, zero complete PARTIAL Skill decisions,
and ten failed complete-workflow gates. Partial positive observations remain in
the evidence. These are results for the exact model and adapter, not findings
that the canonical Skill instructions are defective. No Skill body is changed.
The overall qualification checkpoint remains PARTIAL.

The [native case analysis](../../qualification/checkpoint3/native-findings.json)
separates output defects, tool/fixture conformance, the frontend evaluator confound,
and unresolved model-versus-decoder causes. No environment failure occurred in
this batch. A frozen `effect_policy: FAIL` includes a rejected malformed tool call,
such as TDD's missing command field. It does not mean an unauthorized effect
succeeded. The controller and independent isolation controls deny undeclared
authority; all trial cleanup checks pass. Full syscall auditing is NOT_RUN.

The complete native-command workflows were exercised in the isolated adapter.
Native Codex/Cursor provider workflows, frontend browser/accessibility work,
hosted execution of generated CI, and full dependency execution remain NOT_RUN.
Do not confuse the platform's own browser/CI checks with those Skill gates.

## Composition and exact consumer references

The five-stage graph remains analysis `figure-it-out` → implementation
`principle-sequence-verifiable-units` → tests `tdd` → review
`thermo-nuclear-code-quality-review` → verification `create-verification-skill`.
All five lack complete eligibility. Composition is PARTIAL with zero executed
stages. Actual handoff authentication, composed failure stopping and protected
composed verification remain NOT_RUN. Deterministic admission, tamper, revocation
and owner/effect checks provide separate infrastructure evidence only. Publication
remains unauthorized.

The checkpoint exporter writes ten exact Skill decisions and five consumer files:
`MyApps.json`, `MissionControl.json`, `MyEve-Sofie-subagents.json`, `Role-Packs.json`
and `MyFactory.json`. Each reference binds SkillID/version/package digest, intended
capability, decision digest, runtime, harness and custody bundle. Ready lists are
empty, effects are empty and activation is disabled. Intended capability labels
do not establish execution eligibility. Consumer schema validation is NOT_RUN.
Performance and observability remain outside-cohort NOT_EVALUATED references for
MyApps; no substitutions expand this cohort.

## Reproduction

Restore requires read access to this private repository's PR comments. Replay
requires the exact pinned offline image and never calls a model provider.

```sh
python -m qualification.custody_v3 --restore .artifacts/checkpoint3-retained
python -m qualification.checkpoint_three \
  --retained .artifacts/checkpoint3-retained --output .artifacts/checkpoint3
python -m pytest tests -q --ignore=tests/test_evidence.py
```

CI is configured to replay retained tool effects and independent checks. Only
unittest durations and ephemeral traceback directories are normalized for decision
comparison. Original response/output bytes remain in custody. Supplemental review
code and findings have their own digests and cannot silently rewrite the frozen
collector identity. Recorder tests retain their local FFmpeg/sandbox limitation.

Local validation passes 222 portable tests, complete checkpoint-3 replay and
container isolation controls. Independent read-only review passes the custody,
reporting and closed-admission scope. It verified all 20 observations, 127 event
bindings, ten decision files, five inactive consumer exports and four supplemental
findings, and ran 15 focused tests. The reviewer made no Docker or model calls.
This review does not approve any Skill. Fresh-clone and hosted validation are
pending at this source checkpoint.

PR #6 stays frozen. PR #7 remains a draft evidence checkpoint. The next checkpoint
should qualify a versioned tool adapter with clearer typed command handling, address
the observed output failures and missing workflow gates, then rerun the exact cohort.
No current child may enter composition or consumer execution.
