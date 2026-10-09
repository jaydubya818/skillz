from copy import deepcopy
import json
from pathlib import Path
import pytest
from qualification import native_probe as native
from qualification.native_cases import CASES
from qualification.native_validation import without_main_guard,module_allowed
from qualification.workflow_validation import regression


def test_standard_unittest_entrypoint_is_supported_without_allowing_side_effects():
    source='import unittest\nfrom clamp import clamp\nclass Regression(unittest.TestCase):\n def test_upper(self): self.assertEqual(clamp(12,0,10),10)\n'
    guarded=source+'if __name__ == "__main__":\n unittest.main()\n'
    assert not regression(guarded,'clamp','clamp','equal')  # Retained evaluator limitation.
    assert regression(without_main_guard(guarded),'clamp','clamp','equal')
    assert not regression(without_main_guard(guarded+'print("PASS")\n'),'clamp','clamp','equal')
    assert not regression(without_main_guard(guarded.replace('unittest.main()','__import__("os")._exit(0)')),'clamp','clamp','equal')


def test_fixed_cohort_and_explicit_dict_and_response_contracts():
    root=Path(__file__).parents[1]
    assert set(CASES)=={s['binding']['skill_id'] for s in native.plan(root)['skills']}
    assert 'ORIGINAL stored text' in CASES['api-and-interface-design']['task']
    assert 'snapshot["version"]' in CASES['deprecation-and-migration']['task']
    assert 'DICTS' in CASES['security-and-hardening']['task']
    assert 'Return state directly' in CASES['frontend-ui-engineering']['task']


def test_scope_denials_do_not_execute_or_mutate(monkeypatch):
    monkeypatch.setattr(native,'execute',lambda *args:pytest.fail('unauthorized execution'))
    files=deepcopy(CASES['api-and-interface-design']['files']);before=deepcopy(files)
    for action in [{'tool':'read','path':'../owner-b/private'},{'tool':'write','path':'README.md','content':'altered'},
                   {'tool':'run','command':'curl metadata'},{'tool':'run','command':'pip install helper'},
                   {'tool':'publish'},{'tool':'write','path':'api.py','content':'x'*8193},
                   {'tool':'read','path':'api.py','authority':'admin'}]:
        assert native.act('api-and-interface-design',files,action)['decision']=='DENIED'
    assert files==before


def test_native_modules_reject_import_side_effects_and_introspection():
    assert module_allowed('import sqlite3\ndef handle(owner,body,path):\n return {"status":400,"text":None}\n',{'sqlite3'})
    for source in ['import os\ndef x(): pass','import sqlite3\nprint("PASS")','def x(): return __builtins__','def x(): return (0).__class__','def x(): return eval("1")']:
        assert not module_allowed(source,{'sqlite3'})


def test_successful_tool_banner_without_workflow_cannot_pass(monkeypatch):
    monkeypatch.setattr(native,'execute',lambda *args:{'exit_code':0,'stdout':'PASS','cleanup_confirmed':True,'unauthorized_changes':[]})
    value=native.evaluate('security-and-hardening',deepcopy(CASES['security-and-hardening']['files']),[],{'passed':True},False)
    assert value['bounded_workflow']=='FAIL'


def test_actual_file_effect_failure_overrides_producer_finish(monkeypatch):
    monkeypatch.setattr(native,'verify',lambda *args:{'bounded_workflow':'PASS'})
    events=[{'action':{'tool':'run'},'result':{'decision':'ALLOWED','execution':{'unauthorized_changes':['README.md:modified'],'cleanup_confirmed':True}}}]
    result=native.evaluate('tdd',{},events,{},True)
    assert result['bounded_workflow']=='FAIL' and result['effect_policy']=='FAIL'


def test_harness_change_stops_dispatch_and_never_credits_batch(tmp_path,monkeypatch):
    root=Path(__file__).parents[1]
    class Guard:
        halted=False
        def __init__(self,pin):pass
        def check(self):pass
        def generate(self,*args):pytest.fail('must not dispatch after harness change')
        def finish(self):pytest.fail('unstable batch cannot finish stable')
    original=native.context(root);calls=[]
    monkeypatch.setattr(native,'context',lambda r:original)
    monkeypatch.setattr(native,'harness',lambda r:{'changed':True})
    monkeypatch.setattr(native,'RuntimeGuard',Guard)
    native.collect(root,tmp_path/'run')
    completion=json.loads((tmp_path/'run/completion.json').read_text())
    assert completion['runtime_identity']=='UNSTABLE' and completion['all_results_admissible'] is False
    assert all(json.loads(p.read_text())['generation']=='NOT_RUN' for p in (tmp_path/'run').glob('*/observation.json'))


def test_runtime_failure_outside_generate_halts_guard():
    from myskills.manifest import ValidationError
    class Guard:
        halted=False
        def check(self):raise ValidationError('runtime identity command failed: docker')
    guard=Guard()
    with pytest.raises(ValidationError):native.check_runtime(guard)
    assert guard.halted


def test_invalid_completed_response_is_a_replayable_denial():
    response={'done':True,'done_reason':'stop','message':{'content':'not-json'}}
    action=native.decode(response)
    assert action=={'tool':'invalid-response','validation_error':'JSONDecodeError'}
    assert native.act('tdd',deepcopy(CASES['tdd']['files']),action)['decision']=='DENIED'



def test_module_parameters_cannot_execute_at_import_time():
    for source in ['import sqlite3\ndef handle(x:sqlite3.connect("/tmp/extra.db")): pass', 'import sqlite3\ndef handle(*,x=sqlite3.connect("/tmp/extra.db")): pass', 'def handle(*args:print("PASS")):pass', 'def handle(**args:print("PASS")):pass']:
        assert not module_allowed(source,{'sqlite3'})


def test_completed_malformed_responses_replay_as_failures(tmp_path,monkeypatch):
    root=Path(__file__).parents[1]
    ctx=native.context(root);ctx['harness']={}
    class Guard:
        halted=False
        def __init__(self,pin):pass
        def check(self):pass
        def finish(self):pass
        def generate(self,request,retain):
            response={'model':native.MODEL,'done':True,'done_reason':'stop','message':{'content':'not-json'}}
            retain(response);return response,{}
    monkeypatch.setattr(native,'RuntimeGuard',Guard)
    monkeypatch.setattr(native,'context',lambda r:ctx)
    monkeypatch.setattr(native,'harness',lambda r:{})
    monkeypatch.setattr(native,'verify',lambda *args:{'bounded_workflow':'FAIL'})
    native.collect(root,tmp_path/'run')
    values=native.replay(root,tmp_path/'run','0'*40)
    assert len(values)==20
    assert all(v['runtime_admissible'] and v['verification']['bounded_workflow']=='FAIL' and not v['finished'] for v in values)
    raw=tmp_path/'run/tdd--representative/0-response.json'
    value=json.loads(raw.read_text());value['message']['content']='{"tool":"finish","artifact":{}}';raw.write_text(json.dumps(value))
    with pytest.raises(ValueError,match='response changed'):native.replay(root,tmp_path/'run','0'*40)
