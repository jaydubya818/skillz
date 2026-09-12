# Software Factory Skills

A portable [Agent Skills](https://agentskills.io/specification) collection for
Claude Code, Codex, and Mission Control. Each skill has one canonical
`SKILL.md`; harness-specific metadata lives beside it instead of forking the
workflow. The collection can run as a Claude Code plugin, a Codex plugin, or a
project/user-scoped installation.

This is a mixed-source collection. See [Licensing and attribution](LICENSES.md)
before redistributing an individual skill.

## Available skills

### [before-and-after](skills/before-and-after/SKILL.md)

Captures before/after screenshots of web pages or elements and outputs a PR-ready markdown comparison table. It drives the `@vercel/before-and-after` CLI.

Use it when:

- A PR needs visual proof that a UI change does what it claims
- You want a `| Before | After |` table generated and uploaded in one step
- Comparing two URLs, two existing images, or a mix of both

> Vendored from [vercel-labs/before-and-after](https://github.com/vercel-labs/before-and-after) (PolyForm Shield 1.0.0, license included in the folder). Install the CLI with `npm i -g @vercel/before-and-after agent-browser`.

### [code-structure](skills/code-structure/SKILL.md)

Service layer architecture guidance. Prefers actions for orchestration and
services for reusable operations when a project has no established convention.
Preserves existing persistence and transaction boundaries, and permits a
single-caller abstraction when it provides a concrete benefit.

Use it when:

- Multiple workflows duplicate the same operational logic
- You're deciding what belongs in actions vs. shared services
- A bug fix in one flow doesn't propagate to others doing the same thing
- Adding a feature that shares mechanics with existing ones

Includes a migration checklist for extracting shared logic without changing policy or transaction behavior.

### [evidence-driven-testing](skills/evidence-driven-testing/SKILL.md)

Records visual proof while testing UI behavior. The agent drives the app live via computer use (or [cua-driver](https://github.com/trycua/cua) when the harness has no computer-use tools) while the bundled recorder captures the session, then posts the video and a results summary to the PR and tracker issue. The recorder (`scripts/evidence.py`, Python 3 + FFmpeg) runs on Linux, macOS, and Windows and has `doctor`, `start`, `annotate`, and `stop` commands. It timestamps each annotation as the agent tests, burns them into `evidence.mp4` on stop, and summarizes them in a generated `report.md` and `manifest.json`. Headless environments swap the recorder for scripted screenshots and Playwright captures; non-UI changes still get evidence (measured numbers, output pairs, transcript excerpts).

Use it when changed runtime behavior needs observable verification. Documentation-only work needs content checks and verification of runnable examples.

> The recorder needs `ffmpeg`/`ffprobe` with `libx264` and the `ass` filter, plus a supported desktop capture source. Run `python3 scripts/evidence.py doctor` from the skill directory to check availability. The headless helper, `scripts/run-playwright.sh`, uses Node 20+ and npm to install the pinned Playwright dependency lockfile beside a self-contained capture script in a temporary directory. It keeps dependencies out of the target project. Posting evidence requires an authorized destination and the relevant upload tool.

### [greploop](skills/greploop/SKILL.md)

Addresses Greptile feedback on a PR, MR, or shelved changelist. Targets a fresh
5/5 review of the current revision with no unresolved actionable findings,
within `--max-iterations` cycles, default 10. Stops and reports partial results
at the cap, on timeout, or when the integration cannot verify the revision.
The GitHub helper records each trigger and rejects stale checks and summaries.

Use it to get a PR to a clean Greptile review before merge.

> Vendored from [greptileai/skills](https://github.com/greptileai/skills) (MIT, license included in the folder). Requires Greptile installed on the repo and an authenticated `gh`/`glab`/`p4` CLI.

### [greploop-apps](skills/greploop-apps/SKILL.md)

A compatibility entrypoint for `greploop --trigger @greptile-apps`. It uses
the same workflow and tested GitHub helper, including summaries that update
without a new check run. Install it together with `greploop`.

Use it when greploop's trigger gets "Too many files changed for review".

> Local entrypoint derived from greptileai's greploop. MIT license included.

### [mission-control-delivery](skills/mission-control-delivery/SKILL.md)

Preserves Mission, WorkOrder, Task, Attempt, evidence, pull-request, and release
lineage for work governed by Mission Control. It keeps authority explicit,
requires evidence to identify the exact candidate, and produces an operator
handoff without claiming state transitions the agent did not perform.

Use it for software-factory execution. It is a reasoning and delivery contract;
it does not grant permission to mutate Mission Control, publish, merge, deploy,
or spend money.

### [new-feature](skills/new-feature/SKILL.md)

Isolates repository edits in a Git worktree based on `origin/main`, while
preserving a worktree already assigned to the task. It checks whether overlapping
PRs conflict in behavior, allows independent edits, and leaves other tasks'
work untouched. Read-only reviews and investigations need no new worktree.

Use it when:

- Starting a feature, fix, or documentation edit
- Multiple agents (or sessions) work the same repository concurrently
- You need a consistent branch-per-task convention with safe cleanup

Checks actual worktree ownership instead of assuming the editor created one.

### [unslop](skills/unslop/SKILL.md)

Edits prose to remove AI tells and put a human voice back in. It names 31 patterns to catch (puffery, filler, hedging, chatbot phrases, em dashes, colons as connectors, bold and emoji overuse, abstract metaphor nouns, passive voice) and a short checklist for adding opinion and rhythm, applied as a four-step loop: scan, rewrite, add soul, self-audit.

Use it when:

- Writing anything a person will read: commit messages, PR titles and bodies, docs, README edits, code comments, chat replies
- Cleaning up existing text that reads machine-made

> Vendored from [cursor/plugins (pstack)](https://github.com/cursor/plugins/tree/main/pstack/skills/unslop) (MIT, license included in the folder). The body matches upstream; the frontmatter has two edits so agents apply the skill on their own instead of waiting for a typed `/unslop`. We dropped the `disable-model-invocation: true` line, and the description now names the trigger (text you write or edit for a human reader) in place of upstream's "any writing. Must always apply.", so auto-invocation matches the scope `AGENTS.md` gives it. Restore the flag if you want slash-command-only behavior.

### Pstack workflows and principles

The collection also includes 53 skills from
[`michael-denyer/pstack-claude`](https://github.com/michael-denyer/pstack-claude):
30 public workflows and 23 internal `principle-*` references. They cover design
exploration, codebase explanation, blast-radius analysis, TDD, CI and PR work,
multi-model review, technical writing, decision trails, and long-running work.

They are pinned and reproducibly transformed rather than copied ad hoc. See the
[pstack integration review](docs/PSTACK_REVIEW.md) for the inventory decision,
authority hardening, recommended routes, and update procedure. The upstream
licenses and notice travel inside
[`skills/poteto-mode/references/licenses/`](skills/poteto-mode/references/licenses/).

## Workflow

[`AGENTS.md`](AGENTS.md) selects the applicable steps for each task: isolate
edits, follow the project's architecture, verify the changed behavior, and ship
when the task calls for it. Read-only work skips shipping; small documentation
edits use content checks. Code and executable workflow changes use a bounded
Greptile review loop. Apply `unslop` to prose you write or edit along the way.

For Mission Control work, load `mission-control-delivery` first and use
`poteto-mode` as the workflow selector. Load only the skills selected for the
task; do not preload the entire collection.

## Installation

The installer targets Claude Code, Codex, or both. It refuses conflicting
installs by default, recognizes an already-current install, and preserves a
backup when `--replace` is explicitly selected.

```bash
# Inspect user-scoped changes first
python3 scripts/install_skills.py --all --dry-run

# Install for both harnesses
python3 scripts/install_skills.py --all

# Keep one checkout as the canonical source for a project
python3 scripts/install_skills.py --all --mode symlink --project /path/to/project
```

Use `--claude` or `--codex` to target one harness. Project installs write to
`.claude/skills/` and `.codex/skills/`; user installs write to the corresponding
directory under the current user's home. Run with `--replace` only after
reviewing the dry-run output.

Claude Code can also load the repository directly as a development plugin:

```bash
claude --plugin-dir .
```

Codex reads `.codex-plugin/plugin.json` and each skill's
`agents/openai.yaml`. Claude Code reads `.claude-plugin/plugin.json` and the
shared `skills/` tree. Skills activate from their descriptions and can also be
invoked explicitly by name.

### Mission Control

Install or symlink this collection into a MissionControl checkout with
`--project /path/to/MissionControl`. Mission Control's local scanner discovers
the canonical `skills/` tree plus `.agents/skills/`, `.claude/skills/`,
`.codex/skills/`, and `.cursor/skills/`. Identical cross-harness installs are
collapsed by skill name; conflicting definitions stop the scan and identify
both paths.

Repository scanning does not publish, activate, or grant authority. Import and
activation remain governed Mission Control operations.

## Checks

Run `python3 -m pytest tests/ -q` and `git diff --check`. The package tests
validate both plugin manifests, portable frontmatter, Codex metadata, local
links, and installer conflict handling. The recorder tests
require Python 3.10+, pytest, ffmpeg, and ffprobe with libx264 and the ass filter.
Workflow tests cover review freshness, polling, and isolated Playwright module
resolution. The Playwright runner tests require Node and Bash and stub npm
downloads. For changes to that helper, also run a real Chromium capture using
the documented command. These local tests do not exercise live upload hosts
or every native desktop capture backend.

GitHub Actions runs the portable package, installer, and workflow tests on each
pull request and push to `main`. Native evidence-recorder coverage remains a
host capability check because it requires a supported capture backend and an
FFmpeg build with the `ass` filter.

## Adding a new skill

1. Create `skills/<skill-name>/SKILL.md`; the directory and `name` must use the
   same kebab-case value.
2. Keep the portable top-level fields to `name`, `description`, `license`,
   `compatibility`, `metadata`, and `allowed-tools`. Put Mission Control values
   such as `version`, `owner`, `risk`, and comma-separated `capabilities` under
   `metadata`.
3. Make the description say what the skill does and when it should activate.
4. Add `skills/<skill-name>/agents/openai.yaml` with a clear display name,
   25–64 character short description, and a default prompt that names
   `$skill-name`.
5. Keep `SKILL.md` focused. Put detailed references or deterministic helpers
   beside it and link them with relative paths.
6. Add or update tests, then run the checks above.
