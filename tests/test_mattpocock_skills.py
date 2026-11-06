"""Verify provenance and independent installation of the Matt adaptations."""

import hashlib
import json
from pathlib import Path
import re
import shutil

import pytest

from myskills.catalog import build_catalog, frontmatter
from test_addyosmani_skills import load_script


ROOT = Path(__file__).parents[1]
MANIFEST = json.loads((ROOT / "vendor/mattpocock.json").read_text())
IMPORTED = set(MANIFEST["imported"])


def test_review_accounts_for_all_source_skills():
    assert MANIFEST["upstream"] == "https://github.com/mattpocock/skills"
    assert MANIFEST["integration_mode"] == "curated-rewrite"
    assert len(IMPORTED) == len(MANIFEST["imported"]) == 3
    assert len(MANIFEST["source_paths"]) == 39
    assert len(MANIFEST["excluded"]) == 36
    assert IMPORTED.isdisjoint(MANIFEST["excluded"])
    assert IMPORTED | set(MANIFEST["excluded"]) == set(MANIFEST["source_paths"])
    for name, path in MANIFEST["source_paths"].items():
        assert Path(path).parts[-2:] == (name, "SKILL.md")
        assert path in MANIFEST["source_sha256"]
    for digest in MANIFEST["source_sha256"].values():
        assert re.fullmatch(r"[0-9a-f]{64}", digest)
    for entry in MANIFEST["excluded"].values():
        assert entry["reason"]
        for alternative in entry["alternatives"]:
            assert (ROOT / "skills" / alternative / "SKILL.md").is_file()


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
    assert fields["metadata"]["adaptation"] == "curated-rewrite"
    for markdown in installed.rglob("*.md"):
        for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", markdown.read_text()):
            if target.startswith(("http://", "https://", "#")):
                continue
            resolved = (markdown.parent / target.split("#", 1)[0]).resolve()
            assert resolved.is_relative_to(installed) and resolved.is_file()
    item = next(m for m in build_catalog(ROOT)["skills"] if m["skill_id"] == name)
    assert item["provenance"]["kind"] == "adapted"
    assert item["provenance"]["reference"] == "vendor/mattpocock.json"
    assert item["provenance"]["revision"] == MANIFEST["commit"]
    assert item["trust"] == "UNTRUSTED"
    assert item["qualification"]["status"] == "NOT_EVALUATED"
