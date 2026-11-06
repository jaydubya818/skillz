---
name: mattpocock-handoff
description: "Write a portable handoff for another session or directory."
license: MIT
disable-model-invocation: true
argument-hint: "What will the next session be used for?"
metadata:
  source: mattpocock/skills
  source-commit: 4ae2317ddb22b046e26455e4f9c9b3aaaf62212d
  upstream-name: handoff
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

Write a handoff document summarising the current conversation so a fresh agent can continue the work. Save to the temporary directory of the user's OS (`$TMPDIR`, else `/tmp`; `%TEMP%` on Windows) - not the current workspace.

Include a "suggested skills" section in the document, naming which skills the next agent should call the Skill tool for.

Do not duplicate content already captured in other artifacts (specs, plans, ADRs, issues, commits, diffs). Reference them by path or URL instead.

Redact any sensitive information, such as API keys, passwords, or personally identifiable information.

If the user passed arguments, treat them as a description of what the next session will focus on and tailor the doc accordingly.
