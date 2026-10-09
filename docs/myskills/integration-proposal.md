# Integration after the external-alpha freeze

This proposal is inactive. The current MyFactory cloud parser accepts its exact
MYFACTORY_EXECUTION_V2 keys and rejects an added Skill field. MyEve currently owns
route selection and disallows automatic native fallback. Relay registration is
strict and has no Skill extension. Compatibility probes preserve these facts.

## Proposed change-impact release

1. Use code checkpoint `59d186c4f34116234533dee84ef5785f93c3c172` as the reviewed
   implementation anchor. Pin the final qualified PR #6 head and package digest
   algorithm when opening the separate integration release; documentation or review
   fixes after this anchor do not activate integration.
2. Add an exact Skill binding and resolved composition graph to MyEve's canonical
   Work version and authority. Derive the owner from authenticated Work context.
   Use transactional owner installation/evidence stores in MyEve, including encrypted
   private package custody. Do not deploy the in-memory prototype as a database.
3. Introduce a versioned Factory protocol extension. Bind owner, application, Work,
   generation, workspace, source snapshot, Skill/version/digest, graph, FactoryVersion,
   ExecutionProvider, HarnessProvider, model route, effects, budget and expiry.
   Authenticate this through the existing authority system. An extra unrecognized
   field must keep failing against the frozen protocol.
4. Validate immutable package custody and the whole graph at admission and at the
   existing execution fence. Check revocation again before consequential effects.
   Preserve command/allowed-path confinement and independent verification. Skill
   prose cannot replace these controls. Never substitute another Skill or model.
5. Retain the binding through candidate custody, Result, Proof, Needs You and owner
   publication review. Qualification evidence and Work verification remain separate.
6. Keep Relay Skill advertisements as explicitly public metadata attached to a future
   versioned contract. Relay identity and capabilities grant neither installation
   nor Work authority. Do not expose private Skill identities through discovery.
7. Qualify the new protocol and persistence deterministically, including concurrent
   update/revocation, duplicate delivery, reconnect, fail/recovery, UNKNOWN, budget
   exhaustion and cross-owner attacks. Compute a new FactoryVersion only after these
   execution-relevant boundaries stabilize. Old alpha evidence remains historical.

Accounting must retain separate model, Factory, external API and future Skill
acquisition budgets. Installation and qualification consume no paid model operations
in this workstream. Live canaries require a later explicit decision only if a gap
cannot be closed deterministically.

Rollback disables new Skill-aware admissions while preserving existing Work identity
and evidence. It does not rewrite admitted versions, re-enable revoked evidence,
replay ambiguous paid requests or redirect work to a different Skill. In-flight
recovery follows the existing Factory authority/fencing rules.

## Initial deeper qualification cohort

These are candidates, not Platform Qualified claims. All retain their existing
upstream source and license records in the generated catalog.

| Canonical Skill | Reason to qualify | Overlap to review | Main qualification gap |
| --- | --- | --- | --- |
| figure-it-out | repository and requirement analysis | architect, how | bounded reads and routing |
| principle-sequence-verifiable-units | bounded implementation sequence | tdd, code-structure | executable workflow contract |
| tdd | test-driven implementation | principle-test-behavior-not-implementation | command and filesystem confinement |
| thermo-nuclear-code-quality-review | independent code review | greploop, interrogate | protected corpus and reviewer separation |
| api-and-interface-design | API contracts and retries | code-structure | UNKNOWN, idempotency and owner checks |
| deprecation-and-migration | migration recovery | factory-ship | concurrency and roll-forward evidence |
| frontend-ui-engineering | complete UI states | visual-edit | accessibility and failure-state browser corpus |
| security-and-hardening | security review | blast-radius | adversarial behavior and effect denial |
| ci-cd-and-automation | reproducible checks | fix-ci | no credential/publication escalation |
| create-verification-skill | reusable qualification | evidence-driven-testing | verifier isolation and evidence integrity |

Observability and performance adaptations remain indexed and should follow this
cohort after their contracts and privacy/resource cases are reviewed. No rejected
PR #5 import is reopened by this proposal.

## Marketplace readiness

The foundation reserves publisher, provenance, immutable identity, trust and scope
fields. Future package signatures bind publisher signing identity to the package
digest; they do not prove behavioral qualification. Publisher key rotation and
revocation must preserve old signatures and history. A publisher cannot promote
its own Skill to platform trust.

Public submission requires separate publisher authentication, provenance/license
review, artifact custody, signature verification, independent qualification and
explicit listing approval. Reviews/ranking can aid discovery, never admission.
Payments, revenue, organizations, automated updates, live connector installation,
remote signing and unrestricted Relay federation remain unavailable.

Ambiguous external publication/payment outcomes must be UNKNOWN and reconciled by
idempotency key; no blind retry. Compromise response freezes installations/resolution,
revokes versions/publishers/dependencies/evidence and identifies affected Work while
preserving proof. Feedback may create reviewed improvement proposals, never mutate
published packages. Private evaluation data remains owner-scoped.
