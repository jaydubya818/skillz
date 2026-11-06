# Skill mechanics

Keep a portable `name` and `description` on every skill. The description states
the capability and its trigger. Put detailed instructions in `SKILL.md` and
conditional detail in linked supporting files.

Automatic discovery is the default when authoring a new skill. Use explicit-only
invocation when the user requests it, and preserve an imported skill's existing
policy. Claude Code's `disable-model-invocation: true` and Codex's
`policy.allow_implicit_invocation: false` in `agents/openai.yaml` are client
settings. Do not assume another client implements either setting. Explicit-only
skills still retain descriptions for human discovery and package metadata.

A router names the available skills and explains when to read each one. Reading
a referenced file through host file tools differs from automatic skill selection.
Respect the host's loader and invocation rules rather than assuming all clients
can invoke another skill with the same command.

Split a skill when independent requests need independent triggers, or when a
conditional reference would otherwise obscure the common workflow. Keep shared
reference in one maintained file and link it from its callers.

See [SKILL.md](SKILL.md) for instruction-writing guidance.
