---
name: mattpocock-ask-matt
description: "Choose a Matt Pocock skill or workflow."
license: MIT
disable-model-invocation: true
metadata:
  source: mattpocock/skills
  source-commit: 4ae2317ddb22b046e26455e4f9c9b3aaaf62212d
  upstream-name: ask-matt
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

# Ask Matt

You don't remember every skill, so ask.

Before stating what a skill does or recommending a step be skipped, read that skill's SKILL.md: the summaries here are for orientation only.

A **flow** is a path through the skills. Most paths run along one **main flow**, and two **on-ramps** merge onto it. Everything else is standalone, or a vocabulary layer that runs underneath.

## The main flow: idea → ship

The route most work travels. You have an idea and want it built.

1. **`/mattpocock-grill-with-docs`** sharpens the idea by interview. Start here whenever you are **working in a working directory**: it's stateful, retaining what it learns in `GLOSSARY.md` and ADRs. (No working directory? Use `/mattpocock-grill-me` instead, covered under Standalone. Both run the same `/mattpocock-grilling` primitive; `grill-with-docs` is the one that leaves a paper trail, which makes it the better of the two whenever a repo is there to leave it in.)
2. **Branch: can you settle every question in conversation?** If a question needs a runnable answer (state, business logic, a UI you have to see), detour through a prototype, bridged by **`/mattpocock-handoff`** in both directions (a prototype lives in its own directory, which is exactly what `/mattpocock-handoff` is for; see Phase boundaries):
   - **`/mattpocock-handoff`** out, then open a fresh session against that file,
   - **`/mattpocock-prototype`** to answer the question with throwaway code,
   - **`/mattpocock-handoff`** back what you learned, and reference it from the original idea thread.
3. **Branch: is this a multi-session build?**
   - **Yes** → **`/mattpocock-to-spec`** (turn the thread into a spec), then **`/mattpocock-to-tickets`** to split it into tracer-bullet tickets, each declaring its **blocking edges**. Then work the tickets one of two ways:
     - **`/mattpocock-implement`** per ticket, **`/clear`ing context between each one**. On a local tracker that's one file per ticket under `.scratch/<feature>/issues/`, worked blockers-first by hand; on a real tracker the edges become native blocking links, so any ticket whose blockers are done can be grabbed. Each ticket is self-contained, so the last one's context is disposable.
     - **`/mattpocock-implement-spec`** for the whole spec in one run. It reads the tickets as a **task graph**, runs implementer subagents across the ready **frontier** in parallel, and lands everything on one **integration branch**. Reach for it when you'd rather orchestrate the build than drive each ticket yourself.
   - **No** → **`/mattpocock-implement`** right here, in the same context window.

   Either way, the code gets built by driving **`/mattpocock-tdd`** (one red-green slice at a time) and closes out with **`/mattpocock-code-review`**, a two-axis review (Standards + Spec) of the diff. `/mattpocock-implement` runs both per ticket; `/mattpocock-implement-spec`'s implementers each drive `/mattpocock-tdd`, and it runs one `/mattpocock-code-review` over the integration branch. Reach for **`/mattpocock-tdd`** on its own when you just want to build a concrete behaviour test-first without a full spec, and **`/mattpocock-code-review`** on its own whenever you want to review a branch or PR against a fixed point.

   When the work goes up as a pull request, **`/mattpocock-pr`** shapes the body: the smallest visual that shows the change, before/after evidence that it works, and a one-way or two-way door call. It's model-invoked, so the agent reaches for it whenever it writes a PR.

4. **`/mattpocock-retro`** closes the loop. After a build, and especially one that went sideways, it looks back over the session and suggests changes to the agent's **environment**, not the code: navigation pointers, automated checks, the coding standards `/mattpocock-code-review` enforces, steering files, tooling. Mechanical mistakes become deterministic checks; judgement calls become coding standards. The next build then starts from a better environment.

### Context hygiene

Keep steps 1–3 in **one unbroken context window** (don't compact or clear until after `/mattpocock-to-tickets`) so the grilling, spec, and tickets all build on the same thinking. Each `/mattpocock-implement` then starts fresh, working from the ticket. Run `/mattpocock-retro` in the session it's looking back on, before you clear; after clearing, point it at that session's log instead.

The limit on this is the **[smart zone](https://www.aihero.dev/ai-coding-dictionary/smart-zone)**: the window (~150k tokens on state-of-the-art models) within which the model still reasons sharply. If a session approaches it before `/mattpocock-to-tickets`, don't push on degraded; `/compact` at the nearest phase boundary and carry on (see Phase boundaries).

## On-ramps

A starting situation that generates work, then merges onto the main flow.

- **Bugs and requests piling up** → **`/mattpocock-triage`**. It moves issues through triage roles and produces agent-ready issues, which **`/mattpocock-implement`** later picks up.

  Triage is only for issues **you didn't create**: bug reports, incoming feature requests, anything that arrives raw. Tickets that `/mattpocock-to-tickets` produced are already agent-ready, so **don't triage them**.

- **Something's broken** → **`/mattpocock-diagnosing-bugs`**. For the hard ones: the bug that resists a first glance, the intermittent flake, the regression that crept in between two known-good states. It refuses to theorise until it has a **tight feedback loop** (one command that already goes red on *this* bug), then fixes with a regression test. Once the fix is in, run **`/mattpocock-retro`** in the same session to ask what would have prevented the bug; where the real finding is that there's no good seam to lock it down, that's a job for **`/mattpocock-improve-codebase-architecture`**.

- **A huge, foggy effort: a greenfield project or a huge feature build, too big for one session** → **`/mattpocock-wayfinder`**, the most cognitively demanding flow here. When the way from here to the destination isn't visible yet, it charts a **shared map** of **decision tickets** on the issue tracker and resolves them one at a time, producing **decisions, not deliverables**, until the fog is pushed back and the way is clear. Where **`/mattpocock-grill-with-docs`** sharpens an idea you can hold in one session, wayfinder is for the idea you can't, and it's slower and denser, so save it for exactly that, never a well-scoped feature.

  When the map clears, **it hands off, it doesn't build**: merge onto the main flow at **`/mattpocock-to-spec`**, which collapses the map's linked decisions into a buildable plan, then `/mattpocock-to-tickets` and `/mattpocock-implement` as usual. Looping the map straight into `/mattpocock-implement` skips that collapse and throws the linked detail away, so go straight to `/mattpocock-implement` only when the effort turned out genuinely small.

## Codebase health

Not feature work, just upkeep.

- **`/mattpocock-improve-codebase-architecture`** runs whenever you have a spare moment to keep the codebase good for agents to operate in. It surfaces **deepening opportunities**; picking one _generates an idea_ you can take into the main flow at `/mattpocock-grill-with-docs`. It's the survey that finds the candidates; **`/mattpocock-codebase-design`** (below) is the bench you design the chosen one on.

## Vocabulary underneath

Two model-invoked references that run *beneath* the other skills, each the single source of truth for its vocabulary. Reach for them directly when the **words**, not the process, are the problem; or let the skills above pull them in.

- **`/mattpocock-domain-modeling`**: sharpen the project's *domain* language: challenge a fuzzy term, resolve an overloaded word ("account" doing three jobs), record a hard-to-reverse decision as an ADR. It's the active discipline `/mattpocock-grill-with-docs` drives to keep `GLOSSARY.md` a clean glossary.
- **`/mattpocock-codebase-design`** is the deep-module vocabulary (module, interface, depth, seam, adapter, leverage, locality) for designing a module's *shape*: a lot of behaviour behind a small interface at a clean seam. `/mattpocock-tdd` and `/mattpocock-improve-codebase-architecture` both speak it.

## Phase boundaries

A **phase** is a chunk of work inside a session: the grilling, the implementation, the QA. At the **boundary** between two of them you have five options, and picking between them is the fuzziest decision in this whole map:

- **Continue**: stay put. Costs nothing, loses nothing.
- **`/clear`**: empty the window, when nothing here matters to what's next.
- **`/mattpocock-handoff`** writes a portable markdown file. Narrow: only for a **new harness**, a **new directory**, a **colleague**, or forking a side task **mid-phase**. What it buys is portability.
- **Subagent**: send a tightly-scoped task to its own window and get a report back.
- **`/compact`** compresses this context and seeds a fresh session with it. The **default**, at the bottom of the tree rather than the first reach.

Read [PHASE-BOUNDARIES.md](PHASE-BOUNDARIES.md) for the ordered tree: the five questions, the reasoning behind each branch, and why the primary-source cost makes **Continue** the one to rule out first. Make the decision **at** a boundary; mid-phase, continue or split the rest into subagents.

## Standalone

Off the main flow entirely.

- **`/mattpocock-grill-me`**: the same relentless interview as `/mattpocock-grill-with-docs`, but **stateless**: it saves nothing locally and builds no `GLOSSARY.md`. Reach for it when you are **not working in a working directory** (sharpening a plan, a design, a piece of writing, anything with no repo under it). If you are in a working directory, use `/mattpocock-grill-with-docs` instead: it runs the same interview and leaves a paper trail, so it is strictly the better one.
- **`/mattpocock-grilling`** is the interview primitive itself: rounds, the frontier, facts are the agent's job and decisions are yours. `/mattpocock-grill-me` and `/mattpocock-grill-with-docs` are the two named ways in, and `/mattpocock-triage`, `/mattpocock-wayfinder` and `/mattpocock-improve-codebase-architecture` all run it internally. Reach for it directly only when you want the interview with no wrapper around it.
- **`/mattpocock-prototype`** is a small, throwaway program that answers one design question: does this state model feel right, or what should this UI look like. Throwaway is a constraint on how the code is written, not a promise to destroy it: the answer folds into the real code, and the prototype itself is kept as a **primary source** on a `prototype/<name>` branch out of main, pointed at from the implementation issue. It's the detour in step 2 of the main flow, but reach for it any time a design question is hard to settle on paper.
- **`/mattpocock-research`**: delegate reading legwork to a **background agent**: it investigates a question against **primary sources**, then leaves a cited Markdown file in the repo. Keep working while it reads. The file it produces is something to take *into* the main flow at `/mattpocock-grill-with-docs`, since research feeds the thinking rather than replacing it.
- **`/mattpocock-to-questionnaire`** comes in when the thing blocking you isn't in your head or the codebase but in **someone else's**, and it writes them a questionnaire to fill in. It's the inverse of `/mattpocock-grill-me`: instead of interviewing you about the subject, it interviews you about the **send** (who it's going to, what you need back) and aims the questions at the gap. What comes back is material for `/mattpocock-grill-with-docs` or `/mattpocock-to-spec`.
- **`/mattpocock-wizard`** is for the steps only a **human** can take: provisioning infrastructure, setting up credentials or CI secrets, clicking through an unfamiliar third-party dashboard, running a one-off migration or cutover. It generates an interactive bash script that opens each URL, captures each value, and writes it into `.env` and GitHub secrets, so the procedure stops being something you re-explain to an agent every time. Model-invoked, so the agent reaches for it the moment it hits a wall only you can pass. If the agent could just do it itself, it should; this is for where a human is genuinely in the loop.
- **`/mattpocock-wait-what`** is the corrective for a message that didn't land. Use it mid-conversation, inside any other skill, and the agent re-pitches what it just said with the context you were missing, in plain English, using the `GLOSSARY.md` vocabulary. It works after the fact; `/mattpocock-grill-with-docs` is the upfront cure, because a shared language agreed early is what stops the jargon arriving at all.
- **`/mattpocock-teach`**: learn a concept over multiple sessions, using the current directory as a stateful workspace.
- **`/mattpocock-writing-for-agents`** is the reference for writing documents agents consume: skills, AGENTS.md, pointed-at docs.

## Precondition

**`/mattpocock-setup-matt-pocock-skills`**: run before your first engineering flow to configure the issue tracker, triage labels, and doc layout the other skills assume. Custom issue trackers also work.
