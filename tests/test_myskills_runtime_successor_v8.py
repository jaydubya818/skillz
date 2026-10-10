import copy
import json
from pathlib import Path

import pytest

from myskills.digest import digest_object
from myskills.manifest import ValidationError
from qualification.runtime_successor_v8 import (
    HARNESS, LOCATION, RUNTIME_DIGEST, context, binding, validate_identity,
)


def inputs():
    directory = Path.cwd()/LOCATION
    return [json.loads(path.read_text()) for path in (
        Path('qualification/checkpoint2/runtime-pin.json'), directory/'runtime-pin.json',
        directory/'model-show.json', directory/'historical-show-reconstructed.json',
    )]


def test_exact_successor_admission_preserves_historical_identity():
    values = inputs()
    before = copy.deepcopy(values)
    validate_identity(*values)
    assert values == before
    assert digest_object(values[3]) == values[0]['service']['show_digest']
    assert digest_object(values[2]) != digest_object(values[3])
    from qualification.recovery_probe_v8 import stable_runtime
    assert stable_runtime(values[0]) != stable_runtime(values[1])


@pytest.mark.parametrize('section,key,value', [
    (None, 'model_digest', 'different-model'),
    ('service', 'pid', 'changed-after-pinning'),
    ('service', 'show_digest', 'different-metadata'),
    ('service', 'version', 'different-version'),
    ('environment', 'candidate_network', 'host'),
    ('environment', 'image', 'unqualified-image'),
    ('runtime_binaries', 'ollama', {'digest': 'different', 'bytes': 0}),
])
def test_even_restarted_process_is_not_normalized_during_successor_admission(section, key, value):
    values = inputs()
    target = values[1] if section is None else values[1][section]
    target[key] = value
    with pytest.raises(ValidationError, match='successor runtime changed'):
        validate_identity(*values)


@pytest.mark.parametrize('key,value', [
    ('template', 'injected template'), ('parameters', 'temperature 0'),
    ('modified_at', 'another-time'), ('capabilities', ['completion']),
    ('model_info', {}), ('modelfile', 'FROM a-different-model'),
])
def test_metadata_tampering_fails_before_dispatch(key, value):
    values = inputs(); values[2][key] = value
    with pytest.raises(ValidationError, match='successor metadata changed'):
        validate_identity(*values)


def test_binding_names_separate_runtime_harness_and_exact_tool_contract():
    ctx = context(Path.cwd())
    for name in ctx['fixtures']:
        row = binding(ctx, name)
        assert row['harness']['version'] == HARNESS
        assert row['adapter']['version'] == 'myskills-tools/4.0.1'
        assert row['environment']['runtime_digest'] == RUNTIME_DIGEST
        assert row['environment']['runtime_profile'] == 'myskills-local-runtime/8.2.0'
        assert row['task_class']['schema_digest'] == ctx['runtime_profile']['tool_contracts'][name]


def test_imported_recovery_dependency_is_in_native_identity(monkeypatch):
    from qualification import runtime_successor_v8 as successor
    name = 'qualification/recovery_probe_v8.py'
    before = context(Path.cwd())
    assert name in before['harness']
    original = successor.file_digest
    monkeypatch.setattr(successor, 'file_digest', lambda path:
                        'sha256:changed-dependency' if path == Path.cwd()/name else original(path))
    assert digest_object(context(Path.cwd())) != digest_object(before)


def test_successor_collection_releases_source_when_context_retention_fails(tmp_path, monkeypatch):
    from qualification import successor_probe_v8 as recovery
    events = []
    receipt = {'files': ['source.py']}

    class FaultingVault:
        def __init__(self, *args):
            pass

        def freeze_sources(self, *args):
            events.append('frozen')
            return receipt

        def retain(self, *args):
            raise OSError('context storage failed')

    def git(args, **kwargs):
        return '' if args[1] == 'status' else 'source.py\n' if args[1] == 'ls-files' else 'collector\n'

    monkeypatch.setattr(recovery.subprocess, 'check_output', git)
    monkeypatch.setattr(recovery, 'context', lambda root: {'runtime': {}})
    monkeypatch.setattr(recovery, 'Vault', FaultingVault)
    monkeypatch.setattr(recovery, 'release_sources', lambda root, owner, actual: events.append(('released', actual)))
    with pytest.raises(OSError, match='context storage failed'):
        recovery.collect(tmp_path/'source', tmp_path/'evidence', tmp_path/'evidence/batch')
    assert events == ['frozen', ('released', receipt)]
