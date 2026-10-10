from pathlib import Path
import json

import pytest

from myskills.digest import digest_object
from qualification import workflow_correction_v8 as successor
from qualification.v8.evaluate import bounded_api_policy


def test_workflow_successor_keeps_runtime_tools_source_and_evaluator():
    old = successor.previous.context(Path.cwd())
    new = successor.context(Path.cwd())
    assert new['runtime'] == old['runtime']
    assert new['runtime_profile'] == old['runtime_profile']
    assert new['claim_verifier'] == old['claim_verifier']
    assert new['evaluator'] == old['evaluator']
    for name, fixture in successor.CASES.items():
        source = 'api.py' if fixture['skill'] == 'api-and-interface-design' else 'security.py'
        assert fixture['files'][source] == successor.ORIGINAL[name]['files'][source]
        assert fixture['commands'] == successor.ORIGINAL[name]['commands']
        assert fixture['writable'] == successor.ORIGINAL[name]['writable']
        row = successor.binding(new, name)
        assert row['harness']['version'] == successor.HARNESS
        assert row['task_class']['fixture_digest'] == digest_object(fixture)
        assert row['task_class']['schema_digest'] == old['runtime_profile']['tool_contracts'][name]
        prompt = json.loads(successor.prompt(Path.cwd(), new, name))
        assert prompt['task'] == fixture['task']
    assert new['harness']['qualification/workflow_correction_v8.py']
    assert digest_object(new) != digest_object(old)


def test_frozen_policy_still_rejects_sql_literal_reformatting():
    baseline = successor.ORIGINAL['api-and-interface-design--representative']['files']['api.py']
    corrected = baseline.replace('    conn.execute("PRAGMA journal_mode=WAL")\n', '').replace('timeout=30.0', 'timeout=1.0')
    assert bounded_api_policy(corrected)
    assert not bounded_api_policy(corrected.replace('CREATE TABLE ', 'CREATE  TABLE '))


def test_collector_binding_is_restored_on_failure():
    original = successor.collector.context
    with pytest.raises(RuntimeError):
        with successor.corrected_collector():
            assert successor.collector.context is successor.context
            raise RuntimeError('interruption')
    assert successor.collector.context is original
