# Lauren and Matt upstream review

Checked on November 6, 2026. This review follows the merged 2.7.0 source
refresh. It checks Lauren Tan's original pstack, its Jstack distribution port,
and Matt Pocock's skills. Matt was referenced in earlier comparison notes but
had no distribution manifest in Skillz; this is the first reviewed import.

## Source state

| Source | Latest checked revision | Result |
| --- | --- | --- |
| [Lauren's original pstack](https://github.com/cursor/plugins/tree/main/pstack) | `2776ddd2355d6d6c8747d3964600f28daf62f049` | Unchanged from the revision reviewed in PR #10. |
| [Jstack port](https://github.com/michael-denyer/pstack-claude) | `d88063f3355a5ecff0e6dbb890a11bab4b08bc2e`, 0.9.130 | Already current in the merged 2.7.0 import. |
| [Matt Pocock](https://github.com/mattpocock/skills) | `4ae2317ddb22b046e26455e4f9c9b3aaaf62212d` | Review all 39 source entrypoints; adapt three and record the other 36 decisions. |

The [aggregate receipts](../vendor/upstream-review.json) identify this review's
three-source scope. Other sources retain their November 5 check dates.
The [Matt manifest](../vendor/mattpocock.json) records every source path,
decisions, source hashes, and the complete MIT license hash. The source is
copyright 2026 Matt Pocock.

## Selection

The collection already covers architecture, code review, planning, handoffs,
TDD, and governed delivery. Avoid duplicate routers or new tracker conventions
unless an actual project needs them.

| Upstream skill | Decision and reason |
| --- | --- |
| `ask-matt` | Defer. Source-specific router; Skillz already routes its own collection. Start with `poteto-help`. |
| `chief-of-staff` | Defer. In-progress long-running orchestration and wiki conventions are not needed by the selected workflows. Start with `factory`, `swarm`. |
| `claude-handoff` | Defer. Automatic background-agent launch and a Claude-specific CLI overlap the existing handoff. Start with `handoff`. |
| `code-review` | Defer. Overlaps the existing correctness and maintainability review workflows. Start with `thermos`. |
| `codebase-design` | Defer. Deep-module design overlaps existing architecture and boundary guidance. Start with `architect`, `code-structure`. |
| `diagnosing-bugs` | Adapt. A concrete diagnosis loop beyond the existing testing and root-cause principles. |
| `domain-modeling` | Adapt. Business vocabulary and context modeling beyond the existing code-structure principle. |
| `git-guardrails-claude-code` | Defer. Agent hook installation and global/project configuration need a separate explicit setup task. |
| `grill-me` | Defer. Interview alias duplicates the existing scoped planning route. Start with `figure-it-out`. |
| `grill-with-docs` | Defer. Interview alias and documentation side effects overlap scoped planning and the selected domain workflow. Start with `figure-it-out`, `domain-modeling`. |
| `grilling` | Defer. An additional relentless interview protocol is unnecessary alongside existing product decision rules. Start with `figure-it-out`. |
| `handoff` | Defer. Name collision with the verified continuity workflow already imported. Start with `handoff`. |
| `implement` | Defer. Implementation router overlaps the current delivery workflow. Start with `poteto-mode`. |
| `implement-spec` | Defer. Adds a parallel spec/ticket lifecycle and tracker configuration requirement. Start with `poteto-mode`. |
| `improve-codebase-architecture` | Defer. Architecture scanning and alternatives already have focused workflows. Start with `architect`, `principle-exhaust-the-design-space`. |
| `loop-me` | Defer. In-progress workflow design overlaps configured factory planning. Start with `factory`. |
| `migrate-to-shoehorn` | Defer. A specific testing dependency migration is not currently required. |
| `pr` | Defer. PR-body guidance already lives in the writing and reviewability workflows. Start with `technical-writing`, `make-pr-easy-to-review`. |
| `prototype` | Defer. Existing prototype playbook and visual planning cover bounded experiments. Start with `poteto-mode`, `visual-plan`. |
| `research` | Defer. Primary-source research is already covered; do not add mandatory background delegation. Start with `read-the-damn-docs`. |
| `retro` | Defer. Session learning and enforcement are already covered. Start with `reflect`, `correct`. |
| `scaffold-exercises` | Defer. Course scaffolding and its CLI/commit conventions are outside SellerFi delivery. |
| `setup-matt-pocock-skills` | Defer. A second repository setup and tracker convention is unnecessary for the standalone adaptations. |
| `setup-pre-commit` | Defer. Imposes Husky and Prettier; existing CI guidance follows each project's actual toolchain. Start with `ci-cd-and-automation`. |
| `setup-ts-deep-modules` | Defer. In-progress enforcement imposes a TypeScript layout and dependency-cruiser setup; defer to a project request. Start with `code-structure`. |
| `software-factory` | Defer. In-progress glossary tied to a distinct factory design; retain the current governed factory workflows. Start with `factory`, `mission-control-delivery`. |
| `tdd` | Defer. Name collision with the current Jstack test-first workflow. Start with `tdd`. |
| `teach` | Defer. Name collision with the current Jstack teaching workflow; do not replace it. Start with `teach`. |
| `to-questionnaire` | Defer. Useful for a named stakeholder discovery task, but no such task is currently needed. |
| `to-spec` | Defer. Tracker publication, extensive user-story templates, and a second spec lifecycle need a specific project request. Start with `figure-it-out`, `architect`. |
| `to-tickets` | Defer. Tracker writes and mandatory ticket conventions add another planning lifecycle. Start with `principle-sequence-verifiable-units`. |
| `triage` | Defer. Configured product intake and PR triage already exist; label changes and comments require separate authority. Start with `factory-collect`, `factory-review-prs`. |
| `wait-what` | Defer. Plain-language restatement overlaps the existing explanation workflow. Start with `bro`. |
| `wayfinder` | Defer. A persistent issue-based decision map is more process than the current V1 needs. Start with `figure-it-out`, `show-me-your-work`. |
| `wizard` | Defer. Interactive shell wizards for human-only infrastructure steps need an actual setup task and script validation. |
| `writing-beats` | Defer. In-progress article composition is outside the engineering collection. |
| `writing-for-agents` | Adapt. Portable instruction authoring beyond general technical prose. |
| `writing-fragments` | Defer. In-progress creative writing capture is outside the engineering collection. |
| `writing-shape` | Defer. In-progress article structure workflow is outside the engineering collection. |

Alternatives identify an existing starting point, not identical behavior.
In-progress source workflows remain upstream. Deferred helpers were not
executed or comprehensively security-audited.

## Adaptations

The three adaptations work independently and retain the full MIT notice.
They use normal discovery, as their source entrypoints and UI metadata do.
No source helper, hook, setup configuration, tracker write, or service
dependency is imported.

- `domain-modeling` covers business vocabulary, rules, and context boundaries.
  It complements `principle-model-the-domain`, which shapes code structures.
  Existing glossary and ADR conventions win over fixed filenames. Proposed
  scenarios remain questions, and only approved decisions become accepted
  records. A terminology task does not authorize code or data migration.
- `diagnosing-bugs` preserves Matt's central method: build a symptom-specific
  failure signal, minimize it, test explanations, and verify the original case.
  It allows the code reading needed to construct a probe. It removes rigid
  hypothesis and stress-loop quotas, uses bounded resources, and distinguishes
  intermittent evidence from proof. Production probes, trace capture, and
  destructive experiments require actual environment authority.
- `writing-for-agents` keeps precise discovery, progressive disclosure, clear
  completion criteria, and a single source for maintained instructions. It
  avoids blanket claims about the effect of negative wording and preserves
  concrete privacy and authorization prohibitions. Automatic discovery is the
  default for new skills unless explicitly changed by the user; existing
  policies remain intact and runtime flags are client-specific.

The removed supporting resources are unnecessary for the self-contained
adaptations. The source paths and hashes remain in the manifest for review.

## Distribution changes

Package metadata moves from 2.7.0 to 2.8.0, and the canonical inventory grows
from 109 to 112 skills. This does not publish a release or install user skills.

Five Jstack descriptions are shortened to preserve the unchanged 8,000-byte
discovery limit: `create-verification-skill`, `make-pr-easy-to-review`,
`no-comments`, `principle-encode-lessons-in-structure`, and
`principle-exhaust-the-design-space`. Their workflow bodies are unchanged.
The corresponding overrides live in the vendor generator so a refresh
reproduces them. The 112 descriptions use 7,988 bytes.

Lauren's source revisions, imported workflows, and runtime helpers remain at
the checked versions. The description reductions are local packaging changes,
not a new upstream release.

## Verification and limits

All 185 portable Python tests pass, including source inventory, license,
catalog, metadata, local references, and standalone installation of each new
adaptation. The new directories have no references to absent sibling skills
or source setup files.

Final validation and hosted-check results are recorded in the PR. Static
package checks do not qualify model behavior or production debugging. Catalog
entries remain `UNTRUSTED` and `NOT_EVALUATED`.

All 47 Matt source/license hashes match the pinned checkout. Each new skill
passes the installed skill-creator validator, and all 112 frontmatter blocks
parse as YAML. A fresh project installation contains 112 shared skills,
112 Claude skills, and four companion agents; a second install skips current
copies. Catalog, release metadata, compilation, and whitespace checks pass.

The complete local suite returned 192 passed and 18 recorder-test failures.
Those tests require the missing FFmpeg `ass` filter and process inspection
blocked by the sandbox. Recorder code and tests are unchanged. No imported
runtime helper changed, so the previous refresh's Bun suite was not rerun.

## Manual refresh

1. Fetch the three source repositories into separate review checkouts and
   resolve full commit SHAs. Compare Lauren's original source and the port
   before changing the distribution input.
2. Inventory Matt's entrypoints and compare the recorded source hashes,
   including supporting resources before considering any helper import.
3. Update the curated workflows deliberately, preserving license notices,
   existing policy, local conventions, and action authority.
4. Update the Matt manifest, source metadata, aggregate dates and scope, and
   this selection review. Account for added, removed, and renamed skills.
5. Regenerate the catalog and run package, reference, installer, release, and
   source checks through the isolated branch and PR workflow.
