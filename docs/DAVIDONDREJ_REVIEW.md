# David Ondrej skills integration review

Reviewed on October 31, 2026, against
[davidondrej/skills at 8e90e9d](https://github.com/davidondrej/skills/tree/8e90e9d634983e76e66154e6b36a11d735fd19da).

## Scope and selection

The source contains 62 skills. This review inventories all 62, examines their
entrypoints for fit and dependencies, and adapts five in detail. It is not a
security audit of every deferred script or service. The starting Skillz
collection has 103 skills; this change brings it to 108.

The [source manifest](../vendor/davidondrej.json) pins the commit, upstream paths,
SHA-256 hashes of all 62 entrypoints and the license, and a decision for every
skill. The source is MIT licensed, copyright 2026 David Ondrej. Each imported
directory includes the complete upstream notice.

Selection favors gaps in SellerFi's delivery work. Existing Jstack workflows
already cover planning, code review, orchestration, testing, and shipping.
Optional utilities and service-specific integrations remain upstream until a
concrete task needs them.

| Upstream skill | Decision and reason |
| --- | --- |
| `4x4` | Defer. Rigid sixteen-question interview overlaps existing scoped planning. Start with `figure-it-out`. |
| `adr-verbatim` | Adapt. Record approved decisions without inventing requirements. |
| `anti-sleep` | Defer. Already available in the user's installed skills; macOS utility outside this repo's delivery gaps. |
| `ask-then-build` | Defer. Existing investigation and planning already produce implementation briefs. Start with `figure-it-out`, `architect`. |
| `bb-cli` | Defer. Platform-specific BB runtime management; use the host's supported app tools. |
| `bb-plugins` | Defer. BB plugin authoring is outside the current Jstack and SellerFi delivery needs. |
| `before-building` | Defer. Gut-only advice that forbids reading context conflicts with evidence-based planning. Start with `figure-it-out`. |
| `better-prompt` | Defer. Existing prompt refinement covers this capability. Start with `sharpen`. |
| `boat` | Defer. Separate paid sandbox platform; no established Boat requirement. |
| `browser-harness` | Defer. Additional browser runtime and service lifecycle; existing browser tools cover current needs. Start with `evidence-driven-testing`. |
| `browser-use` | Defer. Alternative browser stack with local or paid remote setup; defer until needed. Start with `evidence-driven-testing`. |
| `cmux` | Defer. Optional terminal product integration; no current cmux requirement. |
| `codex-subagent` | Defer. Existing orchestration covers delegation; avoid another fixed-model launcher. Start with `swarm`, `agent-watchdog`. |
| `create-readonly-db-role` | Adapt. Prepare scoped database access and verify effective privileges. |
| `cua-driver` | Defer. Additional desktop automation stack; use existing host UI tools. Start with `evidence-driven-testing`. |
| `decisions` | Defer. Existing assumption review covers unresolved choices. Start with `interrogate`. |
| `deep-research` | Defer. Requires DeepAPI and a sibling research prompt skill; existing research tools are available. Start with `read-the-damn-docs`. |
| `deep-scrape` | Defer. Paid dossier service and external data handling need a dedicated requirement. |
| `deepapi` | Defer. Forces all research through another paid service and adds unrelated write capabilities. |
| `designs` | Defer. A fixed image count is a prompt preference; existing visual design workflows cover the task. Start with `visual-plan`, `visual-edit`. |
| `distribute-skill-to-all-agents` | Defer. The repository already has a conflict-safe portable installer; avoid blanket global synchronization. |
| `domain-checker` | Defer. Useful standalone utility, but domain naming is not a current SellerFi/Jstack gap. |
| `effective-agent-skills` | Defer. The installed skill-creator already covers authoring and validation. Start with `automate-me`. |
| `fable-review` | Defer. Existing reviews cover this task without a fixed Cloudroom model route. Start with `thermos`. |
| `fable-safe-prompt` | Defer. Refusal-oriented prompt rewriting is outside the delivery collection's needs. |
| `file-tree` | Defer. A simple formatting request does not need another discoverable skill. |
| `fireflies-transcript` | Defer. Needs a Fireflies account and meeting access; no current integration requirement. |
| `git-worktree` | Defer. Duplicate task isolation with Cloudroom-specific routing. Start with `new-feature`. |
| `github-outside-sandbox` | Defer. Sandbox escalation belongs to the host's permission workflow. Start with `new-feature`. |
| `global-agent-guardrails` | Defer. Machine-wide agent hook configuration requires a separate installation task. |
| `goal-loop` | Defer. Existing factory and scoped automation workflows cover ongoing work. Start with `factory`, `stay-within-limits`. |
| `gpt-review` | Defer. Duplicate review workflow with mandatory provider, model, and effort. Start with `thermos`. |
| `handoff` | Adapt. Verified continuation context, separate from history retrieval. |
| `herdr` | Defer. Optional terminal orchestrator; no established Herdr dependency. Start with `swarm`. |
| `image-prompt` | Defer. Image prompt generation is already available in the host's image tools; fixed format is unnecessary. |
| `keep-track` | Defer. Existing task plans and status summaries track remaining decisions. Start with `ketchup`. |
| `kimi-review` | Defer. Duplicate review with multiple paid routing fallbacks and a fixed model. Start with `thermos`. |
| `larp-detector` | Defer. Contributor-motive speculation is not a reliable review criterion; check evidence and impact. Start with `thermo-nuclear-review`, `principle-attack-the-premise`. |
| `muse-review` | Defer. Duplicate review tied to a specific provider and model. Start with `thermos`. |
| `nagent` | Defer. BB thread creation and model defaults are host-specific. Start with `swarm`. |
| `new-grok-bot` | Defer. Separate bot product and deployment workflow; no current requirement. |
| `online-shopping` | Defer. Consumer shopping workflow outside the engineering collection. |
| `openrouter` | Defer. Provider integration should be added when a project actually uses OpenRouter. Start with `read-the-damn-docs`. |
| `persistent-localhost` | Defer. Persistent macOS service and port-management changes need a specific operational requirement. |
| `prompt-for-others` | Adapt. Transfer a verified fix to a teammate's agent. |
| `push-skills` | Defer. Personal private-to-public mirror pipeline and global instructions are not this repo's publishing contract. Start with `make-pr-easy-to-review`. |
| `read-all-adrs` | Defer. Unconditional full-corpus loading conflicts with selective context use. Start with `why`, `principle-guard-the-context-window`. |
| `remind` | Defer. Existing concise status and recap workflows cover this. Start with `quick-recap`, `ketchup`. |
| `rename` | Defer. Cloudroom-specific thread naming; use the current host's rename tool. |
| `rename-process` | Defer. Cross-machine repository and service moves are outside this import's needs. |
| `repo-sync` | Defer. Background automatic commits and pushes conflict with task-owned review branches. Start with `new-feature`, `make-pr-easy-to-review`. |
| `reset-cursor-acp` | Defer. Host-specific recovery, including an all-agent kill option; do not bundle globally. |
| `risky-changes` | Adapt. Measure product and provider assumptions before release. |
| `save-idea` | Defer. Hardcoded ideas repository, content taxonomy, and automatic publication do not fit this collection. |
| `self-archive` | Defer. Cloudroom-specific lifecycle action; use the current host's archive tool. |
| `setup-help` | Defer. Conversational formatting preference; not a missing engineering workflow. |
| `signal-from-expert` | Defer. DeepAPI dependency and full-source archival add scope and permissions beyond current needs. |
| `stop-overthinking` | Defer. A communication preference overlaps existing practical decision principles. Start with `principle-laziness-protocol`. |
| `teach` | Defer. Name collision with the existing Jstack teaching workflow. Start with `teach`. |
| `total-review` | Defer. Five mandatory reviewers in full-permission mode add cost and weaken isolation. Start with `thermos`, `plan-arbiter`. |
| `varied-search` | Defer. Fixed quotas of DeepAPI searches add cost without a task-specific evidence need. |
| `who-is-this` | Defer. DeepAPI people profiling is outside the delivery scope. |

Alternatives are starting points, not claims of identical behavior. Deferred
does not mean defective. Service credentials, billing routes, and platform
adoption require their own project context.

## Adaptations

These are curated rewrites, not byte-for-byte imports. Every directory stands
alone with its license and Codex metadata. No upstream scripts, hooks, global
AGENTS.md, remote service integrations, or new runtime dependencies are included.

- `handoff` checks the worktree and evidence, distinguishes verified state from
  claims, and preserves the user's continuation or pause instruction. It does
  not force a new pause, read every linked file indiscriminately, or message
  another chat. Temporary handoff files have an explicit portability limit.
- `adr-verbatim` records only supported decisions, distinguishes proposed from
  accepted status, uses the project's established location, and preserves
  history when a decision changes. It complements `why`, which investigates
  decisions, and `technical-writing`, which edits prose.
- `risky-changes` evaluates product assumptions using representative cases and
  explicit criteria. It removes mandatory competitor research, arbitrary
  10–20-case counts, and the unsupported promise to check production within a
  day. It keeps existing approvals and separates preparation from release.
- `create-readonly-db-role` replaces blanket current/future table access,
  denylist maintenance, and the RLS bypass example with explicit approved
  objects, columns, and tenant scope. It accounts for inherited and PUBLIC
  grants, callable functions, view ownership, future columns, and migration
  owners. Verification uses isolated fixtures, accepts legitimate empty
  results, and does not treat a rollback as proof of harmless execution.
  Credentials and broad ownership cleanup are excluded from example actions.
- `prompt-for-others` transfers a verified fix with prerequisites, evidence,
  stop conditions, and recipient-specific authorization. It removes the rigid
  one-paragraph constraint and does not run unrelated changes to manufacture
  verification. Untested work becomes a diagnostic prompt.

The database corrections follow PostgreSQL's documentation on
[cumulative privileges](https://www.postgresql.org/docs/current/sql-revoke.html),
[row security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html),
[default privileges](https://www.postgresql.org/docs/current/sql-alterdefaultprivileges.html),
and [function security](https://www.postgresql.org/docs/current/sql-createfunction.html).
The skill requires checking the target server version before preparing SQL.

Codex's existing `allow_implicit_invocation: false` policy is retained for
`handoff`, `create-readonly-db-role`, and `prompt-for-others`. Their prose also
limits use to requests for those tasks. `adr-verbatim` and `risky-changes` use
normal discovery. Client-specific upstream frontmatter was replaced by the
repository's portable scalar and metadata format. Other runtimes may differ
in how they enforce invocation policy.

## Package integration

The package version moves from 2.5.0 to 2.6.0 without publishing a release.
The canonical catalog is regenerated with the new provenance. Entries remain
`UNTRUSTED` and `NOT_EVALUATED`; import and static validation do not qualify a
skill for production execution.

Four existing descriptions are shortened to fit the unchanged 8,000-byte
discovery limit: `mission-control-delivery`, `new-feature`,
`evidence-driven-testing`, and `code-structure`. Their bodies are unchanged.
The resulting 108 descriptions use 7,968 bytes.

## Validation and limits

A direct import failed the existing package checks: five skills were absent
from the expected source inventory, `handoff` used unsupported frontmatter,
and the generated catalog was stale. The adaptations and package updates
address those integration failures.

Validation on Python 3.13:

- The portable suite passed all 164 tests, including provenance, standalone
  copy installation, local references, runtime metadata, and catalog checks.
- All five skills passed the installed skill-creator frontmatter validator.
- All 63 source hashes matched the pinned checkout. Each imported LICENSE
  matched the full upstream notice.
- Catalog validation returned 108 skills, no failures, and NOT_EVALUATED status.
- Release metadata matched v2.6.0. Python compilation and whitespace checks passed.
- The full suite returned 171 passed and 18 failed. Every failure was in the
  unchanged recorder tests: the host lacks FFmpeg's `ass` filter and the
  sandbox blocks `ps` process inspection. The recorder doctor independently
  confirmed the missing filter. No recorder implementation changed.

The portable command was
`python3 -m pytest tests/ -q --ignore=tests/test_evidence.py`.
No database role, production grants, paid service, or user-level skill
installation is changed by this integration. Static checks do not prove live
database isolation or how every model will follow the instructions.

## Manual refresh

1. Fetch the upstream repository into a separate review directory and choose a
   full commit SHA. Compare all entrypoints and the license with
   `source_sha256`; inventory new or removed skills.
2. Reassess each changed workflow against the current Skillz collection and
   actual project needs. Inspect helpers before considering any future import.
3. Update the curated instructions deliberately. Preserve local access
   boundaries, invocation policies, complete license notices, and attribution.
   Do not copy the upstream folders over these adaptations automatically.
4. Update the manifest's revision, paths, hashes, decisions, and each selected
   skill's `source-commit`. Update this review and package counts as needed.
5. Regenerate the catalog and run the validation commands in the root README.
   Deliver through the repository's isolated branch and PR process.
