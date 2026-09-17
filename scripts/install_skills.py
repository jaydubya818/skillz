#!/usr/bin/env python3
"""Install this repository's skills for Claude Code, Codex, or both."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import sys
import tempfile


REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_ROOT = REPO_ROOT / "skills"
AGENTS_ROOT = REPO_ROOT / "agents"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install Software Factory skills without silently overwriting existing skills."
    )
    targets = parser.add_mutually_exclusive_group(required=True)
    targets.add_argument("--claude", action="store_true", help="install for Claude Code")
    targets.add_argument("--codex", action="store_true", help="install for Codex")
    targets.add_argument("--all", action="store_true", help="install for Claude Code and Codex")
    parser.add_argument(
        "--project",
        type=Path,
        help="install into this project's .claude and/or .agents directory instead of user scope",
    )
    parser.add_argument(
        "--mode",
        choices=("copy", "symlink"),
        default="copy",
        help="copy skills or link them to this checkout (default: copy)",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="replace a conflicting install after moving it to a timestamp-free .backup path",
    )
    parser.add_argument("--dry-run", action="store_true", help="print actions without writing")
    return parser.parse_args(argv)


def skill_directories() -> list[Path]:
    return sorted(
        path
        for path in SKILLS_ROOT.iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    )


def selected_harnesses(args: argparse.Namespace) -> tuple[str, ...]:
    if args.all:
        return ("claude", "codex")
    return ("claude",) if args.claude else ("codex",)


def skills_destination_root(harness: str, project: Path | None) -> Path:
    base = project.expanduser().resolve() if project else Path.home()
    if harness == "claude":
        return base / ".claude" / "skills"
    if harness == "codex":
        return base / ".agents" / "skills"
    raise ValueError(f"unsupported harness: {harness}")


def agents_destination_root(project: Path | None) -> Path:
    base = project.expanduser().resolve() if project else Path.home()
    return base / ".claude" / "agents"


def path_digest(path: Path) -> str:
    digest = hashlib.sha256()
    if path.is_file():
        digest.update(path.read_bytes())
        return digest.hexdigest()
    for item in sorted(candidate for candidate in path.rglob("*") if candidate.is_file()):
        digest.update(item.relative_to(path).as_posix().encode())
        digest.update(b"\0")
        digest.update(item.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def same_install(source: Path, destination: Path, mode: str) -> bool:
    if destination.is_symlink():
        return mode == "symlink" and destination.resolve() == source.resolve()
    return (
        mode == "copy"
        and source.is_dir() == destination.is_dir()
        and source.is_file() == destination.is_file()
        and path_digest(source) == path_digest(destination)
    )


def backup_path(destination: Path) -> Path:
    candidate = destination.with_name(f"{destination.name}.backup")
    if not candidate.exists() and not candidate.is_symlink():
        return candidate
    index = 2
    while True:
        candidate = destination.with_name(f"{destination.name}.backup-{index}")
        if not candidate.exists() and not candidate.is_symlink():
            return candidate
        index += 1


def stage_copy(source: Path, destination_root_path: Path) -> Path:
    stage_parent = Path(tempfile.mkdtemp(prefix=".skill-install-", dir=destination_root_path))
    stage = stage_parent / source.name
    if source.is_dir():
        shutil.copytree(source, stage)
    else:
        shutil.copy2(source, stage)
    return stage


def install_one(
    source: Path,
    destination_root_path: Path,
    *,
    mode: str,
    replace: bool,
    dry_run: bool,
) -> str:
    destination = destination_root_path / source.name
    exists = destination.exists() or destination.is_symlink()
    if exists and same_install(source, destination, mode):
        return f"skip {destination} (already current)"
    if exists and not replace:
        raise FileExistsError(
            f"refusing to overwrite {destination}; use --replace to keep a backup and replace it"
        )

    backup = backup_path(destination) if exists else None
    action = f"install {source.name} -> {destination} ({mode})"
    if backup:
        action += f"; backup existing install to {backup}"
    if dry_run:
        return f"dry-run {action}"

    destination_root_path.mkdir(parents=True, exist_ok=True)
    staged: Path | None = None
    stage_parent: Path | None = None
    try:
        if mode == "copy":
            staged = stage_copy(source, destination_root_path)
            stage_parent = staged.parent
        if backup:
            os.replace(destination, backup)
        if mode == "copy":
            assert staged is not None
            os.replace(staged, destination)
        else:
            destination.symlink_to(source.resolve(), target_is_directory=source.is_dir())
    except Exception:
        if backup and backup.exists() and not destination.exists():
            os.replace(backup, destination)
        raise
    finally:
        if stage_parent and stage_parent.exists():
            shutil.rmtree(stage_parent)
    return action


def run(args: argparse.Namespace) -> list[str]:
    if not SKILLS_ROOT.is_dir():
        raise FileNotFoundError(f"skills directory not found: {SKILLS_ROOT}")
    skills = skill_directories()
    if not skills:
        raise FileNotFoundError(f"no skills found under {SKILLS_ROOT}")

    installs = [
        (source, skills_destination_root(harness, args.project))
        for harness in selected_harnesses(args)
        for source in skills
    ]
    if "claude" in selected_harnesses(args):
        if not AGENTS_ROOT.is_dir():
            raise FileNotFoundError(f"companion agents directory not found: {AGENTS_ROOT}")
        installs.extend(
            (source, agents_destination_root(args.project))
            for source in sorted(AGENTS_ROOT.glob("*.md"))
        )
    for source, root in installs:
        destination = root / source.name
        exists = destination.exists() or destination.is_symlink()
        if exists and not same_install(source, destination, args.mode) and not args.replace:
            raise FileExistsError(
                f"refusing to overwrite {destination}; use --replace to keep a backup and replace it"
            )

    output: list[str] = []
    for source, root in installs:
        output.append(
            install_one(
                source,
                root,
                mode=args.mode,
                replace=args.replace,
                dry_run=args.dry_run,
            )
        )
    return output


def main(argv: list[str] | None = None) -> int:
    try:
        for line in run(parse_args(argv)):
            print(line)
    except (FileExistsError, FileNotFoundError, OSError) as error:
        print(f"install_skills: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
