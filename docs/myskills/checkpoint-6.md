# MySkills checkpoint 6

Checkpoint 6 adds `myskills-claims/6.0.0`, a separately versioned source-to-claim
verifier. It reassesses the retained native API and security outputs from
checkpoint 5. It does not rerun a model or change the original Skill instructions.
The accepted `tdd-python-clamp-offline-v1` record, adapter `myskills-tools/4.0.1`
and evaluator `myskills-evaluator/5.0.1` remain byte-for-byte unchanged.

Each claim records an identity, type, statement, origin, modality, exact source
revision, file digest, line range and quoted bytes. Its evidence records the
inspection or executable probe, code digest, actual result, limitations and
receipt digest. The result is VERIFIED, CONTRADICTED, UNSUPPORTED or
NOT_EVALUATED. Empty evidence never establishes a claim.

The controller pins the complete approved proposition and the evidence receipt.
A producer cannot attach a valid concurrency receipt to a broader assertion,
change the expected value to hide a contradiction, or supply its own verdict.
Receipt scope includes the owner and source revision. Missing values cannot be
interpreted as observed null values. Seals detect changed bytes; they are not
signatures or a substitute for source custody and independent execution.

This verifier handles a finite, manually reviewed inventory of material claims.
It is not a general natural-language truth detector. `EXTRACTED` identifies
retained output claims, `SCOPED_VERIFIER_ASSERTION` identifies bounded questions
asked by the verifier, and `REQUIRED_EVIDENCE_GAP` identifies missing support.
A proposed mitigation remains NOT_EVALUATED as implemented behavior. Claim
verification itself grants no Skill trust or execution authority.

## API and security evidence

The input is the original checkpoint-5 bundle
`sha256:c25b7611ff78c77fed3f1fd636cbb91ab40eff96656f8da7d0cac22be7bdef57`,
collected at `d5b3ae95ce000fa76ead2ec83ec7839e7461fa6c`. Custody verification and
native transcript/tool replay run before reassessment. The original native
Skill/model/harness/adapter/fixture/environment bindings accompany each new
claim-verifier binding. The model remains the historical pinned digest
`sha256:accad778b53702521a72c6c21e5e22d1a9bea0b4da33d8894a0779c1079ec173`.
No deterministic control is credited as another model workflow.

Independent probes run in the existing pinned offline image
`sha256:5a750d3be5e5c80275f8c9a5367c3aed99c2875656590c8d0701c7ee687f5f0a`.
The recorded container command requires no network, no host mounts, a read-only
root, an unprivileged user, dropped capabilities and CPU/memory/process limits.
The existing runner confirms container removal. Static policy remains mandatory
alongside isolation; no general JavaScript execution or new effects are enabled.

API probes inspect actual SQLite columns and executed SQL, exercise ordinary
responses, invalid bodies, owner separation, replay/conflicts, a preexisting
schema and legacy row, and two concurrent identical creates. The latter uses
separate processes, a start barrier reached by both workers and independent
database inspection. A conditional missing-row barrier also exposes unsafe
SELECT-before-INSERT implementations; an insert-first implementation does not
enter that conditional barrier. A generated test name or printed success claim
is insufficient.
The result does not establish arbitrary contention, conflicting concurrent
payloads, crash linearizability or compatibility with released consumers.

Security probes exercise the actual CLI with cross-owner requests, malformed
resources, typed principals, missing data, explicitly null data and null/falsy
destinations. A nested destination gives a concrete counterexample to the
threat model's claim about denial anywhere in the payload. An authorized owner
receives its own sentinel data, contradicting the literal claim that no secret
appears in any response. This is an overbroad documentation claim, not evidence
of an unauthorized disclosure. Authentication remains a fixture prerequisite;
validating a nonempty string does not establish a credential service.

API and security retain their functional improvements but receive no new
qualified profile. Both fail the checkpoint-6 claim assessment because material
claims are contradicted. Checkpoint 5's API FAIL and security PARTIAL records
remain intact. The new assessment does not rewrite those historical outcomes.
Incorrect schema, transaction, coverage, threat-model and artifact-content
claims remain permanent regression inputs in
`qualification/checkpoint6/retained-claim-regressions.json`.
The bounded inventory contains 30 claims: 16 VERIFIED, nine CONTRADICTED, four
UNSUPPORTED and one NOT_EVALUATED. These totals describe the retained outputs,
not overall model ability or global Skill trust.

## Qualification and composition limits

The sole qualified profile remains the exact finite TDD clamp corpus. Its
accepted evidence is
`sha256:8693820e6cc24a76610f45ff2f8022eeb271ee321f678517bb1ca2847edc1731`.
Checkpoint 6 adds no requirement to that historical profile and creates no TDD
successor. All 92 catalog Skills remain UNTRUSTED / NOT_EVALUATED globally.

The prepared composition binds the five original proposed children by exact
Skill version/digest. Only the TDD profile is qualified for its own exact test
corpus. Repository Analysis, Implementation, Code Review and Independent
Verification still lack eligible profiles. The graph is immutable and grants
no effects, publication or substitution. Composition remains PARTIAL / NOT_RUN.
The TDD profile cannot fill another stage's responsibility.

MyEve/Sofie, MyFactory, MissionControl and MyApps receive inactive references to
the accepted TDD profile and the new claim assessments. Consumer harness
compatibility remains NOT_ESTABLISHED. References to consumer source remain
bound to the checkpoint-4 inspection; they do not assert current consumer state.
No consumer repositories are modified and no execution is activated.

## Validation and preserved failures

Pure tests cover missing evidence, generated test names, exact reference and
revision mismatches, source traversal, wrong-owner receipts, resealed evidence,
unsupported claim types, proposal/implementation confusion, duplicate or missing
claims, prompt-injection text and nested boolean/integer confusion.

Independent review found and corrected two prequalification defects: receipt
reuse could certify a rewritten proposition, and completed failing tests could
be mislabeled NOT_RUN. The verifier now pins each proposition and separates
execution completion from success. Per-run evidence survives failure of another
probe. A first report attempt also expected the wrong adapter error code for an
unknown argument. The unchanged adapter correctly returned INVALID_ARGUMENT
without dispatch; a regression now checks that exact result. No failed attempt
receives qualification credit.
A later regression check detected inconsistent revision-hash field names in the
preflight expectations. Only that metadata was corrected to bind observation,
native transcript and collector commit. Source quotes, bytes, ranges, statements
and expected verdicts stayed unchanged. The failed report and original fixture
remain retained; a provenance regression guards the corrected format.

CI restores the private pinned native bundle, replays the workflows and produces
all claim ledgers, probe evidence, the matrix, composition and four inactive
consumer records. It makes no model calls. Green CI means the retained outcomes
were faithfully reproduced, including contradictions; it does not promote the
API or security Skills. Recorder tests remain blocked by the retained local
FFmpeg/sandbox limitation and are not counted as passing.

The local portable suite passed 289 tests. Independent source/evidence review
passed all 22 new pure tests and recomputed all 30 claim decisions, including
the nine retained contradictions. That review did not make Docker or model
calls. `qualification/checkpoint6/report-pin.json` binds the eight local exports;
`independent-review.json` records the review scope. Fresh-clone and hosted-CI
results are recorded separately against the pushed SHA after execution.

PR #6 remains frozen. PR #7 stays draft. Paid operations: 0. Production
integration: NOT_RUN. External-alpha impact: NONE. Marketplace activation:
DISABLED. Greptile: DEFERRED.
