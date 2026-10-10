import json
from pathlib import Path
import pytest
from myskills.manifest import ValidationError
from qualification.custody_v5 import package,restore,permitted
from qualification.v5.probe import context


def test_round_trip_rejects_changed_or_out_of_scope_evidence(tmp_path):
    source=tmp_path/'source';source.mkdir();(source/'context.json').write_text('{}')
    pin=package(source,tmp_path/'parts')
    bodies=[(tmp_path/'parts'/f'part-{i}.md').read_text() for i in range(len(pin['parts']))]
    restore(pin,bodies,tmp_path/'restored')
    assert (tmp_path/'restored/context.json').read_text()=='{}'
    with pytest.raises(ValidationError):restore(pin,[bodies[0]+'tampered'],tmp_path/'bad')
    for path in ['../secret','/etc/passwd','tdd--representative/journal/32-completed.json',
                 'tdd--fake/observation.json','tdd--representative/../context.json']:
        assert not permitted(path)


def test_transitive_policy_and_replay_sources_are_bound():
    ctx=context(Path(__file__).parents[1])
    for path in ['qualification/policy_successor_v4.py','qualification/checkpoint_four.py',
                 'qualification/v5/evaluate.py','qualification/v5/execution.py',
                 'qualification/v4/adapter.py','qualification/checkpoint5/profile-policy.json']:
        assert ctx['harness'][path].startswith('sha256:')
