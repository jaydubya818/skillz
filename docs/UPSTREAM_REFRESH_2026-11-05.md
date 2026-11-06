# November 5 upstream refresh

This review checks all eight recorded skill sources against their latest commits
on November 5, 2026. The package moves from 2.6.0 to 2.7.0 and from 108 to 109
skills. The canonical skills, source receipts, runtime metadata, and catalog
remain in the repository's existing distribution.

## Sources and decisions

| Source | Reviewed revision | Decision |
| --- | --- | --- |
| [Builder.io](https://github.com/BuilderIO/skills) | `f4f10b8d513476c24bd995ceac5294bcdd6ee15c` | Refresh the 24 existing skills and add `efficient-orchestrator`. Retain explicit invocation for it and the two aliases. |
| [Jstack port](https://github.com/michael-denyer/pstack-claude) | `d88063f3355a5ecff0e6dbb890a11bab4b08bc2e`, 0.9.130 | Refresh 64 imported skills, supporting resources, and companion agents. Preserve local hardening. |
| [Addy Osmani](https://github.com/addyosmani/agent-skills) | `301b02b12bff98e4688e6984af6556802322bbde` | Review all 25 source skills. Retain seven adaptations and incorporate applicable corrections. |
| [Vercel before-and-after](https://github.com/vercel-labs/before-and-after) | `8306d34f459b6704e08e6adb5829fcddb0dc3557` | No upstream change. Retain the local formatter correction. |
| [Greptile](https://github.com/greptileai/skills) | `59e79eca306a09321ff40d6a3045c98967568b78` | Skill entrypoints are unchanged. Defer bundled CLI 3.8.0 and Devin packaging, which Skillz does not distribute. |
| [Original Cursor pstack](https://github.com/cursor/plugins/tree/main/pstack) | `2776ddd2355d6d6c8747d3964600f28daf62f049` | Check original changes against the port. Keep the port's additional watcher, deadline, and runtime corrections. Keep the existing `unslop` definition. |
| [Michael Shimeles rstack](https://github.com/michaelshimeles/rstack) | `11b15767d7587bab11f6c4957507b5f26d1785c7` | The former `michaelshimeles/skills` URL redirects here. Only its README changed. Retain the reviewed core bodies. |
| [David Ondrej](https://github.com/davidondrej/skills) | `8aa01cf45110ae378bdf5c319cd41ac8fdbdf448` | All 62 skill entrypoints are unchanged. Update the five adaptation receipts. Do not import source global instructions. |

The [review receipts](../vendor/upstream-review.json) record the previous and
reviewed commits, decisions, entrypoint hashes, and license receipts.
Distribution manifests pin the actual Builder.io, Jstack, Addy, and David
inputs. Full source commits also identify supporting files.

This is a review of the packaged collection and relevant upstream changes.
It does not add every plugin from Cursor's broader repository, every source
harness extension, or every locally installed personal skill.

## Changes that affect use

### Explicit orchestration and app hosting

Builder.io replaces two duplicate orchestration bodies with
[`efficient-orchestrator`](../skills/efficient-orchestrator/SKILL.md).
`efficient-fable` and `efficient-frontier` remain aliases. All three retain
`disable-model-invocation: true` for supporting clients and
`allow_implicit_invocation: false` in Codex metadata. Loading the collection
does not itself request delegation. Other runtime and task authority still
controls whether workers may run and which models may be selected.

The media now belongs to the canonical orchestration directory. The app
creation workflow distinguishes local execution from a Builder handoff, keeps
an already chosen hosting route, and resumes unfinished work without
rescaffolding it. Its hosted route retains source-data authorization and
does not silently fall back to another deployment choice.

### Jstack 0.9.130

The updated port includes:

- A fresh-install bootstrap restart so PR commands can resolve the dependency
  installed during that invocation.
- Additional watcher regression coverage, explicit missing-field errors, and
  an empty check list for the no-checks state.
- A macOS/Bun worktree audit fix that avoids a realpath call through autofs.
- Evidence-backed adversarial review, base-aware code cleanup, configurable
  review roles, and clearer session and transcript behavior.
- Runtime mappings and setup notes for additional upstream hosts. These are
  instructions, not newly installed hooks, extensions, or live qualification.

Upstream removed the old scripted orchestration engine. The import removes
that engine and its stale local patch instead of keeping two orchestration
implementations. The multi-backtick plan-checker correction is now upstream;
its regression tests travel with the import. Historical documentation links
to the old patch at its original commit.

The generator still validates every hardening anchor in a temporary tree
before replacing installed content. Stale anchors for fixes now upstream were
removed. Updated anchors retain Mission Control precedence, task authority,
safe worktree cleanup, project-local verification discovery, direct-install
companion agents, and workspace-scoped history.

The new source paragraph that forbids all publication after reflection is
adapted to preserve an explicitly requested canonical repository update.
Cached plugins remain protected.

### Curated engineering guidance

The seven Addy adaptations remain deliberate rewrites. Source example fixes
are not copied over the local API, migration, or security corrections.
Applicable additions are:

- CI caches use the package manager's supported store. New quality gates must
  fail on a known violation and scanner error, and pass a clean control.
- UI measurements wait for fonts and resize-driven layout. Verification checks
  that visible actions reach the intended callback or operation.
- Security triage reports matching filenames rather than printing potential
  secret values. Findings are checked against actual callers and the base.
- Crash and rollback evidence exercises the real boundary in an isolated
  environment. An exception or mocked transaction does not prove either.

No database role, customer data, remote application, deployment, or user-level
installation is changed by these instructions.

### Catalog frontmatter validation

Builder.io's frontmatter fix exposed the same class of gap in Skillz's scalar
parser. The existing parser accepted invalid unquoted values beginning with
characters such as `@`, a backtick, or `%`, and YAML collection indicators.
It also accepted an unquoted mapping separator inside a scalar.

The catalog now rejects these unsupported forms before creating a manifest.
Quoted and folded values remain supported. This keeps metadata validation
within the existing documented scalar subset and adds no YAML dependency.

## Selection and retained limits

`statechart` and `ketchup-video` remain deferred. They bring optional TLA+
visualization and host media dependencies that need their own qualification.
Their new upstream links in help and formal verification instructions are
adapted so Skillz does not refer to absent local files or require an
uninstalled optional skill.

The collection has 109 canonical skill directories. Their descriptions use
7,991 bytes, within the unchanged 8,000-byte discovery budget. The four core
description reductions from the earlier import remain intact. No skill
collection is preloaded by this refresh.

MIT and PolyForm notices remain with the existing distribution. Builder.io's
new directory carries the full MIT notice. Imported instructions do not grant
authority to publish, message, merge, deploy, delete, spend, or change machine
configuration.

## Validation

The unchanged starting checkout passed 164 portable Python tests.

The original vendor tools refused the changed source inventories before
writing. After review, the generators reproduce the selected imports with
the existing portability and authority corrections.

A fresh-install regression control replaced only the candidate bootstrap with
the previous version in a disposable copy. Both PR command help tests failed.
The imported bootstrap passes both tests as part of the 223-test Bun suite.

The invalid-scalar controls failed for all 11 malformed descriptions before
the parser fix. All 15 scalar cases pass afterward, including quoted and
folded controls.

The final local validation passed 181 portable Python tests and 223 Bun tests.
Both vendor generators reproduce their reviewed skill and agent trees.
All 262 source/license hashes match the eight source checkouts; curated
manifest hashes match as well. Catalog validation reports 109 entries without
failures. Release metadata, Python compilation, local links, and whitespace
checks pass.

A fresh project installation contains 109 shared skills, 109 Claude skills,
and four companion agents. A second installation skips current copies. The
three orchestration packages retain their explicit Codex invocation policies.

The complete Python suite returned 188 passed and 18 failed. All failures
are in the unchanged recorder implementation's tests: FFmpeg lacks the
`ass` filter, and the sandbox denies `ps`. The recorder doctor independently
confirmed the missing filter. Hosted-check results are recorded in the PR.

Run the current checks with:

```sh
python3 -m pytest tests -q --ignore=tests/test_evidence.py
bun test skills/poteto-mode/scripts/check-plan.test.ts skills/poteto-mode/scripts/watch-pr
python3 -m myskills validate
python3 scripts/check_release.py v2.7.0
python3 -m compileall -q scripts skills myskills
git diff --check
```

Native recorder coverage depends on the host's FFmpeg build and process
permissions. Catalog entries remain `UNTRUSTED` and `NOT_EVALUATED`. Package
tests do not qualify live provider interactions, model behavior, every new
harness mapping, database isolation, or native desktop recording.
