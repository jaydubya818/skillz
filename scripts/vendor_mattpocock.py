#!/usr/bin/env python3
"""Rebuild the namespaced Matt Pocock collection from its pinned checkout."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
REVISION = "4ae2317ddb22b046e26455e4f9c9b3aaaf62212d"
PREFIX = "mattpocock-"
DESCRIPTIONS = {
    "ask-matt": "Choose a Matt Pocock skill or workflow.",
    "code-review": "Review code against standards and spec.",
    "codebase-design": "Design deep, testable modules.",
    "diagnosing-bugs": "Diagnose bugs with reproducible probes.",
    "domain-modeling": "Resolve domain terms and record ADRs.",
    "grill-with-docs": "Interview a design and retain domain decisions in docs.",
    "implement": "Build a specified piece of work with TDD and review.",
    "implement-spec": "Implement a spec's ticket graph on one integration branch.",
    "improve-codebase-architecture": "Find and compare opportunities to deepen modules.",
    "pr": "Write PR bodies with evidence.",
    "prototype": "Prototype UI and logic decisions.",
    "research": "Research cited primary sources.",
    "retro": "Review a coding session for environment improvements.",
    "setup-matt-pocock-skills": "Configure Matt's tracker, triage labels, and domain docs.",
    "tdd": "Build with red-green-refactor.",
    "to-spec": "Turn a design conversation into a buildable spec.",
    "to-tickets": "Split a spec into verifiable tickets with blocking edges.",
    "triage": "Evaluate incoming issues and prepare agent-ready briefs.",
    "wayfinder": "Map a large effort as linked decision tickets.",
    "wizard": "Script human-only setup steps.",
    "chief-of-staff": "Coordinate a long-running goal and a dated project wiki.",
    "claude-handoff": "Hand work to a fresh Claude background agent.",
    "loop-me": "Interview the user to specify repeatable agent workflows.",
    "setup-ts-deep-modules": "Configure TypeScript module boundaries with dependency-cruiser.",
    "software-factory": "Design software delivery tasks, triggers, and service roles.",
    "writing-beats": "Develop article beats from an agreed writing shape.",
    "writing-fragments": "Capture exploratory writing fragments from an interview.",
    "writing-shape": "Find a structure for an article's existing fragments.",
    "git-guardrails-claude-code": "Set up Claude Git command hooks.",
    "migrate-to-shoehorn": "Migrate test fixtures to Shoehorn.",
    "scaffold-exercises": "Scaffold course exercises.",
    "setup-pre-commit": "Set up Husky and lint-staged.",
    "grill-me": "Interview a design without writing repository docs.",
    "grilling": "Interview a design through questions.",
    "handoff": "Write a portable handoff for another session or directory.",
    "teach": "Build interactive lessons in a persistent learning workspace.",
    "to-questionnaire": "Draft questions for a stakeholder who holds missing context.",
    "wait-what": "Restate the previous explanation in plain language.",
    "writing-for-agents": "Write skills and agent instructions.",
}

PORTABILITY = """## Skillz integration

This is Matt Pocock's version. Skill references use the `mattpocock-` prefix.
Read a referenced skill's `SKILL.md` through the host's skill loader or file tools.
Map AskUserQuestion to the host's question tool and shell examples to its shell.
Use delegation only when available and permitted by the active instructions;
otherwise perform the same work sequentially and report that limit.
The user's scope and repository rules govern setup, file writes, tracker changes,
messages, schedules, publishing, merging, and cleanup. A skill invocation alone
does not broaden the user's request. Preserve existing work and configuration.
Verify provider examples against current primary documentation before use.

"""

EXTRAS = {
    "diagnosing-bugs": "Read enough code to construct the probe. Bound stress tests by time and load in an authorized environment. Treat hypothesis counts and timings as examples. Verify the real crash, recovery, or transaction boundary when it causes the symptom.\n\n",
    "domain-modeling": "Follow existing glossary and ADR locations and formats. Invented scenarios are proposals; record a business rule as decided only when the user confirms it. Modeling does not authorize implementation or data changes.\n\n",
    "writing-for-agents": "Preserve explicit safety prohibitions and user authority. Invocation flags depend on the client; consult SKILL-MECHANICS.md. Normal automatic discovery remains the default when authoring a new skill.\n\n",
    "prototype": "Keep experiments isolated from production and real customer data. Prototype shortcuts apply only to the experiment; record the validation still needed for a shippable implementation.\n\n",
    "wizard": "The template is an authoring example, not an installer. Replace its Stripe stage before use. Confirm destinations before writing credentials, keep secrets out of logs and Git, and validate generated scripts without running live setup.\n\n",
    "git-guardrails-claude-code": "These hooks apply to Claude Code only. The matcher is a best-effort convenience, not a security boundary or a complete shell parser. Test the selected patterns before installing them.\n\n",
    "setup-pre-commit": "Reuse existing hooks and formatters. Merge package scripts and staged-file rules without replacing unrelated checks. Use the repository's package manager and scope staging to this task.\n\n",
    "setup-ts-deep-modules": "This template assumes a flat package layout. Confirm that layout and preserve existing dependency-cruiser rules before adapting the config.\n\n",
    "migrate-to-shoehorn": "Install Shoehorn as a development dependency using the repository's package manager. Keep deliberately invalid fixtures in tests.\n\n",
}


def namespace(text: str, names: set[str]) -> str:
    for name in sorted(names, key=len, reverse=True):
        local = PREFIX + name
        text = re.sub(rf"(?<![\w-])([/$]){re.escape(name)}(?![\w-])", rf"\g<1>{local}", text)
    lines = []
    for line in text.splitlines(keepends=True):
        if "Skill tool" in line or "skill folder" in line or "available skills" in line:
            for name in sorted(names, key=len, reverse=True):
                line = re.sub(rf"([`\"]){re.escape(name)}\1", rf"\g<1>{PREFIX}{name}\g<1>", line)
        lines.append(line)
    return "".join(lines)


def port_markdown(text: str, name: str, names: set[str]) -> str:
    text = namespace(text, names)
    if name == "writing-for-agents" and text.startswith("# Skill mechanics"):
        return """# Skill mechanics

Keep a portable `name` and `description` on every skill. The description states
the capability and its trigger. Put detailed instructions in `SKILL.md` and
conditional detail in linked supporting files.

Automatic discovery is the default when authoring a new skill. Use explicit-only
invocation when the user requests it, and preserve an imported skill's existing
policy. Claude Code's `disable-model-invocation: true` and Codex's
`policy.allow_implicit_invocation: false` in `agents/openai.yaml` are client
settings. Do not assume another client implements either setting. Explicit-only
skills still retain descriptions for human discovery and package metadata.

A router names the available skills and explains when to read each one. Reading
a referenced file through host file tools differs from automatic skill selection.
Respect the host's loader and invocation rules rather than assuming all clients
can invoke another skill with the same command.

Split a skill when independent requests need independent triggers, or when a
conditional reference would otherwise obscure the common workflow. Keep shared
reference in one maintained file and link it from its callers.

See [SKILL.md](SKILL.md) for instruction-writing guidance.
"""
    # Template destinations belong to the consuming project, not this package.
    if name == "domain-modeling":
        text = re.sub(r"\[([^]]+)\]\((\./src/[^)]+)\)", r"\1 at `\2`", text)
    if name == "wayfinder":
        text = text.replace("[<closed ticket title>](link)", "<closed ticket title and URL>")
    if name == "setup-ts-deep-modules":
        text = text.replace("[src/packages/README.md](./src/packages/README.md)", "`src/packages/README.md` in the consuming project")
    return text


def vendor(source: Path, root: Path = ROOT) -> None:
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
    if revision != REVISION:
        raise ValueError(f"expected upstream {REVISION}, got {revision}")
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=source, text=True):
        raise ValueError("upstream checkout has local changes")
    paths = {path.parent.name: path for path in (source / "skills").rglob("SKILL.md")}
    if set(paths) != set(DESCRIPTIONS):
        raise ValueError("upstream skill inventory changed; review it before importing")
    names = set(paths)
    receipt = json.loads((root / "vendor/mattpocock.json").read_text())
    # Check recorded source bytes before modifying any destination.
    for relative, expected in receipt["source_sha256"].items():
        if hashlib.sha256((source / relative).read_bytes()).hexdigest() != expected:
            raise ValueError(f"source hash mismatch: {relative}")
    source_hashes = {"LICENSE": hashlib.sha256((source / "LICENSE").read_bytes()).hexdigest()}
    output_hashes = {}
    explicit = []
    experimental = []
    for name, path in sorted(paths.items()):
        local = PREFIX + name
        destination = root / "skills" / local
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(path.parent, destination)
        for resource in sorted(path.parent.rglob("*")):
            if resource.is_file():
                source_hashes[resource.relative_to(source).as_posix()] = hashlib.sha256(resource.read_bytes()).hexdigest()
        for markdown in destination.rglob("*.md"):
            markdown.write_text(port_markdown(markdown.read_text(), name, names))
        if name == "wizard":
            template = destination / "template.sh"
            template.write_text(template.read_text().replace("$e[Enter keeps current]", "${e}[Enter keeps current]"))
        original = path.read_text()
        header, body = original.split("---", 2)[1:]
        is_explicit = bool(re.search(r"^disable-model-invocation: true$", header, re.M))
        is_experimental = "in-progress" in path.parts
        if is_explicit:
            explicit.append(local)
        if is_experimental:
            experimental.append(local)
        metadata = f"""---
name: {local}
description: {json.dumps(DESCRIPTIONS[name])}
license: MIT
"""
        if is_explicit:
            metadata += "disable-model-invocation: true\n"
        hint = re.search(r"^argument-hint: (.+)$", header, re.M)
        if hint:
            metadata += f"argument-hint: {hint[1]}\n"
        metadata += f"""metadata:
  source: mattpocock/skills
  source-commit: {REVISION}
  upstream-name: {name}
  upstream-status: {"in-progress" if is_experimental else "published"}
  adaptation: namespaced-port
---

"""
        notes = PORTABILITY
        if is_experimental:
            notes += "Upstream marks this workflow as in progress. Treat it as experimental.\n\n"
        notes += EXTRAS.get(name, "")
        (destination / "SKILL.md").write_text(metadata + notes + port_markdown(body.lstrip(), name, names))
        shutil.copyfile(source / "LICENSE", destination / "LICENSE")
        ui = destination / "agents/openai.yaml"
        ui.parent.mkdir(exist_ok=True)
        ui_text = namespace(ui.read_text(), names) if ui.exists() else (
            'interface:\n  display_name: ' + json.dumps(name.replace("-", " ").title()) + '\n'
            + '  short_description: ' + json.dumps(DESCRIPTIONS[name]) + '\n'
        )
        ui_text = re.sub(r'^  display_name: "(.*)"$', r'  display_name: "Matt Pocock: \1"', ui_text, flags=re.M)
        short = DESCRIPTIONS[name]
        if len(short) > 64:
            raise ValueError(f"UI description too long: {name}")
        ui_text = re.sub(r"^  short_description:.*$", "  short_description: " + json.dumps(short), ui_text, flags=re.M)
        ui_text += f"  default_prompt: \"Use ${local} for this task.\"\n" if "policy:" not in ui_text else ""
        if "policy:" in ui_text:
            ui_text = ui_text.replace("policy:", f'  default_prompt: "Use ${local} for this task."\npolicy:')
        elif is_explicit:
            ui_text += "policy:\n  allow_implicit_invocation: false\n"
        ui.write_text(ui_text)
        for resource in sorted(destination.rglob("*")):
            if resource.is_file():
                output_hashes[resource.relative_to(root).as_posix()] = hashlib.sha256(resource.read_bytes()).hexdigest()
    receipt.update({
        "integration_mode": "namespaced-port",
        "imported": sorted(PREFIX + name for name in names),
        "name_map": {name: PREFIX + name for name in sorted(names)},
        "excluded": {},
        "explicit_only": explicit,
        "experimental": experimental,
        "source_sha256": source_hashes,
        "output_sha256": output_hashes,
        "integration": [
            "All 39 source skills and their supporting resources included under mattpocock- names",
            "Preserved upstream invocation policies and MIT notices",
            "Namespaced cross-skill commands, loader references, and UI prompts",
            "Added host tool mappings, scope limits, and targeted setup and debugging guidance",
            "Marked eight upstream in-progress workflows as experimental",
            "Project-output example links rendered as paths instead of broken package links",
            "Normalized frontmatter and discovery descriptions for portable catalog parsing",
            "Braced a wizard prompt variable to resolve ShellCheck SC1087",
        ],
    })
    (root / "vendor/mattpocock.json").write_text(json.dumps(receipt, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="clean checkout at the pinned revision")
    args = parser.parse_args()
    vendor(args.source.resolve())


if __name__ == "__main__":
    main()
