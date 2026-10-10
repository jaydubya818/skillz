# MySkills recovery runtime 8.2

This is a separate qualification profile, authorized on 2026-10-10. PR #7 stays
draft and on HOLD. PR #6 is still open and unmerged at the frozen foundation
commit, so the dependency relationship is unchanged.

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
qualification. Native results, independent
output review and replay must be retained separately before any acceptance.
No Skill instructions, historical observations, catalog trust or consumer
repositories are changed. Paid model operations are zero; production and
marketplace execution remain disabled.
