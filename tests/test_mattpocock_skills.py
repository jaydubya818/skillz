"""Verify the complete namespaced Matt collection and portable resources."""

import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

import pytest

from myskills.catalog import build_catalog, frontmatter
from test_addyosmani_skills import load_script


ROOT = Path(__file__).parents[1]
MANIFEST = json.loads((ROOT / "vendor/mattpocock.json").read_text())
IMPORTED = set(MANIFEST["imported"])


def test_review_accounts_for_all_source_skills():
    assert MANIFEST["upstream"] == "https://github.com/mattpocock/skills"
    assert MANIFEST["integration_mode"] == "namespaced-port"
    assert len(IMPORTED) == len(MANIFEST["imported"]) == 39
    assert len(MANIFEST["source_paths"]) == 39
    assert MANIFEST["excluded"] == {}
    assert MANIFEST["name_map"] == {
        name: f"mattpocock-{name}" for name in MANIFEST["source_paths"]
    }
    assert IMPORTED == set(MANIFEST["name_map"].values())
    assert len(MANIFEST["experimental"]) == 8
    for name, path in MANIFEST["source_paths"].items():
        assert Path(path).parts[-2:] == (name, "SKILL.md")
        assert path in MANIFEST["source_sha256"]
    for digest in MANIFEST["source_sha256"].values():
        assert re.fullmatch(r"[0-9a-f]{64}", digest)
    for path, digest in MANIFEST["output_sha256"].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize("name", sorted(IMPORTED))
def test_adaptation_installs_alone_with_license_and_provenance(name, tmp_path, monkeypatch):
    source = tmp_path / "source"
    original = ROOT / "skills" / name
    shutil.copytree(original, source / name)
    installer = load_script("install_skills")
    monkeypatch.setattr(installer, "SKILLS_ROOT", source)
    destination = tmp_path / "installed"
    installer.run(installer.parse_args(["--portable", str(destination)]))
    shutil.rmtree(source)
    installed = destination / name
    expected = {p.relative_to(original): p.read_bytes() for p in original.rglob("*") if p.is_file()}
    actual = {p.relative_to(installed): p.read_bytes() for p in installed.rglob("*") if p.is_file()}
    assert actual == expected
    assert not any(p.is_symlink() for p in installed.rglob("*"))
    assert hashlib.sha256((installed / "LICENSE").read_bytes()).hexdigest() == MANIFEST["source_sha256"]["LICENSE"]
    fields = frontmatter((installed / "SKILL.md").read_text())
    assert fields["license"] == "MIT"
    assert fields["metadata"]["source"] == "mattpocock/skills"
    assert fields["metadata"]["source-commit"] == MANIFEST["commit"]
    assert fields["metadata"]["adaptation"] == "namespaced-port"
    assert fields["metadata"]["upstream-name"] == name.removeprefix("mattpocock-")
    ui = (installed / "agents/openai.yaml").read_text()
    assert f"${name}" in ui
    assert ("allow_implicit_invocation: false" in ui) == (name in MANIFEST["explicit_only"])
    assert bool(fields.get("disable-model-invocation")) == (name in MANIFEST["explicit_only"])
    for markdown in installed.rglob("*.md"):
        for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", markdown.read_text()):
            if target.startswith(("http://", "https://", "#")):
                continue
            resolved = (markdown.parent / target.split("#", 1)[0]).resolve()
            assert resolved.is_relative_to(installed) and resolved.is_file()
    item = next(m for m in build_catalog(ROOT)["skills"] if m["skill_id"] == name)
    assert item["provenance"]["kind"] == "vendored"
    assert item["provenance"]["reference"] == "vendor/mattpocock.json"
    assert item["provenance"]["revision"] == MANIFEST["commit"]
    assert item["trust"] == "UNTRUSTED"
    assert item["qualification"]["status"] == "NOT_EVALUATED"


def test_matt_references_never_route_to_unprefixed_versions():
    names = "|".join(sorted(MANIFEST["source_paths"], key=len, reverse=True))
    for name in IMPORTED:
        for path in (ROOT / "skills" / name).rglob("*.md"):
            assert not re.search(rf"(?<![\w-])[/$]({names})(?![\w-])", path.read_text()), path
            for line in path.read_text().splitlines():
                if "Skill tool" in line:
                    assert not re.search(rf'([`\"])({names})\1', line), path
    for name in ("tdd", "handoff", "teach"):
        assert (ROOT / "skills" / name / "SKILL.md").is_file()
        assert (ROOT / "skills" / f"mattpocock-{name}" / "SKILL.md").is_file()


def test_imported_shell_templates_parse_without_running_setup():
    helpers = [path for name in IMPORTED for path in (ROOT / "skills" / name).rglob("*.sh")]
    assert len(helpers) == 3
    for path in helpers:
        subprocess.run(["bash", "-n", str(path)], check=True, capture_output=True)


@pytest.mark.parametrize("command,expected", [
    ("git status --short", 0),
    ("git diff --stat", 0),
    ("git push origin feature", 2),
    ("git reset --hard HEAD", 2),
    ("git clean -fd", 2),
    ("git branch -D feature", 2),
])
def test_claude_hook_blocks_documented_commands_without_executing_them(command, expected):
    hook = ROOT / "skills/mattpocock-git-guardrails-claude-code/scripts/block-dangerous-git.sh"
    result = subprocess.run(["bash", str(hook)], input=json.dumps({"tool_input": {"command": command}}),
                            text=True, capture_output=True)
    assert result.returncode == expected, result.stderr
