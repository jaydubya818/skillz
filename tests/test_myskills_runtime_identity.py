from copy import deepcopy
import pytest
from myskills.manifest import ValidationError
from qualification.runtime_identity import require_same, bind_result


def test_identity_changes_fail_closed():
    pin = {'model_digest':'sha256:one','runtime':'0.40.2','runner':'llamacpp','environment':{'arch':'arm64'}}
    for key in pin:
        altered = deepcopy(pin)
        altered[key] = 'changed'
        with pytest.raises(ValidationError):
            require_same(pin,altered)


def test_result_binds_every_identity():
    fields={'runtime':{'model':'exact'},'harness':{'file':'digest'},'skill':{'digest':'skill'},
            'fixture':{'task':1},'evaluation':{'version':2},'output':{'program':'real'}}
    bound=bind_result(**fields)
    for key in fields:
        changed=deepcopy(fields);changed[key]={'changed':True}
        assert bind_result(**changed)['evidence_digest'] != bound['evidence_digest']


def test_local_api_rejects_alias_and_remote_dispatch(monkeypatch):
    from qualification import runtime_identity as runtime
    calls=[]
    monkeypatch.setattr(runtime.urllib.request,'build_opener',lambda *args: calls.append(args))
    for model in ('qwen3.5:35b-a3b-q8_0','cloud-model','sha256-accad778'):
        with pytest.raises(ValidationError):
            runtime.api('chat',{'model':model})
    with pytest.raises(ValidationError):
        runtime.api('pull',{'model':runtime.MODEL})
    assert calls==[]


def test_postcheck_failure_preserves_response_and_halts_later_dispatch(monkeypatch):
    from qualification import runtime_identity as runtime
    guard=object.__new__(runtime.RuntimeGuard);guard.halted=False
    calls=[];retained=[]
    def check():
        if guard.halted or calls:
            raise ValidationError('identity changed')
    guard.check=check
    def api(*args):
        calls.append(args)
        return {'model':runtime.MODEL,'done':True}
    monkeypatch.setattr(runtime,'api',api)
    with pytest.raises(ValidationError):guard.generate({'model':runtime.MODEL},retained.append)
    with pytest.raises(ValidationError):guard.generate({'model':runtime.MODEL},retained.append)
    assert len(calls)==1 and len(retained)==1 and guard.halted


def test_corrected_fixture_is_separate_from_original():
    from pathlib import Path
    from qualification.behavior_v2 import request_for
    from qualification.local_probe import make_request
    import json
    root=Path(__file__).parents[1]
    plan=json.loads((root/'qualification/initial-cohort/plan.json').read_text())
    spec=next(s for s in plan['skills'] if s['binding']['skill_id']=='api-and-interface-design')
    legacy=make_request(root,plan,spec,False)
    revised=request_for(root,plan,spec,'representative')
    old=json.loads(legacy['messages'][1]['content'])
    new=json.loads(revised['messages'][1]['content'])
    assert 'owner' in old['fixture']['requests'][0]
    assert 'trusted_owner' in new['fixture']['requests'][0]
    assert new['binding']==old['binding']
    assert revised['format']['properties']['artifact']['required']==['program']
