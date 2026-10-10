import json
from pathlib import Path

import pytest

from myskills.cohort_assessment import seal
from myskills.manifest import ValidationError
from qualification.v4.adapter import Session
from qualification.v4.probe import entries


def test_strict_mismatch_retains_actual_tool_result(tmp_path, monkeypatch):
    from qualification import replay_v8
    fixture = {'skill': 'tdd', 'files': {'clamp.py': 'old'}, 'writable': ['clamp.py'],
               'commands': {'test': ['python3', '-c', 'fixture']}}
    identity = {'task_class': {'name': 'replay-case'}}
    def result(stdout):
        return {'exit_code': 0, 'stdout': stdout, 'stderr': '', 'cleanup_confirmed': True, 'unauthorized_changes': []}
    retained = tmp_path/'retained'
    session = Session('replay-case', fixture, lambda *args: result('original'), retained/'journal', identity)
    session.call('actual-call', 'run_check', {'command': 'test'})
    record = {'binding': identity, 'entries': entries(retained/'journal'), 'files': session.files,
              'finished': False, 'artifact': {}}
    monkeypatch.setattr(replay_v8, 'executor', lambda skill: lambda *args: result('different'))
    with pytest.raises(ValidationError, match='independent tool replay differs'):
        replay_v8.replay_entries(fixture, record, retained, tmp_path/'actual')
    actual = json.loads((tmp_path/'actual/replay-case/0-completed.json').read_text())
    assert actual['result']['payload']['stdout'] == 'different'
    assert actual['binding'] == identity
    assert actual['request']['call_id'] == 'actual-call'


def test_fallible_independent_execution_is_retained_and_wrappers_restored(tmp_path, monkeypatch):
    from qualification import checkpoint_eight
    from qualification.v7 import evaluate
    def original(skill):
        def fail(*args, **kwargs):
            raise RuntimeError('infrastructure error')
        return fail
    monkeypatch.setattr(evaluate, 'executor', original)
    def report(*args):
        return evaluate.executor('api-and-interface-design')({}, [], [])
    monkeypatch.setattr(checkpoint_eight, 'report', report)
    with pytest.raises(RuntimeError, match='infrastructure error'):
        checkpoint_eight.run(Path.cwd(), tmp_path, tmp_path, tmp_path/'result')
    evidence = json.loads((tmp_path/'result/executions.json').read_text())
    assert evidence['executions'][0]['state'] == 'RAISED'
    assert evidence['executions'][0]['error'] == 'RuntimeError: infrastructure error'
    assert json.loads((tmp_path/'result/failure.json').read_text())['qualification_credit'] is False
    assert evaluate.executor is original


def test_starting_source_requires_exact_native_snapshot(tmp_path, monkeypatch):
    from myskills.digest import digest_object
    from qualification import checkpoint_eight, custody_v7r1
    record = seal({'generation': 'COMPLETED', 'binding': {'skill': 'api'},
                   'collector_commit': 'frozen', 'files': {'api.py': 'original'}})
    bundle = {'files': {'observation': record}}
    digest = digest_object(bundle)
    monkeypatch.setattr(custody_v7r1, 'bundle', lambda directory: bundle)
    pin_path = tmp_path/'qualification/checkpoint7/followup/evidence-pin.json'
    pin_path.parent.mkdir(parents=True)
    pin_path.write_text(json.dumps({'bundle_digest': digest}))
    previous = tmp_path/'previous/api--representative'
    previous.mkdir(parents=True)
    (previous/'observation.json').write_text(json.dumps(record))
    item = {'observation_digest': record['evidence_digest'], 'binding': record['binding'],
            'collector_commit': record['collector_commit'], 'files': record['files']}
    monkeypatch.setattr(checkpoint_eight, 'INPUTS', seal({'bundle_digest': digest, 'skills': {'api': item}}))
    assert checkpoint_eight.verify_starting_source(tmp_path, previous.parent) == digest
    item['files'] = {'api.py': 'substitution'}
    monkeypatch.setattr(checkpoint_eight, 'INPUTS', seal({'bundle_digest': digest, 'skills': {'api': item}}))
    with pytest.raises(ValidationError, match='starting source binding differs'):
        checkpoint_eight.verify_starting_source(tmp_path, previous.parent)


def test_recovery_runtime_allows_only_process_identity_change():
    from qualification.recovery_probe_v8 import stable_runtime
    old = {'model_digest': 'fixed', 'service': {'pid': '1', 'process': 'Fri Oct  9 00:32:19 2026     /exact/ollama serve', 'version': '0.40.2'}, 'environment': {}}
    restarted = {**old, 'service': {**old['service'], 'pid': '2', 'process': 'Fri Oct  9 21:03:19 2026     /exact/ollama serve'}}
    assert stable_runtime(old) == stable_runtime(restarted)
    assert stable_runtime(old) != stable_runtime({**restarted, 'model_digest': 'substitution'})
    assert stable_runtime(old) != stable_runtime({**restarted, 'service': {**restarted['service'], 'version': 'new'}})
    assert stable_runtime(old) != stable_runtime({**restarted, 'service': {**restarted['service'], 'process': 'Fri Oct  9 21:03:19 2026     /different/ollama serve'}})


def test_context_custody_failure_releases_frozen_source(tmp_path, monkeypatch):
    from qualification import recovery_probe_v8 as recovery
    events = []
    receipt = {'files': ['source.py']}

    class FaultingVault:
        def __init__(self, *args):
            pass

        def freeze_sources(self, *args):
            events.append('frozen')
            return receipt

        def retain(self, name, content):
            raise OSError('injected context custody failure')

    def git(args, **kwargs):
        return '' if args[1] == 'status' else 'source.py\n' if args[1] == 'ls-files' else 'collector-sha\n'

    monkeypatch.setattr(recovery.subprocess, 'check_output', git)
    monkeypatch.setattr(recovery, 'context', lambda root: {'runtime': {}})
    monkeypatch.setattr(recovery, 'Vault', FaultingVault)
    monkeypatch.setattr(recovery, 'release_sources', lambda root, owner, actual: events.append(('released', actual)))
    with pytest.raises(OSError, match='injected context custody failure'):
        recovery.collect(tmp_path/'source', tmp_path/'evidence', tmp_path/'evidence/batch')
    assert events == ['frozen', ('released', receipt)]
