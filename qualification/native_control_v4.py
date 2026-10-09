"""Scripted native protocol regression; no model calls or behavioral credit."""
import argparse
import base64
import json
from pathlib import Path

from qualification.runtime_identity import MODEL
from qualification.v4.adapter import Session
from qualification.v4.cases import CASES, POLICY
from qualification.v4.native_transport import run_codex
from qualification.v4.probe import IMAGE
from qualification.v4.provider import validate_native_request


def control():
    count=0
    def provider(request,specs,**limits):
        nonlocal count
        validate_native_request(request,specs)
        count+=1
        if count<=3:
            item={'type':'function_call','id':'fc_'+str(count),'call_id':'read_'+str(count),
                  'namespace':'myskills','name':'read_file','arguments':json.dumps({'path':'clamp.py'})}
        else:
            item={'type':'message','id':'msg_done','role':'assistant','status':'completed',
                  'content':[{'type':'output_text','text':'Protocol control complete.','annotations':[]}]}
        response={'id':'resp_'+str(count),'object':'response','created_at':0,'model':MODEL,'output':[item],'status':'completed'}
        events=[{'type':'response.created','response':{**response,'status':'in_progress','output':[]}},
                {'type':'response.output_item.added','output_index':0,'item':item},
                {'type':'response.output_item.done','output_index':0,'item':item},
                {'type':'response.completed','response':response}]
        body=''.join('event: '+e['type']+'\ndata: '+json.dumps({**e,'sequence_number':i})+'\n\n' for i,e in enumerate(events)).encode()
        return {'status':200,'content_type':'text/event-stream','body':base64.b64encode(body).decode()}
    session=Session('native-request-id-regression',CASES['tdd'],lambda *a:None)
    result=run_codex(IMAGE,MODEL,POLICY,'Perform the scripted read-file control.',session,provider)
    assert count==4 and len(session.events)==3 and result['cleanup_confirmed'] and result['exit_code']==0,result
    turns=[r['value']['params']['turn']['status'] for r in result['records']
           if r['channel']=='event' and r['value'].get('method')=='turn/completed']
    assert turns==['completed'],turns
    return {**result,'adapter_events':session.events,'status':'PASS',
            'credit':'NATIVE_TRANSPORT_CONTROL_ONLY_NO_MODEL_INFERENCE'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    a.output.write_text(json.dumps(control(),sort_keys=True,indent=2)+'\n')
    print('PASS: native bidirectional RPC IDs 0, 1, 2; no model inference')
