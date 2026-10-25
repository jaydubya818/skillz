"""Exercise the vendored formatter without publishing media."""

from pathlib import Path
import subprocess


SCRIPT = Path(__file__).parents[1] / "skills/before-and-after/scripts/format.mjs"


def format_media(directory, *arguments):
    return subprocess.run(
        ["node", str(SCRIPT), *arguments], cwd=directory,
        capture_output=True, text=True, check=False,
    )


def test_replaces_only_the_existing_evidence_block(tmp_path):
    prefix = "A reviewer wrote this.  \n\n\n"
    suffix = "\n\n\n## Verification\nKeep this exact text.  \n\n"
    body = tmp_path / "body.md"
    body.write_text(prefix + "<!-- before-and-after:start -->\nold\n<!-- before-and-after:end -->" + suffix)
    for name in ("before.png", "after.png"):
        (tmp_path / name).write_bytes(b"fixture")
    result = format_media(tmp_path, "--body-file", str(body), "--before", "before.png", "--after", "after.png")
    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith(prefix)
    assert result.stdout.endswith(suffix)
    assert result.stdout.count("<!-- before-and-after:start -->") == 1
    assert "![Before](./before.png)" in result.stdout
    assert "![After](./after.png)" in result.stdout
    assert body.read_text().endswith(suffix)


def test_preview_and_attachment_list_use_the_same_local_file(tmp_path):
    (tmp_path / "preview.webm").write_bytes(b"fixture")
    preview = format_media(tmp_path, "--after", "preview.webm")
    attached = format_media(tmp_path, "--attach-list", "--after", "preview.webm")
    assert preview.returncode == attached.returncode == 0
    assert "Preview" in preview.stdout
    assert "./preview.webm" in preview.stdout
    assert attached.stdout.strip() == "./preview.webm"


def test_missing_media_refuses_to_produce_a_publishable_block(tmp_path):
    result = format_media(tmp_path, "--after", "missing.png")
    assert result.returncode != 0
    assert "<!-- before-and-after:start -->" not in result.stdout
