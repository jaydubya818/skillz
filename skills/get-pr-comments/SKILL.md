---
name: get-pr-comments
description: "Use when pull-request feedback needs to be fetched and summarized for action."
license: MIT
metadata:
  author: jstack-maintainers
  source: michael-denyer/pstack-claude
  source-version: "0.9.102"
  source-commit: 356c6e0f978df729eb16f227d795f34d221c5aad
  owner: software-factory
  risk: low
  capabilities: jstack,pull-request-workflow
---

# Get PR comments

## Trigger

Need a concise, actionable summary of feedback on the active pull request.

## Workflow

1. Resolve the active PR for the current branch.
2. Fetch review comments and discussion comments.
3. Group feedback by severity and actionability.
4. Return a concise action list.

## Output

- Grouped feedback summary
- Action list ordered by priority
- Open questions that still need clarification
