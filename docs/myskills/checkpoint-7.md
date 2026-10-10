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
