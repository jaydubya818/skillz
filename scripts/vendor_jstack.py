#!/usr/bin/env python3
"""Build the Jstack distribution from the upstream pstack Agent Skills tree."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess


REPO_ROOT = Path(__file__).resolve().parent.parent
DESTINATION = REPO_ROOT / "skills"
MANIFEST = REPO_ROOT / "vendor" / "jstack.json"
EXCLUDED = {"unslop": "the collection keeps its existing enhanced definition"}
LOCAL_NAME_BY_SOURCE = {"setup-pstack": "setup-jstack"}

JSTACK_BRANDING_REPLACEMENTS = (
    ("setup-pstack", "setup-jstack"),
    ("pstack-models", "jstack-models"),
    ("pstack:poteto-agent", "jstack:poteto-agent"),
    ("pstack:comment-sicko", "jstack:comment-sicko"),
    ("Configure which models pstack uses", "Configure which models Jstack uses"),
    ("configure pstack models", "configure Jstack models"),
    ("with the pstack workflow", "with the Jstack workflow"),
    ("for pstack workflows", "for Jstack workflows"),
    ("pstack workflows", "Jstack workflows"),
    ("pstack skills", "Jstack skills"),
    ("pstack skill", "Jstack skill"),
    ("pstack SKILL.md", "Jstack SKILL.md"),
    ("pstack's model choices", "Jstack's model choices"),
    ("pstack poteto-mode tooling", "Jstack poteto-mode tooling"),
    ("Codex tool mapping for pstack", "Codex tool mapping for Jstack"),
    ("pstack / Claude action", "Jstack / Claude action"),
    ("skills pstack references", "Jstack references"),
    ("named in pstack", "named in Jstack"),
    ("# Setup pstack", "# Setup Jstack"),
    ("# pstack model configuration", "# Jstack model configuration"),
    ("fix(pstack):", "fix(jstack):"),
    ("such as `pstack`", "such as `jstack`"),
    (
        "Role defaults, stamped from `plugins/pstack/models.json` (edit there, rerun `tools/generate.mjs`).",
        "Role defaults originate from the upstream `plugins/pstack/models.json`. Refresh them through `scripts/vendor_jstack.py` after reviewing the upstream change.",
    ),
    (
        "Stamped from `plugins/pstack/models.json` (edit there, rerun `tools/generate.mjs`).",
        "Defaults originate from the upstream `plugins/pstack/models.json`. Refresh them through `scripts/vendor_jstack.py` after reviewing the upstream change.",
    ),
)

SHORT_DESCRIPTIONS = {
    "architect": "Design types and module boundaries before coding",
    "arena": "Compare parallel solutions and synthesize the best",
    "automate-me": "Turn recurring work preferences into a personal skill",
    "babysit": "Shepherd an authorized pull request to a ready state",
    "blast-radius": "Find and prove hidden downstream change risks",
    "bro": "Restate a technical answer in plain human language",
    "create-verification-skill": "Create a project-specific real-behavior verifier",
    "deslop": "Remove unnecessary AI-generated code complexity",
    "figure-it-out": "Design an auditable workflow for unusual work",
    "fix-ci": "Diagnose and fix failing pull-request checks",
    "fix-merge-conflicts": "Resolve merge conflicts and verify the result",
    "get-pr-comments": "Fetch and summarize actionable pull-request feedback",
    "how": "Explain how a subsystem works and where it belongs",
    "interrogate": "Run an adversarial multi-model implementation review",
    "maintain-verification-skill": "Audit and refresh a project's verification skill",
    "make-pr-easy-to-review": "Improve pull-request clarity without behavior changes",
    "no-comments": "Review comments and encode accepted constraints",
    "poteto-mode": "Route nontrivial work through rigorous workflows",
    "recall": "Reconstruct recent project context from scoped records",
    "reflect": "Turn approved session learnings into durable improvements",
    "setup-jstack": "Configure per-role model choices for Jstack workflows",
    "show-me-your-work": "Keep an auditable decision log for long-running work",
    "swarm": "Coordinate parallel workers and return one checked result",
    "tdd": "Reproduce a bug with a focused test before fixing it",
    "teach": "Explain what a system is, how it works, and why",
    "technical-writing": "Write clear technical prose for tired engineers",
    "thermo-nuclear-code-quality-review": "Run a strict maintainability and structure review",
    "typescript-best-practices": "Apply disciplined type modeling to TypeScript code",
    "what-did-i-get-done": "Summarize authored work for a concrete time period",
    "why": "Investigate and cite why a system was designed this way",
}

MEDIUM_RISK = {
    "architect",
    "arena",
    "automate-me",
    "babysit",
    "create-verification-skill",
    "deslop",
    "figure-it-out",
    "fix-ci",
    "make-pr-easy-to-review",
    "maintain-verification-skill",
    "no-comments",
    "reflect",
    "setup-jstack",
    "swarm",
    "tdd",
}
HIGH_RISK = {"fix-merge-conflicts", "poteto-mode"}
ACTIVATION_RE = re.compile(
    r"\b(use (?:this skill )?(?:when|for)|invoke when|apply when|trigger|activates? when)\b",
    re.IGNORECASE,
)

DESCRIPTION_OVERRIDES = {
    "principle-never-block-on-the-human": (
        "Apply when tempted to ask about a low-risk, reversible implementation detail inside the authorized scope. "
        "Proceed and present the result, but preserve product-owner decisions, approval policy, and external-write boundaries."
    ),
}

HARDENINGS = {
    "poteto-mode": [
        (
            "`codex-tools.md` is not a cross-runtime map.\n\n",
            "`codex-tools.md` is not a cross-runtime map.\n\n"
            "**Governance precedence.** When Mission Control governs the task, read and follow "
            "the **mission-control-delivery** skill first. Its execution contract controls authority, "
            "lineage, evidence, and state transitions. System, user, and repository instructions "
            "also take precedence. Poteto mode selects methods; it never broadens the authorized "
            "scope or grants permission to publish, message, merge, deploy, delete, or spend.\n\n",
        ),
        (
            "**Just do it.** Use any MCP tool. Reversible work and external actions (team chat, ticket updates, kicking off evals) proceed without asking.\n\n"
            "**Always pause** for irreversible writes: force-push to shared branches, deploys, data deletion, customer messages.",
            "**Proceed inside the contract.** Use available tools for read-only investigation and low-risk, reversible implementation work already authorized by the task.\n\n"
            "**Pause at authority boundaries.** Team chat, ticket updates, eval launches, publishing, merges, deploys, destructive cleanup, customer messages, spending, and writes outside the authorized repository scope require explicit task authority. Product and preference decisions remain with the user even when an experiment can inform the choice.",
        ),
        (
            "- Broken skill mid-task → fix it in its own PR. Don't block. Don't silently work around it.",
            "- Broken skill mid-task → record the failure and propose a focused fix. Implement or publish that fix only when it falls inside the authorized scope.",
        ),
    ],
    "principle-never-block-on-the-human": [
        (
            "The human supervises asynchronously. Agents must stay unblocked: make reasonable decisions, proceed, and let the human course-correct after the fact.",
            "The human can supervise implementation asynchronously. Make reasonable low-risk decisions inside the authorized scope, then present the result for review.",
        ),
        (
            "- **Proceed, then present.** Do the work, show the result. Don't ask \"should I do X?\" Do X, explain why.",
            "- **Proceed, then present.** Handle reversible implementation details that do not change product intent, authority, cost, or external state. Show the result and explain why.",
        ),
        (
            "- **Irreversible actions** (force-push, delete production data, send external messages) still require confirmation.\n"
            "- **Reversible actions** (write code, edit notes, split tasks) should proceed without blocking.\n"
            "- **Product direction** comes from the human; *execution* should not block.",
            "- **Approval policy wins.** Mission Control contracts plus system, user, and repository instructions define what the agent may do.\n"
            "- **External writes need authority.** Messages, tickets, pull-request mutations, eval launches, publishing, merges, deploys, spending, and destructive cleanup do not become authorized merely because they are reversible.\n"
            "- **Product direction stays with the human.** Experiments can inform a decision; they do not make the decision.\n"
            "- **In-scope implementation should not stall.** Write code, edit local notes, and split internal tasks when those actions stay within the accepted outcome and scope.",
        ),
    ],
    "reflect": [
        (
            "Backlog items file to whatever devex / backlog tracker your team uses automatically. Only the Accepted list waits for approval.",
            "File Backlog items only when the task authorizes writes to the named devex or backlog tracker. Otherwise return them as proposed backlog entries. The Accepted list always waits for approval.",
        ),
    ],
    "automate-me": [
        (
            "A guided flow for turning the user's working conventions into a skill agents will follow.",
            "A guided flow for turning the user's working conventions into a skill agents will follow. Creating or editing a user-scoped skill requires the user's explicit choice of user scope; otherwise keep the output project-local.",
        ),
    ],
    "create-verification-skill": [
        (
            "This skill generates that as a project-local skill (`.claude/skills/verify/`) tailored to the repo. Name it `verify`.",
            "This skill generates that as a project-local skill tailored to the repo. Use `.claude/skills/verify/` for Claude Code or `.codex/skills/verify/` for Codex. When both harnesses need one canonical definition, place it under `.agents/skills/verify/` and add conflict-checked relative links from both harness directories. Name it `verify`.",
        ),
        (
            "Write `.claude/skills/verify/SKILL.md` with YAML frontmatter",
            "Write the selected project-local `verify/SKILL.md` with YAML frontmatter",
        ),
        (
            "Create `.claude/skills/verify/features/README.md` plus one file per user-facing feature",
            "Create `features/README.md` under the selected `verify` skill plus one file per user-facing feature",
        ),
    ],
    "recall": [
        (
            "# Recall\n\n",
            "# Recall\n\nOn Codex or another harness, use its current-task history APIs or documented workspace-scoped transcript location. Do not assume Claude Code's transcript path exists, and never cross workspace boundaries.\n\n",
        ),
    ],
    "show-me-your-work": [
        (
            "At the end of the run, before handing back, check the log told the truth. Read this run's transcript under Claude Code's per-project transcripts directory at `~/.claude/projects/<encoded-cwd>/`.",
            "At the end of the run, before handing back, check the log told the truth. On Claude Code, read this run's transcript under its per-project transcript directory at `~/.claude/projects/<encoded-cwd>/`. On Codex or another harness, use its current-task history API or documented workspace-scoped transcript location.",
        ),
    ],
    "poteto-mode/playbooks/opening-a-pr.md": [
        (
            "**Worktree.** Work from a git worktree off main; subagents inherit it. Multiple `Agent` calls on the same branch each get their own worktree, or `git fetch && git reset --hard origin/<branch>` between them. Dirty branch with unrelated work: patch out, fresh worktree, apply. Snarled worktree: reset from main, redo minimally.",
            "**Authority.** Commit, push, or open a pull request only when the user's request or Mission Control execution contract authorizes that publication step. Otherwise stop with a verified local handoff.\n\n**Worktree.** Work from a git worktree off main; subagents inherit it. Give each writing agent its own branch and worktree. Never reset a shared or dirty worktree to coordinate agents. Leave unrelated work untouched and create a fresh worktree for the authorized change.",
        ),
    ],
    "poteto-mode/playbooks/worktree-cleanup.md": [
        (
            "`scratch:N` is untracked throwaway, safe to drop, but name the files. Per Autonomy, clean and merged and not-in-use proceeds; `wip` and in-use pause.",
            "`scratch:N` is untracked and may still be valuable, so name the files. Get explicit approval for every deletion target; `wip` and in-use always stay held back.",
        ),
        (
            "Per path, `git worktree remove --force <path>`; if the dir survives on ignored build artifacts, `rm -rf` it, then `git worktree prune`.",
            "Per approved, explicit path, use `git worktree remove <path>` and let Git refuse unsafe removal. If ignored artifacts keep the directory in place, report the exact path and size for a separate cleanup decision; do not escalate to recursive deletion inside this playbook. Then run `git worktree prune`.",
        ),
    ],
    "poteto-mode/playbooks/autonomous-run.md": [
        (
            "Put out-of-band fixes in their own PR. Do not park reversible work for the human or use `AskUserQuestion`.",
            "Put an out-of-band fix in its own PR only when the standing task authorizes that scope and publication. Otherwise log it as follow-up work and return to the predicate.",
        ),
    ],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Vendor michael-denyer/pstack-claude skills into this collection."
    )
    parser.add_argument("source", type=Path, help="path to a pstack-claude checkout")
    parser.add_argument("--replace", action="store_true", help="replace a previous vendored copy")
    return parser.parse_args()


def git_value(source: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=source, check=True, text=True, capture_output=True
    ).stdout.strip()


def risk_for(name: str) -> str:
    if name in HIGH_RISK:
        return "high"
    if name in MEDIUM_RISK:
        return "medium"
    return "low"


def capability_for(name: str) -> str:
    if name.startswith("principle-"):
        return "engineering-principle"
    if name in {"babysit", "fix-ci", "fix-merge-conflicts", "get-pr-comments", "make-pr-easy-to-review"}:
        return "pull-request-workflow"
    if name in {"architect", "arena", "interrogate", "reflect", "swarm"}:
        return "multi-agent-workflow"
    if name in {"how", "why", "recall", "teach", "what-did-i-get-done"}:
        return "engineering-research"
    if name in {"tdd", "blast-radius", "create-verification-skill", "maintain-verification-skill"}:
        return "verification"
    return "engineering-workflow"


def decode_description(value: str, path: Path) -> str:
    value = value.strip()
    if value.startswith('"'):
        decoded = json.loads(value)
        if not isinstance(decoded, str):
            raise ValueError(f"description is not a string: {path}")
        return decoded
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("''", "'")
    return value


def apply_jstack_branding(path: Path) -> None:
    """Rename local product identifiers without rewriting upstream provenance."""
    for target in path.rglob("*"):
        if not target.is_file() or "licenses" in target.parts:
            continue
        try:
            text = target.read_text()
        except UnicodeDecodeError:
            continue
        branded = text
        for old, new in JSTACK_BRANDING_REPLACEMENTS:
            branded = branded.replace(old, new)
        if branded != text:
            target.write_text(branded)


def normalize_skill(path: Path, *, version: str, commit: str) -> None:
    skill_file = path / "SKILL.md"
    text = skill_file.read_text()
    for old, new in HARDENINGS.get(path.name, []):
        if old not in text:
            raise ValueError(f"Jstack hardening anchor changed in {skill_file}: {old[:80]!r}")
        text = text.replace(old, new, 1)
    for relative_path, replacements in HARDENINGS.items():
        if "/" not in relative_path or not relative_path.startswith(f"{path.name}/"):
            continue
        target = path / relative_path.removeprefix(f"{path.name}/")
        target_text = target.read_text()
        for old, new in replacements:
            if old not in target_text:
                raise ValueError(f"Jstack hardening anchor changed in {target}: {old[:80]!r}")
            target_text = target_text.replace(old, new, 1)
        target.write_text(target_text)
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ValueError(f"missing frontmatter: {skill_file}")
    try:
        close = lines.index("---", 1)
    except ValueError as error:
        raise ValueError(f"unterminated frontmatter: {skill_file}") from error

    frontmatter = lines[1:close]
    name_line = next((line for line in frontmatter if line.startswith("name:")), None)
    description_line = next((line for line in frontmatter if line.startswith("description:")), None)
    if name_line is None or description_line is None:
        raise ValueError(f"missing name or description: {skill_file}")
    name = name_line.split(":", 1)[1].strip()
    if name != path.name:
        raise ValueError(f"frontmatter name {name!r} does not match {path.name!r}")
    if any(line.startswith("metadata:") for line in frontmatter):
        raise ValueError(f"source already has metadata; review the upstream schema before updating: {skill_file}")

    description = DESCRIPTION_OVERRIDES.get(
        name, decode_description(description_line.split(":", 1)[1], skill_file)
    )
    if not ACTIVATION_RE.search(description):
        readable = name.replace("-", " ")
        description += f" Use this skill when the user asks for {readable} or the task clearly matches this workflow."
    if len(description) < 80:
        description += " Use it only when the current task clearly matches this focused workflow."

    preserved = [
        line
        for line in frontmatter
        if not line.startswith(("name:", "description:", "paths:"))
    ]
    new_frontmatter = [
        f"name: {name}",
        f"description: {json.dumps(description)}",
        "license: MIT",
        "metadata:",
        "  author: jstack-maintainers",
        "  source: michael-denyer/pstack-claude",
        f'  source-version: "{version}"',
        f"  source-commit: {commit}",
        "  owner: software-factory",
        f"  risk: {risk_for(name)}",
        f"  capabilities: jstack,{capability_for(name)}",
        *preserved,
    ]
    skill_file.write_text("\n".join(["---", *new_frontmatter, "---", *lines[close + 1 :]]) + "\n")

    display_name = " ".join(word.capitalize() for word in name.split("-"))
    if name.startswith("principle-"):
        short = f"Apply {name.removeprefix('principle-').replace('-', ' ')} with discipline"
        default = f"Use ${name} to apply this engineering principle to the current decision."
    else:
        short = SHORT_DESCRIPTIONS[name]
        default = f"Use ${name} to handle this task with the Jstack workflow and return a verified result."
    if not 25 <= len(short) <= 64:
        raise ValueError(f"short description for {name} must be 25-64 characters: {short!r}")
    agents = path / "agents"
    agents.mkdir(exist_ok=True)
    (agents / "openai.yaml").write_text(
        "interface:\n"
        f"  display_name: {json.dumps(display_name)}\n"
        f"  short_description: {json.dumps(short)}\n"
        f"  default_prompt: {json.dumps(default)}\n"
    )


def main() -> int:
    args = parse_args()
    source = args.source.expanduser().resolve()
    source_skills = source / "plugins" / "pstack" / "skills"
    if not source_skills.is_dir():
        raise SystemExit(f"not a pstack-claude checkout: {source}")
    version = (source / "VERSION").read_text().strip()
    commit = git_value(source, "rev-parse", "HEAD")
    remote = git_value(source, "remote", "get-url", "origin")
    if "michael-denyer/pstack-claude" not in remote:
        raise SystemExit(f"unexpected source remote: {remote}")

    source_names = sorted(path.name for path in source_skills.iterdir() if (path / "SKILL.md").is_file())
    imported_sources = [name for name in source_names if name not in EXCLUDED]
    imported = [LOCAL_NAME_BY_SOURCE.get(name, name) for name in imported_sources]
    conflicts = [name for name in imported if (DESTINATION / name).exists()]
    legacy_destinations = [
        DESTINATION / source_name
        for source_name, local_name in LOCAL_NAME_BY_SOURCE.items()
        if source_name != local_name and (DESTINATION / source_name).exists()
    ]
    if conflicts and not args.replace:
        raise SystemExit(f"destination skills already exist; rerun with --replace: {', '.join(conflicts)}")
    if legacy_destinations and not args.replace:
        names = ", ".join(path.name for path in legacy_destinations)
        raise SystemExit(f"legacy skill names still exist; rerun with --replace: {names}")

    for legacy in legacy_destinations:
        shutil.rmtree(legacy)

    for source_name, local_name in zip(imported_sources, imported, strict=True):
        destination = DESTINATION / local_name
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(source_skills / source_name, destination)
        apply_jstack_branding(destination)
        normalize_skill(destination, version=version, commit=commit)

    MANIFEST.parent.mkdir(exist_ok=True)
    MANIFEST.write_text(
        json.dumps(
            {
                "schema": "vendored-agent-skills/v1",
                "upstream": "https://github.com/michael-denyer/pstack-claude",
                "commit": commit,
                "version": version,
                "imported": imported,
                "excluded": EXCLUDED,
            },
            indent=2,
        )
        + "\n"
    )
    print(f"Built {len(imported)} Jstack skills from upstream {version} ({commit[:12]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
