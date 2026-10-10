# MySkills checkpoint 7

This checkpoint tests corrected API and security outputs against exact source,
executed checks and native tool records. It preserves the original Skills,
adapter 4.0.1, evaluator 5.0.1 and accepted TDD profile. The successor profile
evaluator is `myskills-profile-evaluator/7.0.0`; the collection harness is
`codex-app-server/0.157.0+myskills-native-7.0.0`.

Each Skill has one representative and one adversarial correction workflow.
The starting source and incorrect documents come from the pinned checkpoint-5
native bundle. A protected gateway provides synthetic token authentication;
candidate code receives owner context through that boundary. This tests correct
integration with the fixture, not a real identity provider. The legacy consumer
is the exact checkpoint-3 executable fixture, not a released external consumer.

API checks cover contract bodies, malformed inputs, actual SQLite schema, owner
isolation, retries, two-process identical and conflicting creates, the synthetic
gateway and the frozen consumer. Security checks exercise the actual CLI and
gateway, cross-owner access, malformed resources, missing versus null data,
credential context spoofing and null/falsy destination requests. Nested data
remains inert and may be returned to its authorized owner.

Final documents use fixed claim identities whose propositions and limitations
are defined by the protected fixture. Each claim must bind its exact source
digest and a real successful test call. The finish artifact binds the final
document digest and final test call. The verifier independently executes source
and recomputes every claim. Native final prose, notes and code comments still
require independent output review; structured claims do not make arbitrary prose
trustworthy. Qualification is limited to these finite correction workflows.

Pretrial review found shared-process verifier interference. API code could
replace the verifier's SQLite connection; security code could mutate the
verifier's expected nested value. Both bypasses were reproduced and retained.
Gateway calls now execute in separate child interpreters, with responses and
database state checked by the untouched parent. Permanent executable controls
must accept the original functional source and reject both malicious variants.
The adapter and restrictive source policy are unchanged.

Completed native evidence is sealed before fallible evaluation. An evaluator
failure is retained and stops further model dispatch. Completed typed false
observations remain evaluated contradictions; they are distinct from missing
execution. Interrupted batches cannot receive qualification credit.

Collection, output review, fresh-clone replay and hosted validation are separate
gates. Deterministic evaluator controls receive no native behavioral credit.
Exact profile results and final validation receipts are added after execution.
No consumer repository or production system is modified. Catalog defaults stay
UNTRUSTED / NOT_EVALUATED. Publishing and marketplace activation remain disabled.

The initial four-case batch receives no qualification credit. Three native turns
completed; the last reached its output limit after repeated post-close calls.
Runtime identity stayed stable and container cleanup was confirmed. The sealed
reconciliation, raw transcripts, exact artifacts and four failed output reviews
are retained. API output kept an inaccurate BEGIN IMMEDIATE comment; one final
message misstated a test citation. Security output confused call identities with
evidence digests, and the interrupted case mistyped its final document digest.

One versioned successor batch uses harness 7.1.0 with explicit reviewer feedback
and the sealed failed representative outputs as its starting artifacts. It
keeps the same checks, permitted effects, adapter, model and profile evaluator.
Any resulting candidate applies only to this reviewer-assisted correction task.
It cannot establish unassisted generation or general-purpose Skill trust.

The successor completed all four native turns with stable pinned runtime identity
and confirmed cleanup. Its workflow evaluator observed PASS / FAIL / PASS / PASS
(API representative/adversarial, then security representative/adversarial).
The API adversarial case edited source before documenting its contract.

Hosted run 38016597220 also retained an actual checkpoint-6 API concurrency
failure: one concurrent request raised `sqlite3.OperationalError: database is
locked` at `PRAGMA journal_mode=WAL`. The unchanged operation runs before the
candidate's try/finally. The harness did not inject that exception. Removing a
comment or changing later SQL whitespace does not fix this behavior. A separate
passing race cannot cancel the failed execution. The exact hosted claim,
source, test, source revision and artifact digest are committed in
`qualification/checkpoint7/hosted-counterexample.json`. An explicit adverse
evidence gate prevents either successor API observation from qualifying.

Independent review distinguishes these generated-output and workflow failures
from defects in the original Skill instructions; no Skill-body defect has been
established. No additional model trial is planned for this checkpoint. Security
acceptance still requires matching fresh-clone and hosted verification.

Local independent replay yields API FAIL and security candidate PASS. Every
security claim binds its actual source revision and successful tool execution;
all 18 claim instances across its two cases independently verify. The exact
profile is `security-and-hardening-review-assisted-offline-v1`, using harness
7.1.0 and profile evaluator 7.0.0 with unchanged adapter 4.0.1 and inherited
terminal policy 5.0.1. Model, images, task fixtures, evaluator and Skill digests
are recorded in `qualification/checkpoint7/result-index.json`.

`qualification/checkpoint7/consumer-compatibility.json` contains inactive exact
references for MyEve/Sofie, MyFactory, MissionControl and MyApps. Their native
compatibility is NOT_ESTABLISHED and execution is disabled. The five-stage
composition is PARTIAL/NOT_RUN: Repository Analysis, Implementation, Code Review
and Independent Verification lack eligible profiles. Existing TDD covers only
its finite clamp corpus. No API/security profile substitutes for those children.

The result index preserves candidates separately from acceptance. A final PR
receipt must bind the exact source SHA, fresh-clone checks, hosted run/artifact,
independent review and matching report bytes before a candidate is accepted.
Recorder tests remain excluded from the portable suite because of the retained
FFmpeg/sandbox limitation. Greptile remains DEFERRED; no new source disclosure
was authorized. Paid provider operations are zero.

Final validation run 38017403315 failed the historical checkpoint-5 follow-up
comparison before checkpoint 7 ran. Its specific differing evaluator output was
not retained by the legacy reporter, so this second failure is INCONCLUSIVE and
must not be asserted to be the earlier confirmed WAL exception. The exact log
and artifact identity are preserved separately. A diagnostic wrapper now records
the raw evaluator result before that unchanged strict comparison. It returns
the original result and rethrows failures; it never retries or suppresses them.
The wrapper and its regression are separate from all frozen native/evaluator
identities. Fresh-clone checkpoint-7 exports at that revision matched all16
local report bytes, but hosted acceptance was withheld.
