#!/usr/bin/env python3
"""Vendor the reviewed BuilderIO/skills collection into Skillz."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess


ROOT = Path(__file__).parents[1]
DESTINATION = ROOT / "skills"
MANIFEST = ROOT / "vendor" / "builderio.json"
MCP_CONFIG = ROOT / ".mcp.json"

EXPECTED_SKILLS = {
    "agent-watchdog",
    "an",
    "efficient-fable",
    "efficient-frontier",
    "factory",
    "factory-babysit-pr",
    "factory-collect",
    "factory-human-digest",
    "factory-lookback",
    "factory-recover",
    "factory-review-prs",
    "factory-ship",
    "factory-watchdog",
    "plan-arbiter",
    "plow-ahead",
    "quick-recap",
    "read-the-damn-docs",
    "rewind",
    "stay-within-limits",
    "turn-into-app",
    "visual-edit",
    "visual-plan",
    "visual-recap",
    "webmcp",
}

DESCRIPTIONS = {
    "agent-watchdog": "Audit or monitor another agent's session, PR, branch, or transcript. Use when asked to watch, compare, review, or repair agent work.",
    "an": "Operate Agent-Native apps through Dispatch MCP. Use for /an or work in a granted Agent-Native app.",
    "efficient-fable": "Keep judgment with Claude Fable and delegate bounded work. Use for large Fable tasks with independent slices.",
    "efficient-frontier": "Keep judgment with a frontier model and delegate bounded work. Use for costly tasks with independent slices.",
    "factory": "Configure sources, schedules, isolation, and action gates. Use when setting up governed delivery automation.",
    "factory-babysit-pr": "Monitor one authorized PR and apply separate fix, publish, reply, approval, merge, and soak gates.",
    "factory-collect": "Collect and triage configured product signals under separate fix, reply, and close policies. Use for current intake.",
    "factory-human-digest": "Summarize configured work that needs human judgment. Use for a read-only decision queue.",
    "factory-lookback": "Audit bounded signal history for recurring patterns and systemic fixes. Use for periodic lookbacks.",
    "factory-recover": "Resume eligible interrupted coding runs without repeating completed actions. Use after an interrupted run.",
    "factory-review-prs": "Review configured PR queues under independent reply, approval, and merge gates. Use for PR triage.",
    "factory-ship": "Complete authorized delivery work under explicit publish, merge, deployment, closure, and notification gates.",
    "factory-watchdog": "Monitor authorized delivery work for verified stalls. Use for policy-gated scheduled follow-through.",
    "plan-arbiter": "Compare competing plans and recommend one executable path. Use when asked to judge, merge, or cross-review plans.",
    "plow-ahead": "Proceed through routine ambiguity with stated assumptions. Use when the user requests autonomous progress.",
    "quick-recap": "Add or follow a red, yellow, or green status-line convention. Use for compact agent completion status.",
    "read-the-damn-docs": "Read current primary docs before relying on memory. Use for external APIs, packages, or high-stakes behavior.",
    "rewind": "Retrieve bounded local Clips Rewind context. Use when the user refers to something they recently saw or said.",
    "stay-within-limits": "Check host usage between bounded work waves. Use when long-running or parallel work must stay within limits.",
    "turn-into-app": "Build a verified Agent-Native app from a visible workflow, skill, thread, project, or spreadsheet.",
    "visual-edit": "Open a running local app in Agent-Native Design. Use for visual editing, responsive review, or source handoff.",
    "visual-plan": "Create a structured Agent-Native plan with optional visual review. Use when a plan needs an interactive review surface.",
    "visual-recap": "Turn a PR, branch, commit, or diff into a grounded Agent-Native visual recap for substantial changes.",
    "webmcp": "Use a web app through its page MCP tools before UI automation. Use for /webmcp or page-tool work.",
}

SHORT_DESCRIPTIONS = {
    "agent-watchdog": "Audit agent work and repair verified gaps",
    "an": "Operate Agent-Native apps through Dispatch",
    "efficient-fable": "Delegate bounded work while Fable decides",
    "efficient-frontier": "Use frontier tokens for judgment and review",
    "factory": "Configure governed delivery automation",
    "factory-babysit-pr": "Follow one authorized PR through its gates",
    "factory-collect": "Collect and triage configured product signals",
    "factory-human-digest": "Build a read-only human decision queue",
    "factory-lookback": "Find recurring signals and systemic fixes",
    "factory-recover": "Resume eligible interrupted coding runs",
    "factory-review-prs": "Review configured pull-request queues",
    "factory-ship": "Ship authorized work through explicit gates",
    "factory-watchdog": "Report verified stalls in delivery work",
    "plan-arbiter": "Choose one executable plan from alternatives",
    "plow-ahead": "Keep moving through routine ambiguity",
    "quick-recap": "End agent responses with clear status",
    "read-the-damn-docs": "Ground external behavior in current docs",
    "rewind": "Retrieve bounded local Rewind context",
    "stay-within-limits": "Throttle long work around usage limits",
    "turn-into-app": "Package repeatable workflows as apps",
    "visual-edit": "Edit a running local app in Design",
    "visual-plan": "Publish an interactive visual plan",
    "visual-recap": "Publish a grounded visual change recap",
    "webmcp": "Use a web app through its page tools",
}

RISK = {
    "agent-watchdog": "medium",
    "an": "medium",
    "efficient-fable": "low",
    "efficient-frontier": "low",
    "factory": "medium",
    "factory-babysit-pr": "high",
    "factory-collect": "medium",
    "factory-human-digest": "low",
    "factory-lookback": "medium",
    "factory-recover": "medium",
    "factory-review-prs": "high",
    "factory-ship": "high",
    "factory-watchdog": "medium",
    "plan-arbiter": "low",
    "plow-ahead": "medium",
    "quick-recap": "medium",
    "read-the-damn-docs": "low",
    "rewind": "high",
    "stay-within-limits": "low",
    "turn-into-app": "high",
    "visual-edit": "high",
    "visual-plan": "medium",
    "visual-recap": "medium",
    "webmcp": "high",
}

CAPABILITY = {
    "agent-watchdog": "agent-review",
    "an": "agent-native-apps",
    "efficient-fable": "model-orchestration",
    "efficient-frontier": "model-orchestration",
    "factory": "factory-configuration",
    "factory-babysit-pr": "factory-pr-delivery",
    "factory-collect": "factory-signal-intake",
    "factory-human-digest": "factory-human-review",
    "factory-lookback": "factory-systemic-review",
    "factory-recover": "factory-recovery",
    "factory-review-prs": "factory-pr-review",
    "factory-ship": "factory-delivery",
    "factory-watchdog": "factory-monitoring",
    "plan-arbiter": "plan-review",
    "plow-ahead": "autonomous-execution",
    "quick-recap": "status-reporting",
    "read-the-damn-docs": "documentation-research",
    "rewind": "local-screen-memory",
    "stay-within-limits": "usage-governance",
    "turn-into-app": "agent-native-app-building",
    "visual-edit": "visual-editing",
    "visual-plan": "visual-planning",
    "visual-recap": "visual-review",
    "webmcp": "browser-page-tools",
}

COMPATIBILITY = {
    "an": "Requires the Agent-Native Dispatch MCP connector and a host that supports MCP Apps or returned links.",
    "factory": "Works in Agent Skills runtimes with the configured integrations and scheduler capabilities used by the selected workflow.",
    "rewind": "Requires macOS, Clips Desktop with Rewind enabled, and the local Screen Memory MCP connection.",
    "turn-into-app": "Local builds require Node.js, pnpm, and a coding host; browser-only handoffs require authenticated Agent-Native Dispatch.",
    "visual-edit": "Requires a browser-capable coding host plus the hosted Agent-Native Design connector or page WebMCP tools.",
    "visual-plan": "Hosted mode requires the Agent-Native Plan connector; local-files mode requires the Agent-Native CLI.",
    "visual-recap": "Hosted mode requires the Agent-Native Plan connector; local-files mode requires the Agent-Native CLI.",
    "webmcp": "Requires a built-in browser with native WebMCP support or a page-world JavaScript evaluator.",
}

FACTORY_SKILLS = {name for name in EXPECTED_SKILLS if name == "factory" or name.startswith("factory-")}
EXPORTED_SKILLS = {"an", "rewind", "turn-into-app", "visual-edit", "visual-plan", "visual-recap", "webmcp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Vendor BuilderIO/skills into the Skillz collection."
    )
    parser.add_argument("source", type=Path, help="path to a BuilderIO/skills checkout")
    parser.add_argument("--replace", action="store_true", help="replace a previous reviewed import")
    return parser.parse_args()


def git_value(source: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=source, check=True, text=True, capture_output=True
    ).stdout.strip()


def display_name(name: str) -> str:
    overrides = {
        "an": "Agent-Native Apps",
        "read-the-damn-docs": "Read The Damn Docs",
        "webmcp": "WebMCP",
    }
    return overrides.get(name, " ".join(word.capitalize() for word in name.split("-")))


def body_after_frontmatter(path: Path) -> str:
    text = path.read_text()
    match = re.match(r"^---\n[\s\S]*?\n---\n([\s\S]*)$", text)
    if not match:
        raise ValueError(f"missing or invalid frontmatter: {path}")
    return match.group(1)


def normalize_skill(path: Path, *, commit: str) -> None:
    name = path.name
    skill_file = path / "SKILL.md"
    body = body_after_frontmatter(skill_file)
    compatibility = COMPATIBILITY.get(
        name,
        "Works in Claude Code, Codex, Cursor, and Agent Skills-compatible harnesses when the required host tools are available.",
    )
    metadata = [
        "  author: Builder.io",
        "  source: BuilderIO/skills",
        f"  source-commit: {commit}",
        "  owner: software-factory",
        f"  risk: {RISK[name]}",
        f"  capabilities: builderio,{CAPABILITY[name]}",
    ]
    if name in FACTORY_SKILLS:
        metadata.append("  installer-group: factory")
    if name in EXPORTED_SKILLS:
        metadata.append("  visibility: exported")
    frontmatter = [
        "---",
        f"name: {name}",
        f"description: {json.dumps(DESCRIPTIONS[name])}",
        "license: MIT",
        f"compatibility: {json.dumps(compatibility)}",
        "metadata:",
        *metadata,
        "---",
    ]
    skill_file.write_text("\n".join(frontmatter) + "\n\n" + body.lstrip())

    short = SHORT_DESCRIPTIONS[name]
    if not 25 <= len(short) <= 64:
        raise ValueError(f"short description for {name} must be 25-64 characters: {short!r}")
    agents = path / "agents"
    agents.mkdir(exist_ok=True)
    (agents / "openai.yaml").write_text(
        "interface:\n"
        f"  display_name: {json.dumps(display_name(name))}\n"
        f"  short_description: {json.dumps(short)}\n"
        f"  default_prompt: {json.dumps(f'Use ${name} for this task and return a verified result.')}\n"
    )


def replace_text(path: Path, replacements: list[tuple[str, str]]) -> None:
    text = path.read_text()
    for old, new in replacements:
        if old not in text:
            raise ValueError(f"Builder.io integration anchor changed in {path}: {old!r}")
        text = text.replace(old, new)
    path.write_text(text)


def package_shared_resources(source: Path) -> None:
    factory_references = DESTINATION / "factory" / "references"
    factory_references.mkdir(exist_ok=True)
    shutil.copy2(source / "docs" / "factory" / "README.md", factory_references / "factory-guide.md")
    shutil.copy2(
        source / "docs" / "factory" / "configuration.md",
        factory_references / "factory-configuration.md",
    )
    replace_text(
        factory_references / "factory-guide.md",
        [("](configuration.md)", "](factory-configuration.md)")],
    )
    replace_text(
        factory_references / "factory-configuration.md",
        [("](README.md)", "](factory-guide.md)")],
    )

    for name in FACTORY_SKILLS:
        for markdown in (DESTINATION / name).glob("*.md"):
            text = markdown.read_text()
            text = text.replace(
                "../../docs/factory/README.md",
                "../factory/references/factory-guide.md",
            )
            text = re.sub(
                r"https://github\.com/BuilderIO/skills/blob/main/docs/factory/configuration\.md",
                "../factory/references/factory-configuration.md",
                text,
            )
            text = text.replace(
                "../../docs/factory/configuration.md",
                "../factory/references/factory-configuration.md",
            )
            markdown.write_text(text)

    media = {
        "visual-plan": "visual-plan.png",
        "visual-recap": "visual-recap.gif",
    }
    for name, filename in media.items():
        assets = DESTINATION / name / "assets"
        assets.mkdir(exist_ok=True)
        shutil.copy2(source / "media" / filename, assets / filename)
        readme = DESTINATION / name / "README.md"
        replace_text(readme, [(f"../../media/{filename}", f"assets/{filename}")])

    turn_into_app = DESTINATION / "turn-into-app" / "SKILL.md"
    replace_text(
        turn_into_app,
        [
            (
                "[Agent-Native\napp configuration guide](/docs/agent-native-config)",
                "[Agent-Native\napp configuration guide](https://www.agent-native.com/docs/agent-native-config/)",
            )
        ],
    )


def update_mcp_config(source: Path) -> None:
    upstream = json.loads((source / ".mcp.json").read_text())
    expected = {
        "mcpServers": {
            "agent-native-dispatch": {
                "type": "http",
                "url": "https://dispatch.agent-native.com/mcp",
            }
        }
    }
    if upstream != expected:
        raise ValueError("unexpected Builder.io Dispatch MCP configuration")
    dispatch = expected["mcpServers"]["agent-native-dispatch"]
    current = json.loads(MCP_CONFIG.read_text()) if MCP_CONFIG.exists() else {"mcpServers": {}}
    servers = current.setdefault("mcpServers", {})
    servers["agent-native-dispatch"] = dispatch
    MCP_CONFIG.write_text(json.dumps(current, indent=2) + "\n")


def main() -> int:
    args = parse_args()
    source = args.source.expanduser().resolve()
    source_skills = source / "skills"
    if not source_skills.is_dir() or not (source / "LICENSE").is_file():
        raise SystemExit(f"not a BuilderIO/skills checkout: {source}")
    remote = git_value(source, "remote", "get-url", "origin")
    if "BuilderIO/skills" not in remote:
        raise SystemExit(f"unexpected source remote: {remote}")
    if git_value(source, "status", "--porcelain"):
        raise SystemExit("BuilderIO/skills checkout must be clean")
    commit = git_value(source, "rev-parse", "HEAD")

    source_names = {
        path.name for path in source_skills.iterdir() if (path / "SKILL.md").is_file()
    }
    if source_names != EXPECTED_SKILLS:
        added = sorted(source_names - EXPECTED_SKILLS)
        removed = sorted(EXPECTED_SKILLS - source_names)
        raise SystemExit(f"Builder.io skill inventory changed; added={added}, removed={removed}")

    previous = set()
    if MANIFEST.exists():
        previous = set(json.loads(MANIFEST.read_text()).get("imported", []))
    conflicts = sorted(name for name in EXPECTED_SKILLS if (DESTINATION / name).exists())
    foreign_conflicts = sorted(set(conflicts) - previous)
    if foreign_conflicts:
        raise SystemExit(f"refusing to replace non-Builder skills: {', '.join(foreign_conflicts)}")
    if conflicts and not args.replace:
        raise SystemExit(f"destination skills already exist; rerun with --replace: {', '.join(conflicts)}")

    for name in sorted(EXPECTED_SKILLS):
        destination = DESTINATION / name
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(source_skills / name, destination)
        shutil.copy2(source / "LICENSE", destination / "LICENSE")
        normalize_skill(destination, commit=commit)

    package_shared_resources(source)
    update_mcp_config(source)

    MANIFEST.parent.mkdir(exist_ok=True)
    MANIFEST.write_text(
        json.dumps(
            {
                "schema": "vendored-agent-skills/v1",
                "upstream": "https://github.com/BuilderIO/skills",
                "commit": commit,
                "license": "MIT",
                "copyright": "Copyright (c) 2026 Builder.io",
                "imported": sorted(EXPECTED_SKILLS),
                "shared_resources": {
                    "factory": "skills/factory/references/",
                    "visual-plan-media": "skills/visual-plan/assets/visual-plan.png",
                    "visual-recap-media": "skills/visual-recap/assets/visual-recap.gif",
                    "dispatch-mcp": ".mcp.json",
                },
                "integration": [
                    "portable frontmatter and concise activation descriptions",
                    "Codex agents/openai.yaml metadata",
                    "self-contained MIT notices",
                    "installed-tree-safe Factory and media references",
                    "optional Agent-Native Dispatch MCP configuration",
                ],
            },
            indent=2,
        )
        + "\n"
    )
    print(f"Built {len(EXPECTED_SKILLS)} Builder.io skills from {commit[:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
