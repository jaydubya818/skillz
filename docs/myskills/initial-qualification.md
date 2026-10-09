# Initial behavioral qualification checkpoint

This is a blocked qualification checkpoint, not a release approval. **0 of 10 Skills
are deep-qualified.** All 92 catalog entries and manifests retain UNTRUSTED /
NOT_EVALUATED defaults. No existing Skill body, attribution, license or PR #5
curation decision changed.

The exact cohort comes from the accepted [integration proposal](integration-proposal.md)
at foundation `d57ff77b8522f897fc6ae392cf59b3141295ba82`. Canonical Skill source remains
`4942dde4b2a442df3ee45879bb22734c658426df`. The assessment checks source objects,
package bytes, executable modes, installer bytes and the retained proposal before
running the installer. The [plan](../../qualification/initial-cohort/plan.json)
binds every Skill, version, digest, source reference, intended capability, prospective
test effect, representative task and adversarial case.

## Decisions

PARTIAL describes bounded experimental evidence. It is separate from catalog
qualification, which remains NOT_EVALUATED for every Skill. NOT_RUN means the
local runtime identity boundary prevented a behavioral attempt. No row grants
production execution, publishing, credentials or dependency-loading authority.
The original collector used PARTIAL as its transcript-envelope label even for
unstarted cases. The checkpoint ignores that label and derives behavioral status
from verified observations. Original transcript bytes remain unchanged.

| Exact SkillID | Behavioral result / trust | Retained observation | Missing qualification |
|---|---|---|---|
| figure-it-out | PARTIAL / UNTRUSTED | Both artifact oracles failed. The representative plan falsely said Python rejects `int("-1")`; independent execution returned -1. The adapter also required a literal rejection marker that was absent. | Actual repository workflow, factual review, native tools and dependencies |
| principle-sequence-verifiable-units | PARTIAL / UNTRUSTED | Representative scheduling predicate passed; adversarial artifact omitted the required program field. | Observed edits and checks at each unit boundary, failure propagation during real work |
| tdd | PARTIAL / UNTRUSTED | Both clamp artifact probes passed; generated regression failed against the baseline and passed against the candidate. | Model test-before-edit ordering and full repository workflow |
| thermo-nuclear-code-quality-review | PARTIAL / UNTRUSTED | Both strict artifact oracles failed. The reviewer identified the fallback but gave incorrect source/output details. | Broader independent review, accurate source locations and native workflow |
| api-and-interface-design | PARTIAL / UNTRUSTED | Representative artifact failed the adapter contract. The adversarial response was retained but identity verification failed after generation. | Durable endpoint, concurrency, lost-response recovery and stable runtime |
| deprecation-and-migration | NOT_RUN / UNTRUSTED | Stopped before dispatch after runtime identity mismatch. | Disposable database, concurrent writes, interruption and recovery |
| frontend-ui-engineering | NOT_RUN / UNTRUSTED | Stopped before dispatch after runtime identity mismatch. | Browser states, accessibility, keyboard, layout and stale-response tests |
| security-and-hardening | NOT_RUN / UNTRUSTED | Stopped before dispatch after runtime identity mismatch. | Generated application authorization, secret handling and attempted-effect observation |
| ci-cd-and-automation | NOT_RUN / UNTRUSTED | Stopped before dispatch after runtime identity mismatch. | Generated workflow, fork permissions and actual failure propagation |
| create-verification-skill | NOT_RUN / UNTRUSTED | Stopped before dispatch after runtime identity mismatch. | Generated verifier, real CLI driving, teardown and retained evidence |

Ten model responses were retained. Nine completed independent artifact verification:
three artifact PASS results and six artifact FAIL results. Replaying the retained
candidate bytes reproduced all nine verdicts, including the failures. These are
small adapter tests; neither artifact PASS nor successful replay is a Skill PASS.
Formatting failures are evidence about this adapter's compatibility, not proof that
the underlying Skill is universally incapable. Full workflow qualification and
native Codex compatibility remain NOT_RUN.

## Runtime and evidence

The unpaid local model was `qwen3.5:35b-a3b-q8_0`, pinned to
`655d273ede3adc056594f511c120d616d92bf4c4d5bcfe580f3cfa29abe8109d`, using Ollama
0.40.2, temperature 0, seed 7381, a 32,768-token context and a 2,048-token output
limit. The model received the exact Skill body and selected local reference text.
Named dependency bindings were retained but never silently loaded or substituted.
The adapter grants only synthetic artifact production and isolated evaluation.

The model pin failed after the tenth response. A separate metadata read confirmed
that the installed name then pointed to digest
`accad778b53702521a72c6c21e5e22d1a9bea0b4da33d8894a0779c1079ec173`. The cause is
unknown. The run stopped; the unverified response earns no behavioral credit.
The [drift record](../../qualification/initial-cohort/model-drift.json) identifies
the boundary. No reinstall, model alias or silent replacement was attempted.

The earlier collection's temporary checkout and process handles became unavailable
when the environment resumed. Its completion is UNKNOWN and earns no qualification
credit. The [interruption record](../../qualification/initial-cohort/interruption.json)
keeps that attempt separate from the retained second attempt.

Generated Python never executes on the host or in the verifier's process. Each
candidate runs in the pinned image
`node:24-bookworm@sha256:5a750d3be5e5c80275f8c9a5367c3aed99c2875656590c8d0701c7ee687f5f0a`
with no network, host mounts, inherited credentials, capabilities or writable root.
It runs as UID 65534 with bounded CPU, memory, processes, output and duration.
The host compares candidate outputs against independent expectations. Printed PASS
and zero exit status alone do not qualify an artifact. Cleanup must be confirmed
before another attempt can start.

Live confinement probes rejected root writes, external egress and host-model access;
confirmed absent credential variables and separate owner-container state; rejected
forged PASS output; and removed timed-out or output-flooding containers. These checks
do not prove kernel escape resistance or record every attempted syscall.

The [retained evidence comment](https://github.com/jaydubya818/skillz/pull/7#issuecomment-6084558182)
contains synthetic request, response and observation bytes. The committed
[observation pin](../../qualification/initial-cohort/observations-pin.json) binds the
whole bundle and collector source at `7eafed97eb7368a6da55fc2b9400d7048fb7c287`.
The current verifier identifies its own code separately. A later fix makes even a
transient post-generation model-check error halt collection immediately; it does
not alter or relabel the retained observations.

The [assessment pin](../../qualification/initial-cohort/assessment-pin.json) binds the
reproducible package/admission assessment. Generated reports stay in `.artifacts/`.
GitHub CI restores the pinned PR comment, independently replays candidate bytes,
runs confinement checks and uploads the resulting per-Skill decisions and MyApps
references. CI does not call a model provider. Hashes establish content identity,
not cryptographic model authorship. Temperature zero is not a claim of deterministic
inference; see [Ollama's chat API](https://docs.ollama.com/api/chat) and
[structured output guidance](https://docs.ollama.com/capabilities/structured-outputs).

## Composition

The exact pinned graph is:

`figure-it-out → principle-sequence-verifiable-units → tdd → thermo-nuclear-code-quality-review → create-verification-skill`

Composition qualification is PARTIAL. The existing composer rejects the actual
cohort at admission because no member has sufficient qualification. Zero stages
execute and no candidate is created. No substitute Skill or synthetic successful
software handoff is presented as a qualified-member composition.

Executed boundary checks prove that the ordered graph is digest-bound, a changed
child invalidates it, a merge effect cannot broaden child authority, an exact
revoked child is unavailable, and admission failure leaves no candidate. Publication
remains unauthorized. Mid-execution revocation and stage-failure behavior for this
actual cohort remain NOT_RUN. A successful five-stage software-work composition
must wait for qualified children and their runtime dependencies.

## MyApps consumption

MyApps-ready Skills: **none**. The checkpoint emits `myapps.json` with ten exact
candidate bindings, decision-file digests, capability mappings and
`execution_eligible: false`. It also retains exact outside-cohort references for
`performance-optimization` and `observability-and-instrumentation`, both NOT_RUN /
UNTRUSTED. They were not substituted into the ten-Skill cohort.

Potential coverage after qualification: `figure-it-out` for bounded planning;
`thermo-nuclear-code-quality-review` for code review; sequencing and TDD for
implementation/testing; API contracts, migrations, frontend/accessibility,
security and CI through their corresponding Skills; and `create-verification-skill`
for verification. These are capability candidates, not an assertion that application
architecture, accessibility or any other category is currently qualified.

To reproduce without a model:

```sh
python -m qualification.retain --restore .artifacts/qualification/retained \
  --pin qualification/initial-cohort/observations-pin.json
python -m qualification.checkpoint --observations .artifacts/qualification/retained \
  --output .artifacts/qualification/checkpoint
```

Use a full Git clone, authenticated `gh` for the evidence comment and the exact
installed container image. The replay command never pulls an image or invokes Ollama.
Consumers must trust the reviewed repository pin independently and verify the bundle;
a producer-supplied digest alone is insufficient.

## Release boundary

The implementation at `549556d867efce07e5c5497f675fc04913183706` passed 184 portable
tests in a fresh remote clone. That clone restored the evidence from GitHub and
reproduced checkpoint digest
`sha256:f7cca1def77510c717a30b5bf28055447f7a52988f93aa3f73b96fb5371035d3`.
Independent review passed 29 focused tests, repeated all nine artifact verdicts
and reran live confinement checks without any model call.

[Hosted CI](https://github.com/jaydubya818/skillz/actions/runs/37957469071) passed all
three jobs: 184 portable tests, 21 existing browser checks, and offline qualification
replay. The [qualification artifact](https://github.com/jaydubya818/skillz/actions/runs/37957469071/artifacts/11628118824)
contains `checkpoint/checkpoint.json`, `checkpoint/skills/*.json`, and
`checkpoint/myapps.json`. Replay success preserves the six observed artifact
failures; it does not turn them into behavioral PASS results. The PR records the
latest CI revision and the separate bounded Greploop outcome.

Recommended PR #6 disposition: SPLIT. PR #6 remains at the accepted foundation
commit. The experimental runtime and this checkpoint belong to dependent PR #7.
Neither PR is merged by this task.

Next boundary: investigate and stabilize the local model identity, then run the
remaining exact cohort in a supported isolated agent harness. Establish actual
workflow traces, dependency behavior, full application verifiers and the qualified
five-stage composition before any production integration or MyApps consumption.

Production integration: NOT_RUN. External-alpha impact: NONE. Paid model operations:
0. No MyEve, MyFactory, Relay or MyApps production source changed. No FactoryVersion,
marketplace publishing, deployment or persistent production owner custody changed.
Recorder tests retain the prior local FFmpeg/sandbox limitation; this checkpoint's
portable suite excludes them. Greploop must be reported separately from independent
review and hosted CI, and never inferred from either.
