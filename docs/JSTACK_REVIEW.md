# Jstack integration review

## Decision

Vendor the 53 unique skills from
[`michael-denyer/pstack-claude`](https://github.com/michael-denyer/pstack-claude)
v0.9.30 at commit `45f768349a6d7d7e71509fee3f5bccfad54b3bad`.
Keep this collection's `unslop` definition because the upstream tree contains
the same skill name and Mission Control rejects ambiguous definitions.

The imported work originates in
[Cursor's pstack plugin](https://github.com/cursor/plugins/tree/main/pstack),
created by Lauren Tan and released under the MIT license. Jstack is the name of
this repository's integration, not a claim of original authorship.

The imported tree includes 30 user-facing workflows and 23 internal
`principle-*` references. Its source files, scripts, and relative references
stay intact. `scripts/vendor_jstack.py` applies the integration layer and
`vendor/jstack.json` records the exact input.

## What the integration adds

- MIT license declarations and source provenance on every imported skill
- Mission Control `owner`, `risk`, and capability values under portable
  `metadata`
- `agents/openai.yaml` for Codex display and explicit invocation
- trigger language where the source description did not explain when to use
  the skill
- one canonical skill tree for Claude Code, Codex, and Mission Control

## Safety and compatibility changes

Jstack's core methods are strong: design before implementation, test observable
behavior, inspect blast radius, keep work reviewable, and use evidence. Several
defaults were too broad for a governed software factory. The vendor tool makes
these changes every time the source is refreshed:

- `mission-control-delivery`, system instructions, user instructions, and
  repository rules take precedence over `poteto-mode`.
- Reversible work can proceed only inside the authorized contract. External
  writes do not become authorized because they can be undone.
- Team messages, ticket changes, eval launches, publication, merge, deployment,
  spending, and destructive cleanup require explicit task authority.
- Product and preference decisions remain with the Product Owner. Experiments
  inform those decisions; they do not replace them.
- Pull-request playbooks can hand off verified local work when commit, push, or
  PR publication was not requested.
- Worktree cleanup no longer treats untracked files as disposable or escalates
  automatically to recursive deletion.
- Transcript workflows use the active harness's workspace-scoped history and
  never search unrelated project histories.
- Project verification skills can target Claude Code, Codex, or one canonical
  definition linked into both harness directories.

## Recommended operating model

Use `mission-control-delivery` first for non-trivial Mission Control work. It
binds the Attempt to scope, authority, evidence, and handoff. Then use
`poteto-mode` to select a workflow and load only the applicable public skills
or principles.

Do not preload all 61 skills. That wastes context and increases instruction
collisions. The descriptions are the routing layer; the selected `SKILL.md`
files are the execution layer.

Good default routes:

| Work | Skills |
| --- | --- |
| Feature or fix | `mission-control-delivery`, `poteto-mode`, `new-feature`, then `architect` or `tdd` as applicable |
| Architecture review | `how`, `why`, `blast-radius`, `architect` |
| High-risk review | `interrogate`, `thermo-nuclear-code-quality-review` |
| UI verification | `evidence-driven-testing`, `before-and-after` |
| Pull-request follow-through | `babysit`; add `greploop` only when Greptile is the requested reviewer |
| Documentation | `technical-writing`, then `unslop` |
| Long unattended run | `show-me-your-work` plus the selected bounded playbook |

## What not to make automatic

- Do not port the upstream Claude Code `SessionStart` hook into this collection.
  Codex has no equivalent hook, and unconditional injection would bypass
  project-specific routing and consume context on trivial tasks.
- Do not auto-enable multi-agent fan-out. Use it only when a selected workflow
  requires independent parallel work and the harness allows it.
- Do not auto-publish imported skills to the Mission Control Registry. Review,
  version, evaluate, and publish them through the normal governed path.
- Do not silently replace existing user-level skill directories. Run the
  installer with `--dry-run`; use `--replace` only after reviewing the named
  backups.

## Updating the vendor

Clone or fetch the upstream repository, inspect its release notes, then run:

```bash
python3 scripts/vendor_jstack.py /path/to/pstack-claude --replace
python3 -m pytest tests/ -q
git diff --check
```

Review changes to `vendor/jstack.json`, every reported hardening anchor, the
Codex mapping, and the upstream notices before accepting the refresh. The tool
stops if upstream changes a hardening anchor or introduces its own `metadata`
schema, so those changes cannot silently erase the integration policy.
