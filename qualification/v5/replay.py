"""Checkpoint-5 custody validation; frozen v4 verifier remains unchanged."""
import base64
import json
from myskills.digest import digest_object
from qualification.checkpoint_four import require,unseal
from qualification.v4.adapter import Session,validate_output,codex_response,schemas
from qualification.v4.provider import validate_native_request
from qualification.runtime_identity import MODEL
from qualification.workflow_probe import normalized
from qualification.v5.policy import executor


def replay_entries(fixture,record,directory=None):
    identity=record['binding'];name=identity['task_class']['name']
    session=Session(name,fixture,executor(fixture['skill']))
    previous='GENESIS'
    for index,entry in enumerate(record['entries']):
        request=entry['request'];result=entry['result']
        validate_output(result,name,request['call_id'],digest_object(request))
        require(result['previous']==previous,'tool chain reordered')
        previous=result['evidence_digest']
        if directory is not None:
            completed=json.loads((directory/'journal'/f'{index}-completed.json').read_text());unseal(completed)
            require(completed['binding']==identity and completed['request']==request and completed['result']==result and completed['files']==entry['files'],'journal changed')
            dispatched=directory/'journal'/f'{index}-dispatched.json'
            if result['status']=='OK':require(dispatched.exists(),'missing pre-effect record')
            if dispatched.exists():
                before=json.loads(dispatched.read_text());unseal(before)
                require(before['binding']==identity and before['request']==request and before['files']==session.files,'pre-effect state changed')
        actual=session.call(request['call_id'],request['tool'],request['arguments'])
        stable=lambda v:normalized({k:w for k,w in v.items() if k not in ('previous','evidence_digest')})
        require(stable(actual)==stable(result) and session.files==entry['files'],'independent tool replay differs')
    require(session.files==record['files'] and session.finished==record['finished'] and session.artifact==record['artifact'],'final state differs')
    return session

def native_complete(directory,record,fixture):
    path=directory/'native.jsonl'
    if not path.exists():
        require(not record['entries'],'tools without native custody')
        return False
    native=[json.loads(line) for line in path.read_text().splitlines()]
    requests=[r for r in native if r['channel'] in ('tool','provider')]
    responses=[r for r in native if r['channel']=='host_response']
    by_id={r['id']:r['value'] for r in responses}
    require(len(by_id)==len(responses),'duplicate native response identity')
    require(len({r['id'] for r in requests})==len(requests),'duplicate native request identity')
    require(set(by_id).issubset({r['id'] for r in requests}),'orphan native response')
    complete=True;index=0;seen={};model_calls=set();provider_count=0
    for item in requests:
        if item['channel']!='provider':continue
        provider_count+=1;reply=by_id.get(item['id'])
        if reply is None or reply.get('status')!=200:complete=False;continue
        raw=base64.b64decode(reply['body'],validate=True).decode()
        stream=[json.loads(line[6:]) for line in raw.splitlines() if line.startswith('data: {')]
        finished=[e['response'] for e in stream if e.get('type')=='response.completed']
        if len(finished)!=1:complete=False;continue
        require(finished[0].get('model')==MODEL,'response model identity differs')
        complete=complete and finished[0].get('status')=='completed'
        for output in finished[0].get('output',[]):
            if output['type']=='function_call' and output.get('namespace')=='myskills':
                model_calls.add(digest_object({'call_id':output['call_id'],'tool':output['name'],
                                               'arguments':json.loads(output['arguments'])}))
    for item in requests:
        value=item['value'];reply=by_id.get(item['id'])
        if item['channel']=='provider':
            validate_native_request(value,schemas(fixture))
            complete=complete and reply is not None and reply.get('status')==200
            continue
        request={'call_id':value['callId'],'tool':value['tool'] if value.get('namespace')=='myskills' else 'unauthorized-native-tool',
                 'arguments':value['arguments'] if value.get('namespace')=='myskills' else {}}
        key=digest_object(request)
        if provider_count and key not in model_calls:complete=False
        if index<len(record['entries']) and record['entries'][index]['request']==request:
            entry=record['entries'][index];index+=1;seen[key]=entry['result']
        elif key in seen:entry={'result':seen[key]}
        else:
            require(reply is None,'unaccounted native tool response')
            complete=False;continue
        if reply is None:complete=False
        else:require(reply==codex_response(entry['result']),'native tool response differs from journal')
    require(index==len(record['entries']),'unaccounted journal effect')
    transport_path=directory/'transport.json'
    if not transport_path.exists():return False
    transport=json.loads(transport_path.read_text())
    require(transport['records']==native,'native transport transcript differs')
    turns=[r['value']['params']['turn']['status'] for r in native
           if r['channel']=='event' and r['value'].get('method')=='turn/completed']
    return provider_count>0 and complete and transport['cleanup_confirmed'] is True and transport['exit_code']==0 and transport['failure'] is None and turns==['completed']
