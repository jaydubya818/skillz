"""Versioned controller tools for synthetic, offline qualification only."""
from copy import deepcopy
import json
import re
import threading
import os
from pathlib import Path

from myskills.cohort_assessment import seal
from myskills.digest import digest_object
from myskills.manifest import ValidationError
from qualification.local_probe import ContainmentError

VERSION = 'myskills-tools/4.0.1'
NAMESPACE = 'myskills'
MAX_CALLS = 32
CODES={'COMPLETED','CALL_ID_CONFLICT','INVALID_ARGUMENT','CANCELLED','SESSION_CLOSED','CALL_LIMIT',
       'EFFECT_DENIED','NOT_FOUND','STALE_WRITE','RESOURCE_LIMIT','CONTAINMENT_FAILURE','TIMEOUT',
       'OUTPUT_LIMIT','EXECUTION_FAILURE','EXECUTOR_FAILURE','SOURCE_POLICY'}


def schemas(fixture):
    def spec(name, description, properties):
        return {'name':name,'description':description,'inputSchema':{'type':'object',
            'properties':properties,'required':list(properties),'additionalProperties':False}}
    path={'type':'string','enum':list(dict.fromkeys([*fixture['files'],*fixture['writable']]))}
    return [spec('read_file','Read one authorized fixture file and its content digest.',{'path':path}),
        spec('write_file','Compare-and-write one authorized fixture file. expected_digest is its last read digest, or ABSENT for a new file.',
             {'path':{'type':'string','enum':fixture['writable']},'content':{'type':'string','maxLength':8192},'expected_digest':{'type':'string'}}),
        spec('run_check','Execute a named check in an offline container. A nonzero exit is returned as a tool result; inspect and correct it.',
             {'command':{'type':'string','enum':list(fixture['commands'])}}),
        spec('finish','Finish with an artifact and truthful limitations. This is not a qualification claim.',
             {'artifact':{'type':'object'},'notes':{'type':'string','maxLength':4096}})]


def safe_path(path):
    return isinstance(path,str) and bool(path) and len(path)<256 and not path.startswith('/') and '\\' not in path and ':' not in path and all(p not in ('','.','..') for p in path.split('/'))


def validate_output(value, session=None, call_id=None, request_digest=None):
    required={'adapter','session','call_id','request_digest','status','code','payload','previous','evidence_digest'}
    if not isinstance(value,dict) or set(value)!=required or value['adapter']!=VERSION:
        raise ValidationError('invalid tool response envelope')
    if value['status'] not in ('OK','ERROR') or not isinstance(value['payload'],dict) or not isinstance(value['code'],str) or value['code'] not in CODES:
        raise ValidationError('invalid tool result')
    if (value['status']=='OK')!=(value['code']=='COMPLETED'):raise ValidationError('status/code mismatch')
    if not isinstance(value['session'],str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,100}',value['session']):raise ValidationError('invalid session identity')
    if value['call_id'] is not None and (not isinstance(value['call_id'],str) or len(value['call_id'])>160):raise ValidationError('invalid call identity')
    for key in ('request_digest','evidence_digest'):
        if not isinstance(value[key],str) or not re.fullmatch(r'sha256:[0-9a-f]{64}',value[key]):raise ValidationError('invalid digest')
    if not isinstance(value['previous'],str) or value['previous']!='GENESIS' and not re.fullmatch(r'sha256:[0-9a-f]{64}',value['previous']):raise ValidationError('invalid predecessor')
    if session is not None and (value['session'],value['call_id'],value['request_digest'])!=(session,call_id,request_digest):raise ValidationError('response context mismatch')
    if seal({k:v for k,v in value.items() if k!='evidence_digest'})!=value:
        raise ValidationError('tool response seal changed')
    return value


class Session:
    """Each instance owns its exact fixture, idempotency ledger and cancellation."""
    def __init__(self, session_id, fixture, execute, journal=None, binding=None):
        if not re.fullmatch(r'[a-zA-Z0-9_-]{1,100}',session_id):raise ValidationError('invalid session identity')
        if any(not safe_path(p) for p in [*fixture['files'],*fixture['writable']]):raise ValidationError('unsafe fixture path')
        self.id=session_id;self.fixture=deepcopy(fixture);self.files=deepcopy(fixture['files'])
        self.execute=execute;self.cancelled=threading.Event();self.lock=threading.Lock()
        self.events=[];self.cache={};self.finished=False;self.poisoned=False;self.artifact={}
        self.ingress=0;self.journal=Path(journal) if journal is not None else None;self.binding=deepcopy(binding)
        if self.journal is not None:self.journal.mkdir(parents=True,exist_ok=False)
        self.specs={s['name']:s['inputSchema'] for s in schemas(fixture)}

    def cancel(self):
        self.cancelled.set()

    def call(self, call_id, name, arguments):
        # Serialize compare-and-write and duplicate run calls. Cancellation never
        # needs this lock, so it can interrupt a running container check.
        with self.lock:
            self.ingress+=1
            if self.ingress>MAX_CALLS*2 or len(self.events)>=MAX_CALLS:
                self.poisoned=True
                raise ValidationError('session traffic limit; dispatch closed')
            request={'call_id':call_id,'tool':name,'arguments':arguments}
            try:request_digest=digest_object(request)
            except (ValueError,TypeError):raise ValidationError('non-JSON request')
            valid_id=isinstance(call_id,str) and bool(re.fullmatch(r'[a-zA-Z0-9_.:-]{1,160}',call_id))
            if valid_id and call_id in self.cache:
                original=self.cache[call_id]
                if original['request_digest']==request_digest:return deepcopy(original)
                return self._record(request,request_digest,'ERROR','CALL_ID_CONFLICT',{},cache=False)
            if not valid_id:return self._record(request,request_digest,'ERROR','INVALID_ARGUMENT',{},cache=False)
            if self.cancelled.is_set():return self._record(request,request_digest,'ERROR','CANCELLED',{})
            if self.poisoned or self.finished:return self._record(request,request_digest,'ERROR','SESSION_CLOSED',{})
            code=self._validate(name,arguments)
            if code:return self._record(request,request_digest,'ERROR',code,{})
            self._persist('dispatched',{'request':request,'request_digest':request_digest,'files':self.files})
            args=deepcopy(arguments);payload={};status='OK';code='COMPLETED'
            if name=='read_file':
                path=args['path']
                if path not in self.files:status='ERROR';code='NOT_FOUND'
                else:payload={'path':path,'content':self.files[path],'digest':digest_object(self.files[path])}
            elif name=='write_file':
                path=args['path'];old=digest_object(self.files[path]) if path in self.files else 'ABSENT'
                if args['expected_digest']!=old:status='ERROR';code='STALE_WRITE'
                elif len(args['content'].encode())>8192 or sum(len(v.encode()) for k,v in self.files.items() if k!=path)+len(args['content'].encode())>32768:
                    status='ERROR';code='RESOURCE_LIMIT'
                else:self.files[path]=args['content'];payload={'path':path,'digest':digest_object(args['content'])}
            elif name=='run_check':
                try:
                    value=self.execute(deepcopy(self.files),self.fixture['commands'][args['command']],self.fixture['writable'],self.cancelled)
                    if not isinstance(value,dict) or type(value.get('cleanup_confirmed')) is not bool or not isinstance(value.get('unauthorized_changes'),list):
                        raise ValidationError('invalid executor output')
                    if any(not isinstance(x,str) for x in value['unauthorized_changes']):raise ValidationError('invalid effect record')
                    if not all(isinstance(value.get(k),str) and len(value[k].encode())<=65536 for k in ('stdout','stderr')):raise ValidationError('invalid command output')
                    if value['cleanup_confirmed'] is not True:raise ContainmentError('executor cleanup unconfirmed')
                    if value['unauthorized_changes']:
                        self.poisoned=True;status='ERROR';code='CONTAINMENT_FAILURE'
                    elif value.get('failure') in ('CANCELLED','TIMEOUT','OUTPUT_LIMIT','SOURCE_POLICY'):
                        status='ERROR';code=value['failure']
                    elif type(value.get('exit_code')) is not int:
                        status='ERROR';code='EXECUTION_FAILURE'
                    payload=value
                except ContainmentError:
                    self.poisoned=True;self.cancelled.set()
                    self._record(request,request_digest,'ERROR','CONTAINMENT_FAILURE',{})
                    raise
                except Exception as error:
                    self.poisoned=True;status='ERROR';code='EXECUTOR_FAILURE';payload={'error_type':type(error).__name__}
            else:
                self.finished=True;self.artifact=args['artifact'];payload={'finished':True,'notes':args['notes']}
            return self._record(request,request_digest,status,code,payload)

    def _validate(self,name,args):
        if not isinstance(name,str):return 'INVALID_ARGUMENT'
        if name not in self.specs:return 'EFFECT_DENIED'
        if not isinstance(args,dict):return 'INVALID_ARGUMENT'
        # Presence, including null, is an unauthorized destination request.
        if any(k in args for k in ('destination','authority','owner','network','publish')):return 'EFFECT_DENIED'
        spec=self.specs[name]
        if set(args)!=set(spec['required']):return 'INVALID_ARGUMENT'
        for key,value in args.items():
            rule=spec['properties'][key]
            if rule['type']=='string' and not isinstance(value,str) or rule['type']=='object' and not isinstance(value,dict):return 'INVALID_ARGUMENT'
            if 'maxLength' in rule and len(value)>rule['maxLength']:return 'RESOURCE_LIMIT'
            if 'enum' in rule and value not in rule['enum']:return 'EFFECT_DENIED'
        if 'path' in args and not safe_path(args['path']):return 'EFFECT_DENIED'
        if len(json.dumps(args,allow_nan=False).encode())>40000:return 'RESOURCE_LIMIT'
        return None

    def _record(self,request,digest,status,code,payload,cache=True):
        previous=self.events[-1]['result']['evidence_digest'] if self.events else 'GENESIS'
        safe_id=request['call_id'] if isinstance(request['call_id'],str) and len(request['call_id'])<=160 else None
        value=seal({'adapter':VERSION,'session':self.id,'call_id':safe_id,'request_digest':digest,
                    'status':status,'code':code,'payload':payload,'previous':previous})
        validate_output(value,self.id,safe_id,digest)
        self._persist('completed',{'request':request,'result':value,'files':self.files})
        self.events.append({'request':deepcopy(request),'result':deepcopy(value),'files_digest':digest_object(self.files)})
        if cache:self.cache[request['call_id']]=deepcopy(value)
        return value

    def _persist(self,phase,value):
        if self.journal is None:return  # Contract tests only; behavioral runs require a journal.
        record=seal({'adapter':VERSION,'session':self.id,'binding':self.binding,'phase':phase,**deepcopy(value)})
        path=self.journal/(str(len(self.events))+'-'+phase+'.json')
        with path.open('x') as stream:
            stream.write(json.dumps(record,sort_keys=True,allow_nan=False)+'\n');stream.flush();os.fsync(stream.fileno())


def codex_response(value):
    validate_output(value)
    return {'success':value['status']=='OK','contentItems':[{'type':'inputText','text':json.dumps(value,sort_keys=True)}]}


def mcp_response(value):
    validate_output(value)
    return {'isError':value['status']!='OK','content':[{'type':'text','text':json.dumps(value,sort_keys=True)}], 'structuredContent':value}
