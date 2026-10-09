"""Verify provenance and standalone installation of the curated adaptations."""

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil

import pytest

from test_skill_package import description_value, frontmatter, scalar_field


ROOT = Path(__file__).parents[1]
MANIFEST = json.loads((ROOT / "vendor" / "addyosmani.json").read_text())
ADAPTED = {
    "api-and-interface-design",
    "ci-cd-and-automation",
    "deprecation-and-migration",
    "frontend-ui-engineering",
    "observability-and-instrumentation",
    "performance-optimization",
    "security-and-hardening",
}


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_review_accounts_for_the_pinned_source_inventory():
    assert MANIFEST["upstream"] == "https://github.com/addyosmani/agent-skills"
    assert MANIFEST["commit"] == "1401c8b8030e023baeebb31781a6653fe8e93026"
    assert MANIFEST["integration_mode"] == "curated-rewrite"
    assert set(MANIFEST["imported"]) == ADAPTED
    excluded = MANIFEST["excluded"]
    assert len(excluded) == 18
    assert ADAPTED.isdisjoint(excluded)
    source_skills = {
        Path(path).parts[1]
        for path in MANIFEST["source_sha256"]
        if re.fullmatch(r"skills/[^/]+/SKILL\.md", path)
    }
    assert source_skills == ADAPTED | set(excluded)
    for digest in MANIFEST["source_sha256"].values():
        assert re.fullmatch(r"[0-9a-f]{64}", digest)
    for alternatives in excluded.values():
        assert alternatives
        for alternative in alternatives:
            assert (ROOT / "skills" / alternative / "SKILL.md").is_file()


@pytest.mark.parametrize("name", sorted(ADAPTED))
def test_adaptation_retains_provenance_and_complete_upstream_license(name):
    skill = ROOT / "skills" / name
    block = frontmatter(skill / "SKILL.md")
    assert scalar_field(block, "source") == "addyosmani/agent-skills"
    assert scalar_field(block, "source-commit") == MANIFEST["commit"]
    assert scalar_field(block, "adaptation") == "curated-rewrite"
    assert scalar_field(block, "license") == "MIT"
    assert hashlib.sha256((skill / "LICENSE").read_bytes()).hexdigest() == (
        MANIFEST["source_sha256"]["LICENSE"]
    )


@pytest.mark.parametrize("name", sorted(ADAPTED))
def test_single_skill_copy_survives_without_source_or_sibling_skills(name, tmp_path, monkeypatch):
    installer = load_script("install_skills")
    source = tmp_path / "source"
    shutil.copytree(ROOT / "skills" / name, source / name)
    monkeypatch.setattr(installer, "SKILLS_ROOT", source)
    destination = tmp_path / "installed"
    installer.run(installer.parse_args(["--portable", str(destination)]))
    shutil.rmtree(source)

    installed = destination / name
    expected_files = {
        p.relative_to(ROOT / "skills" / name): p.read_bytes()
        for p in (ROOT / "skills" / name).rglob("*") if p.is_file()
    }
    actual_files = {
        p.relative_to(installed): p.read_bytes()
        for p in installed.rglob("*") if p.is_file()
    }
    assert actual_files == expected_files
    assert not any(p.is_symlink() for p in installed.rglob("*"))
    for markdown in installed.rglob("*.md"):
        for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", markdown.read_text()):
            if target.startswith(("https://", "http://", "#")):
                continue
            resolved = (markdown.parent / target.split("#", 1)[0]).resolve()
            assert resolved.is_relative_to(installed)
            assert resolved.is_file()


def test_builderio_routing_descriptions_match_the_refresh_tool():
    vendor = load_script("vendor_builderio")
    for name, description in vendor.DESCRIPTIONS.items():
        assert description_value(frontmatter(ROOT / "skills" / name / "SKILL.md")) == description
