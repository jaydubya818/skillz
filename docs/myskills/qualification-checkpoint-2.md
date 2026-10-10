# Behavioral qualification checkpoint 2

This checkpoint preserves PR #6 at `d57ff77b8522f897fc6ae392cf59b3141295ba82`.
PR #7 continues the qualification experiment. All 92 packages and manifests,
licenses, attribution and PR #5 curation decisions remain unchanged. No Skill
receives platform trust or execution eligibility from these experiments.

## Runtime investigation

Ollama 0.40.2 started a local compatibility GGUF migration at 08:57:41 on
2026-10-09 and completed it at 08:59:15, Pacific time. That migration created
new model and projector artifacts and changed the preferred runnable manifest.
The original model blob remains and passes a full SHA-256 check. Both old and
new configs declare Q8_0. This establishes a local conversion and selection
change; it does not establish identical inference behavior across formats.

Removing the new `runner` and `format` fields from the retained legacy child
reconstructs the original manifest exactly, including SHA-256 `655d273…`.
This is a reconstruction check, not a claim that the old standalone manifest
file is still present. The manifest-list digest `414448…` differs from the
runnable child digest `accad778…`. The new collector addresses the full child
digest directly and never falls back to the mutable model tag.

The new pinned model is
`sha256:accad778b53702521a72c6c21e5e22d1a9bea0b4da33d8894a0779c1079ec173`.
Its weight artifact is `sha256:2ff4caf9bbdc57827703b50471b7e4df7f26e306626d19e556c0c0beeabaeb13`;
its projector is `sha256:489d5e0a682060521694bf97aea6504cb30ab4286af8a7e8a3d73ed8a81907e2`.

The [investigation](../../qualification/checkpoint2/migration-investigation.json)
retains the targeted log observations, reconstructed manifest identity, full
large-artifact hashes, and exact upstream source references. The relevant
Ollama source is [compatibility migration](https://github.com/ollama/ollama/blob/v0.40.2/compatmigrate/migrate.go)
and [local digest resolution](https://github.com/ollama/ollama/blob/v0.40.2/manifest/paths.go).

The [runtime pin](../../qualification/checkpoint2/runtime-pin.json) binds model
blobs, config, runner libraries and binaries, service version/process/start time,
show metadata, OS/architecture/hardware, host Python, Docker engine build and the
offline image. Every result also binds the Skill, request fixture, evaluation,
harness source and output digest. Full artifact hashes are checked at batch
admission and completion; file identities and service/loaded-model observations
are checked around requests. Missing or changed identities halt dispatch.

This is an observation under a trusted local-host/service assumption. It is
not cryptographic model authorship, hostile-host protection, or a guarantee
against concurrent mutation that deliberately preserves file metadata. No
provider credentials or remote model endpoint are used. Candidate code has no
network, host mount, host environment or Docker socket.

## Original verdicts

All nine verdicts from the accepted checkpoint remain byte-bound to their
original evidence. The separate [failure analysis](../../qualification/checkpoint2/failure-analysis.json)
classifies the six failures and the interrupted tenth response:

- Parser planning had an unstated literal rejection encoding in the evaluator.
  The representative response also made a false claim about Python `int("-1")`.
- The sequencing response used the wrong artifact key. Exhausted-unit stopping
  semantics also needed an explicit fixture rule.
- Both code-review responses found the real defect but gave the wrong source
  line and output representation.
- The API response used the wrong artifact key. Its owner-field diagnosis was
  confounded by inconsistent example and adapter field names.
- The tenth response crossed the model identity change and remains unverified.

No Skill instruction defect is established. Version 2 clarifies encoding and
fixture fields and supplies a machine-readable program field. It does not edit
Skill instructions or overwrite earlier failures.

## Two qualification layers

Layer A covers deterministic package loading, manifests, digest/dependency
binding, denied authority, tool restrictions, confinement, revocation,
evidence custody and result identity. Its PASS results are limited to the
specific controls tested. Dependency resolution does not prove child execution.

Layer B covers model-produced artifacts and bounded tool transcripts. The
artifact batch ran representative, adversarial and repeated requests for all
ten exact Skills: 30 requests, 13 artifact PASS and 17 artifact FAIL verdicts.
All ten representative outputs equaled their single repeat byte-for-byte.
Both batch-wide model hash checks passed. A single repeat does not establish
general inference determinism.

The finite tool adapter adds individual fixtures for the five composition
roles. It only reads/writes allowlisted synthetic file data and invokes named
commands in disposable offline containers. It is not a Work scheduler,
production provider, agent service or competing orchestration engine.

Independent review found and closed false-PASS paths before tool model trials:
printed assertion messages, test-name shadowing, library rebinding, missing
regressions, checks before the final edit, fabricated CLI evidence, incomplete
Skill metadata and malformed result data. The supported Python forms are
explicitly restricted for these fixtures. Rejected forms are adapter limitations
or violations of the fixture contract, not proof that the canonical Skill is
incapable of the broader workflow.

## Composition and consumers

The exact graph remains analysis `figure-it-out` → implementation
`principle-sequence-verifiable-units` → tests `tdd` → review
`thermo-nuclear-code-quality-review` → verification `create-verification-skill`.
Every child has its original exact version/digest. No child is execution-eligible.
The actual five-stage composition therefore remains PARTIAL with zero executed
stages. Individual fixture observations do not count as composed execution.
Actual inter-stage output authentication, failure-stop and protected composed
verification remain NOT_RUN. Admission tamper, revocation, immutable identities,
owner boundaries and effect escalation are separate deterministic checks.
Publication remains unauthorized.

Generated `myapps.json` and `missioncontrol.json` export exact bindings,
decision/evidence digests, runtime references, effect ceilings and closed
eligibility. Ready lists are empty. Consumer schema validation is NOT_RUN.
MyApps' Checkpoint I context comes from the owner's instruction; this workstream
does not independently certify that application. Architecture analysis is not
an application-architecture qualification. Performance and observability keep
their exact outside-cohort NOT_EVALUATED references.

MissionControl references cover Engineering Role Packs, Specialized Agents,
Multi-Agent compositions, Factory WorkOrders, Independent Verification and
Enterprise Quality Contracts. MissionControl retains orchestration authority.
Neither consumer repository is changed.

## Reproduction and boundaries

The artifact collector used commit
`dec465447cf975ac5f4681aaa8180a43b9520909`. Later error-reporting fixes do not
retroactively strengthen that batch's runtime claims. Replay checks those
historical source hashes without executing the historical collector.

Evidence is compressed into bounded PR comments. A committed custody pin
identifies every part and the complete bundle. Restore rejects changed,
reordered, oversized, symlinked or unexpected paths. Independent replay reruns
candidate artifacts and checks traces; a producer PASS string is insufficient.
Hosted replay makes no model calls.

```sh
python -m qualification.custody_v2 --restore .artifacts/checkpoint2-retained
python -m qualification.checkpoint_two \
  --retained .artifacts/checkpoint2-retained --output .artifacts/checkpoint2
python -m pytest tests -q --ignore=tests/test_evidence.py
```

Paid model operations remain 0. Production integration is NOT_RUN. External
alpha, MyApps and MissionControl changes are 0. Marketplace activation and
automatic promotion remain disabled. No deployment, production owner custody
or external-alpha FactoryVersion change is authorized or performed. Recorder
tests retain their existing local FFmpeg/sandbox limitation.

## Interrupted tool batch

Docker Desktop's app requested shutdown twice while this task was active. The
first interruption occurred in a known-control test; reopening the existing
runtime restored the same engine version, confirmed the named container absent,
and allowed that control to pass. The second shutdown interrupted the model-driven
tool batch. Its named container's cleanup remains unconfirmed while the engine
is unavailable. No further model request was dispatched. An owner question is
pending before another shared-runtime restart.

Six tool cases finished before the second interruption: parser planning passed
both bounded cases; sequencing and TDD failed both under the explicit adapter
contract. Sequencing left negative input accepted and omitted the required
regression. TDD produced a working clamp and real red-before-edit/green evidence,
but added a main block outside the declared syntax subset. That is a fixture
adherence/adapter limitation, not evidence that TDD cannot fix the bug. Review
stopped after one completed read and an interrupted command; its adversarial
case and both verifier-generation cases were not started.

The tool batch has no successful final runtime check, so all of its qualification
credit is withheld. Replay can independently check its retained completed
artifacts, but cannot turn the batch into a stable model run. Overall runtime
status is UNSTABLE. The separately completed 30-request artifact batch remains
STABLE within its observed interval. The incident record is
[container-interruption.json](../../qualification/checkpoint2/container-interruption.json).

## Checkpoint validation

[Hosted CI at ff58a34](https://github.com/jaydubya818/skillz/actions/runs/37980147393)
passed all three jobs: 207 portable tests, 21 browser checks and offline evidence
replay. Replay verified all 30 artifact observations and the six completed tool
cases while withholding the entire interrupted tool batch's qualification credit.
A fresh GitHub clone of the same revision passed 207 portable tests locally.
Local Docker replay remains blocked at the shared-runtime restart boundary.

The [compatibility artifact pin](../../qualification/checkpoint2/compatibility-artifact-pin.json)
records the exact hosted archive and file digests for `checkpoint2/myapps.json`,
`checkpoint2/missioncontrol.json` and all ten per-Skill decisions. These are
consumer references with empty ready lists and execution disabled. The artifact
can be [downloaded from CI](https://github.com/jaydubya818/skillz/actions/runs/37980147393/artifacts/11640532417).
If hosted retention expires, restore and replay the pinned source revision.

Independent review passed the runtime investigation, fixture controls, custody
and interrupted-evidence handling within the reviewed scope. It found no remaining
blocking findings. The reviewer did not restart Docker or make model calls;
hosted CI supplied the separate container replay evidence.

Keep PR #6 at its accepted foundation revision and preserve the split. PR #7
remains a draft evidence checkpoint, not a qualification or deployment approval.
The next checkpoint requires restoring the isolated runtime, confirming cleanup
of the interrupted container, and starting a new tool-trial attempt with fresh
identity checks. Native workflow and dependency gates must pass before any
composition member becomes eligible.
