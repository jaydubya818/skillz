#!/usr/bin/env python3
"""Check that a release tag matches every public package manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys


REPO_ROOT = Path(__file__).resolve().parent.parent
TAG_RE = re.compile(r"^v(?P<version>\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?)$")


def read_json(relative_path: str) -> dict:
    return json.loads((REPO_ROOT / relative_path).read_text())


def manifest_versions() -> dict[str, str]:
    claude_marketplace = read_json(".claude-plugin/marketplace.json")
    marketplace_plugins = claude_marketplace.get("plugins", [])
    if len(marketplace_plugins) != 1:
        raise ValueError("Claude marketplace must contain exactly one plugin")
    return {
        "plugin.json": read_json("plugin.json")["version"],
        ".claude-plugin/plugin.json": read_json(".claude-plugin/plugin.json")["version"],
        ".codex-plugin/plugin.json": read_json(".codex-plugin/plugin.json")["version"],
        ".cursor-plugin/plugin.json": read_json(".cursor-plugin/plugin.json")["version"],
        ".claude-plugin/marketplace.json": claude_marketplace["version"],
        ".claude-plugin/marketplace.json plugin": marketplace_plugins[0]["version"],
    }


def check(tag: str) -> list[str]:
    match = TAG_RE.fullmatch(tag)
    if not match:
        return [f"release tag must use vMAJOR.MINOR.PATCH: {tag}"]
    expected = match.group("version")
    return [
        f"{path} has version {version}, expected {expected}"
        for path, version in manifest_versions().items()
        if version != expected
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag", help="release tag, for example v2.3.0")
    args = parser.parse_args(argv)
    errors = check(args.tag)
    if errors:
        for error in errors:
            print(f"check_release: {error}", file=sys.stderr)
        return 1
    print(f"release metadata matches {args.tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
