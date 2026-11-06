---
name: diagnosing-bugs
description: "Diagnose hard bugs with a reproducible feedback loop."
license: MIT
metadata:
  author: Matt Pocock and Skillz contributors
  source: mattpocock/skills
  source-commit: 4ae2317ddb22b046e26455e4f9c9b3aaaf62212d
  adaptation: curated-rewrite
  owner: software-factory
  risk: medium
  capabilities: mattpocock,bug-diagnosis
---

# Diagnose a hard bug

Use for a bug or regression that needs investigation. Start with the user's
actual symptom, expected behavior, affected version or environment, and the
available evidence. Separate an observed failure from a suspected cause.
A small obvious fix does not need a full investigation ceremony.

## Build a useful feedback loop

Inspect enough code and configuration to choose a test or probe that reaches
the failing behavior. Prefer a targeted test, fixture-driven CLI call, local
HTTP request, browser assertion, or sanitized trace replay. The signal must
detect the reported symptom, not just a nearby exception or a clean exit.

Run it against the affected candidate and record the command, revision, inputs,
expected result, and observed result. Reduce setup and inputs while retaining
the failure. Verify the original scenario as well as the minimized case.

For intermittent bugs, record seeds, timing, trigger frequency, and outcomes
over an appropriate sample. A single passing attempt does not prove a fix.
Stress tests, fuzzing, and bisection need bounded time and resources. Run Git
bisection in a task-owned checkout so another actor's branch is preserved.

Use isolated fixtures for mutations, crash probes, and rollback tests.
A thrown exception is not process termination, and a mocked transaction is
not evidence of database rollback. Live traffic, customer data, paid calls,
and production instrumentation require authority for that environment.
Keep secrets and private records out of commands, logs, and shared evidence.

If the environment or data prevents reproduction, state exactly what was tried
and which access or sanitized artifact would distinguish the remaining cases.
Continue safe investigation, but do not claim the symptom is reproduced or fixed.

## Test causes, then fix

Form competing explanations proportional to the uncertainty. Give each a
prediction that can be tested. For a straightforward defect, do not manufacture
a quota of hypotheses. Change one relevant variable at a time and prefer
targeted debugger inspection or bounded instrumentation over broad logging.

For a performance regression, use a comparable workload and profile the
measured bottleneck. Preserve correctness and authorization while measuring.

Once evidence identifies the cause, make a scoped correction and keep a
regression check at the seam that actually exposes the failure. Verify it
failed before the correction and passes afterward when that evidence is
available. A shallow mock or an assertion that repeats the implementation
does not lock down the bug.

Rerun the original feedback loop and relevant neighboring behavior. Remove
this task's temporary instrumentation and preserve useful sanitized evidence.
Do not delete another actor's diagnostics or reset unrelated changes.
Report the supported cause, correction, checks, and remaining uncertainty.
