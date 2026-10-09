# Addy Osmani skills integration review

## Scope and selection

This review inventories all 25 skills in
[addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) at commit
[1401c8b8030e023baeebb31781a6653fe8e93026](https://github.com/addyosmani/agent-skills/commit/1401c8b8030e023baeebb31781a6653fe8e93026)
and examines the seven selected workflows in detail. The source uses the MIT
license, copyright 2025 Addy Osmani. The manifest in
[vendor/addyosmani.json](../vendor/addyosmani.json) records the revision, source
file hashes, adaptations, and alternatives for every excluded skill.

The supplied video transcript argues for selecting methods by the task's stakes
instead of loading three complete frameworks. This integration follows that
principle. The transcript is context, not evidence for repository contents,
technical claims, current affiliations, or popularity figures. Matt Pocock's
collection was mentioned as comparison context and is not imported here.

Skillz already has 85 skills, including Jstack's pstack-derived investigation
and verification workflows. These seven additions fill specialist gaps rather
than replace the existing lifecycle:

| Upstream skill | Decision and reason |
| --- | --- |
| api-and-interface-design | Adapt: public contracts, compatibility, pagination, concurrency, and duplicate-safe effects. |
| ci-cd-and-automation | Adapt: pipeline design and artifact promotion beyond repairing a failing check. |
| deprecation-and-migration | Adapt: consumers and persistent data that cannot all change in one deployment. |
| frontend-ui-engineering | Adapt: interaction states, accessibility, async behavior, and rendered verification. |
| observability-and-instrumentation | Adapt: diagnostic signals, cardinality, privacy, and collector verification. |
| performance-optimization | Adapt: measured bottlenecks and comparable performance evidence. |
| security-and-hardening | Adapt: threat boundaries, abuse cases, dependency review, and scoped findings. |
| using-agent-skills | Exclude: poteto-mode already selects the smallest applicable workflow. |
| interview-me | Defer the prescriptive interview style; figure-it-out supports investigation and clarification. |
| idea-refine | Exclude overlapping exploration; use figure-it-out for uncertain scope. |
| spec-driven-development | Defer the mandatory PRD lifecycle; figure-it-out and architect cover scoped planning and contracts. |
| constraint-driven-development | Defer a new CONSTRAINTS.md workflow; use repository checks, create-verification-skill, and mission-control-delivery. |
| planning-and-task-breakdown | Exclude overlapping planning; use figure-it-out and principle-sequence-verifiable-units. |
| incremental-implementation | Exclude overlap with principle-sequence-verifiable-units. |
| context-engineering | Exclude overlap with principle-guard-the-context-window and recall. |
| source-driven-development | Exclude overlap with read-the-damn-docs. |
| doubt-driven-development | Exclude overlap with interrogate, blast-radius, and arena; do not add automatic delegation. |
| browser-testing-with-devtools | Exclude connector-specific overlap with evidence-driven-testing and create-verification-skill. |
| debugging-and-error-recovery | Exclude overlap with principle-fix-root-causes and fix-ci. |
| code-review-and-quality | Exclude overlap with thermo-nuclear-code-quality-review and make-pr-easy-to-review. |
| code-simplification | Exclude overlap with deslop and principle-subtract-before-you-add. |
| git-workflow-and-versioning | Exclude overlap with new-feature and make-pr-easy-to-review. |
| documentation-and-adrs | Exclude overlap with technical-writing and why. |
| shipping-and-launch | Exclude overlap with factory-ship and mission-control-delivery. |
| test-driven-development | Exclude overlap with tdd and principle-test-behavior-not-implementation. |

Alternatives indicate where to start, not identical behavior. The deferred
interview, PRD, and constraints conventions remain available upstream if a
project explicitly chooses them later.

## Adaptation decisions

These are reviewed rewrites with provenance, not byte-for-byte vendoring. Each
skill has a concise entrypoint, narrowly scoped description, Codex UI metadata,
and the complete upstream MIT notice. Substantial conditional detail lives in
local references. Each directory works alone, without repository-root
checklists, sibling skills, upstream hooks, or personas.

The source's useful principles remain: contracts before implementation,
measure before optimizing, observe production behavior, migrate consumers
deliberately, and prove outcomes. Generic tutorials, repeated rationalization
tables, and mandatory ceremony were removed. The adaptations preserve existing
authorization and avoid asking again for actions already granted by the user.

Specific improvements:

- API contracts scope idempotency keys to tenant and operation, authorize
  replays, distinguish unknown outcomes, and reconcile the crash window between
  provider success and local acknowledgment. A local uniqueness constraint
  alone cannot guarantee one external effect. Strict decoders and enum consumers
  mean an additive change is not automatically compatible.
- CI guidance derives commands and versions from the repository instead of
  copying a Node-specific example. Untrusted PRs cannot execute with deployment
  credentials. Artifact identity, skipped required checks, and deployment
  concurrency are explicit. See
  [GitHub's secure-use guidance](https://docs.github.com/en/actions/reference/security/secure-use).
- Migration guidance removes claims that additions are always safe and every
  migration must have a safe down command. It checks lock behavior, concurrent
  backfill writes, reconciliation, and irreversible recovery limits. See
  [PostgreSQL's ALTER TABLE documentation](https://www.postgresql.org/docs/current/sql-altertable.html).
- UI guidance covers stale requests, permission states, recoverable forms,
  authoritative confirmation for payments, and complete modal behavior.
  [WCAG 2.2](https://www.w3.org/TR/WCAG22/) replaces the older 2.1-only reference
  as the proposed baseline for projects without an agreed target.
- Observability validates caller-supplied correlation fields, bounds metric
  dimensions, distinguishes retries from operations, and tests exporter loss
  and redaction. Operational logs do not replace financial ledgers or audits.
- Performance guidance separates field data from lab results and requires
  comparable workloads. Synthetic interaction timing cannot establish production
  INP. Cache keys and invalidation must preserve tenant and permission boundaries.
- Security guidance avoids universal legal consent claims, arbitrary mandatory
  rate limits, and blanket approval gates for already-authorized changes.
  It includes replay, tenant access, race-prone filesystem operations, and
  recovery-aware retention without promising impossible backup erasure.

## Routing budget and change scope

The collection grows from 85 to 92 skills. Its descriptions use 7,389 bytes;
the existing 8,000-byte budget remains unchanged. The 24 Builder.io descriptions were shortened, and
their generator was updated to match. Their workflow bodies, references,
permissions, and UI metadata are unchanged. This is the only existing skill
content adjustment required to keep discovery within budget.

All package manifests move together to 2.4.0. That is a package metadata change;
it does not by itself publish a release or install skills into the user's home.
No new connector or global configuration is added.

## Scenario inspection

The following are manual instruction walkthroughs, not model evaluations or
runtime integration tests. Each case was checked against the adapted text.

| Request or failure | Expected guidance found in the adaptation |
| --- | --- |
| Change a button's color | Focused rendered check; no mandatory PRD, audit, or full lifecycle. |
| Payment timed out after provider success | Keep outcome unknown, reconcile using the stable provider key, do not charge again blindly. |
| Two tenants use the same idempotency key | Scope the key and authorize replay; no cross-tenant response reuse. |
| Backfill races with a customer's profile edit | Use conditional/versioned writes; do not overwrite the newer value. |
| Drop a column and promise a code revert will restore it | State recovery limits and require evidence that old readers/writers are gone. |
| Fork PR contains a malicious install script | Run untrusted checks without production secrets; do not use privileged events to execute it. |
| Metrics label includes every payment ID | Move unbounded identifiers out of metric dimensions and verify series growth. |
| Lighthouse looks faster on one local run | Repeat comparable measurements and do not claim a field INP improvement. |
| Security fix is already authorized | Complete scoped fixes; do not add a redundant permission gate. |
| UI mutation receives only an asynchronous acknowledgment | Keep pending until authoritative confirmation or a status reconciliation. |

## Validation and limits

The portable suite passes all 83 tests. All seven adaptations also pass the
skill-creator frontmatter validator. The package suite checks inventory,
provenance fields, complete license hashes,
local links, metadata, versions, and the description budget. New installation
tests copy each adaptation by itself through the real portable installer,
remove its source, and verify that every file and local reference survives.
The suite also checks that shortened Builder.io descriptions match their
refresh generator.

Use the portable suite on hosts without recorder dependencies:

```bash
python3 -m pytest tests -q --ignore=tests/test_evidence.py
python3 -m compileall -q scripts skills
python3 scripts/check_release.py v2.4.0
git diff --check
```

The initial full-suite run on the development Mac had 73 passes and 17 recorder
failures because the installed FFmpeg lacks the `ass` filter and the sandbox
blocks process inspection. Recorder code was not changed. CI runs the portable
suite. Neither these checks nor the manual walkthroughs prove live payment,
deployment, migration, accessibility, or security behavior in a consuming app.

## Refresh procedure

1. Fetch the upstream repository and compare the recorded commit to a proposed
   new revision. Check the license and the complete skill inventory first.
2. Review changes in selected skills and their supporting resources. Revisit
   excluded skills only when they fill a demonstrated gap or the user requests
   that workflow. The manifest's source hashes describe upstream files, not
   the adapted output.
3. Apply useful changes manually to the canonical Skillz directories. Preserve
   the corrections above and self-contained references. Do not run a raw copy
   over an adaptation or invent an automated refresh command.
4. Update the source revision, source file hashes, selection record, and this
   review together. Retain the upstream MIT notice in each directory.
5. Validate changed skills, rerun relevant scenario inspections, and run the
   package and installation checks before publishing the update.

The checked-in adaptations are the source of truth. A source checkout alone
does not regenerate these editorial changes; Git history records them.
