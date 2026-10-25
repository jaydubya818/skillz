---
name: principle-migrate-callers-then-delete-legacy-apis
description: "Apply when replacing an internal API without leaving ambiguous dual paths."
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

# Migrate Callers Then Delete Legacy APIs

- Update tests to assert the new contract, and delete tests that only protect pre-refactor implementation details

**When this applies:**
- No external users depend on backward compatibility
- The project can absorb coordinated breaking changes
- The new API is part of a simplification or refactor initiative
