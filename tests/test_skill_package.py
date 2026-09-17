import json
from pathlib import Path
import re


ROOT = Path(__file__).parents[1]
SKILLS = ROOT / "skills"
CORE_SKILLS = {
    "before-and-after",
    "code-structure",
    "evidence-driven-testing",
    "greploop",
    "greploop-apps",
    "mission-control-delivery",
    "new-feature",
    "unslop",
}


def expected_skills() -> set[str]:
    vendor = json.loads((ROOT / "vendor" / "jstack.json").read_text())
    assert vendor["schema"] == "vendored-agent-skills/v1"
    assert vendor["excluded"] == {
        "unslop": "the collection keeps its existing enhanced definition"
    }
    return CORE_SKILLS | set(vendor["imported"])


def frontmatter(path: Path) -> str:
    text = path.read_text()
    match = re.match(r"^---\n([\s\S]*?)\n---\n", text)
    assert match, f"missing frontmatter: {path}"
    return match.group(1)


def scalar_field(block: str, name: str) -> str:
    match = re.search(rf"^[ \t]*{re.escape(name)}:\s*(.+)$", block, re.MULTILINE)
    assert match, f"missing {name}"
    return match.group(1).strip().strip('"')


def description_value(block: str) -> str:
    lines = block.splitlines()
    for index, line in enumerate(lines):
        if not line.startswith("description:"):
            continue
        value = line.split(":", 1)[1].strip()
        if value in {">", ">-", "|", "|-"}:
            continuation = []
            for candidate in lines[index + 1:]:
                if not candidate.startswith((" ", "\t")):
                    break
                continuation.append(candidate.strip())
            return " ".join(continuation)
        return json.loads(value) if value.startswith('"') else value
    raise AssertionError("missing description")


def test_plugin_layout_has_one_canonical_skill_tree():
    discovered = {path.name for path in SKILLS.iterdir() if (path / "SKILL.md").is_file()}
    assert discovered == expected_skills()
    assert not [path for path in ROOT.iterdir() if path.is_dir() and (path / "SKILL.md").exists()]


def test_skill_frontmatter_uses_portable_fields_and_codex_metadata():
    for name in expected_skills():
        skill = SKILLS / name
        block = frontmatter(skill / "SKILL.md")
        assert scalar_field(block, "name") == name
        assert re.search(r"^description:", block, re.MULTILINE)
        assert re.search(r"^metadata:\n(?:  [a-z0-9-]+: .+\n?)+", block, re.MULTILINE)
        for legacy in ("owner", "risk", "capabilities", "requires_tools", "related_skills"):
            assert not re.search(rf"^{legacy}:", block, re.MULTILINE), f"legacy top-level field in {name}"
        if re.search(r"^allowed-tools:", block, re.MULTILINE):
            assert not re.search(r"^allowed-tools:\s*\n\s+-", block, re.MULTILINE)

        openai = (skill / "agents" / "openai.yaml").read_text()
        assert f"${name}" in openai
        short = scalar_field(openai, "short_description")
        assert 25 <= len(short) <= 64


def test_skill_descriptions_fit_the_codex_discovery_budget():
    descriptions = [
        description_value(frontmatter(SKILLS / name / "SKILL.md"))
        for name in expected_skills()
    ]
    byte_lengths = [len(description.encode("utf-8")) for description in descriptions]
    assert all(length <= 220 for length in byte_lengths)
    assert sum(byte_lengths) <= 8000


def test_local_markdown_links_resolve():
    for markdown in ROOT.rglob("*.md"):
        for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", markdown.read_text()):
            if target.startswith(("http://", "https://", "#")):
                continue
            clean = target.split("#", 1)[0]
            if clean:
                assert (markdown.parent / clean).resolve().exists(), f"broken link {target} in {markdown}"


def test_plugin_manifests_target_shared_skills_directory():
    claude = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
    codex = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text())
    assert claude["name"] == codex["name"] == "software-factory-skills"
    assert claude["version"] == codex["version"] == "2.1.0"
    assert codex["skills"] == "./skills/"


def test_claude_companion_agents_are_packaged_and_referenced_for_both_install_modes():
    plugin_name = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())["name"]
    expected = {"comment-sicko", "poteto-agent"}
    packaged = {path.stem for path in (ROOT / "agents").glob("*.md")}
    assert packaged == expected
    for name in expected:
        assert scalar_field(frontmatter(ROOT / "agents" / f"{name}.md"), "name") == name

    mode = (SKILLS / "poteto-mode" / "SKILL.md").read_text()
    plan = (SKILLS / "poteto-mode" / "playbooks" / "multi-phase-plan.md").read_text()
    comments = (SKILLS / "no-comments" / "SKILL.md").read_text()
    assert f'{plugin_name}:poteto-agent' in mode
    assert f'{plugin_name}:poteto-agent' in plan
    assert f'{plugin_name}:comment-sicko' in comments
    assert "For a direct install, use the bare" in mode
    assert "For a direct install, use the bare" in comments


def test_jstack_vendor_is_pinned_attributed_branded_and_hardened():
    vendor = json.loads((ROOT / "vendor" / "jstack.json").read_text())
    assert vendor["version"] == "0.9.30"
    assert vendor["commit"] == "45f768349a6d7d7e71509fee3f5bccfad54b3bad"
    assert len(vendor["imported"]) == 53
    assert "setup-jstack" in vendor["imported"]
    assert "setup-pstack" not in vendor["imported"]
    assert not (ROOT / "vendor" / "pstack.json").exists()
    assert not (ROOT / "scripts" / "vendor_pstack.py").exists()
    assert not (ROOT / "docs" / "PSTACK_REVIEW.md").exists()
    assert not (SKILLS / "setup-pstack").exists()
    for name in vendor["imported"]:
        block = frontmatter(SKILLS / name / "SKILL.md")
        assert "source: michael-denyer/pstack-claude" in block
        assert f"source-commit: {vendor['commit']}" in block
        assert "license: MIT" in block
        assert "capabilities: jstack," in block

        openai = (SKILLS / name / "agents" / "openai.yaml").read_text()
        assert "pstack workflow" not in openai.lower()

    setup = (SKILLS / "setup-jstack" / "SKILL.md").read_text()
    assert "name: setup-jstack" in setup
    assert "jstack-models.md" in setup
    assert "pstack-models.md" not in setup

    mode = (SKILLS / "poteto-mode" / "SKILL.md").read_text()
    assert "Poteto mode selects methods; it never broadens the authorized scope" in mode
    assert "external actions (team chat, ticket updates, kicking off evals) proceed without asking" not in mode
    cleanup = (SKILLS / "poteto-mode" / "playbooks" / "worktree-cleanup.md").read_text()
    assert "rm -rf" not in cleanup
    reflect = (SKILLS / "reflect" / "SKILL.md").read_text()
    assert "only when the task authorizes writes" in reflect


def test_jstack_credits_original_pstack_authorship():
    for path in (ROOT / "README.md", ROOT / "LICENSES.md"):
        text = path.read_text()
        assert "https://github.com/cursor/plugins/tree/main/pstack" in text
        assert "Lauren Tan" in text
        assert "https://github.com/michael-denyer/pstack-claude" in text
