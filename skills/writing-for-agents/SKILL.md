---
name: writing-for-agents
description: "Write or review agent instructions and skill documents."
license: MIT
metadata:
  author: Matt Pocock and Skillz contributors
  source: mattpocock/skills
  source-commit: 4ae2317ddb22b046e26455e4f9c9b3aaaf62212d
  adaptation: curated-rewrite
  owner: software-factory
  risk: low
  capabilities: mattpocock,agent-instructions
---

# Write reliable instructions for agents

Use when authoring or reviewing a skill, repository instructions, or another
document an agent follows. Define the task it should improve and the intended
reader. Keep the user's objective, product decisions, and existing authority
above the workflow.

## Make discovery precise

A pointer should say what a document covers and when to read it. Use distinct
trigger conditions rather than a list of synonyms for the same case. Keep
always-loaded descriptions short; put detailed procedures in the selected
document. Do not make every task load the entire collection.

Keep guidance in one authoritative place. Link to existing commands or
configuration instead of maintaining a second copy of facts the agent can
inspect. Keep a definition beside its conditions and exceptions.

## Structure around the task

State the needed inputs, intended result, and relevant constraints. Order
dependent actions and name the observable condition that finishes each step.
Use concrete evidence such as a saved artifact, verified status, or a check
result instead of an instruction to feel confident.

Keep shared steps in the entrypoint. Move substantial branch-specific detail
to a linked reference and say when that reference applies. Split documents
when tasks have separate triggers or outcomes, not merely to meet a line count.
A short workflow needs no routing layer.

Use familiar terms consistently and define project-specific terms before
depending on them. Prefer direct descriptions of the intended behavior.
Keep explicit prohibitions where they protect a real authority, privacy, or
destructive-action boundary; brevity is not a reason to remove those limits.

Avoid mandatory delegation, fixed model choices, arbitrary iteration counts,
or whole-repository changes unless the requested workflow actually needs them.
For retries or external actions, give a stopping condition and preserve
existing approval and budget rules.

## Package and verify

For a skill, provide a matching folder name and frontmatter name, a precise
description, and only resources the workflow needs. Preserve supported runtime
metadata and existing invocation policy. Automatic discovery is the default
for new skills unless the user requests explicit-only behavior; runtime flags
have client-specific semantics and must be checked for the target client.

Check local references, runnable examples, frontmatter, and the promised output.
Read the instructions against realistic requests, including missing inputs,
an unavailable tool, and an already authorized action. Check that the workflow
keeps the original task's scope and does not ask again for permission already
granted. Static validation checks packaging; it does not prove how a model
will follow the instructions.

Return the changed instruction paths, intended behavior, validation, and
material limits. Publishing, installing globally, or altering unrelated
repository instructions follows the task's existing authority.
