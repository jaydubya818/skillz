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
