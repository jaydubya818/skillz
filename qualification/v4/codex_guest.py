"""Pinned native app-server inside an offline container; stdio is its only bridge."""
import base64
import http.server
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import uuid

config=json.loads(sys.stdin.readline())
pending={};output_lock=threading.Lock();pending_lock=threading.Lock()


def emit(value):
    with output_lock:print(json.dumps(value),flush=True)


def exchange(channel,value):
    key=uuid.uuid4().hex;q=queue.Queue()
    with pending_lock:pending[key]=q
    emit({'channel':channel,'id':key,'value':value})
    try:return q.get(timeout=280)
    finally:
        with pending_lock:pending.pop(key,None)


def receive():
    for line in sys.stdin:
        value=json.loads(line)
        with pending_lock:q=pending.get(value['id'])
        if q:q.put(value['value'])


class Provider(http.server.BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_POST(self):
        size=int(self.headers.get('Content-Length','0'))
        if self.path!='/v1/responses' or not 0<size<=600000:
            self.send_error(400);return
        request=json.loads(self.rfile.read(size))
        value=exchange('provider',request)
        body=base64.b64decode(value['body'])
        self.send_response(value['status']);self.send_header('Content-Type',value['content_type'])
        self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)


threading.Thread(target=receive,daemon=True).start()
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Provider)
threading.Thread(target=server.serve_forever,daemon=True).start()
home=Path('/tmp/native-home');work=Path('/tmp/native-work');home.mkdir();work.mkdir();(home/'codex').mkdir()
env={'PATH':'/usr/bin:/bin','HOME':str(home),'CODEX_HOME':str(home/'codex'),'RUST_LOG':'error'}
options={'model_provider':'qualification','model_providers.qualification.name':'Qualification local bridge',
 'model_providers.qualification.base_url':f'http://127.0.0.1:{server.server_port}/v1',
 'model_providers.qualification.wire_api':'responses','model_providers.qualification.requires_openai_auth':False,
 'model_providers.qualification.supports_websockets':False,'model_providers.qualification.request_max_retries':0,
 'model_providers.qualification.stream_max_retries':0,'web_search':'disabled','project_doc_max_bytes':0,
 'features.shell_tool':False,'features.unified_exec':False,'features.multi_agent':False,
 'features.goals':False,
 'features.code_mode':False,'features.code_mode_host':False,'features.sleep_tool':False,
 'features.tool_suggest':False,'features.skill_mcp_dependency_install':False,'mcp_servers':{},
 'analytics.enabled':False,'feedback.enabled':False,'model_context_window':32768}
argv=['/opt/codex/vendor/x86_64-unknown-linux-musl/bin/codex','app-server','--listen','stdio://']
for key,value in options.items():
    rendered='{}' if isinstance(value,dict) else json.dumps(value)
    argv+=['-c',key+'='+rendered]
proc=subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env,cwd=work)
threading.Thread(target=lambda:emit({'channel':'stderr','value':proc.stderr.read(32768)}),daemon=True).start()
def send(value):proc.stdin.write(json.dumps(value)+'\n');proc.stdin.flush()
send({'id':1,'method':'initialize','params':{'clientInfo':{'name':'myskills_qualification','version':'4.0.1'},'capabilities':{'experimentalApi':True}}})
try:
    for line in proc.stdout:
        value=json.loads(line);emit({'channel':'event','value':value})
        if 'method' not in value and value.get('id')==1:
            if 'error' in value:break
            send({'method':'initialized','params':{}})
            send({'id':2,'method':'thread/start','params':{'model':config['model'],'modelProvider':'qualification',
                 'cwd':str(work),'approvalPolicy':'never','sandbox':'read-only','ephemeral':True,
                 'baseInstructions':config['policy'],'dynamicTools':config['tools'],
                 'experimentalRawEvents':True,'environments':[]}})
        elif 'method' not in value and value.get('id')==2:
            if 'error' in value:break
            thread=value['result']['thread']['id']
            send({'id':3,'method':'turn/start','params':{'threadId':thread,'input':[{'type':'text','text':config['prompt']} ]}})
        elif value.get('method')=='item/tool/call':
            result=exchange('tool',value['params']);send({'id':value['id'],'result':result})
        elif value.get('method')=='turn/completed':break
        elif 'id' in value and 'method' in value:
            send({'id':value['id'],'error':{'code':-32601,'message':'Unauthorized native server request'}})
finally:
    proc.terminate()
    try:proc.wait(timeout=3)
    except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=3)
    server.shutdown()
emit({'channel':'guest_complete','value':{'codex_exit':proc.returncode}})
