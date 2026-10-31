"""Check the curated import's provenance and standalone package integrity."""

import hashlib
import json
from pathlib import Path
import re
import shutil

import pytest

from myskills.catalog import build_catalog, frontmatter
from test_addyosmani_skills import load_script


ROOT = Path(__file__).parents[1]
MANIFEST = json.loads((ROOT / "vendor/davidondrej.json").read_text())
IMPORTED = set(MANIFEST["imported"])


def test_review_partitions_the_complete_pinned_inventory():
    assert MANIFEST["schema"] == "vendored-agent-skills/v1"
    assert MANIFEST["upstream"] == "https://github.com/davidondrej/skills"
    assert re.fullmatch(r"[0-9a-f]{40}", MANIFEST["commit"])
    assert MANIFEST["integration_mode"] == "curated-rewrite"
    assert len(IMPORTED) == len(MANIFEST["imported"]) == 5
    excluded = MANIFEST["excluded"]
    assert len(MANIFEST["source_paths"]) == 62
    assert IMPORTED.isdisjoint(excluded)
    assert IMPORTED | set(excluded) == set(MANIFEST["source_paths"])
    assert set(MANIFEST["source_sha256"]) == {
        *MANIFEST["source_paths"].values(), "LICENSE"
    }
    review = (ROOT / "docs/DAVIDONDREJ_REVIEW.md").read_text()
    for name, path in MANIFEST["source_paths"].items():
        assert Path(path).parts[-2:] == (name, "SKILL.md")
        assert f"| `{name}` |" in review
    for digest in MANIFEST["source_sha256"].values():
        assert re.fullmatch(r"[0-9a-f]{64}", digest)
    for entry in excluded.values():
        assert entry["reason"]
        for alternative in entry["alternatives"]:
            assert (ROOT / "skills" / alternative / "SKILL.md").is_file()


@pytest.mark.parametrize("name", sorted(IMPORTED))
def test_standalone_copy_retains_license_metadata_and_local_references(name, tmp_path, monkeypatch):
    source = tmp_path / "source"
    original = ROOT / "skills" / name
    shutil.copytree(original, source / name)
    installer = load_script("install_skills")
    monkeypatch.setattr(installer, "SKILLS_ROOT", source)
    destination = tmp_path / "installed"
    installer.run(installer.parse_args(["--portable", str(destination)]))
    shutil.rmtree(source)
    installed = destination / name

    def files(path):
        return {p.relative_to(path): p.read_bytes() for p in path.rglob("*") if p.is_file()}

    assert files(installed) == files(original)
    assert not any(p.is_symlink() for p in installed.rglob("*"))
    assert hashlib.sha256((installed / "LICENSE").read_bytes()).hexdigest() == (
        MANIFEST["source_sha256"]["LICENSE"]
    )
    fields = frontmatter((installed / "SKILL.md").read_text())
    assert fields["license"] == "MIT"
    assert fields["metadata"]["source"] == "davidondrej/skills"
    assert fields["metadata"]["source-commit"] == MANIFEST["commit"]
    assert fields["metadata"]["adaptation"] == "curated-rewrite"
    for markdown in installed.rglob("*.md"):
        for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", markdown.read_text()):
            if target.startswith(("https://", "http://", "#")):
                continue
            resolved = (markdown.parent / target.split("#", 1)[0]).resolve()
            assert resolved.is_relative_to(installed)
            assert resolved.is_file()

    catalog = build_catalog(ROOT)
    item = next(m for m in catalog["skills"] if m["skill_id"] == name)
    assert item["provenance"]["kind"] == "adapted"
    assert item["provenance"]["reference"] == "vendor/davidondrej.json"
    assert item["provenance"]["revision"] == MANIFEST["commit"]
    assert item["trust"] == "UNTRUSTED"
    assert item["qualification"]["status"] == "NOT_EVALUATED"
