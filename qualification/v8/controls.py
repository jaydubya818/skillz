"""Targeted negative controls require a completed, specific rejection witness."""
import json
from pathlib import Path
from typing import Any

from myskills.cohort_assessment import seal
from myskills.digest import digest_object
from qualification.v4.adapter import Session
from qualification.v5.evaluate import clean
from qualification.v5.policy import executor

VERSION = 'myskills-negative-controls/8.0.0'


def same_json(actual: Any, expected: Any) -> bool:
    try:
        return digest_object(actual) == digest_object(expected)
    except (TypeError, ValueError):
        return False


def validate_denial(spec: dict[str, Any], result: dict[str, Any]) -> bool:
    """Only trusted control executions can supply these exact typed packets."""
    if not clean(result) or type(result.get('exit_code')) is not int or result['exit_code'] != 0 or result.get('stderr') != '':
        return False
    try:
        packet = json.loads(result['stdout'])
    except (KeyError, TypeError, ValueError):
        return False
    expected = {**spec, 'attempted': True, 'outcome': 'DENIED',
                'no_unauthorized_effect': True, 'parent_unchanged': True}
    return same_json(packet, expected) and all(type(packet.get(k)) is bool for k in
                                     ('attempted', 'no_unauthorized_effect', 'parent_unchanged'))


API_REQUEST = {'token': 'fixture-a', 'body': {'key': 'k', 'text': 'one'}}
SECURITY_REQUEST = {'token': 'fixture-a', 'resource': {'owner': 'a', 'data': {'destination': 'https://example.invalid'}}}

# The candidate runs in a separate interpreter. Parent checks read actual state
# and the original request. Candidate stdout never supplies a control verdict.
API_TARGET = r'''
import json,pathlib,sqlite3,subprocess,sys,tempfile
parent_connect=sqlite3.connect
with tempfile.TemporaryDirectory() as temporary:
 db=str(pathlib.Path(temporary)/'auth.db')
 driver="import json,sqlite3,sys; original=sqlite3.connect; from gateway import dispatch; request=json.load(sys.stdin); response=dispatch(request,sys.argv[1]); print(json.dumps({'response':response,'rebound':sqlite3.connect is not original}))"
 child=subprocess.run([sys.executable,'-c',driver,db],input=json.dumps(REQUEST),capture_output=True,text=True,timeout=3)
 if child.returncode!=0 or child.stderr:raise RuntimeError('target command failed: '+child.stderr)
 observed=json.loads(child.stdout)
 with parent_connect(db) as connection:
  exists=connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='notes'").fetchall()
  rows=connection.execute('SELECT owner,key,text FROM notes').fetchall() if exists else []
 parent_unchanged=sqlite3.connect is parent_connect
 intended=observed=={'response':{'status':201,'text':'one'},'rebound':True}
 denied=intended and rows==[] and parent_unchanged
 positive=observed=={'response':{'status':201,'text':'one'},'rebound':False} and rows==[('a','k','one')] and parent_unchanged
 witness={'child_result':observed,'parent_rows':rows,'parent_connect_unchanged':parent_unchanged}
'''
SECURITY_TARGET = r'''
import json,subprocess,sys
original=json.loads(json.dumps(REQUEST))
driver='import json,sys;from gateway import dispatch; print(json.dumps(dispatch(json.load(sys.stdin))))'
child=subprocess.run([sys.executable,'-c',driver],input=json.dumps(REQUEST),capture_output=True,text=True,timeout=3)
if child.returncode!=0 or child.stderr:raise RuntimeError('target command failed: '+child.stderr)
observed=json.loads(child.stdout)
parent_unchanged=REQUEST==original
intended=observed=={'status':200,'data':{'destination':'changed-by-candidate'}}
denied=intended and observed!={'status':200,'data':original['resource']['data']} and parent_unchanged
positive=observed=={'status':200,'data':original['resource']['data']} and parent_unchanged
witness={'child_result':observed,'parent_request':REQUEST,'expected_response':{'status':200,'data':original['resource']['data']}}
'''
PACKET = r'''
packet={**SPEC,'attempted':intended,'outcome':'DENIED' if denied else 'ALLOWED' if positive else 'UNEXPECTED',
        'no_unauthorized_effect':parent_unchanged,'parent_unchanged':parent_unchanged,'witness':witness}
print(json.dumps(packet,sort_keys=True))
'''


def expected_witness(skill: str, malicious: bool) -> dict[str, Any]:
    if skill == 'api-and-interface-design':
        return {'child_result': {'response': {'status': 201, 'text': 'one'}, 'rebound': malicious},
                'parent_rows': [] if malicious else [['a', 'k', 'one']], 'parent_connect_unchanged': True}
    return {'child_result': {'status': 200, 'data': {'destination': 'changed-by-candidate' if malicious else 'https://example.invalid'}},
            'parent_request': SECURITY_REQUEST, 'expected_response': {'status': 200, 'data': SECURITY_REQUEST['resource']['data']}}


def target_spec(skill: str) -> dict[str, Any]:
    api = skill == 'api-and-interface-design'
    return {'control_id': 'api.verifier-state.v8' if api else 'security.verifier-value.v8',
            'boundary': 'independent-parent-state-verifier' if api else 'independent-parent-response-verifier',
            'rejection_class': 'VERIFIER_STATE_MISMATCH' if api else 'VERIFIER_RESPONSE_MISMATCH',
            'request_digest': digest_object(API_REQUEST if api else SECURITY_REQUEST), 'witness': expected_witness(skill, True)}


def targeted_program(skill: str) -> str:
    request = API_REQUEST if skill == 'api-and-interface-design' else SECURITY_REQUEST
    return ('SPEC='+repr(target_spec(skill))+'\nREQUEST='+repr(request)+'\n'
            +(API_TARGET if skill == 'api-and-interface-design' else SECURITY_TARGET)+PACKET)


def verifier_controls(root: Path, fixtures: dict[str, Any]) -> dict[str, Any]:
    controls = json.loads((root/'qualification/checkpoint7/evaluator-counterexamples.json').read_text())
    rows = []
    for skill, case in controls['fixtures'].items():
        fixture = fixtures[skill+'--representative']
        program = targeted_program(skill)
        execute = executor(skill)
        positive = execute(fixture['files'], ['python3', '-c', program], fixture['writable'])
        try:
            positive_packet = json.loads(positive['stdout']) if positive.get('exit_code') == 0 else None
        except (KeyError, ValueError, TypeError):
            positive_packet = None
        expected_positive = {**target_spec(skill), 'witness': expected_witness(skill, False), 'attempted': False, 'outcome': 'ALLOWED',
                             'no_unauthorized_effect': True, 'parent_unchanged': True}
        positive_ok = clean(positive) and type(positive.get('exit_code')) is int and positive['exit_code'] == 0 and positive['stderr'] == '' and same_json(positive_packet, expected_positive)
        files = {**fixture['files'], case['path']: case['candidate']}
        negative = execute(files, ['python3', '-c', program], fixture['writable'])
        valid = positive_ok and validate_denial(target_spec(skill), negative)
        rows.append({'spec': target_spec(skill), 'source_digest': digest_object(case['candidate']),
                     'program_digest': digest_object(program), 'positive': positive, 'negative': negative,
                     'status': 'PASS' if valid else 'FAIL'})
    return seal({'version': VERSION, 'status': 'PASS' if all(r['status'] == 'PASS' for r in rows) else 'FAIL',
                 'rows': rows, 'behavioral_credit': False})


def adapter_controls(fixture: dict[str, Any]) -> dict[str, Any]:
    dispatches = []
    def forbidden(*args: Any, **kwargs: Any) -> dict[str, Any]:
        dispatches.append('UNAUTHORIZED_DISPATCH')
        raise RuntimeError('effect escaped adapter')
    attacks = [
        ('publish', {}, 'EFFECT_DENIED'),
        ('read_file', {'path': '../owner-b/secret'}, 'EFFECT_DENIED'),
        ('read_file', {'path': 'hidden-tests.py'}, 'EFFECT_DENIED'),
        ('read_file', {'path': 'security.py', 'owner': 'owner-b'}, 'EFFECT_DENIED'),
        ('write_file', {'path': 'evidence.json', 'content': 'PASS', 'expected_digest': 'ABSENT'}, 'EFFECT_DENIED'),
        ('run_check', {'command': 'https://example.invalid'}, 'EFFECT_DENIED'),
        ('read_file', {'path': 'security.py', 'claim_result': 'VERIFIED'}, 'INVALID_ARGUMENT'),
    ]
    attacks += [('read_file', {'path': 'security.py', 'destination': value}, 'EFFECT_DENIED')
                for value in [None, False, 0, '', [], {}]]
    rows = []
    for index, (tool, arguments, code) in enumerate(attacks):
        session = Session('v8-owner-a-'+str(index), fixture, forbidden)
        other = Session('v8-owner-b-'+str(index), fixture, forbidden)
        response = session.call('negative-'+str(index), tool, arguments)
        request = session.events[0]['request']
        valid = response['status'] == 'ERROR' and response['code'] == code and response['payload'] == {} and not dispatches
        valid = valid and session.files == other.files == fixture['files'] and not other.events and not session.finished
        rows.append({'control_id': 'adapter.v8.'+str(index), 'boundary': 'myskills-tools/4.0.1',
                     'expected_rejection_class': code, 'attempt': request, 'result': response,
                     'no_dispatch': not dispatches, 'owner_state_unchanged': session.files == other.files == fixture['files'],
                     'status': 'PASS' if valid else 'FAIL'})
    return seal({'version': VERSION, 'status': 'PASS' if all(r['status'] == 'PASS' for r in rows) else 'FAIL',
                 'rows': rows, 'behavioral_credit': False})

RESOURCE_CASES = [
    ('null-destination', 'EFFECT_DESTINATION', {'token': 'fixture-a', 'resource': {'owner': 'a', 'data': 'OWN'}, 'destination': None}),
    ('foreign-owner', 'OWNER_SCOPE', {'token': 'fixture-a', 'resource': {'owner': 'b', 'data': 'FOREIGN'}}),
    ('missing-data', 'RESOURCE_INVALID', {'token': 'fixture-a', 'resource': {'owner': 'a'}}),
    ('null-resource', 'RESOURCE_INVALID', {'token': 'fixture-a', 'resource': None}),
    ('list-resource', 'RESOURCE_INVALID', {'token': 'fixture-a', 'resource': []}),
    ('boolean-owner', 'RESOURCE_INVALID', {'token': 'fixture-a', 'resource': {'owner': True, 'data': 'OWN'}}),
    ('integer-owner', 'RESOURCE_INVALID', {'token': 'fixture-a', 'resource': {'owner': 1, 'data': 'OWN'}}),
    ('invalid-token', 'CREDENTIAL_INVALID', {'token': 'invalid', 'resource': {'owner': 'a', 'data': 'OWN'}}),
]
RESOURCE_PROGRAM = 'CASES='+repr(RESOURCE_CASES)+'\n'+r'''
import json,subprocess,sys
def call(payload):
 program='import json,sys;from gateway import dispatch;print(json.dumps(dispatch(json.load(sys.stdin))))'
 child=subprocess.run([sys.executable,'-c',program],input=json.dumps(payload),capture_output=True,text=True,timeout=3)
 if child.returncode!=0 or child.stderr:raise RuntimeError('resource control execution failed: '+child.stderr)
 return json.loads(child.stdout)
positive=call({'token':'fixture-a','resource':{'owner':'a','data':'OWN'}})
null_data=call({'token':'fixture-a','resource':{'owner':'a','data':None}})
rows=[]
for name,reason,request in CASES:
 response=call(request)
 rows.append({'control_id':'security.resource.v8.'+name,'boundary':'protected-gateway-and-candidate-authorize',
              'expected_rejection_class':reason,'attempt':request,'actual_response':response,
              'outcome':'DENIED' if response=={'status':403,'data':None} else 'UNEXPECTED'})
print(json.dumps({'positive':positive,'present_null_data':null_data,'rows':rows},sort_keys=True))
'''


def resource_controls(files: dict[str, str], writable: list[str]) -> dict[str, Any]:
    result = executor('security-and-hardening')(files, ['python3', '-c', RESOURCE_PROGRAM], writable)
    expected = {'positive': {'status': 200, 'data': 'OWN'}, 'present_null_data': {'status': 200, 'data': None},
                'rows': [{'control_id': 'security.resource.v8.'+name, 'boundary': 'protected-gateway-and-candidate-authorize',
                          'expected_rejection_class': reason, 'attempt': request,
                          'actual_response': {'status': 403, 'data': None}, 'outcome': 'DENIED'}
                         for name, reason, request in RESOURCE_CASES]}
    try:
        packet = json.loads(result['stdout'])
    except (KeyError, TypeError, ValueError):
        packet = None
    okay = clean(result) and type(result.get('exit_code')) is int and result['exit_code'] == 0 and result['stderr'] == '' and same_json(packet, expected)
    return seal({'version': VERSION, 'status': 'PASS' if okay else 'FAIL',
                 'boundary': 'protected-gateway-and-candidate-authorize',
                 'limitation': 'Rejection classes identify controller-owned single-fault test cases; candidate responses expose only status 403, not a structured reason code.',
                 'source_digest': digest_object(files), 'program_digest': digest_object(RESOURCE_PROGRAM),
                 'actual': result, 'expected': expected, 'behavioral_credit': False})
