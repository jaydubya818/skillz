---
name: mattpocock-research
description: "Research cited primary sources."
license: MIT
metadata:
  source: mattpocock/skills
  source-commit: 4ae2317ddb22b046e26455e4f9c9b3aaaf62212d
  upstream-name: research
  upstream-status: published
  adaptation: namespaced-port
---

## Skillz integration

This is Matt Pocock's version. Skill references use the `mattpocock-` prefix.
Read a referenced skill's `SKILL.md` through the host's skill loader or file tools.
Map AskUserQuestion to the host's question tool and shell examples to its shell.
Use delegation only when available and permitted by the active instructions;
otherwise perform the same work sequentially and report that limit.
The user's scope and repository rules govern setup, file writes, tracker changes,
messages, schedules, publishing, merging, and cleanup. A skill invocation alone
does not broaden the user's request. Preserve existing work and configuration.
Verify provider examples against current primary documentation before use.

Spin up a **background agent** to do the research, so you keep working while it reads. Start it with a fresh context window.

Its job:

1. Investigate the question against **primary sources** (official docs, source code, specs, first-party APIs), not a secondary write-up of them. Follow every claim back to the source that owns it.
2. Write the findings to a single Markdown file, citing each claim's source.
3. Save it where the repo already keeps such notes; match the existing convention, and if there is none, put it somewhere sensible and say where.
