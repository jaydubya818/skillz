---
name: principle-experience-first
description: "Apply when scope threatens a polished, clear, and trustworthy user experience."
license: MIT
metadata:
  author: jstack-maintainers
  source: michael-denyer/pstack-claude
  source-version: "0.9.102"
  source-commit: 356c6e0f978df729eb16f227d795f34d221c5aad
  owner: software-factory
  risk: low
  capabilities: jstack,engineering-principle
user-invocable: false
---

# Experience First

When implementation convenience conflicts with user delight, choose delight.

- Every feature, control, and option must be justified
- Ship less, ship better (polished experience with three features beats rough one with ten)
- Prototype before committing (design decisions are cheaper in throwaway HTML than production code)
- Get the details right (transitions, alignment, spacing, feedback, error states)
- Tighten the core loop (every feature should serve the central workflow or get out of the way)

The user is whoever consumes the work. For a UI that is the end user. For a library or an internal API it is the colleague who imports it. The engineer who maintains the code next is a user too. Weigh their experience the same way, and explain impact from their perspective.

Foundations should serve the experience. Foundational thinking governs the *sequence* of work. This principle governs the *target*.
