import json
import os
from pathlib import Path
import stat

import pytest

from myskills.cohort_assessment import file_digest, seal
from myskills.manifest import ValidationError
from qualification.custody_guard import protect, release_sources, require_owner, validate_roots


@pytest.mark.parametrize('checkout,evidence', [
    ('/private/tmp/check', '/Users/owner/evidence'),
    ('/Users/owner/.codex/visualizations/day/work', '/Users/owner/evidence'),
    ('/Users/owner/source', '/Users/owner/source/evidence'),
    ('/Users/owner/evidence/source', '/Users/owner/evidence'),
])
def test_disposable_or_overlapping_roots_are_rejected(checkout, evidence):
    with pytest.raises(ValidationError):
        validate_roots(Path(checkout), Path(evidence))


def test_foreign_workstream_cannot_release_protection(tmp_path):
    marker = tmp_path/'.myskills-active.json'
    marker.write_text(json.dumps({'owner': 'task-a'}))
    with pytest.raises(ValidationError, match='foreign workstream'):
        release_sources(tmp_path, 'task-b', {'owner': 'task-a'})
    with pytest.raises(ValidationError):
        require_owner(marker, '')


@pytest.mark.skipif(not hasattr(os, 'chflags'), reason='macOS filesystem protection requires native host check')
def test_immutable_file_rejects_overwrite_and_unlink(tmp_path):
    path = tmp_path/'evidence.json'
    path.write_text('retained')
    original = path.stat().st_flags
    try:
        protect(path)
        with pytest.raises(PermissionError):
            path.write_text('replacement')
        with pytest.raises(PermissionError):
            path.unlink()
        assert path.read_text() == 'retained'
    finally:
        os.chflags(path, original)


@pytest.mark.skipif(not hasattr(os, 'chflags'), reason='macOS filesystem protection requires native host check')
def test_append_only_evidence_allows_append_but_not_truncate_or_delete(tmp_path):
    path = tmp_path/'events.jsonl'
    path.write_text('first\n')
    original = path.stat().st_flags
    try:
        protect(path, append_only=True)
        with path.open('a') as stream:
            stream.write('second\n')
        with pytest.raises(PermissionError):
            path.write_text('replacement')
        with pytest.raises(PermissionError):
            path.unlink()
        assert path.read_text() == 'first\nsecond\n'
    finally:
        os.chflags(path, original)


def test_protection_receipt_rejects_path_escape(tmp_path):
    (tmp_path/'.myskills-active.json').write_text(json.dumps({'owner': 'task-a'}))
    receipt = seal({'owner': 'task-a', 'checkout': str(tmp_path),
                    'files': [{'path': '../foreign', 'digest': 'unused', 'original_flags': 0}]})
    with pytest.raises(ValidationError, match='protected source changed'):
        release_sources(tmp_path, 'task-a', receipt)


def test_object_directory_symlink_is_rejected_before_write(tmp_path):
    from qualification.custody_guard import Vault
    outside = tmp_path/'foreign'
    outside.mkdir()
    vault = Vault.__new__(Vault)
    vault.root = tmp_path/'vault'
    vault.root.mkdir()
    vault.objects = vault.root/'objects'
    vault.objects.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValidationError, match='escaped the vault'):
        vault._validate_objects()
    assert list(outside.iterdir()) == []


def test_partial_source_freeze_restores_every_original_flag(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from qualification import custody_guard
    paths = [tmp_path/'a.py', tmp_path/'b.py']
    for path in paths:
        path.write_text('source')
    original_flags = {paths[0]: 0, paths[1]: 64}
    flags = dict(original_flags)
    original_stat = Path.stat

    def simulated_stat(path, *args, **kwargs):
        actual = original_stat(path, *args, **kwargs)
        return SimpleNamespace(st_flags=flags[path], st_mode=actual.st_mode) if path in flags else actual

    def failing_protect(path):
        flags[path] |= 2
        if path == paths[1]:
            raise OSError('injected protection failure')

    monkeypatch.setattr(Path, 'stat', simulated_stat)
    monkeypatch.setattr(custody_guard, 'protect', failing_protect)
    monkeypatch.setattr(custody_guard.os, 'chflags',
                        lambda path, value, **kwargs: flags.__setitem__(path, value), raising=False)
    vault = custody_guard.Vault.__new__(custody_guard.Vault)
    vault.owner = 'task-a'
    vault.lease = {'owner': vault.owner, 'checkout': str(tmp_path)}
    (tmp_path/'.myskills-active.json').write_text(json.dumps(vault.lease))
    retained = []
    vault.retain = lambda name, content: retained.append((name, content))
    with pytest.raises(OSError, match='injected protection failure'):
        vault.freeze_sources(tmp_path, ['a.py', 'b.py'])
    assert flags == original_flags
    assert len(retained) == 1
    assert json.loads(retained[0][1])['files'][1]['original_flags'] == 64
