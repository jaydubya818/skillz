---
name: domain-modeling
description: "Define business terms, domain rules, and bounded contexts."
license: MIT
metadata:
  author: Matt Pocock and Skillz contributors
  source: mattpocock/skills
  source-commit: 4ae2317ddb22b046e26455e4f9c9b3aaaf62212d
  adaptation: curated-rewrite
  owner: software-factory
  risk: low
  capabilities: mattpocock,domain-vocabulary
---

# Business domain modeling

Use when business terminology, relationships, or domain boundaries need to be
defined or corrected. Read the project's existing glossary, domain map, product
docs, relevant ADRs, and code before proposing a model. A coding refactor alone
does not need a new glossary.

## Resolve the business meaning

Identify overloaded terms and distinguish concepts by their business meaning.
For example, an account, a person, and a company may have different identities
and permissions. Use the product's actual nouns rather than imposing those
examples on it.

Check definitions against concrete scenarios: who owns the object, which
states it can reach, which transitions are allowed, and what happens at the
boundary with another business area. Label invented edge cases as questions
or probes, not established requirements. Compare the stated rule with actual
code and observed behavior. A contradiction needs a decision; existing code
does not automatically establish the intended business rule.

Keep approved definitions separate from agent proposals. Resolve consequential
product choices with the product owner. Routine wording corrections can follow
existing scope and conventions.

## Capture the resolved model

Use the established documentation location and format. Create a glossary only
when there are resolved terms to record. If no convention exists, a compact
entry can contain the canonical term, its business definition, the context
where it applies, and ambiguous alternatives to avoid. Keep implementation
instructions and speculative requirements out of glossary entries.

Use separate context glossaries only when the business meanings actually
differ. Preserve a project's existing glossary map; do not introduce multiple
contexts merely because the repository has several folders.

Record durable, approved tradeoffs in an ADR when a future reader needs the
reason. Follow the existing ADR convention, preserve historical decisions,
and distinguish proposed from accepted status. Do not invent approval or
change a prior decision through a terminology edit.

Before handing off, check that the recorded definitions agree with the
approved examples and identify code or docs that still disagree. Return the
changed paths and unresolved choices. Writing the model does not authorize
renaming code, migrating data, or changing product behavior.
