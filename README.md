# Skillz

Production-minded Agent Skills for Claude Code, Codex, and Mission Control.

This repository packages 61 skills behind one canonical `skills/` tree:

- 8 core delivery, architecture, evidence, review, and writing skills
- 30 pstack workflows for planning, implementation, review, and operations
- 23 pstack engineering principles

Every skill uses portable
[Agent Skills](https://agentskills.io/specification) frontmatter. Claude Code
and Codex read the same `SKILL.md` bodies, while harness-specific presentation
metadata lives beside those files. Mission Control governance metadata is kept
inside the standard `metadata` map instead of forking the skill format.

This is a mixed-source collection. Read [Licensing and attribution](LICENSES.md)
before redistributing an individual skill.

## Why this repository exists

Agent workflows become unreliable when each harness has a different copy,
skills silently overwrite one another, or an orchestration prompt is mistaken
for permission to publish, merge, deploy, or spend money.

Skillz provides:

- one source of truth for Claude Code, Codex, and Agent Skills-compatible tools
- explicit activation descriptions instead of loading every skill into context
- a Mission Control delivery contract from mission to release evidence
- a pinned, reproducible pstack import with source attribution
- tightened authority boundaries for external writes and product decisions
- conflict-safe user and project installers
- package, link, manifest, installer, and workflow tests

## Start here

For non-trivial software-factory work:

1. Load [`mission-control-delivery`](skills/mission-control-delivery/SKILL.md)
   when Mission Control or another governed execution system owns the work.
2. Use [`poteto-mode`](skills/poteto-mode/SKILL.md) to select the smallest
   applicable workflow.
3. Load only the specialist skills that match the task.
4. Verify the exact candidate before declaring the work complete.
5. Treat publication, merge, deployment, destructive cleanup, external
   communication, and spending as separate authority boundaries.

Do not preload all 61 skills. Descriptions are the routing layer; the selected
`SKILL.md` files are the execution layer.

## Quick installation

```bash
git clone https://github.com/jaydubya818/skillz.git
cd skillz

# Always inspect the user-level change first.
python3 scripts/install_skills.py --all --dry-run

# Install for both Claude Code and Codex.
python3 scripts/install_skills.py --all
```

If a destination already contains a different skill with the same name, the
installer stops before writing anything. Review the conflict, then explicitly
choose replacement if the collection should win:

```bash
python3 scripts/install_skills.py --all --replace
```

Replacement moves the old directory to `<skill>.backup`, then `.backup-2`, and
so on. An already-current copy is skipped, making repeated installs idempotent.

## Installation options

### User-level Claude Code installation

```bash
python3 scripts/install_skills.py --claude --dry-run
python3 scripts/install_skills.py --claude
```

Destination: `~/.claude/skills/`

Claude Code can also load a checkout directly while developing the plugin:

```bash
claude --plugin-dir /path/to/skillz
```

The Claude plugin manifest is
[`.claude-plugin/plugin.json`](.claude-plugin/plugin.json).

### User-level Codex installation

```bash
python3 scripts/install_skills.py --codex --dry-run
python3 scripts/install_skills.py --codex
```

Destination: `~/.codex/skills/`

Each skill includes `agents/openai.yaml` for its Codex display name, concise
description, and explicit invocation prompt. The collection manifest is
[`.codex-plugin/plugin.json`](.codex-plugin/plugin.json).

### Project-scoped installation

Copy the skills into both harness directories for one project:

```bash
python3 scripts/install_skills.py \
  --all \
  --project /path/to/project
```

Or keep this checkout as the canonical source and create links:

```bash
python3 scripts/install_skills.py \
  --all \
  --mode symlink \
  --project /path/to/project
```

Project installs target `.claude/skills/` and `.codex/skills/`. Copy mode is
portable. Symlink mode is better for active skill development because edits in
this checkout are immediately visible to both harnesses.

## Mission Control integration

[`mission-control-delivery`](skills/mission-control-delivery/SKILL.md) maps
agent work onto this lineage:

```text
Mission
└── WorkOrder
    └── Task
        └── Attempt
            ├── decisions and run log
            ├── evidence tied to an exact candidate
            ├── pull request or reviewed artifact
            └── release handoff
```

The skill is a reasoning and handoff contract. It does not grant permission to
claim work, change Mission Control state, publish a context package, merge a
pull request, deploy a release, or spend money. API-specific Mission Control
skills and the active approval policy remain authoritative for those actions.

For Mission Control builds with the portable Agent Skills compatibility layer,
the local scanner checks these roots in deterministic order:

1. `skills/`
2. `.agents/skills/`
3. `.claude/skills/`
4. `.codex/skills/`
5. `.cursor/skills/`

Identical same-name installations collapse to one skill. Different definitions
with the same name stop discovery and report both paths. Repository discovery
does not publish, activate, or grant authority by itself.

The recommended standing repository policy is:

```markdown
For non-trivial work, start with mission-control-delivery. Then use
poteto-mode to select a workflow and load only the applicable specialist
skills. System, user, Mission Control, and repository instructions override
skill guidance. External writes require explicit task authority.
```

## Recommended routes

| Work | Recommended skill sequence |
| --- | --- |
| Feature | `mission-control-delivery` → `poteto-mode` → `new-feature` → `architect` → targeted implementation and evidence |
| Bug fix | `mission-control-delivery` → `poteto-mode` bug-fix playbook → `blast-radius` → `tdd` when appropriate |
| Architecture review | `how` → `why` → `blast-radius` → `architect` |
| Adversarial review | `interrogate` → `thermo-nuclear-code-quality-review` |
| UI proof | `evidence-driven-testing` → `before-and-after` |
| Pull-request follow-through | `make-pr-easy-to-review` → `babysit`; add `greploop` only when Greptile is the requested reviewer |
| Documentation | `technical-writing` → `unslop` |
| Explain a subsystem | `teach`, which combines `how` and `why` |
| Long unattended work | selected bounded playbook → `show-me-your-work` |
| No clear playbook | `figure-it-out` with an explicit hypothesis and evidence loop |

## Complete skill catalog

Risk is a routing and review hint, not permission. A low-risk skill can still
propose an action that requires approval in the current task.

### Core collection: 8 skills

| Skill | Risk | Purpose and activation |
| --- | --- | --- |
| [`before-and-after`](skills/before-and-after/SKILL.md) | Medium | Capture two URLs or images and produce a PR-ready visual comparison. Use for screenshots, visual diffs, and UI change evidence. |
| [`code-structure`](skills/code-structure/SKILL.md) | Low | Place orchestration in actions and reusable mechanics in focused services while preserving existing transaction boundaries. Use when operational logic is duplicated or a feature shares mechanics with another flow. |
| [`evidence-driven-testing`](skills/evidence-driven-testing/SKILL.md) | Medium | Record observable proof of runtime behavior with annotated video, screenshots, or measured output pairs. Use when a change needs evidence beyond a test report. |
| [`greploop`](skills/greploop/SKILL.md) | Medium | Run bounded Greptile review-and-fix cycles while rejecting stale checks and summaries. Use when Greptile review is an explicit delivery gate. |
| [`greploop-apps`](skills/greploop-apps/SKILL.md) | Medium | Invoke the same Greptile workflow through `@greptile-apps` when the normal trigger rejects a large pull request. |
| [`mission-control-delivery`](skills/mission-control-delivery/SKILL.md) | Low | Preserve Mission → WorkOrder → Task → Attempt → evidence → PR → release lineage. Use for governed software-factory work. |
| [`new-feature`](skills/new-feature/SKILL.md) | Low | Isolate repository edits in a task-owned worktree without disturbing other work. Use before features, fixes, or documentation changes that edit Git. |
| [`unslop`](skills/unslop/SKILL.md) | Low | Remove filler, generic AI phrasing, and mechanical prose from human-facing writing. Use on documentation, PR copy, comments, commits, and replies you edit. |

### Pstack planning, architecture, and understanding

| Skill | Risk | Purpose and activation |
| --- | --- | --- |
| [`architect`](skills/architect/SKILL.md) | Medium | Sketch types, signatures, and module boundaries before implementation, then keep the architecture current while the code fills in. |
| [`blast-radius`](skills/blast-radius/SKILL.md) | Low | Trace what a change could break outside the diff and prove the key safety assumption with executable evidence. |
| [`figure-it-out`](skills/figure-it-out/SKILL.md) | Medium | Design an auditable playbook for a migration, large multi-part change, or novel task when no narrower workflow fits. |
| [`how`](skills/how/SKILL.md) | Low | Explain runtime flow, ownership, layering, and subsystem architecture. Use for “how does this work?” or “where should this live?” |
| [`teach`](skills/teach/SKILL.md) | Low | Combine `how` and `why` into one plain-language explanation that builds a usable mental model. |
| [`why`](skills/why/SKILL.md) | Low | Recover design rationale from source history, issues, documents, chat, observability, and analytics, then return a cited explanation. |

### Pstack implementation and quality

| Skill | Risk | Purpose and activation |
| --- | --- | --- |
| [`automate-me`](skills/automate-me/SKILL.md) | Medium | Turn a user’s working preferences into a reusable personal mode skill, optionally grounded in recent workspace-scoped transcripts. |
| [`create-verification-skill`](skills/create-verification-skill/SKILL.md) | Medium | Generate a project-local driver skill that verifies a UI, CLI, or service the way a user operates it. |
| [`deslop`](skills/deslop/SKILL.md) | Medium | Remove low-quality generated-code patterns and simplify the result without changing intended behavior. |
| [`maintain-verification-skill`](skills/maintain-verification-skill/SKILL.md) | Medium | Audit a project’s verification skill and feature map against current source and one live verification session. |
| [`no-comments`](skills/no-comments/SKILL.md) | Medium | Review comments as possible signs of unclear structure, fix accepted findings, and encode real constraints where code can enforce them. |
| [`tdd`](skills/tdd/SKILL.md) | Medium | Use a failing test first when the user requests TDD or a cheap, direct regression target exists. Avoid forcing TDD onto expensive or unclear integration paths. |
| [`technical-writing`](skills/technical-writing/SKILL.md) | Low | Apply Diátaxis structure, direct developer style, controlled instructions, and globally readable English to technical prose. |
| [`typescript-best-practices`](skills/typescript-best-practices/SKILL.md) | Low | Apply focused TypeScript type-safety, API, error-handling, and maintainability guidance when reading or editing `.ts` and `.tsx`. |

### Pstack parallel work and adversarial review

| Skill | Risk | Purpose and activation |
| --- | --- | --- |
| [`arena`](skills/arena/SKILL.md) | Medium | Produce several independent candidates, judge them, choose a base, and graft in the strongest parts of the alternatives. |
| [`interrogate`](skills/interrogate/SKILL.md) | Low | Challenge a change from independent review angles to expose blind spots, invalid assumptions, and weak evidence. |
| [`swarm`](skills/swarm/SKILL.md) | Medium | Fan out bounded, independent work and synthesize one result. Use only when parallelism is authorized and the tasks do not share mutable state. |
| [`thermo-nuclear-code-quality-review`](skills/thermo-nuclear-code-quality-review/SKILL.md) | Low | Run an intentionally strict maintainability review for poor abstractions, giant files, branching growth, and reader load. |

### Pstack pull-request and delivery workflows

| Skill | Risk | Purpose and activation |
| --- | --- | --- |
| [`babysit`](skills/babysit/SKILL.md) | Medium | Monitor an authorized open PR, fix straightforward CI and review issues, and drive it toward a mergeable state without claiming merge authority. |
| [`fix-ci`](skills/fix-ci/SKILL.md) | Medium | Inspect failing PR checks and logs, identify the smallest root-cause fix, and verify the affected gate. |
| [`fix-merge-conflicts`](skills/fix-merge-conflicts/SKILL.md) | High | Resolve merge conflicts non-interactively, validate the result, and stop before publication when push authority is absent. |
| [`get-pr-comments`](skills/get-pr-comments/SKILL.md) | Low | Fetch and summarize the active pull request’s review comments for triage or follow-up. |
| [`make-pr-easy-to-review`](skills/make-pr-easy-to-review/SKILL.md) | Medium | Reduce review friction through clear history, a useful description, and reviewer guidance without changing code behavior. |
| [`what-did-i-get-done`](skills/what-did-i-get-done/SKILL.md) | Low | Summarize authored commits over a requested time window into a concise status update. |

### Pstack context and operating workflows

| Skill | Risk | Purpose and activation |
| --- | --- | --- |
| [`bro`](skills/bro/SKILL.md) | Low | Restate the previous message in direct, jargon-free language. |
| [`poteto-mode`](skills/poteto-mode/SKILL.md) | High | Select a rigorous workflow, keep prose concise, use parallel work deliberately, prefer simple code, and demand verification. It never broadens the active task’s authority. |
| [`recall`](skills/recall/SKILL.md) | Low | Reconstruct current project context from the active harness’s workspace-scoped history, live state, and shared records. |
| [`reflect`](skills/reflect/SKILL.md) | Medium | Review the active transcript from multiple angles and turn reusable lessons into authorized improvements to existing skills. |
| [`setup-pstack`](skills/setup-pstack/SKILL.md) | Medium | Configure confirmed model choices for pstack roles. Claude-specific model overrides remain optional and explicit. |
| [`show-me-your-work`](skills/show-me-your-work/SKILL.md) | Low | Keep a TSV decision trail for long-running work, recording what changed, why, evidence, and result. Commit it only when a reviewer needs it. |

### Pstack engineering principles: 23 skills

These are focused reasoning aids. They should be loaded when the situation
matches, not injected into every task.

| Principle | Use it when |
| --- | --- |
| [`principle-attack-the-premise`](skills/principle-attack-the-premise/SKILL.md) | Several fixes sharing one assumption fail the same gate; inventory the actors and challenge the assumption. |
| [`principle-boundary-discipline`](skills/principle-boundary-discipline/SKILL.md) | Validation or adapters are spreading into business logic; guard external boundaries and keep the core pure. |
| [`principle-build-the-lever`](skills/principle-build-the-lever/SKILL.md) | A script, codemod, generator, or repeatable check can make the work auditable and rerunnable. |
| [`principle-encode-lessons-in-structure`](skills/principle-encode-lessons-in-structure/SKILL.md) | The same instruction or correction appears twice; encode it as metadata, lint, a check, or a tool. |
| [`principle-exhaust-the-design-space`](skills/principle-exhaust-the-design-space/SKILL.md) | A novel UX or architecture choice has no precedent; compare two or three real candidates before committing. |
| [`principle-experience-first`](skills/principle-experience-first/SKILL.md) | Product scope or UX is contested; favor fewer polished capabilities over more unfinished ones. |
| [`principle-fix-root-causes`](skills/principle-fix-root-causes/SKILL.md) | Debugging a symptom; reproduce it, trace it, and repair the cause instead of masking the crash. |
| [`principle-foundational-thinking`](skills/principle-foundational-thinking/SKILL.md) | Choosing core types, data structures, or shared state that will shape the rest of the system. |
| [`principle-guard-the-context-window`](skills/principle-guard-the-context-window/SKILL.md) | Raw output, large files, or broad parallel exploration threatens the main reasoning context. |
| [`principle-laziness-protocol`](skills/principle-laziness-protocol/SKILL.md) | A refactor is growing layers or abstractions; seek deletion and the smallest sufficient change. |
| [`principle-make-operations-idempotent`](skills/principle-make-operations-idempotent/SKILL.md) | Commands or lifecycle steps may be retried after crashes, restarts, or partial completion. |
| [`principle-migrate-callers-then-delete-legacy-apis`](skills/principle-migrate-callers-then-delete-legacy-apis/SKILL.md) | Replacing an internal API; migrate callers and remove the old path in the same bounded wave. |
| [`principle-minimize-reader-load`](skills/principle-minimize-reader-load/SKILL.md) | Code requires too many layers, wrappers, or hidden state to answer a simple question. |
| [`principle-model-the-domain`](skills/principle-model-the-domain/SKILL.md) | Stateful logic repeats conditionals or structural assumptions that belong in an explicit model. |
| [`principle-never-block-on-the-human`](skills/principle-never-block-on-the-human/SKILL.md) | A low-risk, reversible implementation detail is inside scope; proceed without consuming a product decision or new authority. |
| [`principle-outcome-oriented-execution`](skills/principle-outcome-oriented-execution/SKILL.md) | A planned migration has clear phase boundaries; converge on the target instead of adding throwaway compatibility layers. |
| [`principle-prove-it-works`](skills/principle-prove-it-works/SKILL.md) | Work appears complete; verify the actual candidate and observable result rather than relying on proxies. |
| [`principle-redesign-from-first-principles`](skills/principle-redesign-from-first-principles/SKILL.md) | A new requirement changes a foundational assumption; redesign coherently instead of bolting it on. |
| [`principle-separate-before-serializing-shared-state`](skills/principle-separate-before-serializing-shared-state/SKILL.md) | Concurrent actors may write the same file, branch, key, or object; remove sharing before adding locks. |
| [`principle-sequence-verifiable-units`](skills/principle-sequence-verifiable-units/SKILL.md) | Multi-step work or stacked delivery needs each unit to end in a reviewable, passing state. |
| [`principle-subtract-before-you-add`](skills/principle-subtract-before-you-add/SKILL.md) | An addition or rewrite sits on dead or redundant structure; simplify the base first. |
| [`principle-test-behavior-not-implementation`](skills/principle-test-behavior-not-implementation/SKILL.md) | Writing or reviewing tests; call code as users do and assert literal observable outcomes. |
| [`principle-type-system-discipline`](skills/principle-type-system-discipline/SKILL.md) | Designing typed APIs; make invalid states unrepresentable and parse external data at boundaries. |

## Pstack provenance and hardening

The collection imports 53 unique skills from
[`michael-denyer/pstack-claude`](https://github.com/michael-denyer/pstack-claude)
v0.9.29 at commit
[`458050195fdb347955a63812e6d749f164a8f62d`](https://github.com/michael-denyer/pstack-claude/commit/458050195fdb347955a63812e6d749f164a8f62d).
Its duplicate `unslop` is excluded because this collection keeps the existing
enhanced definition as the canonical skill.

[`vendor/pstack.json`](vendor/pstack.json) records the exact source, revision,
53 imported names, and exclusion. [`scripts/vendor_pstack.py`](scripts/vendor_pstack.py)
rebuilds the import instead of relying on an undocumented manual copy.

The integration preserves pstack’s design-first, evidence-driven methods while
tightening assumptions that are too broad for a governed software factory:

- system, user, Mission Control, and repository rules override pstack methods
- reversible actions still require authority when they write to external state
- team messages, ticket updates, eval launches, publishing, merging,
  deployment, spending, and destructive cleanup are not implicitly authorized
- experiments inform Product Owner decisions; they do not replace them
- PR playbooks produce a verified local handoff when publication is not allowed
- worktree cleanup never treats untracked files as disposable
- transcript tools stay inside the active harness and workspace
- multi-agent fan-out remains task-selected and harness-authorized

The complete integration rationale is in
[`docs/PSTACK_REVIEW.md`](docs/PSTACK_REVIEW.md).

### Updating pstack

Review upstream release notes and breaking changes first. Then clone or fetch a
clean upstream checkout and run:

```bash
python3 scripts/vendor_pstack.py /path/to/pstack-claude --replace
python3 -m pytest tests -q
git diff --check
```

The vendor tool verifies the source remote and pinned commit, reapplies
frontmatter and Codex metadata, and checks every authority-hardening anchor. It
stops if upstream moves an anchor or introduces conflicting metadata so safety
changes cannot disappear silently.

After a refresh, review:

1. `vendor/pstack.json`
2. every changed `SKILL.md`, script, and reference
3. upstream licenses and notices
4. Codex tool mappings
5. external-write and approval boundaries
6. package tests and Mission Control lint scores

## Repository structure

```text
skillz/
├── .claude-plugin/plugin.json     # Claude Code plugin metadata
├── .codex-plugin/plugin.json      # Codex plugin metadata
├── .github/workflows/validate.yml # Portable CI checks
├── docs/PSTACK_REVIEW.md          # Import and governance review
├── scripts/
│   ├── install_skills.py          # Safe Claude/Codex installer
│   └── vendor_pstack.py           # Reproducible pstack import
├── skills/
│   └── <skill>/
│       ├── SKILL.md               # Canonical Agent Skill
│       ├── agents/openai.yaml      # Codex UI and invocation metadata
│       ├── references/             # Optional detailed guidance
│       └── scripts/                # Optional deterministic helpers
├── tests/                          # Package and workflow contracts
├── vendor/pstack.json              # Pinned pstack inventory
├── AGENTS.md                       # Repository execution policy
└── LICENSES.md                     # Per-source licensing map
```

## Compatibility contract

### Portable `SKILL.md`

The public Agent Skills fields are the portable source format:

- `name`
- `description`
- `license`
- `compatibility`
- `metadata`
- scalar `allowed-tools`

Descriptions state both what the skill does and when it should activate.
Mission Control extensions such as `version`, `owner`, `risk`, and
comma-separated capabilities live under `metadata`.

### Claude Code

Claude Code discovers the standard `SKILL.md` tree. Product-specific invocation
controls can remain in Claude-facing metadata where needed, but shared bodies
must not assume that Claude-only tools exist in every harness.

### Codex

Codex uses the same skill bodies and reads `agents/openai.yaml` for display and
explicit invocation. Pstack workflows consult
[`skills/poteto-mode/references/codex-tools.md`](skills/poteto-mode/references/codex-tools.md)
when Claude tool names need a Codex equivalent.

### Mission Control

Mission Control reads portable fields first and resolves optional governance
metadata at the ingestion boundary. Legacy top-level Mission Control metadata
can remain supported by the application, but new portable skills should not
depend on it.

## Authority model

Skills describe methods. They do not create authority.

The effective precedence is:

1. system and platform safety requirements
2. explicit user instructions and approvals
3. Mission Control execution contract
4. repository policy such as `AGENTS.md` or `CLAUDE.md`
5. selected skill guidance

Stop and request direction when a choice changes product behavior, expands
scope, accepts failed evidence, or requires authority the active task does not
provide. Continue through low-risk, reversible implementation details that are
already inside the authorized contract.

## Requirements

Most skills are Markdown-only. Individual workflows may need additional tools:

| Capability | Requirement |
| --- | --- |
| Installer, vendor tool, tests | Python 3.10+ |
| Test runner | `pytest` |
| Headless browser evidence | Node.js 20+ and npm; Playwright is installed from the pinned helper lockfile in a temporary directory |
| Native video evidence | `ffmpeg` and `ffprobe` with `libx264`, the `ass` filter, and a supported capture source |
| GitHub pull-request workflows | Authenticated `gh` CLI |
| GitLab workflows | Authenticated `glab` CLI |
| Perforce workflows | Configured `p4` CLI |
| Visual comparison uploads | `@vercel/before-and-after`, `agent-browser`, and an authorized upload destination |
| Parallel skills | A harness that exposes and authorizes independent agents or workers |

Run the evidence environment check before recording:

```bash
python3 skills/evidence-driven-testing/scripts/evidence.py doctor --json
```

## Validation

Install the single test dependency and run the portable suite:

```bash
python3 -m pip install pytest
python3 -m pytest tests -q --ignore=tests/test_evidence.py
python3 -m compileall -q scripts skills
git diff --check
```

Run the complete suite on a host with the native evidence dependencies:

```bash
python3 -m pytest tests -q
```

The tests verify:

- exactly 61 canonical skill directories
- portable frontmatter and matching directory names
- Codex metadata for every skill
- Claude and Codex manifests pointing at the shared tree
- local Markdown links
- pinned pstack provenance and hardening
- conflict refusal, backups, dry runs, copy mode, symlink mode, and idempotency
- Greptile review freshness and bounded polling
- isolated Playwright dependency handling
- evidence recorder lifecycle on capable hosts

GitHub Actions runs the portable tests and Python syntax checks on every pull
request and push to `main`. Native recorder coverage remains host-specific
because desktop capture and FFmpeg filter availability vary.

## Adding a skill

1. Create `skills/<skill-name>/SKILL.md`.
2. Match the directory name and frontmatter `name` using lowercase letters,
   numbers, and hyphens.
3. Write a precise description covering behavior and activation conditions.
4. Keep portable fields at the top level and Mission Control governance values
   inside `metadata`.
5. Add `skills/<skill-name>/agents/openai.yaml` with a clear display name, a
   25–64 character short description, and a default prompt naming
   `$skill-name`.
6. Keep `SKILL.md` focused. Put deep guidance in linked references and
   deterministic operations in scripts.
7. Declare the source and license. Do not broaden an upstream license.
8. Add or update tests and run the validation commands.

## What is intentionally not automatic

- No unconditional startup hook injects the entire pstack workflow.
- No skill is preloaded solely because it is installed.
- No same-name user skill is silently overwritten.
- No imported skill is automatically published to a registry.
- No multi-agent fan-out is enabled without a matching task and harness support.
- No skill can silently authorize external writes, merge, deployment, deletion,
  spending, or a Product Owner decision.

## Sources and acknowledgements

- [`michaelshimeles/skills`](https://github.com/michaelshimeles/skills) provides
  the repository history and original core collection.
- [`michael-denyer/pstack-claude`](https://github.com/michael-denyer/pstack-claude)
  provides the pinned Claude/Codex pstack port.
- [Cursor pstack](https://github.com/cursor/plugins/tree/main/pstack) is the
  upstream origin of the pstack methods.
- [`vercel-labs/before-and-after`](https://github.com/vercel-labs/before-and-after)
  provides the visual-comparison workflow.
- [`greptileai/skills`](https://github.com/greptileai/skills) provides the
  Greptile review workflow.
- [Agent Skills](https://agentskills.io/specification) defines the portable
  skill format.

See [`LICENSES.md`](LICENSES.md) and the license files inside individual skill
directories for exact terms.
