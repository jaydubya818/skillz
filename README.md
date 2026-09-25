# Skillz

Production software skills for Claude Code, Codex, Cursor, Mission Control,
and other Agent Skills runtimes.

Jstack is this repository's governed, cross-harness distribution of the
planning, implementation, review, and engineering-principle skills imported
from the credited upstream sources.

Jstack is derived from
[Cursor's pstack plugin](https://github.com/cursor/plugins/tree/main/pstack),
created by Lauren Tan and released under the MIT license. This repository is a
cross-runtime port. The Jstack name identifies this repository's integration
and safety work. It does not replace pstack's authorship.

The collection also includes a reviewed, pinned import of 24 skills from
[`BuilderIO/skills`](https://github.com/BuilderIO/skills). They cover agent
review, model orchestration, Agent-Native apps, visual planning and editing,
WebMCP, and experimental software-factory workflows.

This repository packages 85 skills behind one canonical `skills/` tree:

- 8 core delivery, architecture, evidence, review, and writing skills
- 30 Jstack workflows for planning, implementation, review, and operations
- 23 Jstack engineering principles
- 24 Builder.io and Agent-Native workflows

Every skill uses portable
[Agent Skills](https://agentskills.io/specification) frontmatter. Claude Code,
Codex, Cursor, and custom runtimes read the same `SKILL.md` bodies. Runtime
metadata and plugin manifests stay beside the canonical tree. Mission Control
governance metadata stays inside the standard `metadata` map.

This is a mixed-source collection. Read [Licensing and attribution](LICENSES.md)
before redistributing an individual skill.

## Why this repository exists

Agent workflows become unreliable when each harness has a different copy,
skills silently overwrite one another, or an orchestration prompt is mistaken
for permission to publish, merge, deploy, or spend money.

Skillz provides:

- one source of truth for Claude Code, Codex, Cursor, and custom runtimes
- explicit activation descriptions instead of loading every skill into context
- a tested package-wide routing budget so all skill descriptions remain discoverable
- a Mission Control delivery contract from mission to release evidence
- a pinned, reproducible distribution with upstream attribution
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

Do not preload all 85 skills. Descriptions are the routing layer; the selected
`SKILL.md` files are the execution layer.

## Choose an installation

Mission Control is optional. It is one consumer of this repository, not a
requirement for Claude Code, Codex, Cursor, or another runtime.

| Runtime | Public package | User install | Project install |
| --- | --- | --- | --- |
| Claude Code | `.claude-plugin/plugin.json` and the `skillz` marketplace | `--claude` writes `~/.claude/skills/` and `~/.claude/agents/` | `.claude/skills/` and `.claude/agents/` |
| Codex | `plugin.json` and `.codex-plugin/plugin.json` | `--codex` writes `~/.agents/skills/` | `.agents/skills/` |
| Cursor | `plugin.json` and `.cursor-plugin/plugin.json` | `--cursor` writes `~/.cursor/skills/` | `.agents/skills/` |
| Other runtime | Standard `skills/` tree | `--portable PATH` writes the exact path | Use the runtime's documented Agent Skills directory |

### Install with the repository installer

```bash
git clone https://github.com/jaydubya818/skillz.git
cd skillz

# Always inspect the user-level change first.
python3 scripts/install_skills.py --all --dry-run

# Install for Claude Code, Codex, and Cursor.
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

## Runtime-specific installation

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

To install the public Claude plugin from inside Claude Code, add this repository
as a marketplace and install its package:

```text
/plugin marketplace add jaydubya818/skillz
/plugin install software-factory-skills@skillz
```

### User-level Codex installation

```bash
python3 scripts/install_skills.py --codex --dry-run
python3 scripts/install_skills.py --codex
```

Destination: `~/.agents/skills/`, the user-level location documented by
[OpenAI's skill guide](https://developers.openai.com/codex/skills).

Each skill includes `agents/openai.yaml` for its Codex display name, concise
description, and explicit invocation prompt. The collection manifest is
[`.codex-plugin/plugin.json`](.codex-plugin/plugin.json).

The root [`plugin.json`](plugin.json) follows the Agent Plugins standard. It
packages the same tree for products that support that format.

### User-level Cursor installation

```bash
python3 scripts/install_skills.py --cursor --dry-run
python3 scripts/install_skills.py --cursor
```

Destination: `~/.cursor/skills/`. Cursor syncs personal skills from this path
to Cursor Cloud Agents. The repository also includes
[`.cursor-plugin/plugin.json`](.cursor-plugin/plugin.json) for local plugin
testing and marketplace submission.

### Custom runtime installation

Pass the runtime's skill directory as an exact destination:

```bash
python3 scripts/install_skills.py \
  --portable /path/to/runtime/skills \
  --dry-run

python3 scripts/install_skills.py \
  --portable /path/to/runtime/skills
```

This mode installs only the canonical skills. A custom runtime must map its
tools and worker controls with the
[`harness-tools.md`](skills/poteto-mode/references/harness-tools.md) guide.

### Optional Agent-Native connections

The repository installer copies skill instructions only. It does not install
desktop software, authenticate accounts, or edit a runtime's MCP settings.
Plugin-capable Claude and Codex installs can read the bundled [`.mcp.json`](.mcp.json),
which declares only the Agent-Native Dispatch server. The runtime still controls
connection approval, authentication, and app grants.

| Skills | Additional requirement |
| --- | --- |
| `an` | Agent-Native Dispatch at `https://dispatch.agent-native.com/mcp`; authenticate and grant each app explicitly. |
| `visual-plan`, `visual-recap` | Agent-Native Plan connector, or the documented local-files mode. |
| `visual-edit` | A browser-capable coding host plus Agent-Native Design MCP or page WebMCP. |
| `rewind` | macOS, the signed Clips Desktop app, Rewind enabled by the user, and the local Screen Memory MCP connection. |
| `turn-into-app` | Node.js and pnpm for local builds, or authenticated Dispatch for a browser-only handoff. |
| `webmcp` | A built-in browser with native WebMCP support or a page-world JavaScript evaluator. |
| `factory*` | The source integrations, repository access, and scheduler capabilities named in the project config. |

When a companion capability is missing, these skills stop with setup guidance;
they do not silently install software, bypass authentication, or substitute an
unapproved external service. Cursor and custom harness users must configure the
required connectors through their runtime's documented MCP settings.

### Project-scoped installation

Copy the skills into the shared runtime directories for one project:

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

Project installs target `.claude/skills/` for Claude Code. Codex and Cursor
share `.agents/skills/`, so `--all` writes that tree once. Claude installs also
place the two companion agents in `.claude/agents/`. Copy mode is portable.
Symlink mode lets an active checkout feed each runtime without duplicate edits.

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
4. `.codex/skills/` (legacy compatibility)
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
| Audit another agent | `agent-watchdog`; add repairs only when the request authorizes edits |
| Compare proposed plans | `plan-arbiter` → one recommended execution handoff |
| Interactive planning | `visual-plan`; use local-files mode for private or repo-owned artifacts |
| Substantial change recap | `visual-recap` after verifying the exact diff |
| Configure delivery automation | `factory` → enable one bounded, read-only workflow first |
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

### Builder.io agent and orchestration workflows

| Skill | Risk | Purpose and activation |
| --- | --- | --- |
| [`agent-watchdog`](skills/agent-watchdog/SKILL.md) | Medium | Monitor or independently audit another agent's session, branch, PR, or transcript. It defaults to audit-only when repair authority is unclear. |
| [`efficient-fable`](skills/efficient-fable/SKILL.md) | Low | Keep planning and final judgment with Claude Fable while cheaper agents handle bounded, independent work. |
| [`efficient-frontier`](skills/efficient-frontier/SKILL.md) | Low | Apply the same bounded delegation pattern to any high-cost frontier model. |
| [`plan-arbiter`](skills/plan-arbiter/SKILL.md) | Low | Compare competing plans against the real task and codebase, then return one executable recommendation. |
| [`plow-ahead`](skills/plow-ahead/SKILL.md) | Medium | Continue through routine ambiguity with stated, reversible assumptions while preserving authority and safety stop conditions. |
| [`quick-recap`](skills/quick-recap/SKILL.md) | Medium | Add or follow a compact red, yellow, or green final status-line convention. |
| [`read-the-damn-docs`](skills/read-the-damn-docs/SKILL.md) | Low | Consult current primary documentation before acting on external APIs, packages, providers, or high-stakes behavior. |
| [`stay-within-limits`](skills/stay-within-limits/SKILL.md) | Low | Check host usage between bounded work waves and pause before the active limit is exhausted. |

### Builder.io Agent-Native workflows

| Skill | Risk | Purpose and activation |
| --- | --- | --- |
| [`an`](skills/an/SKILL.md) | Medium | Open and operate explicitly granted Agent-Native workspace apps through Dispatch MCP. |
| [`rewind`](skills/rewind/SKILL.md) | High | Retrieve a bounded range of local Clips Rewind context without exposing archive paths or uploading local frames. |
| [`turn-into-app`](skills/turn-into-app/SKILL.md) | High | Convert a visible workflow, project, skill, thread, or spreadsheet into a verified Agent-Native app or Builder handoff. |
| [`visual-edit`](skills/visual-edit/SKILL.md) | High | Open a running local app in Agent-Native Design, collect visual edits, and apply them back through explicit consent and conflict checks. |
| [`visual-plan`](skills/visual-plan/SKILL.md) | Medium | Publish a structured interactive plan, or create a local-files plan when hosted writes are not appropriate. |
| [`visual-recap`](skills/visual-recap/SKILL.md) | Medium | Turn an exact PR, branch, commit, or diff into a grounded visual review artifact. |
| [`webmcp`](skills/webmcp/SKILL.md) | High | Use a web app's page tools through the host browser and verify mutations with readback before reporting success. |

### Builder.io experimental Factory workflows

Factory modules share the configuration guide bundled under
[`skills/factory/references/`](skills/factory/references/). Start with manual or
read-only operation. Fixes, replies, publication, approval, merge, deployment,
recovery, and notifications remain separate gates.

| Skill | Risk | Purpose and activation |
| --- | --- | --- |
| [`factory`](skills/factory/SKILL.md) | Medium | Configure source scope, schedules, isolation, prompt overlays, and independent action policies. |
| [`factory-collect`](skills/factory-collect/SKILL.md) | Medium | Collect and triage configured feedback, telemetry, errors, and issues. |
| [`factory-lookback`](skills/factory-lookback/SKILL.md) | Medium | Review bounded signal history for recurring patterns and systemic fixes. |
| [`factory-human-digest`](skills/factory-human-digest/SKILL.md) | Low | Produce a read-only queue of work that still needs human judgment. |
| [`factory-review-prs`](skills/factory-review-prs/SKILL.md) | High | Review a configured PR queue under independent review, reply, approval, and merge rules. |
| [`factory-babysit-pr`](skills/factory-babysit-pr/SKILL.md) | High | Follow one explicitly authorized PR through fix, publish, reply, approval, merge, and soak gates. |
| [`factory-ship`](skills/factory-ship/SKILL.md) | High | Complete an authorized delivery lifecycle without inferring publication, merge, deployment, or notification authority. |
| [`factory-watchdog`](skills/factory-watchdog/SKILL.md) | Medium | Find verified stalls and notify only when the configured policy permits a concrete next step. |
| [`factory-recover`](skills/factory-recover/SKILL.md) | Medium | Resume eligible interrupted work while preserving ownership and avoiding duplicate external actions. |

### Jstack planning, architecture, and understanding

| Skill | Risk | Purpose and activation |
| --- | --- | --- |
| [`architect`](skills/architect/SKILL.md) | Medium | Sketch types, signatures, and module boundaries before implementation, then keep the architecture current while the code fills in. |
| [`blast-radius`](skills/blast-radius/SKILL.md) | Low | Trace what a change could break outside the diff and prove the key safety assumption with executable evidence. |
| [`figure-it-out`](skills/figure-it-out/SKILL.md) | Medium | Design an auditable playbook for a migration, large multi-part change, or novel task when no narrower workflow fits. |
| [`how`](skills/how/SKILL.md) | Low | Explain runtime flow, ownership, layering, and subsystem architecture. Use for “how does this work?” or “where should this live?” |
| [`teach`](skills/teach/SKILL.md) | Low | Combine `how` and `why` into one plain-language explanation that builds a usable mental model. |
| [`why`](skills/why/SKILL.md) | Low | Recover design rationale from source history, issues, documents, chat, observability, and analytics, then return a cited explanation. |

### Jstack implementation and quality

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

### Jstack parallel work and adversarial review

| Skill | Risk | Purpose and activation |
| --- | --- | --- |
| [`arena`](skills/arena/SKILL.md) | Medium | Produce several independent candidates, judge them, choose a base, and graft in the strongest parts of the alternatives. |
| [`interrogate`](skills/interrogate/SKILL.md) | Low | Challenge a change from independent review angles to expose blind spots, invalid assumptions, and weak evidence. |
| [`swarm`](skills/swarm/SKILL.md) | Medium | Fan out bounded, independent work and synthesize one result. Use only when parallelism is authorized and the tasks do not share mutable state. |
| [`thermo-nuclear-code-quality-review`](skills/thermo-nuclear-code-quality-review/SKILL.md) | Low | Run an intentionally strict maintainability review for poor abstractions, giant files, branching growth, and reader load. |

### Jstack pull-request and delivery workflows

| Skill | Risk | Purpose and activation |
| --- | --- | --- |
| [`babysit`](skills/babysit/SKILL.md) | Medium | Monitor an authorized open PR, fix straightforward CI and review issues, and drive it toward a mergeable state without claiming merge authority. |
| [`fix-ci`](skills/fix-ci/SKILL.md) | Medium | Inspect failing PR checks and logs, identify the smallest root-cause fix, and verify the affected gate. |
| [`fix-merge-conflicts`](skills/fix-merge-conflicts/SKILL.md) | High | Resolve merge conflicts non-interactively, validate the result, and stop before publication when push authority is absent. |
| [`get-pr-comments`](skills/get-pr-comments/SKILL.md) | Low | Fetch and summarize the active pull request’s review comments for triage or follow-up. |
| [`make-pr-easy-to-review`](skills/make-pr-easy-to-review/SKILL.md) | Medium | Reduce review friction through clear history, a useful description, and reviewer guidance without changing code behavior. |
| [`what-did-i-get-done`](skills/what-did-i-get-done/SKILL.md) | Low | Summarize authored commits over a requested time window into a concise status update. |

### Jstack context and operating workflows

| Skill | Risk | Purpose and activation |
| --- | --- | --- |
| [`bro`](skills/bro/SKILL.md) | Low | Restate the previous message in direct, jargon-free language. |
| [`poteto-mode`](skills/poteto-mode/SKILL.md) | High | Select a rigorous workflow, keep prose concise, use parallel work deliberately, prefer simple code, and demand verification. It never broadens the active task’s authority. |
| [`recall`](skills/recall/SKILL.md) | Low | Reconstruct current project context from the active harness’s workspace-scoped history, live state, and shared records. |
| [`reflect`](skills/reflect/SKILL.md) | Medium | Review the active transcript from multiple angles and turn reusable lessons into authorized improvements to existing skills. |
| [`setup-jstack`](skills/setup-jstack/SKILL.md) | Medium | Configure confirmed model choices for Jstack roles. Claude-specific model overrides remain optional and explicit. |
| [`show-me-your-work`](skills/show-me-your-work/SKILL.md) | Low | Keep a TSV decision trail for long-running work, recording what changed, why, evidence, and result. Commit it only when a reviewer needs it. |

### Jstack engineering principles: 23 skills

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

## Builder.io provenance and portability

The collection imports 24 skills from
[`BuilderIO/skills`](https://github.com/BuilderIO/skills) at commit
[`fd8f20a879b507cf09feba08663a1edf7a949353`](https://github.com/BuilderIO/skills/commit/fd8f20a879b507cf09feba08663a1edf7a949353).
Builder.io released the source under the MIT license. Every imported directory
includes that license notice so direct and portable installs retain it.

[`vendor/builderio.json`](vendor/builderio.json) records the source revision,
inventory, shared resources, and integration changes.
[`scripts/vendor_builderio.py`](scripts/vendor_builderio.py) reproduces the
import and refuses an unreviewed skill inventory or name collision.

The integration keeps the upstream skill bodies while adding package-level
portability:

- concise activation descriptions within the existing discovery budget
- standard `metadata` provenance, risk, owner, and capability fields
- `agents/openai.yaml` for explicit Codex discovery and invocation
- a complete MIT notice in every imported skill directory
- installed-tree-safe Factory references and bundled visual media
- the reviewed Dispatch MCP declaration used by the `an` workflow
- explicit compatibility notes and fail-closed setup behavior

No imported skill grants authority to authenticate, publish, reply, approve,
merge, deploy, notify, install desktop software, enable capture, or expose a
hosted artifact. The active user request, repository rules, runtime permissions,
and Factory action policies remain in control.

The complete review and recommendations are in
[`docs/BUILDERIO_REVIEW.md`](docs/BUILDERIO_REVIEW.md).

### Updating the Builder.io import

Review upstream changes first, then use a clean checkout:

```bash
python3 scripts/vendor_builderio.py /path/to/BuilderIO-skills --replace
python3 -m pytest tests -q --ignore=tests/test_evidence.py
git diff --check
```

The vendor tool stops when upstream adds or removes a skill. Review the new
inventory, dependencies, licenses, authority boundaries, and generated
Agent-Native sources before changing the expected set.

## Jstack provenance and hardening

The collection imports 53 unique skills from
[`michael-denyer/pstack-claude`](https://github.com/michael-denyer/pstack-claude)
v0.9.30 at commit
[`45f768349a6d7d7e71509fee3f5bccfad54b3bad`](https://github.com/michael-denyer/pstack-claude/commit/45f768349a6d7d7e71509fee3f5bccfad54b3bad).
Its duplicate `unslop` is excluded because this collection keeps the existing
enhanced definition as the canonical skill.

[`vendor/jstack.json`](vendor/jstack.json) records the exact source, revision,
53 imported names, and exclusion. [`scripts/vendor_jstack.py`](scripts/vendor_jstack.py)
rebuilds the import instead of relying on an undocumented manual copy.

The integration preserves the upstream design-first, evidence-driven methods while
tightening assumptions that are too broad for a governed software factory:

- system, user, Mission Control, and repository rules override methods
- reversible actions still require authority when they write to external state
- team messages, ticket updates, eval launches, publishing, merging,
  deployment, spending, and destructive cleanup are not implicitly authorized
- experiments inform Product Owner decisions; they do not replace them
- PR playbooks produce a verified local handoff when publication is not allowed
- worktree cleanup never treats untracked files as disposable
- transcript tools stay inside the active harness and workspace
- multi-agent fan-out remains task-selected and harness-authorized

The complete integration rationale is in
[`docs/JSTACK_REVIEW.md`](docs/JSTACK_REVIEW.md).

### Updating Jstack

Review upstream release notes and breaking changes first. Then clone or fetch a
clean upstream checkout and run:

```bash
python3 scripts/vendor_jstack.py /path/to/pstack-claude --replace
python3 -m pytest tests -q
git diff --check
```

The vendor tool verifies the source remote and pinned commit, reapplies
frontmatter and Codex metadata, and checks every authority-hardening anchor. It
stops if upstream moves an anchor or introduces conflicting metadata so safety
changes cannot disappear silently.

After a refresh, review:

1. `vendor/jstack.json`
2. every changed `SKILL.md`, script, and reference
3. upstream licenses and notices
4. cross-runtime tool mappings
5. external-write and approval boundaries
6. package tests and Mission Control lint scores

## Repository structure

```text
skillz/
├── plugin.json                    # Portable Agent Plugin metadata
├── .claude-plugin/                # Claude plugin and marketplace metadata
├── .codex-plugin/plugin.json      # Codex plugin metadata
├── .cursor-plugin/plugin.json     # Cursor plugin metadata
├── .mcp.json                      # Optional Agent-Native Dispatch declaration
├── .github/workflows/             # Validation and tagged-release jobs
├── agents/                        # Packaged companion agents
├── docs/                          # Import, governance, and recommendation reviews
├── scripts/
│   ├── check_release.py           # Release-version gate
│   ├── install_skills.py          # Conflict-safe runtime installer
│   ├── vendor_builderio.py        # Reproducible Builder.io import
│   └── vendor_jstack.py           # Reproducible Jstack build
├── skills/
│   └── <skill>/
│       ├── SKILL.md               # Canonical Agent Skill
│       ├── agents/openai.yaml      # Codex UI and invocation metadata
│       ├── references/             # Optional detailed guidance
│       └── scripts/                # Optional deterministic helpers
├── tests/                         # Package and workflow contracts
├── vendor/                        # Pinned inventories and generated map source
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

Claude Code discovers the standard `SKILL.md` tree. Per the
[Claude plugin reference](https://code.claude.com/docs/en/plugins-reference),
plugin installs also discover the definitions in `agents/` under the
`software-factory-skills:<agent-name>` namespace. Direct installs receive the
same definitions in `.claude/agents/` and use their bare names. Shared bodies
must not assume that Claude-only tools exist in every harness. Plugin installs
can also discover the Dispatch declaration in `.mcp.json`; direct skill copies
do not modify Claude's connector configuration.

### Codex

Codex uses the same skill bodies and reads `agents/openai.yaml` for display and
explicit invocation. Jstack workflows consult
[`skills/poteto-mode/references/harness-tools.md`](skills/poteto-mode/references/harness-tools.md)
when Claude tool names need a Codex equivalent. The Codex plugin manifest also
points at the optional Dispatch declaration. Authentication and app access are
still user-controlled.

### Cursor

Cursor can load the root Agent Plugin or the Cursor-specific manifest. User
skill installs use `~/.cursor/skills/` so Cursor Cloud Agents can receive them.
Project installs share `.agents/skills/` with Codex and other compatible tools.
The runtime map explains how to replace Claude-only worker and model fields.

### Other runtimes

Other runtimes receive the same skill directories through `--portable PATH`.
The runtime must discover standard Agent Skills or explicitly load the selected
`SKILL.md`. The runtime map defines safe fallbacks when workers, task tracking,
scheduled checks, or structured questions are unavailable.

Builder.io skills name their required host capabilities in `compatibility`.
Runtimes may map equivalent tools, but they must not invent successful writes
or bypass a missing connector. Factory skills read the bundled sibling guide;
install the complete collection when using those modules.

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
| Agent-Native Dispatch | MCP client support plus an authenticated, explicitly granted Dispatch connection |
| Agent-Native visual workflows | Plan or Design connector, or the documented local-files/browser path |
| Clips Rewind | macOS, Clips Desktop, user-enabled capture, and Screen Memory MCP |

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
python3 scripts/check_release.py v2.3.0
git diff --check
```

Run the complete suite on a host with the native evidence dependencies:

```bash
python3 -m pytest tests -q
```

The tests verify:

- exactly 85 canonical skill directories
- portable frontmatter and matching directory names
- concise activation descriptions within the package-wide discovery budget
- Codex metadata for every skill
- portable, Claude, Codex, and Cursor manifests for one package version
- the Claude marketplace entry and the tagged-release version gate
- packaged companion agents and valid plugin or direct-install routing
- local Markdown links
- pinned Jstack and Builder.io provenance, licenses, portability, and hardening
- Claude, Codex, Cursor, and custom-runtime installer destinations
- conflict refusal, backups, dry runs, copy mode, symlink mode, deduplication, and idempotency
- Greptile review freshness and bounded polling
- isolated Playwright dependency handling
- evidence recorder lifecycle on capable hosts

GitHub Actions runs the portable tests and Python syntax checks on every pull
request and push to `main`. A `v*` tag must match every package manifest before
the release job publishes source archives and SHA-256 checksums. Native recorder
coverage remains host-specific because desktop capture and FFmpeg filter
availability vary.

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

- No unconditional startup hook injects the entire Jstack workflow.
- No skill is preloaded solely because it is installed.
- No same-name user skill is silently overwritten.
- No imported skill is automatically published to a registry.
- No direct installer silently configures MCP, downloads Clips, or enables capture.
- No multi-agent fan-out is enabled without a matching task and harness support.
- No skill can silently authorize external writes, merge, deployment, deletion,
  spending, or a Product Owner decision.

## Sources and acknowledgements

- [`michaelshimeles/skills`](https://github.com/michaelshimeles/skills) provides
  the repository history and original core collection.
- [`michael-denyer/pstack-claude`](https://github.com/michael-denyer/pstack-claude)
  provides the pinned upstream source used to build Jstack.
- [`BuilderIO/skills`](https://github.com/BuilderIO/skills) provides the pinned
  Builder.io, Agent-Native, and experimental Factory workflows under MIT.
- [Cursor's upstream plugin](https://github.com/cursor/plugins/tree/main/pstack)
  is the original source of the methods distributed as Jstack.
- [`vercel-labs/before-and-after`](https://github.com/vercel-labs/before-and-after)
  provides the visual-comparison workflow.
- [`greptileai/skills`](https://github.com/greptileai/skills) provides the
  Greptile review workflow.
- [Agent Skills](https://agentskills.io/specification) defines the portable
  skill format.
- [Agent Plugins](https://agent-plugins.org/) defines the portable package
  manifest.
- [Claude plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces),
  [OpenAI's skill guide](https://developers.openai.com/codex/skills), and
  [Cursor plugins](https://cursor.com/docs/plugins) define the runtime-specific
  distribution paths.

See [`LICENSES.md`](LICENSES.md) and the license files inside individual skill
directories for exact terms.
