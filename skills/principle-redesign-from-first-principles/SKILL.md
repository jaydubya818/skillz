---
name: principle-redesign-from-first-principles
description: "Apply when a requirement breaks a foundational assumption and needs coherent redesign."
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

# Redesign From First Principles

When integrating a change, don't bolt it onto the existing design. Redesign as if the requirement had been a foundational assumption from the start.

- Read all affected files and understand the current design
- Ask: "if we were writing this from scratch with this new requirement, what would we build?"
- Propagate the change through every reference: types, docs, examples, rationale sections
- Think about the whole redesign, then deliver it incrementally

This is the method for preserving option value when integrating changes into an existing design.
