# MySkills behavioral qualification — checkpoint 4

Checkpoint 4 establishes a working native Codex tool path and finds defects in
both the harness and generated outputs. No complete two-case Skill profile is
approved. All 92 Skills/manifests, Skill bodies, licenses, attribution and catalog
defaults remain unchanged. PR #6 remains frozen; this work continues in PR #7.

| Skill | Representative review | Adversarial review | Qualification |
| --- | --- | --- | --- |
| `tdd` | PASS for the bounded clamp workflow | PARTIAL; producer checks never ran | PARTIAL |
| `api-and-interface-design` | FAIL | FAIL | FAIL |
| `security-and-hardening` | FAIL despite frozen numeric PASS | FAIL despite frozen numeric PASS | FAIL |

The completed native batch used collector
`6cf855ed865c6e3137460babd515efad2ec6dea4`, adapter `myskills-tools/4.0.1`,
Codex app-server `0.157.0`, and model
`sha256:accad778b53702521a72c6c21e5e22d1a9bea0b4da33d8894a0779c1079ec173`.
All six native turns completed with 49 journaled tool calls. Runtime/model
identity remained stable, including full-byte checks before and after the batch.
This is local inference, with zero paid model operations. Inference determinism
and general-purpose Skill reliability are not established.

The first batch, collector `2bb7a10a135df32e6ceef4c3af5193c89600a887`, remains
INCONCLUSIVE. Its guest confused bidirectional RPC IDs with startup responses.
Version 4.0.1 distinguishes request/response message types. A real native
three-call scripted regression covers the colliding IDs; it receives transport
credit only. No failed attempt was overwritten or rerun unchanged.

The four adapter tools use exact input schemas, sealed output envelopes, call
identities, compare-and-write digests and in-session duplicate suppression.
Behavioral sessions retain fsynced pre-effect and completion journals. A reused
journal cannot silently resume. Paths and commands are explicit allowlists;
`destination: null` and every other destination request fail before dispatch.
The candidate runtime has no network or host mounts, a read-only root, an
unprivileged UID and CPU/memory/PID/time limits. Cleanup uncertainty halts the
batch. Provider cancellation disconnects but cannot attest daemon inference abort.

Review closed a builtin-rebinding hole (`max = eval`) in the TDD syntax guard,
removed evidence/cache filesystem exemptions, and corrected deadline and batch
admissibility handling. Eight actual container controls cover good/bad API and
security output, symlink effects, evidence/cache writes, timeout, cancellation
and network denial. Portable tests also cover traversal, secret/hidden-test
requests, schema confusion, malformed input, publication, evidence tampering,
native RPC custody and substitution of independent review approval.

Two strict-policy defects remain visible in the frozen workflow results:
authorized missing-file reads were counted as effect violations, and inert test
docstrings / `sqlite3.IntegrityError` handlers were rejected. The separate
`fixture-policy/4.0.2` correction has regressions and supplemental final-code
checks. Those checks establish artifact behavior only. They do not reconstruct
the producer's missing TDD ordering or API test execution, and native workflow
qualification of that policy successor is NOT_RUN.

Independent review found genuine output failures as well. API output cites an
incorrect contract digest and makes atomicity/validation claims that disagree
with the code. Both security outputs accept
`{"trusted_owner":"a","resource":{"owner":"a"}}` with status 200, although
the task and generated threat model require malformed resources to be denied.
The independent replay reproduces that failure and verifies a known-good control.
The old PASS observations remain preserved, but cannot approve a profile.

The 17 older artifact failures retain their original analysis and digests. This
checkpoint does not establish that original Skill instructions caused them.
Model-output defects, fixture ambiguity, adapter errors, evaluator omissions and
environment restrictions are recorded separately. Changing several components
does not provide a controlled causal ablation.

Acorn 8.15.0 replaces the comment-sensitive lexical experiment for a narrow pure
JavaScript reducer grammar. It parses without executing, rejects dynamic/global
effect paths, and admits harmless comments containing `process`. The accepted
control passed actual offline Node checks. Runtime isolation remains mandatory;
browser/accessibility and unrestricted JavaScript qualification remain NOT_RUN.

Native contracts differ. Codex was exercised with controller-supplied exact Skill
text and dynamic tools; native Skill discovery/install lifecycle is NOT_RUN.
Installed Cursor has no verified local-provider route. Current MyEve marks the
historical DeepAgents path unqualified and uses a different paid native route.
MyFactory retains native shell/files and a spend gateway; its cloud harness also
requires infrastructure authority. MissionControl's isolated workload bridge is
not a general Skill executor, and its local model route has a different pin.
Exact source commits, file hashes and boundaries are in
[`native-compatibility.json`](../../qualification/checkpoint4/native-compatibility.json).
The separate authorization envelope allows zero spend and no execution. It lists
the provider/model/endpoint and budget bindings that still require owner approval.
No consumer source was changed or uploaded as qualification evidence.

The matrix binds SkillID/version/digest, model/digest, harness/version/digest,
adapter/version/digest, task/fixture and environment. Each row also binds the raw
observation and independent review. `narrow_behavioral_passes` and
`platform_qualified` are both zero. Catalog trust remains UNTRUSTED and catalog
qualification remains NOT_EVALUATED. All five consumer references are closed.
The five-stage composition remains PARTIAL/NOT_RUN: its required children are
not eligible, and publication remains unauthorized.

The ten-part private PR custody bundle is pinned in
[`evidence-pin.json`](../../qualification/checkpoint4/evidence-pin.json).
It retains the interrupted batch, completed batch, raw native transcripts,
journals, controls and counterexamples. The independent review is separately
sealed and pinned. Replay verifies custody, source revisions, native request and
response identities, exact model responses, effects, outputs and review bindings.
It makes no model calls. XZ restoration has explicit compressed, expanded and
decoder-memory bounds.

Qualification output can be regenerated with:

```sh
python -m qualification.custody_v4 --restore .artifacts/checkpoint4-retained
python -m qualification.checkpoint_four --retained .artifacts/checkpoint4-retained --output .artifacts/checkpoint4
```

The outputs are `checkpoint.json`, `matrix.json`, and exact closed references for
MyApps, MissionControl, MyEve/Sofie subagents, Role Packs and MyFactory. Hosted CI
replays checkpoints 1–4 and retains these artifacts. Recorder tests remain locally
blocked by the previously recorded FFmpeg/sandbox limitations; portable tests do
not replace them.

The fresh GitHub clone at `8072604fa8180ec85725ec786c80dcc21e4c87b1` passed 252
portable tests, 21 browser checks, catalog validation and checkpoint-4 replay.
[Hosted validation](https://github.com/jaydubya818/skillz/actions/runs/37996305509)
passed all three jobs, including replays of checkpoints 1–4. The seven generated
report/reference files are byte-identical locally, in the fresh clone and in the
verified hosted artifact. Their exact hashes and artifact identity are recorded
in [`validation-pin.json`](../../qualification/checkpoint4/validation-pin.json).

Next checkpoint: qualify the corrected fixture policy with an explicit principal
and resource schema, and require generated contracts/evidence claims to match
actual results. Preserve the current model and Skill digests unless a separately
identified successor is justified. Do not repeat a failing configuration without
a concrete correction. PR #7 remains a draft qualification checkpoint; PR #6 is
unchanged. Greptile remains DEFERRED. Production integration is NOT_RUN,
external-alpha impact is NONE, and marketplace/consumer activation is disabled.
