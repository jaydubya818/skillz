import copy
import json
from pathlib import Path

import pytest

from qualification.v8.controls import validate_denial

SPEC = {'control_id': 'api.verifier-state.v8', 'boundary': 'independent-parent-state-verifier',
        'rejection_class': 'VERIFIER_STATE_MISMATCH', 'request_digest': 'sha256:request'}


def valid_result():
    packet = {**SPEC, 'attempted': True, 'outcome': 'DENIED', 'no_unauthorized_effect': True,
              'parent_unchanged': True}
    return {'exit_code': 0, 'stdout': json.dumps(packet), 'stderr': '',
            'cleanup_confirmed': True, 'unauthorized_changes': []}


def test_exact_denial_requires_identity_boundary_attempt_and_specific_reason():
    assert validate_denial(SPEC, valid_result())
    for key in SPEC:
        result = valid_result(); packet = json.loads(result['stdout']); packet[key] = 'wrong'
        result['stdout'] = json.dumps(packet)
        assert not validate_denial(SPEC, result)


@pytest.mark.parametrize('key,value', [
    ('exit_code', 1), ('exit_code', None), ('exit_code', False),
    ('failure', 'TIMEOUT'), ('failure', 'SOURCE_POLICY'), ('failure', 'EXECUTION_FAILURE'),
    ('stderr', 'dependency missing'), ('stdout', 'not-json'),
    ('cleanup_confirmed', False), ('unauthorized_changes', ['outside-workspace:file']),
])
def test_unrelated_failure_never_counts_as_control_success(key, value):
    result = valid_result(); result[key] = value
    assert not validate_denial(SPEC, result)


@pytest.mark.parametrize('change', [
    {'attempted': False}, {'attempted': 1}, {'outcome': 'ERROR'},
    {'outcome': 'ALLOWED'}, {'parent_unchanged': False}, {'no_unauthorized_effect': False},
    {'extra': 'producer-claim'},
])
def test_malformed_or_unestablished_attempt_is_not_a_denial(change):
    result = valid_result(); packet = json.loads(result['stdout']); packet.update(change)
    result['stdout'] = json.dumps(packet)
    assert not validate_denial(SPEC, result)


def test_retained_wrong_reason_control_failure_cannot_pass():
    hold = json.loads(Path('qualification/checkpoint7/acceptance-hold.json').read_text())
    result = hold['diagnostic_evaluator_controls']['results'][0]['counterexample']
    assert result['exit_code'] != 0 and 'database is locked' in result['stderr']
    assert not validate_denial(SPEC, result)


def test_contract_plan_precedes_every_implementation_write():
    from qualification.v8.evaluate import plan_before_implementation
    from qualification.v8.cases import CASES
    fixture = CASES['api-and-interface-design--adversarial']
    def write(path, content):
        return {'request': {'tool': 'write_file', 'arguments': {'path': path, 'content': content}}, 'result': {'status': 'OK'}}
    plan = write('contract.md', fixture['files']['contract-plan.json'])
    source = write('api.py', 'implementation')
    assert plan_before_implementation(fixture, [plan, source])
    assert not plan_before_implementation(fixture, [source, plan])
    assert not plan_before_implementation(fixture, [write('contract.md', '{}'), source, plan])
    bad = copy.deepcopy(plan)
    bad['request']['arguments']['content'] = bad['request']['arguments']['content'].replace('false', '0')
    assert not plan_before_implementation(fixture, [bad, source])


def test_api_connection_wait_is_bounded_without_retry_loop():
    from qualification.v8.evaluate import bounded_api_policy
    from qualification.v8.cases import INPUTS
    old = INPUTS['skills']['api-and-interface-design']['files']['api.py']
    fixed = old.replace('    conn.execute("PRAGMA journal_mode=WAL")\n', '').replace('timeout=30.0', 'timeout=1.0')
    assert bounded_api_policy(fixed)
    assert bounded_api_policy('# harmless formatting\n'+fixed)
    for candidate in [old, fixed.replace('timeout=1.0', 'timeout=30.0'),
                      fixed.replace('    try:', '    conn.execute("PRAGMA busy_timeout=30000")\n    try:', 1),
                      fixed.replace('    try:', '    conn.execute("PRAGMA journal_mode=WAL")\n    try:', 1),
                      'import sqlite3\ndef handle(path):\n while True: sqlite3.connect(path,timeout=1.0)',
                      'import sqlite3\ndef handle(path):\n return [sqlite3.connect(path,timeout=1.0) for i in [1,2]]',
                      'import sqlite3\ndef handle(path):\n try: return sqlite3.connect(path,timeout=1.0)\n except Exception: return handle(path)']:
        assert not bounded_api_policy(candidate)


def test_negative_witness_types_and_nonfinite_numbers_fail_closed():
    from qualification.v8.controls import target_spec
    spec = target_spec('api-and-interface-design')
    result = valid_result()
    packet = {**spec, 'attempted': True, 'outcome': 'DENIED', 'parent_unchanged': True, 'no_unauthorized_effect': True}
    result['stdout'] = json.dumps(packet)
    assert validate_denial(spec, result)
    packet['witness']['child_result']['rebound'] = 1
    result['stdout'] = json.dumps(packet)
    assert not validate_denial(target_spec('api-and-interface-design'), result)
    result['stdout'] = 'NaN'
    assert not validate_denial(spec, result)
