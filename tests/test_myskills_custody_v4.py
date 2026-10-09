from copy import deepcopy
import json
import pytest

from myskills.manifest import ValidationError
from qualification.checkpoint_four import native_complete
from qualification.custody_v4 import package,restore,permitted
from qualification.v4.adapter import Session,codex_response
from qualification.v4.cases import CASES


def test_custody_allows_only_exact_case_paths_and_detects_tampering(tmp_path):
    for name in ('../context.json','tdd--representative/../../x','other/observation.json',
                 'tdd--representative/journal/32-completed.json','interrupted-4.0.0/interrupted-4.0.0/context.json'):
        assert not permitted(name)
    source=tmp_path/'source';source.mkdir();(source/'context.json').write_text('{}')
    parts=tmp_path/'parts';pin=package(source,parts)
    bodies=[p.read_text() for p in sorted(parts.glob('part-*.md'))]
    restore(pin,bodies,tmp_path/'restored')
    with pytest.raises(ValidationError):restore(pin,[bodies[0]+'altered'],tmp_path/'tampered')


def test_native_custody_reconciles_duplicates_pending_and_wrong_responses(tmp_path,monkeypatch):
    import base64
    from qualification.runtime_identity import MODEL
    monkeypatch.setattr('qualification.checkpoint_four.validate_native_request',lambda *args:None)
    session=Session('test',CASES['tdd'],lambda *a:None)
    request={'call_id':'call1','tool':'read_file','arguments':{'path':'clamp.py'}}
    result=session.call(**{'call_id':request['call_id'],'name':request['tool'],'arguments':request['arguments']})
    record={'entries':[{'request':request,'result':result,'files':session.files}]}
    tool={'channel':'tool','id':'rpc1','value':{'callId':'call1','namespace':'myskills','tool':'read_file','arguments':request['arguments']}}
    reply={'channel':'host_response','id':'rpc1','value':codex_response(result)}
    done={'channel':'event','value':{'method':'turn/completed','params':{'turn':{'status':'completed'}}}}
    output={'type':'function_call','call_id':'call1','namespace':'myskills','name':'read_file','arguments':json.dumps(request['arguments'])}
    sse='data: '+json.dumps({'type':'response.completed','response':{'model':MODEL,'status':'completed','output':[output]}})+'\n'
    provider=[{'channel':'provider','id':'model1','value':{'model':MODEL}},
              {'channel':'host_response','id':'model1','value':{'status':200,'body':base64.b64encode(sse.encode()).decode()}}]
    def write(records,cleanup=True):
        records=provider+records
        (tmp_path/'native.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in records))
        (tmp_path/'transport.json').write_text(json.dumps({'records':records,'cleanup_confirmed':cleanup,'exit_code':0,'failure':None}))
    write([tool,reply,{**tool,'id':'rpc2'},{**reply,'id':'rpc2'},done])
    assert native_complete(tmp_path,record,'tdd')
    write([tool,reply,done],False)
    assert not native_complete(tmp_path,record,'tdd')
    pending={**tool,'id':'pending','value':{**tool['value'],'callId':'new'}}
    write([tool,reply,pending,done])
    assert not native_complete(tmp_path,record,'tdd')
    wrong=deepcopy(reply);wrong['value']['success']=False
    write([tool,wrong,done])
    with pytest.raises(ValidationError,match='differs'):native_complete(tmp_path,record,'tdd')


def test_output_review_cannot_be_substituted_with_a_stale_pin(tmp_path):
    from pathlib import Path
    from qualification.checkpoint_four import load_output_review
    from myskills.cohort_assessment import seal
    root=Path(__file__).parents[1]
    target=tmp_path/'qualification/checkpoint4';target.mkdir(parents=True)
    for name in ('output-review.json','output-review-pin.json'):
        (target/name).write_bytes((root/'qualification/checkpoint4'/name).read_bytes())
    value=json.loads((target/'output-review.json').read_text())
    value['cases'][-1]['verdict']='PASS'
    (target/'output-review.json').write_text(json.dumps(value))
    with pytest.raises(ValidationError,match='review file pin'):
        load_output_review(tmp_path,value['collector_commit'],seal({'runtime_identity':'STABLE'}))
