# MySkills recovery runtime 8.2

This is a separate qualification profile, authorized on 2026-10-10. PR #7 stays
draft and on HOLD. PR #6 merged as `dee52b0344c700237f18f6bff1a4eb016a8317a4`.
Canonical main has the same tree as frozen foundation `d57ff77b…`. PR #7 still
targets `codex/myskills-platform`; retargeting requires owner approval. The
read-only comparison is retained in `retarget-assessment.json`.

The model manifest remains
`sha256:accad778b53702521a72c6c21e5e22d1a9bea0b4da33d8894a0779c1079ec173`.
Every model blob, runtime binary, operating-environment field and service
configuration matches the original pin, except the recorded daemon PID/start
and model display metadata. The original runtime identity remains
`sha256:9edd4313e400254d9a6c765c089010562a8db2eafa6e5c1771b69d79d02a5a14`.
The separate successor is
`sha256:ac26a2e9bf3afc13b7513772a816c522740767924fbee3c801faa08dce769276`.

## Exact metadata difference

An original tool response retained in the task session contains the old
modification timestamp, model details, capabilities and parameter display order.
Combining that subset with the current metadata and enumerating the 24 possible
orders of four distinct Modelfile parameter lines produces exactly one canonical
object whose digest equals the original committed metadata digest `277347f0…`.
The reconstruction and original excerpt are retained in
`qualification/checkpoint8/successor/`. This is a digest-authenticated canonical
reconstruction, not an original raw HTTP capture.

The exact differences are:

- `modified_at`: the restored manifest's new filesystem modification time.
- `parameters`: ordering of the same four option/value pairs.
- `modelfile`: ordering of the same four `PARAMETER` lines.

All other fields match, including template, model/projector metadata and
capabilities. The pinned upstream Ollama source assigns the modification time
from manifest filesystem metadata and renders parameter options by iterating a
map. The retained source object binds the actual inspected lines, rather than
relying on mutable web line numbers. The installed build reports the same source
revision with a dirty-build marker; its exact executable hashes remain the
authority. See [Ollama source at the recorded revision](https://github.com/ollama/ollama/blob/b061384d90ff455462bc32745dd0de479de717a3/server/routes.go).

These display differences establish no change in semantic option values. They
do not prove behavioral equivalence. Loading, prompt handling, tool calling,
context handling and output correctness still require actual successor trials.
Tokenizer/model metadata preservation is not a separate tokenizer conformance
test.

## Bound execution profile

The runtime profile is `myskills-local-runtime/8.2.0`; the native harness is
`codex-app-server/0.157.0+myskills-native-8.2.0-recovery`. Adapter
`myskills-tools/4.0.1` and evaluator `myskills-profile-evaluator/8.0.0` remain
unchanged. Historical evaluator 5.0.1, harness identities and TDD qualification
also remain unchanged.

`profile.json` binds the complete runtime, raw current metadata, exact manifest,
historical reconstruction, four existing representative/adversarial fixtures,
and each tool schema. Each trial is limited to 32 provider calls and 600 seconds.
The provider is explicitly local; candidate containers have no network or host
mounts. Runtime checks compare the complete successor pin before and after
trials. No timestamp, parameter order or process identity is normalized during
active execution. Any subsequent identity change stops the batch.

The native API tasks must make the reviewed two-edit correction: remove
per-request WAL configuration and bound the connection wait to one second.
Tests retain all original assertions, reader contention in DELETE/WAL modes,
and concurrent idempotency/conflict requests. No application retries or relaxed
assertions are permitted. Both Skills must establish their complete contract
plan before implementation, execute tests, and bind every claim to actual
source and tool results. Independent review and strict fresh replay remain
mandatory.

At source preparation, focused identity, tamper, evaluator and custody tests
pass 54 cases. Review found one missing imported harness dependency; its regression
failed before the binding correction and passes afterward. This is not behavioral
qualification.
No Skill instructions, historical observations, catalog trust or consumer
repositories are changed. Paid model operations are zero; production and
marketplace execution remain disabled.

## Native results

Collector `5044c86af8934cf23838a33bc0cd9df3909ba6d3` completed all four trials.
Admission and closing full-byte hashes matched the complete successor runtime
pin. The batch reports STABLE, no halt, and all results admissible. Tool
containers were removed after each trial. Independent review checked every
model-to-tool request, journal chain, source/test/document binding, workflow
order, final response and recorded cleanup.

| Case | Evaluator and independent review |
|---|---|
| API representative | FAIL |
| API adversarial | PASS |
| Security representative | PASS |
| Security adversarial | PASS |

The API representative changed whitespace inside its CREATE TABLE SQL string
in addition to the two reviewed edits. The exact AST policy rejects that extra
change. This is an out-of-profile edit, not an observed retry, timeout or
concurrency failure. Every recorded functional and source-claim check passed.
The adversarial API output satisfies the exact edit policy. Both API cases
recorded the full contract before implementation and ran the concurrency and
legacy checks. The API profile remains FAIL because both cases must pass.

Both security cases preserved the retained implementation and generated
source-supported claim records after actual tests. Resource checks distinguish
missing data from present null data and exercise eight denials. The candidate
returns status 403 without a reason code; rejection classes identify controlled
single-fault fixtures. This does not establish reason-coded production error
semantics. Security remains a candidate pending fresh and hosted validation.

The native bundle digest is
`sha256:af12d52061c706aee5be94aa2d23e74b53d4d05ac262a44becd1f1e2a301974c`.
It contains 144 files and is retained in the separate immutable evidence vault.
Public transcript publication is pending explicit authorization. Automatic
approval review rejected the attempted PR evidence comment before publication;
no bundle comment was posted. Eight prepared parts total 466,548 bytes. Common
credential-pattern checks found no matches, but that check does not grant
disclosure authority. Review summaries and digests are recorded separately.

The first local assisted replay reproduced all four native verdicts exactly.
Specific verifier denials and 13 adapter effect/owner controls passed. Its
sealed report is `9cda189094deb588dcbf843133bedfac1d3f36b1f68470f516ffb9028db1cb87`.
The post-run container inventory found no remaining MySkills containers.
`native-validation.json` records this checkpoint without accepting a new profile.

Historical evaluation results and the checkpoint-7 hold remain unchanged.
Hosted run `38070021442` at collector `5044c86…` passed 354 portable tests with
two macOS-only skips and the browser job. Its historical checkpoint-7 replay
failed in the original positive control. The failed artifact is retained as
SHA-256 `433e7b0c5088c5efd726a1dbed6d54326400dd50dcc111dfea83e9b72018e4a3`.
No CI gate was removed or bypassed. Fresh successor hosted replay cannot run
until authorized evidence custody is available to the runner.

## Fresh checkout

A fresh GitHub clone of `dd8655cf3d9710f46313d1576158b38cff9fff03` passed all
356 portable tests and validated the unchanged 92-Skill catalog. It reused the
existing Python environment and installed only `acorn@8.15.0` from the offline
cache using the committed lockfile and disabled install scripts.

The fresh checkout restored the eight local parts against the committed bundle
digest. Its assisted replay report is byte-identical to the first local replay.
Historical TDD replay reproduced accepted candidate digest `b9b9e51c…`.
Historical custody verification preserved all 520 original files and the
checkpoint-7 acceptance hold. The checkout stayed clean. Exact references are
in `fresh-validation.json`.

Hosted run `38071359010` on that commit passed the existing package, browser and
historical replay jobs. This later green run does not erase the earlier SQLite
failure, repair the historical evaluator, or validate successor transcripts.
The workflow is unchanged and has not run successor replay. No new profile is
accepted. The eight evidence parts need explicit disclosure authorization
before hosted replay can be enabled. PR #7 remains draft and on HOLD.
