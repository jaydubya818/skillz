# MySkills checkpoint 8

Status: source recovery validated; native qualification BLOCKED. PR #7 remains
draft and on HOLD. This source checkpoint grants no new behavioral qualification.

This checkpoint keeps PR #6 frozen and continues PR #7 from
`c7c53a261552297d9398b00e822d7cfaf7c63fff`. Original Skill bodies, manifests,
attribution, adapter 4.0.1, historical evaluators and the accepted TDD profile
remain unchanged. New evaluation uses `myskills-profile-evaluator/8.0.0` and
`myskills-negative-controls/8.0.0`. Native collection uses the pinned local model
through the recovery successor
`codex-app-server/0.157.0+myskills-native-8.1.0-recovery`.

The retained generated API configures `PRAGMA journal_mode=WAL` on every request.
A fresh recovery sample of 24 two-process pairs reproduced SQLITE_BUSY once.
Two other schedules did not reproduce it; these fresh observations remain
retained. The original local SQLite captures were lost. No exception
was injected and no successful observation cancels the failure. This identifies
a generated implementation/connection-configuration defect under contention.
It does not establish a defect in the original Skill instructions.

The reference correction removes the per-request journal change and changes the
connection wait from 30 seconds to one second. It preserves the insert-first
transaction, response contract, schema and connection cleanup. There are no
application retries. SQLite documents journal mode as persistent configuration
and permits only one simultaneous write transaction. See the official
[journal-mode documentation](https://www.sqlite.org/pragma.html#pragma_journal_mode)
and [transaction documentation](https://www.sqlite.org/lang_transaction.html).

The API successor profile admits only this exact two-edit AST, apart from
comments and formatting. A timeout keyword by itself was insufficient: review
found PRAGMA overrides, recursive retries and repeated connections could evade
that weaker check. These cases now have permanent regressions. This deliberate
restriction establishes only a finite assisted repair workflow, not general
API implementation capability. Actual runtime checks are still mandatory.

Tests retain the original checks and add real reader contention in DELETE/WAL
modes, preservation of the configured journal mode, and eight additional
concurrent request pairs. Every pair must complete within its bound and preserve
one-row idempotency/conflict behavior. No failed request is retried or omitted.

Targeted verifier controls isolate the intended API state-forgery and security
value-mutation attempts from unrelated concurrency work. Trusted parent checks
retain the actual child result and independent database/request witness. A
control passes only on the expected identity, boundary, rejection class,
attempt witness and unchanged parent state, with clean command completion and
confirmed cleanup. Generic nonzero exits, policy failures, timeouts, missing
dependencies, malformed packets and unrelated exceptions fail qualification.
Adapter controls retain exact rejected requests and deny codes, require no
executor dispatch, and verify both owner states remain unchanged.

Security resource controls pair valid owner/null-data requests with actual
malformed-resource, foreign-owner, invalid-token and null-destination attempts.
Their classifications identify controller-owned test cases. The candidate's
interface returns status 403, not a structured reason code. Always-deny
implementations fail the required positive controls and inherited suite.

Both native workflows start from the exact sealed checkpoint-7 representative
outputs. The first write must record the full protected contract plan before
any implementation edit. A placeholder document cannot satisfy this gate.
Final claims must bind exact source digests and actual successful test calls
from the same trial. Final source, documentation and finish evidence still
require independent review. No generated explanation establishes qualification.

The controller-written positive control receives no Skill behavioral credit.
New profiles require completed native representative/adversarial trials,
independent output review and complete fresh-clone/hosted validation. The old
checkpoint-7 hold and all old verdicts remain historical records; any successful
checkpoint-8 profile is a distinct successor.

Composition stays disabled. Consumer repositories and execution remain
unchanged. Marketplace activation is disabled, production integration is
NOT_RUN, external-alpha impact is NONE and paid model operations are zero.
Greptile stays deferred under the existing source-disclosure boundary.

## Recovery and custody

The interrupted checkout and its local evidence disappeared while an observed
`rm -rf` process traversed the shared Codex visualization directory. Process
ancestry ties that command to an iTerm login shell. The initiating person,
chat, or automation is not established. The retained interruption report and
bounded investigation are in `qualification/checkpoint8/`. The interrupted
batch receives no qualification credit.

Recovery cloned the exact retained checkpoint-7 baseline commit into
`/Users/jaywest/Downloads/skillz/myskills-checkpoint8-recovery`. The ten recovered
collector, evaluator and fixture files match their pre-interruption hashes.
Historical GitHub evidence was restored and checked against its committed pins.
Qualification evidence now lives separately at
`/Users/jaywest/MySkillsEvidence/checkpoint8-recovery`.

The recovery harness preserves the existing tool and evaluation contracts. Its
successor runtime pin may change only the observed daemon PID and start time;
the command, model bytes, binaries, environment and model metadata must match
the historical pin. Runtime checks run before and after each trial. Missing or
changed model bytes prevent dispatch.

Task-owned lease markers reject foreign-workstream protection changes. Native
collection freezes tracked source files, protects tool journals and observations,
and copies evidence into immutable content-addressed objects with an append-only
index. Ordinary deletion and overwrite attempts are tested against macOS file
flags. These controls do not protect against an administrator or another process
deliberately removing those flags. Cleanup restores only this task's captured
source flags; it never removes retained evidence.

Source-freeze failures restore the original file flags even when protection
stops partway through. A failure retaining the initial context also releases
the frozen source. Both defects reproduced before correction; the custody and
replay suite passes 15 tests afterward, including native macOS flag checks.
Independent review passed 13 portable cases and reviewed both fixes; that
reviewer did not rerun the two macOS flag tests. The complete portable suite
passes 339 tests, excluding the existing FFmpeg-dependent recorder suite.

Fresh offline controller executions also pass the specific verifier controls,
adapter effect/owner controls, security resource controls, and API reference
correction test/legacy commands. Their actual outputs are retained alongside
the source validation receipt. This is controller verification only; it does
not establish the native Skill workflow or qualify a new execution profile.

Exact model recovery reproduced the pinned manifest and every model blob,
runtime binary and environment field. Admission still failed because the
`/api/show` response digest changed from `277347f005e74b3203152b1a6ad444b9e80c096bbbb95c6a7b4c612506e00ee3`
to `0c90c3e0a5236b1f0c3f378dff8f5ae0ddb6009d5157c7b69899a750265f876e`.
The current response includes a new modification timestamp, but the historical
raw response was not retained, so the exact metadata change is not established.
`qualification/checkpoint8/recovery-admission.json` records this boundary.
No recovery runtime pin was accepted and no new native batch was dispatched.
The historical guard remains unchanged. Resuming requires resolving the exact
metadata identity or explicit authorization for a separately pinned successor.

Hosted validation keeps every existing checkpoint gate. Checkpoint-8 native
replay activation is deferred until a completed, pinned batch and independent
output review exist; its proposed workflow was retained in the external vault.
The implemented successor replay requires those artifacts and fails closed
when they are absent. Neither source tests nor hosted historical replay can
establish a new native behavioral PASS or override a failed fresh replay.

PR #7 currently targets the frozen PR #6 branch. Merging it now would modify
that foundation branch. Merge sequencing and any later retargeting require
the owner's decision. Repository workflows run validation on pull requests
and pushes to main; release publishing runs only on `v*` tags. No merge-triggered
deployment workflow, repository webhook, deployment or environment was found
during the 2026-10-10 inspection. No branch protection or ruleset was configured;
the documented review and qualification holds still apply.
