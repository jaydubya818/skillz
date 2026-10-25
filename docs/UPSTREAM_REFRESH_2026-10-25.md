# Upstream review, October 25, 2026

This refresh starts from Skillz main at `dee52b0344c700237f18f6bff1a4eb016a8317a4`.
It checks clean default-branch checkouts of all seven credited source repositories.
It updates the collection from 92 to 103 skills and the package metadata from
2.4.0 to 2.5.0. It does not publish a release, merge a PR, install user skills,
or change the separate MySkills qualification branch.

## Source review

| Source | Reviewed revision | Result |
| --- | --- | --- |
| [pstack cross-runtime port](https://github.com/michael-denyer/pstack-claude) | `356c6e0f978df729eb16f227d795f34d221c5aad`, 0.9.102 | Refresh 53 existing skills and accept 11 additions. Retain Skillz branding, activation budget, runtime mapping, and authority boundaries. |
| [Original Cursor plugins](https://github.com/cursor/plugins) | `99b609a72323b70204eab407c622f436e858e112` | Refresh unslop directly; review pstack changes after the port's original-source pin. Carry applicable fixes without replacing port-specific work. |
| [Builder.io](https://github.com/BuilderIO/skills) | `fecf1ffac18165d165bef520b5c6bd49553c7968` | Refresh all 24 selected skills. Material body changes are in turn-into-app and visual-edit. |
| [Addy Osmani](https://github.com/addyosmani/agent-skills) | `aeac41d4d005999432bb7312f7ff06383a91d59d` | Review all 25 source skills and retain the seven curated rewrites. Refresh provenance and source hashes. |
| [Vercel before-and-after](https://github.com/vercel-labs/before-and-after) | `8306d34f459b6704e08e6adb5829fcddb0dc3557` | Replace the obsolete capture CLI instructions with the current formatter and attachment workflow. |
| [Greptile](https://github.com/greptileai/skills) | `941290ad67b4de2a143dfc80e15b2773ed4855d0` | Review polling, edited-summary, and layout changes. Retain the stronger local revision-bound helper and bounded review loop. Do not install the separate login/review plugin or replace this workflow with it. |
| [Original core collection](https://github.com/michaelshimeles/skills) | `69558ea1f5328da7b40ba171dfe2171f00ff4884` | Import the pidfd capability fallback and its regression tests. Preserve the local workflow adaptations and remove superseded before-and-after helpers. |

[The source receipt](../vendor/upstream-review.json) contains exact source hashes
and license-file hashes. The three existing vendor manifests identify the
selected packages. Core skill metadata now records reviewed source revisions.
`mission-control-delivery` is local original work and has no external refresh.

## New skill selection

All 11 additions in the latest pstack port are accepted. They remain optional
routes; their presence does not require invoking them for ordinary work.

| Addition | Reason and integration |
| --- | --- |
| benchmark-checklist | Adds measurement validity checks to performance work. Use a portable core-count command. |
| principle-explain-the-number | Connects benchmark and evaluation claims to their limitations. |
| correct | Turns repeated mistakes into enforceable constraints. Limit execution to requested correction work and the agreed repository scope. |
| create-formal-verification-skill | Adds bounded verification with code mappings and deliberately failing controls. Support shared `.agents/skills/` discovery. |
| maintain-formal-verification-skill | Detects stale models that still pass; keeps verification changes separate from product fixes. |
| in-your-own-words | Restates the requested outcome without starting implementation. |
| ketchup | Gives a read-only progress catch-up and complete pending decisions. |
| poteto-help | Exposes the installed workflow catalog. Explain Skillz installation and the absence of upstream routing hooks. |
| sharpen | Uses the newer original Cursor prompt-refinement behavior and leaves product choices open. |
| thermo-nuclear-review | Adds a correctness/security audit distinct from the existing maintainability review. |
| thermos | Combines both review passes. Bundle both companion definitions; support direct installs and sequential fallback when delegation is unavailable or unauthorized. |

The original Cursor tree has two additional skills not yet in the port.
`statechart` is deferred to a separate integration because its first-use Java/TLC
bootstrap downloads about 305 MB and needs an explicit dependency and execution
review. The accepted formal-verification skills work without it. `ketchup-video`
is deferred because it adds a rendering workflow beyond the accepted text and
existing-media catch-up. Neither is copied into the installed tree.

## Original-source changes beyond the port

The latest port records original pstack at
`7b353f78f6ec193bdbe48ed8059444eb09b6878e`. Review the original-source delta
separately from the port's release number.

- Carry multi-backtick handling into the plan validator and retain its upstream
  regression tests.
- Prefer a sole active PR over closed or merged PRs with the same branch.
  Preserve the port's full repository identity checks and historical anchors.
- The port already handles fork-safe stack discovery and bounded watcher
  deadlines. Do not overwrite those stronger implementations with an older
  original-source implementation.
- Carry the newer sharpen instructions, swarm numbering fix, and protection
  against editing cached plugins. Adapt destinations to the requested canonical
  source or project/user scope instead of assuming a Cursor-only installation.
- Keep original-source regression additions in
  [cursor-pstack-tests.patch](../vendor/cursor-pstack-tests.patch). The Jstack
  generator applies them before replacing any installed output.

The Jstack importer now rejects dirty sources and inventory drift and stages
all transformations before replacing the skill tree. A changed hardening anchor
therefore leaves the installed output untouched.

## Other integration decisions

Builder.io's current turn-into-app separates local implementation from browser
handoff, carries source and spreadsheet review guidance, and includes explicit
verification and deployment distinctions. Its new supporting references and
README image are bundled. Factory configuration and connector declarations
retain their existing scope.

Addy's changes fix a missing `refetch`, JavaScript code-fence labels, validation
after trimming, and prose in excluded workflows. Those code examples are not
present in the curated Skillz rewrites. Preserve the existing API, migration,
telemetry, UI, and security corrections rather than copying generic examples
back into the collection.

The Vercel formatter handles existing images and videos, previews, attachment
lists, and marked PR blocks. Resolve its script from the installed skill while
running in the target repository. Remove the obsolete screenshot, public Gist,
and upload-adapter scripts. Add capability checks before using `gh --attach`.
The development host's gh 2.86.0 does not have that flag; the current
[PR edit manual](https://cli.github.com/manual/gh_pr_edit) and
[PR comment manual](https://cli.github.com/manual/gh_pr_comment) document it.
Local formatting remains available on older hosts. No CLI upgrade or media
upload is performed by this refresh.

A regression test reproduced the upstream formatter trimming whitespace from
unrelated PR text. The adapted formatter now preserves every byte outside an
existing marked block. Its tests also cover previews, attachment paths, and
missing media. They use local fixtures and do not establish live upload behavior.

The original recorder fix probes whether pidfds are actually usable instead of
checking only whether Python exposes the function. A refused pidfd uses the
supervisor path, and stop reports an explicit recorder failure rather than
signalling an unverified process. The executable is the exact upstream file.

Updated MIT notices retain Cursor team-kit and thermos attribution. The Vercel
PolyForm Shield license remains unchanged. No license is broadened.

## Validation and limits

The unchanged portable suite passed 155 tests before editing. Validation of the
refresh covers package metadata, local links, discovery budget, installation,
catalog generation, source provenance, the formatter, recorder regressions, and
the imported local script suites. Exact final results belong in the PR.

Local results:

- 158 portable Python tests pass.
- 264 imported Bun script tests pass, including the carried original-source cases.
- Both new pidfd regression tests pass with process inspection enabled.
- The same original-source regression controls fail against the unpatched port.
- Both generators reproduce their output byte for byte. A deliberately changed
  hardening anchor is rejected without changing any installed output.
- A fresh project install contains 103 shared skills, 103 Claude skills, and
  four companion agents. It changes no user-level installation.
- All 103 catalog entries validate. Descriptions use 7,870 of the unchanged
  8,000-byte discovery budget. Release metadata and whitespace checks pass.

The host FFmpeg lacks the `ass` filter, so recorder rendering is not claimed.

Regenerate the catalog after changing skill content:

```bash
python3 -m myskills catalog > catalog/myskills.json
python3 -m myskills validate
python3 -m pytest tests -q --ignore=tests/test_evidence.py
python3 -m compileall -q scripts skills
python3 scripts/check_release.py v2.5.0
bun test skills/poteto-mode/scripts/check-plan.test.ts skills/poteto-mode/scripts/orch skills/poteto-mode/scripts/watch-pr
git diff --check
```

The catalog remains UNTRUSTED and NOT_EVALUATED. New source versions invalidate
old package identities; this refresh grants no behavioral qualification or
consumer activation. Recorder rendering still depends on the host's FFmpeg
filters and process permissions. No live deployment, paid model evaluation,
video upload, production integration, or automatic routing hook is exercised.
