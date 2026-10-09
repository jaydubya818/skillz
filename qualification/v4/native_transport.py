"""Local native Codex transport; container stdio is the sole host channel."""
import base64
import json
import selectors
import subprocess
import time
import uuid
from pathlib import Path
from qualification.local_probe import ContainmentError
from qualification.v4.adapter import schemas,codex_response


def run_codex(image,model,policy,prompt,session,provider,timeout=600,journal=None):
    if not __import__('re').fullmatch(r'sha256:[0-9a-f]{64}',image):raise ValueError('immutable image required')
    name='myskills-native-'+uuid.uuid4().hex
    source=Path(__file__).with_name('codex_guest.py').read_text()
    cmd=['docker','run','--rm','--name',name,'--pull=never','--platform=linux/amd64','--network=none',
        '--read-only','--cap-drop=ALL','--security-opt=no-new-privileges','--user=65534:65534',
        '--cpus=1','--memory=768m','--memory-swap=768m','--pids-limit=96','--log-driver=none',
        '--tmpfs','/tmp:rw,noexec,nosuid,size=128m','--entrypoint=python3','-i',image,'-u','-c',source]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    tools=[{**s,'namespace':'myskills','deferLoading':False} for s in schemas(session.fixture)]
    data={'model':model,'policy':policy,'prompt':prompt,'tools':tools}
    records=[];stderr=bytearray();pending=bytearray();total=0;failure=None
    def retain(record):
        records.append(record)
        if journal is not None:
            with Path(journal).open('a') as stream:
                stream.write(json.dumps(record,sort_keys=True)+'\n');stream.flush();__import__('os').fsync(stream.fileno())
    try:
        proc.stdin.write((json.dumps(data)+'\n').encode());proc.stdin.flush()
        end=time.monotonic()+timeout
        with selectors.DefaultSelector() as selector:
            selector.register(proc.stdout,selectors.EVENT_READ,'out');selector.register(proc.stderr,selectors.EVENT_READ,'err')
            while selector.get_map():
                if session.cancelled.is_set():failure='CANCELLED';break
                if time.monotonic()>end:failure='TIMEOUT';break
                for key,_ in selector.select(.1):
                    chunk=__import__('os').read(key.fd,65536)
                    if not chunk:selector.unregister(key.fileobj);continue
                    total+=len(chunk)
                    if total>4_000_000:failure='OUTPUT_LIMIT';break
                    if key.data=='err':stderr.extend(chunk);continue
                    pending.extend(chunk)
                    while b'\n' in pending:
                        line,_,remaining=pending.partition(b'\n');pending=bytearray(remaining)
                        record=json.loads(line);retain(record)
                        if record['channel']=='provider':reply=provider(record['value'],tools,deadline=end,cancel=session.cancelled)
                        elif record['channel']=='tool':
                            value=record['value']
                            if value.get('namespace')!='myskills':
                                result=session.call(value.get('callId'),'unauthorized-native-tool',{})
                            else:result=session.call(value.get('callId'),value.get('tool'),value.get('arguments'))
                            reply=codex_response(result)
                        else:continue
                        retain({'channel':'host_response','id':record['id'],'value':reply})
                        proc.stdin.write((json.dumps({'id':record['id'],'value':reply})+'\n').encode());proc.stdin.flush()
                if failure:break
        if failure:session.cancel();proc.kill()
        proc.wait(timeout=5)
    finally:
        try:
            if proc.poll() is None:proc.kill();proc.wait(timeout=5)
        finally:
            try:
                for pipe in (proc.stdin,proc.stdout,proc.stderr):pipe.close()
            finally:
                try:
                    subprocess.run(['docker','rm','-f',name],capture_output=True,timeout=10)
                    removed=subprocess.run(['docker','container','inspect',name],capture_output=True,timeout=10)
                    if removed.returncode!=1 or not any(s in removed.stderr for s in (b'No such container',b'No such object')):
                        raise ContainmentError('native container cleanup unconfirmed: '+name)
                except (OSError,subprocess.TimeoutExpired) as error:
                    raise ContainmentError('native cleanup unavailable: '+name) from error
    return {'records':records,'stderr':stderr.decode(errors='replace'),'exit_code':proc.returncode,
            'failure':failure,'cleanup_confirmed':True,'image':image,'provider':'explicit caller only',
            'host_mounts':[],'network':'none'}


def denied_provider(request,tools,**limits):
    body=json.dumps({'error':{'message':'Qualification inspection only: provider dispatch unauthorized','type':'qualification_boundary'}}).encode()
    return {'status':403,'content_type':'application/json','body':base64.b64encode(body).decode()}
