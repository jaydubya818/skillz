---
name: principle-encode-lessons-in-structure
description: "Apply when a repeated instruction should become enforceable in tests, lint, metadata, or tools."
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

# Encode Lessons in Structure

If the lesson needs judgment and cannot be encoded, make the instruction more prominent and add an example of the failure mode.

**Corollary:** If the fix is structural, only use the structural fix. The instruction is the symptom.
