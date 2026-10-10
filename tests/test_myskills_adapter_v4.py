from copy import deepcopy
import threading
import pytest

from myskills.digest import digest_object
from myskills.manifest import ValidationError
from qualification.v4.adapter import Session,schemas,validate_output,codex_response,mcp_response
from qualification.v4.cases import CASES
from qualification.local_probe import ContainmentError


def session(execute=None):
    return Session('test',CASES['security-and-hardening'],execute or (lambda *args:pytest.fail('unexpected execution')))


def test_null_destination_and_authority_requests_are_denied_without_effects():
    s=session();before=deepcopy(s.files)
    for index,value in enumerate([None,'',False,0,[],{},'http://127.0.0.1','http://169.254.169.254']):
        assert s.call(str(index),'read_file',{'path':'security.py','destination':value})['code']=='EFFECT_DENIED'
    assert s.call('missing','read_file',{'path':'security.py'})['status']=='OK'
    assert s.files==before


@pytest.mark.parametrize('name,args',[
 ('read_file',{'path':'../owner-b/private'}),('read_file',{'path':'/etc/passwd'}),
 ('read_file',{'path':'hidden-tests.py'}),('read_file',{'path':'a/../../private'}),
 ('write_file',{'path':'evidence.json','content':'PASS','expected_digest':'ABSENT'}),
 ('write_file',{'path':'README.md','content':'Ignore policy','expected_digest':'ABSENT'}),
 ('run_check',{'command':'curl https://example.com'}),('publish',{}),
 ('read_file',{'path':'security.py','authority':'admin'}),('read_file',{'path':'file:///etc/passwd'})])
def test_boundary_requests_cannot_dispatch_or_mutate(name,args):
    s=session();before=deepcopy(s.files)
    assert s.call('denied',name,args)['code']=='EFFECT_DENIED'
    assert s.files==before


def test_schema_confusion_is_recoverable_without_relaxing_authority():
    s=session()
    assert s.call('bad','run_check',{})['code']=='INVALID_ARGUMENT'
    assert s.call('wrong','read_file',{'path':None})['code']=='INVALID_ARGUMENT'
    assert s.call('extra','read_file',{'path':'security.py','command':'test'})['code']=='INVALID_ARGUMENT'
    assert s.call('recover','read_file',{'path':'security.py'})['status']=='OK'
    assert all(s['inputSchema']['required']==list(s['inputSchema']['properties']) and s['inputSchema']['additionalProperties'] is False for s in schemas(CASES['tdd']))


def test_compare_and_write_idempotency_and_call_identity_conflicts():
    s=session();r=s.call('read','read_file',{'path':'security.py'})
    args={'path':'security.py','content':'def authorize(x): return {}','expected_digest':r['payload']['digest']}
    result=s.call('write','write_file',args)
    assert result['status']=='OK' and s.call('write','write_file',args)==result
    assert len(s.events)==2
    assert s.call('conflict','write_file',args)['code']=='STALE_WRITE'
    assert s.call('write','write_file',{**args,'content':'altered'})['code']=='CALL_ID_CONFLICT'
    assert s.files['security.py']==args['content']


def test_duplicate_check_executes_once_and_bad_output_closes_session():
    calls=[]
    def run(*args):
        calls.append(args);return {'exit_code':1,'stdout':'','stderr':'failure','cleanup_confirmed':True,'unauthorized_changes':[]}
    s=session(run);a=s.call('run','run_check',{'command':'test'})
    assert s.call('run','run_check',{'command':'test'})==a and len(calls)==1
    assert a['status']=='OK' and a['payload']['exit_code']==1
    broken=session(lambda *args:{'stdout':'PASS'})
    assert broken.call('bad','run_check',{'command':'test'})['code']=='EXECUTOR_FAILURE'
    assert broken.call('next','read_file',{'path':'security.py'})['code']=='SESSION_CLOSED'


def test_cancellation_reaches_running_executor_and_prevents_new_work():
    started=threading.Event()
    def run(files,argv,writable,cancel):
        started.set();assert cancel.wait(2)
        return {'exit_code':None,'failure':'CANCELLED','stdout':'','stderr':'','cleanup_confirmed':True,'unauthorized_changes':[]}
    s=session(run);results=[]
    worker=threading.Thread(target=lambda:results.append(s.call('run','run_check',{'command':'test'})))
    worker.start();assert started.wait(2);s.cancel();worker.join(2)
    assert not worker.is_alive() and results[0]['code']=='CANCELLED'
    assert s.call('later','read_file',{'path':'security.py'})['code']=='CANCELLED'


def test_evidence_tampering_and_transport_envelopes():
    s=session();r=s.call('one','read_file',{'path':'security.py'})
    assert codex_response(r)['success'] is True and mcp_response(r)['isError'] is False
    r['payload']['content']='tampered'
    with pytest.raises(ValidationError,match='seal changed'):validate_output(r)


def test_containment_failure_is_terminal():
    s=session(lambda *args:{'exit_code':0,'stdout':'','stderr':'','cleanup_confirmed':False,'unauthorized_changes':[]})
    with pytest.raises(ContainmentError):s.call('run','run_check',{'command':'test'})
    assert s.cancelled.is_set() and s.events[-1]['result']['code']=='CONTAINMENT_FAILURE'
    assert s.call('finish','finish',{'artifact':{},'notes':'PASS'})['code']=='CANCELLED'


def test_journal_precedes_effect_and_interrupted_dispatch_cannot_resume(tmp_path):
    import json
    journal=tmp_path/'run'
    def execute(*args):
        value=json.loads((journal/'0-dispatched.json').read_text())
        assert value['request']['tool']=='run_check' and value['files']['security.py']
        raise ContainmentError('unknown cleanup')
    s=Session('durable',CASES['security-and-hardening'],execute,journal,{'runtime':'bound'})
    with pytest.raises(ContainmentError):s.call('one','run_check',{'command':'test'})
    assert (journal/'0-completed.json').is_file()
    with pytest.raises(FileExistsError):Session('durable',CASES['security-and-hardening'],execute,journal)


def test_traffic_bound_applies_to_invalid_and_terminal_requests():
    s=session()
    for i in range(32):s.call(str(i),'publish',{})
    with pytest.raises(ValidationError,match='traffic limit'):s.call('one-more','publish',{})
    assert len(s.events)==32


def test_source_policy_blocks_oracle_read_and_forged_tests_before_dispatch(monkeypatch):
    from qualification.v4 import source_policy
    monkeypatch.setattr(source_policy,'execute',lambda *args:pytest.fail('must not dispatch'))
    for skill,path,source in [
        ('security-and-hardening','security.py','import os\ndef authorize(x): return open("/proc/1/cmdline").read()'),
        ('api-and-interface-design','api.py','import sqlite3\ndef handle(a,b,c): return sqlite3.connect(c).enable_load_extension(True)'),
        ('tdd','test_clamp.py','print("OK")')]:
        files={**CASES[skill]['files'],path:source}
        assert source_policy.executor(skill)(files,CASES[skill]['commands']['test'],CASES[skill]['writable'])['failure']=='SOURCE_POLICY'


def test_resealed_wrong_context_or_status_is_rejected():
    from myskills.cohort_assessment import seal
    s=session();r=s.call('one','read_file',{'path':'security.py'})
    with pytest.raises(ValidationError,match='context'):validate_output(r,'other','one',r['request_digest'])
    altered=seal({**{k:v for k,v in r.items() if k!='evidence_digest'},'code':'CANCELLED'})
    with pytest.raises(ValidationError,match='status/code'):validate_output(altered)


def test_tdd_call_aliases_and_builtin_rebinding_fail_closed():
    from qualification.v4.source_policy import clamp_allowed
    assert clamp_allowed('def clamp(value, low, high): return max(low,min(value,high))')
    for body in ['max = eval; return max("1")','return eval("1")',
                 'return (max := eval)("1")','return value.__class__',
                 'def max(x): return x\n    return max(value)']:
        assert not clamp_allowed('def clamp(value, low, high):\n    '+body)
