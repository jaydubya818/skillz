import json
from pathlib import Path

import pytest

from myskills.manifest import ValidationError
from qualification.checkpoint_four import unseal


@pytest.mark.parametrize('checkpoint', ['5-followup', '6'])
def test_tool_mismatch_captures_actual_result_and_restores_adapter(tmp_path, monkeypatch, checkpoint):
    from qualification import replay_tool_diagnostics_v2 as observer
    fixture = {'skill': 'tdd', 'files': {'clamp.py': 'old'}, 'writable': ['clamp.py'],
               'commands': {'test': ['python3', '-c', 'fixture']}}
    name = 'case'
    directory = tmp_path/name; directory.mkdir()
    (directory/'observation.json').write_text(json.dumps({'binding': {'fixture': 'bound'}}))
    original = observer.tools_replay.Session
    def fail(root, retained, output):
        output.mkdir()
        def execute(*args):
            return {'exit_code': 1, 'stdout': '', 'stderr': 'actual failure',
                    'cleanup_confirmed': True, 'unauthorized_changes': []}
        session = observer.tools_replay.Session(name, fixture, execute)
        session.call('actual-call', 'run_check', {'command': 'test'})
        raise ValidationError('independent tool replay differs')
    runner = observer.followup if checkpoint == '5-followup' else observer.claims
    monkeypatch.setattr(runner, 'replay', fail)
    with pytest.raises(ValidationError, match='tool replay differs'):
        observer.replay(Path.cwd(), tmp_path, tmp_path/'result', checkpoint)
    actual = json.loads((tmp_path/'result/replay-journal/case/0-completed.json').read_text())
    unseal(actual)
    assert actual['binding'] == {'fixture': 'bound'}
    assert actual['result']['payload']['stderr'] == 'actual failure'
    receipt = json.loads((tmp_path/'result/tool-observer.json').read_text()); unseal(receipt)
    assert receipt['qualification_credit'] is False
    assert observer.tools_replay.Session is original
