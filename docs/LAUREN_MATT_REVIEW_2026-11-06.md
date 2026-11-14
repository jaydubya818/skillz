# Lauren and Matt upstream review

Checked on November 6, 2026, after the merged 2.7.0 source refresh.
The user requested Matt's complete collection with distinct names.

## Source state

| Source | Latest checked revision | Result |
| --- | --- | --- |
| [Lauren's original pstack](https://github.com/cursor/plugins/tree/main/pstack) | `2776ddd2355d6d6c8747d3964600f28daf62f049` | Unchanged from PR #10. |
| [Jstack port](https://github.com/michael-denyer/pstack-claude) | `d88063f3355a5ecff0e6dbb890a11bab4b08bc2e`, 0.9.130 | Already current in 2.7.0. |
| [Matt Pocock](https://github.com/mattpocock/skills) | `4ae2317ddb22b046e26455e4f9c9b3aaaf62212d` | All 39 skills and their supporting resources imported. |

The [aggregate receipts](../vendor/upstream-review.json) identify this review's
three-source scope. Other sources retain their November 5 check dates.
The [Matt manifest](../vendor/mattpocock.json) records source paths, local names,
source and output hashes, invocation policies, and experimental status. Each
skill retains the complete MIT notice, copyright 2026 Matt Pocock.

## Complete inventory

All 39 names use the `mattpocock-` prefix, including names without an existing
collision. Existing `tdd`, `handoff`, `teach`, factory, and review workflows keep
their names and behavior. The initial three unprefixed Matt adaptations in this
PR are replaced by the complete namespaced ports.

| Upstream name | Local skill | Source group | Invocation and status |
| --- | --- | --- | --- |
| `ask-matt` | [`mattpocock-ask-matt`](../skills/mattpocock-ask-matt/SKILL.md) | engineering | Explicit only |
| `chief-of-staff` | [`mattpocock-chief-of-staff`](../skills/mattpocock-chief-of-staff/SKILL.md) | in-progress | Explicit only; in progress |
| `claude-handoff` | [`mattpocock-claude-handoff`](../skills/mattpocock-claude-handoff/SKILL.md) | in-progress | Explicit only; in progress |
| `code-review` | [`mattpocock-code-review`](../skills/mattpocock-code-review/SKILL.md) | engineering | Automatic discovery |
| `codebase-design` | [`mattpocock-codebase-design`](../skills/mattpocock-codebase-design/SKILL.md) | engineering | Automatic discovery |
| `diagnosing-bugs` | [`mattpocock-diagnosing-bugs`](../skills/mattpocock-diagnosing-bugs/SKILL.md) | engineering | Automatic discovery |
| `domain-modeling` | [`mattpocock-domain-modeling`](../skills/mattpocock-domain-modeling/SKILL.md) | engineering | Automatic discovery |
| `git-guardrails-claude-code` | [`mattpocock-git-guardrails-claude-code`](../skills/mattpocock-git-guardrails-claude-code/SKILL.md) | misc | Automatic discovery |
| `grill-me` | [`mattpocock-grill-me`](../skills/mattpocock-grill-me/SKILL.md) | productivity | Explicit only |
| `grill-with-docs` | [`mattpocock-grill-with-docs`](../skills/mattpocock-grill-with-docs/SKILL.md) | engineering | Explicit only |
| `grilling` | [`mattpocock-grilling`](../skills/mattpocock-grilling/SKILL.md) | productivity | Automatic discovery |
| `handoff` | [`mattpocock-handoff`](../skills/mattpocock-handoff/SKILL.md) | productivity | Explicit only |
| `implement` | [`mattpocock-implement`](../skills/mattpocock-implement/SKILL.md) | engineering | Explicit only |
| `implement-spec` | [`mattpocock-implement-spec`](../skills/mattpocock-implement-spec/SKILL.md) | engineering | Explicit only |
| `improve-codebase-architecture` | [`mattpocock-improve-codebase-architecture`](../skills/mattpocock-improve-codebase-architecture/SKILL.md) | engineering | Explicit only |
| `loop-me` | [`mattpocock-loop-me`](../skills/mattpocock-loop-me/SKILL.md) | in-progress | Explicit only; in progress |
| `migrate-to-shoehorn` | [`mattpocock-migrate-to-shoehorn`](../skills/mattpocock-migrate-to-shoehorn/SKILL.md) | misc | Automatic discovery |
| `pr` | [`mattpocock-pr`](../skills/mattpocock-pr/SKILL.md) | engineering | Automatic discovery |
| `prototype` | [`mattpocock-prototype`](../skills/mattpocock-prototype/SKILL.md) | engineering | Automatic discovery |
| `research` | [`mattpocock-research`](../skills/mattpocock-research/SKILL.md) | engineering | Automatic discovery |
| `retro` | [`mattpocock-retro`](../skills/mattpocock-retro/SKILL.md) | engineering | Explicit only |
| `scaffold-exercises` | [`mattpocock-scaffold-exercises`](../skills/mattpocock-scaffold-exercises/SKILL.md) | misc | Automatic discovery |
| `setup-matt-pocock-skills` | [`mattpocock-setup-matt-pocock-skills`](../skills/mattpocock-setup-matt-pocock-skills/SKILL.md) | engineering | Explicit only |
| `setup-pre-commit` | [`mattpocock-setup-pre-commit`](../skills/mattpocock-setup-pre-commit/SKILL.md) | misc | Automatic discovery |
| `setup-ts-deep-modules` | [`mattpocock-setup-ts-deep-modules`](../skills/mattpocock-setup-ts-deep-modules/SKILL.md) | in-progress | Explicit only; in progress |
| `software-factory` | [`mattpocock-software-factory`](../skills/mattpocock-software-factory/SKILL.md) | in-progress | Explicit only; in progress |
| `tdd` | [`mattpocock-tdd`](../skills/mattpocock-tdd/SKILL.md) | engineering | Automatic discovery |
| `teach` | [`mattpocock-teach`](../skills/mattpocock-teach/SKILL.md) | productivity | Explicit only |
| `to-questionnaire` | [`mattpocock-to-questionnaire`](../skills/mattpocock-to-questionnaire/SKILL.md) | productivity | Explicit only |
| `to-spec` | [`mattpocock-to-spec`](../skills/mattpocock-to-spec/SKILL.md) | engineering | Explicit only |
| `to-tickets` | [`mattpocock-to-tickets`](../skills/mattpocock-to-tickets/SKILL.md) | engineering | Explicit only |
| `triage` | [`mattpocock-triage`](../skills/mattpocock-triage/SKILL.md) | engineering | Explicit only |
| `wait-what` | [`mattpocock-wait-what`](../skills/mattpocock-wait-what/SKILL.md) | productivity | Explicit only |
| `wayfinder` | [`mattpocock-wayfinder`](../skills/mattpocock-wayfinder/SKILL.md) | engineering | Explicit only |
| `wizard` | [`mattpocock-wizard`](../skills/mattpocock-wizard/SKILL.md) | engineering | Automatic discovery |
| `writing-beats` | [`mattpocock-writing-beats`](../skills/mattpocock-writing-beats/SKILL.md) | in-progress | Explicit only; in progress |
| `writing-for-agents` | [`mattpocock-writing-for-agents`](../skills/mattpocock-writing-for-agents/SKILL.md) | productivity | Automatic discovery |
| `writing-fragments` | [`mattpocock-writing-fragments`](../skills/mattpocock-writing-fragments/SKILL.md) | in-progress | Explicit only; in progress |
| `writing-shape` | [`mattpocock-writing-shape`](../skills/mattpocock-writing-shape/SKILL.md) | in-progress | Explicit only; in progress |

## Integration changes

- Namespaced command references, skill-loader arguments, and UI prompts route
  to Matt's versions. UI display names identify Matt Pocock.
- All supporting templates, references, shell scripts, and the dependency-cruiser
  config are included. Project-output example links render as paths rather than
  broken package links. Skill frontmatter is normalized for portable parsing.
  A wizard prompt variable uses braces to resolve ShellCheck SC1087.
- Preserved all 24 explicit-only policies, including adding the missing Codex
  UI metadata for the source's explicit-only software-factory skill. The other
  15 workflows retain automatic discovery. Installing files runs no setup.
- Added host tool mappings and a sequential fallback when delegation is not
  available or permitted. User scope and repository rules govern tracker writes,
  publishing, cleanup, configuration, schedules, and messages.
- Marked all eight source `in-progress` workflows as experimental. Their presence
  does not qualify them for unattended use. Claude hook and background-agent
  workflows remain Claude-specific.
- Added targeted notes for isolated prototypes, bounded debugging probes, real
  crash and transaction boundaries, approved domain decisions, credential
  destinations, existing hook/config preservation, and development-only fixtures.
- Replaced the instruction-authoring mechanics reference with client-specific
  invocation guidance. Existing safety prohibitions remain valid; normal
  automatic discovery remains the default when authoring a new skill.

Matt's engineering flows may need tracker and domain conventions. Run
`mattpocock-setup-matt-pocock-skills` only for a requested configuration task;
reuse an existing compatible setup. Hook matching is a best-effort convenience,
not a shell security boundary. The wizard's Stripe stage is an authoring example
that must be replaced. Do not run templates as a collection installer.

## Packaging

Package metadata remains 2.8.0 for this unmerged PR. The collection grows from
109 to 148 skills. Five Jstack discovery descriptions remain shortened in the
existing generator overrides, with their workflow bodies unchanged.

The 8,000-byte Codex discovery check now measures automatically discoverable
skills, excluding those whose Codex policy sets `allow_implicit_invocation: false`.
Every description, including explicit-only entries, still has a 220-byte cap.
Automatic descriptions use 7,943 bytes; all descriptions use 9,608 bytes. No
existing skill's invocation policy changes to make the budget pass.

## Verification and limits

All 229 portable Python tests pass. Verification covers all 39 packaged skills,
license retention, source and output
hashes, portable YAML, local links, namespaced references, invocation policies,
standalone file installation, catalog provenance, shell syntax, ShellCheck at
warning severity, and synthetic
Claude-hook inputs. The vendor generator must reproduce the tree from the
clean pinned checkout. A fresh project install and repeat install check shared
and Claude skill copies plus the four existing companion agents.

Static package checks do not qualify all model behavior, third-party services,
live credentials, or human-driven setup. Catalog entries remain `UNTRUSTED` and
`NOT_EVALUATED`. Final test counts and hosted checks are recorded in the PR.
The generic skill-creator validator accepts the 15 automatic skills. Its
allowlist rejects `disable-model-invocation` and `argument-hint` on the other
24; these are preserved client extensions, checked by package tests and YAML
parsing rather than removed to satisfy that validator.

The previous complete local suite had 192 passes and 18 recorder failures from
the missing FFmpeg `ass` filter and sandbox restrictions on process inspection.
Recorder code and tests remain unchanged. This expansion tests the newly bundled
helpers without running live setup or installing hooks on this computer.

## Manual refresh

1. Fetch the source repositories into separate clean review checkouts and resolve
   full commit SHAs. Compare Lauren's original source and the Jstack port before
   changing distribution inputs.
2. Review Matt's complete skill inventory and supporting resources. Account for
   source additions, removals, invocation changes, and experimental status.
3. Update the pinned revision and reviewed transformations in
   [vendor_mattpocock.py](../scripts/vendor_mattpocock.py). Preserve the namespace,
   MIT notices, user authority, and existing project conventions.
4. Run `python3 scripts/vendor_mattpocock.py /path/to/pinned/checkout`. It refuses
   the wrong revision, a dirty source checkout, an unexpected inventory, or a
   mismatch against recorded source hashes before replacing generated folders. Review and update the source-hash
   receipt when intentionally advancing to a new upstream revision.
5. Update aggregate receipts, package metadata, and this review. Regenerate the
   catalog and run package, helper, installer, and release checks before pushing.
