# Builder.io skills integration review

## Review scope

This review covers the 24 skills imported from
[`BuilderIO/skills`](https://github.com/BuilderIO/skills) at commit
[`fd8f20a879b507cf09feba08663a1edf7a949353`](https://github.com/BuilderIO/skills/commit/fd8f20a879b507cf09feba08663a1edf7a949353).
The source commit is dated September 23, 2026 and uses the MIT license,
copyright Builder.io 2026.

The import adds three groups:

| Group | Skills |
| --- | --- |
| Agent review and orchestration | `agent-watchdog`, `efficient-fable`, `efficient-frontier`, `plan-arbiter`, `plow-ahead`, `quick-recap`, `read-the-damn-docs`, `stay-within-limits` |
| Agent-Native apps and visual workflows | `an`, `rewind`, `turn-into-app`, `visual-edit`, `visual-plan`, `visual-recap`, `webmcp` |
| Experimental Factory | `factory`, `factory-babysit-pr`, `factory-collect`, `factory-human-digest`, `factory-lookback`, `factory-recover`, `factory-review-prs`, `factory-ship`, `factory-watchdog` |

There were no name collisions with the 61 skills already in Skillz.

## Assessment

The upstream collection is strong where production agent workflows usually
fail: it separates read evidence from write authority, requires readback after
mutations, distinguishes unavailable data from empty data, and treats checks,
approval, publication, merge, deployment, and notification as separate gates.
The Factory modules are especially careful about live-state verification and
stale evidence.

The import needed packaging work rather than a rewrite of those methods.
Builder's repository is a complete plugin, while Skillz also supports direct
copies into Claude Code, Codex, Cursor, and arbitrary Agent Skills directories.
Files that work in a repository checkout can break when only the skill
directories are installed.

## Changes made for Skillz

### Portable metadata

Every imported `SKILL.md` now has:

- a concise activation description;
- an MIT license identifier;
- a runtime-specific `compatibility` note where companion tools are required;
- source repository and commit provenance;
- Skillz owner, risk, and capability metadata;
- Builder's `visibility` and Factory `installer-group` values inside the
  standard `metadata` map instead of custom top-level fields.

The descriptions keep the complete 85-skill collection within the existing
8,000-byte discovery budget. Detailed instructions remain in each skill body.

### Codex metadata

Each imported skill includes `agents/openai.yaml` with a display name, a short
description, and a default prompt that names the skill explicitly. Claude Code,
Cursor, and custom runtimes continue to read the same canonical `SKILL.md`.

### Installed-tree-safe resources

The original Factory skills linked to `docs/factory/` outside the skill tree.
Skillz's direct installer copies the canonical skill directories, so those
links would not survive a user or project install. The guide and configuration
reference now live under `skills/factory/references/`, and every Factory link
uses that installed location.

The visual-plan and visual-recap README images now live in their own skill
directories. The turn-into-app skill's root-relative Agent-Native documentation
link now points to the official absolute documentation URL.

### License retention

Each imported directory carries Builder.io's complete MIT notice. This keeps
the attribution and license available when a user installs one directory
without the repository root.

### Optional connector configuration

The reviewed `.mcp.json` declares one server:

```json
{
  "mcpServers": {
    "agent-native-dispatch": {
      "type": "http",
      "url": "https://dispatch.agent-native.com/mcp"
    }
  }
}
```

Claude and Codex plugin manifests reference this file. The direct installer
does not edit runtime configuration. Declaring the server does not authenticate
the user, grant an app, install software, enable capture, or authorize a tool
call.

Plan, Design, and Screen Memory connectors are not registered globally in this
package. Their skills explain the required setup and stop when the capability
is missing. This avoids prompting every Skillz user to authenticate services
they may never use.

### Reproducible updates

[`scripts/vendor_builderio.py`](../scripts/vendor_builderio.py) verifies the
source remote, requires a clean checkout, checks the exact 24-skill inventory,
refuses foreign name collisions, copies all supporting files, applies the
reviewed portability transformations, and records the source revision in
[`vendor/builderio.json`](../vendor/builderio.json).

The inventory check is deliberate. A new upstream skill can add a connector,
license, external write, or product assumption. Refreshes stop until that skill
has been reviewed and added explicitly.

## Authority and privacy review

The imported workflows retain these boundaries:

- `agent-watchdog` defaults to audit-only when repair authority is unclear.
- `plow-ahead` continues through routine ambiguity but stops at destructive,
  production, credential, privacy, legal, and reserved user decisions.
- Factory actions use independent policies. Permission to fix does not grant
  permission to reply, publish, approve, merge, deploy, recover, close, or
  notify.
- `rewind` requires user-controlled Clips installation, capture enablement, and
  bounded local retrieval. It does not crawl app data or upload local frames.
- `visual-edit` keeps source writes behind human consent and version checks.
- `visual-plan` and `visual-recap` support local-files mode when hosted writes
  are inappropriate, and hosted visibility must match source sensitivity.
- `webmcp` prefers named page tools, never treats an acknowledgment as proof of
  a write, and does not fall back to state-changing UI automation silently.
- `turn-into-app` distinguishes local coding hosts from browser-only handoffs
  and does not claim an app or deployment exists without direct evidence.

Risk labels in Skillz are routing and review hints, not permission grants.

## Dependencies and limits

| Area | Limit |
| --- | --- |
| Agent-Native apps | `an` needs authenticated Dispatch and explicit app grants. |
| Visual plans and recaps | Hosted mode needs Plan MCP; local-files mode needs the Agent-Native CLI. |
| Visual editing | Needs a browser-capable coding host and Design MCP or page WebMCP. |
| Rewind | Needs macOS, Clips Desktop, user-enabled capture, and Screen Memory MCP. |
| Factory | Skills do not provide source connectors, credentials, schedulers, or repository access. |
| Model orchestration | Subagent or worker behavior depends on the active harness and its policy. |
| Usage limits | The host must expose reliable usage data or the documented client-specific command. |

The upstream `npm run check:skills` validation passes in the standalone source
checkout. Its generated Agent-Native sync check expects a sibling
`BuilderIO/agent-native` checkout and cannot complete from `BuilderIO/skills`
alone. Skillz therefore validates the imported result with its own frontmatter,
link, metadata, inventory, installer, and reproducibility tests.

## Recommendations

1. Keep Factory manual or read-only until one real project proves complete
   source enumeration, pagination, isolation, verification, and human holds.
2. Do not enable reply, approval, merge, production deployment, recovery, or
   notification in the same rollout. Turn on one action policy at a time and
   verify its live readback.
3. Use local-files mode for sensitive plans and recaps unless the team has
   confirmed hosted visibility, retention, and organization access.
4. Keep Dispatch as the only package-level connector. Add Plan, Design, or
   Screen Memory per runtime and per need rather than forcing them on every
   installation.
5. Treat `efficient-fable` as Claude-specific. Use `efficient-frontier` for the
   same orchestration pattern in Codex, Cursor, or another model family.
6. Preserve the upstream-generated Agent-Native skill bodies during refreshes.
   Contribute large content changes upstream, then revendor, instead of carrying
   an unreviewable fork in Skillz.
7. Upstream should make the generated-skill sync check self-contained or return
   a distinct documented skip when the sibling Agent-Native source is absent.
8. Upstream should move the longest visual skill details into versioned
   references where possible. The current files are useful but exceed the usual
   progressive-disclosure target for one skill body.
9. Consider a future machine-readable dependency map for optional MCP servers,
   desktop apps, CLIs, and host capabilities. Keep `compatibility` as the human
   fallback until runtimes share a dependency schema.

## Refresh procedure

1. Review upstream commits and license changes.
2. Run Builder's available source checks in a clean checkout.
3. Run `python3 scripts/vendor_builderio.py /path/to/BuilderIO-skills --replace`.
4. Review every changed skill, reference, connector, license, and manifest.
5. Confirm external-write, privacy, installation, and authentication boundaries.
6. Run the Skillz portable test suite, Python compilation, release check, and
   whitespace check.
7. Commit the source revision and integration changes together.

Do not update the recorded commit without regenerating the imported files from
that exact checkout.
