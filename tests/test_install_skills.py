import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).parents[1] / "scripts" / "install_skills.py"
SPEC = importlib.util.spec_from_file_location("install_skills", SCRIPT)
assert SPEC and SPEC.loader
INSTALLER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INSTALLER)


@pytest.fixture
def source_tree(tmp_path, monkeypatch):
    source = tmp_path / "source" / "skills"
    for name in ("alpha", "beta"):
        skill = source / name
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(f"---\nname: {name}\ndescription: test\n---\n")
    monkeypatch.setattr(INSTALLER, "SKILLS_ROOT", source)
    agents = tmp_path / "source" / "agents"
    agents.mkdir()
    for name in ("alpha-agent", "beta-agent"):
        (agents / f"{name}.md").write_text(f"---\nname: {name}\n---\n")
    monkeypatch.setattr(INSTALLER, "AGENTS_ROOT", agents)
    return source


def args(*values):
    return INSTALLER.parse_args(list(values))


def test_dry_run_does_not_create_project_directories(source_tree, tmp_path):
    project = tmp_path / "project"
    output = INSTALLER.run(args("--all", "--project", str(project), "--dry-run"))
    assert len(output) == 6
    assert all(line.startswith("dry-run install") for line in output)
    assert not project.exists()


def test_copy_installs_both_harnesses_and_is_idempotent(source_tree, tmp_path):
    project = tmp_path / "project"
    first = INSTALLER.run(args("--all", "--project", str(project)))
    second = INSTALLER.run(args("--all", "--project", str(project)))
    assert len(first) == 6
    assert all(
        (project / root / "skills" / name / "SKILL.md").is_file()
        for root in (".claude", ".agents")
        for name in ("alpha", "beta")
    )
    assert all(
        (project / ".claude" / "agents" / f"{name}.md").is_file()
        for name in ("alpha-agent", "beta-agent")
    )
    assert all(line.startswith("skip ") for line in second)


def test_conflict_is_rejected_without_replace(source_tree, tmp_path):
    project = tmp_path / "project"
    destination = project / ".agents" / "skills" / "alpha"
    destination.mkdir(parents=True)
    (destination / "SKILL.md").write_text("different")
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        INSTALLER.run(args("--codex", "--project", str(project)))
    assert (destination / "SKILL.md").read_text() == "different"


def test_preflight_rejects_late_conflict_without_partial_install(source_tree, tmp_path):
    project = tmp_path / "project"
    destination = project / ".agents" / "skills" / "beta"
    destination.mkdir(parents=True)
    (destination / "SKILL.md").write_text("different")
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        INSTALLER.run(args("--codex", "--project", str(project)))
    assert not (project / ".agents" / "skills" / "alpha").exists()


def test_claude_agent_conflict_is_preflighted(source_tree, tmp_path):
    project = tmp_path / "project"
    destination = project / ".claude" / "agents" / "beta-agent.md"
    destination.parent.mkdir(parents=True)
    destination.write_text("different")
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        INSTALLER.run(args("--claude", "--project", str(project)))
    assert not (project / ".claude" / "skills" / "alpha").exists()


def test_replace_preserves_conflicting_install_as_backup(source_tree, tmp_path):
    project = tmp_path / "project"
    destination = project / ".claude" / "skills" / "alpha"
    destination.mkdir(parents=True)
    (destination / "SKILL.md").write_text("old")
    INSTALLER.run(args("--claude", "--project", str(project), "--replace"))
    assert (destination / "SKILL.md").read_text().startswith("---")
    assert (destination.with_name("alpha.backup") / "SKILL.md").read_text() == "old"


def test_symlink_mode_links_claude_skills_and_companion_agents(source_tree, tmp_path):
    project = tmp_path / "project"
    INSTALLER.run(args("--claude", "--project", str(project), "--mode", "symlink"))
    assert (project / ".claude" / "skills" / "alpha").is_symlink()
    assert (project / ".claude" / "agents" / "alpha-agent.md").is_symlink()
