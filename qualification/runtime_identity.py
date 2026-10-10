"""Exact local-runtime observations for tests; no provider or production adapter."""
import argparse
from hashlib import file_digest as hash_file
import json
import os
from pathlib import Path
import platform
import subprocess
import urllib.request

from myskills.cohort_assessment import seal
from myskills.digest import digest_object
from myskills.manifest import ValidationError
from qualification.local_probe import IMAGE_REFERENCE, NoRedirect

MODEL_DIGEST = 'accad778b53702521a72c6c21e5e22d1a9bea0b4da33d8894a0779c1079ec173'
MODEL = 'sha256-' + MODEL_DIGEST
RUNTIME_VERSION = '0.40.2'
ENDPOINT = 'http://127.0.0.1:11434/api/'
STORE = Path('/Users/jaywest/.ollama/models/blobs')
BINARIES = Path('/Applications/Ollama.app/Contents/Resources')
PIN = Path('qualification/checkpoint2/runtime-pin.json')


def require_same(expected, actual):
    if expected != actual:
        raise ValidationError('runtime identity changed; no dispatch or qualification credit')


def bind_result(*, runtime, harness, skill, fixture, evaluation, output):
    return seal({'schema':'myskills.behavior-result-identity.v2',
        'runtime_digest':digest_object(runtime), 'harness_digest':digest_object(harness),
        'skill':skill, 'fixture_digest':digest_object(fixture),
        'evaluation_digest':digest_object(evaluation), 'output_digest':digest_object(output)})


def api(path, body=None):
    if path not in ('version','show','ps','chat'):
        raise ValidationError('endpoint denied')
    if path in ('show','chat') and (not isinstance(body,dict) or body.get('model') != MODEL):
        raise ValidationError('only the complete pinned local manifest digest is allowed')
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    data=None if body is None else json.dumps(body).encode()
    request=urllib.request.Request(ENDPOINT+path,data=data,headers={'Content-Type':'application/json'})
    with opener.open(request,timeout=240) as response:
        raw=response.read(2_000_001)
    if len(raw)>2_000_000:
        raise ValidationError('model response exceeded bound')
    return json.loads(raw)


def command(args):
    try:
        return subprocess.run(args,check=True,capture_output=True,text=True,timeout=15).stdout.strip()
    except subprocess.SubprocessError as error:
        raise ValidationError('runtime identity command failed: '+args[0]) from error


def hashed(path):
    before=path.stat()
    with path.open('rb') as stream:
        digest='sha256:'+hash_file(stream,'sha256').hexdigest()
    require_same((before.st_size,before.st_mtime_ns,before.st_ino),stamp(path))
    return {'digest':digest,'bytes':before.st_size}


def stamp(path):
    info=path.stat()
    return info.st_size,info.st_mtime_ns,info.st_ino


def artifact_paths():
    manifest_path=STORE/MODEL
    require_same('sha256:'+MODEL_DIGEST,hashed(manifest_path)['digest'])
    manifest=json.loads(manifest_path.read_bytes())
    require_same('llamacpp',manifest.get('runner'))
    paths={MODEL:manifest_path}
    for entry in [manifest['config'],*manifest['layers']]:
        digest=entry['digest']
        if not __import__('re').fullmatch(r'sha256:[0-9a-f]{64}',digest):
            raise ValidationError('invalid model blob digest')
        paths[digest.replace(':','-')]=STORE/digest.replace(':','-')
    return paths


def binary_paths():
    return {p.name:p for p in BINARIES.iterdir() if p.is_file() and
            (p.name in ('ollama','llama-server') or p.suffix in ('.dylib','.so'))}


def environment():
    # Pin only runtime-routing controls, not arbitrary host values or credentials.
    controls={k:os.environ[k] for k in sorted(os.environ)
              if k.startswith(('OLLAMA_','LLAMA_','DYLD_')) or
              k.upper() in ('HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','NO_PROXY')}
    if controls:
        raise ValidationError('qualification launcher requires no routing/runtime overrides')
    return {'system':platform.system(),'release':platform.release(),'machine':platform.machine(),
        'python':platform.python_version(),'runtime_overrides':{},
        'hardware':command(['/usr/sbin/sysctl','hw.model','hw.memsize','hw.ncpu']),
        'docker':json.loads(command(['docker','version','--format','{{json .Server}}'])),
        'image':json.loads(command(['docker','image','inspect',IMAGE_REFERENCE]))[0]['Id'],
        'image_reference':IMAGE_REFERENCE,'candidate_network':'none','candidate_host_mounts':[]}


def service():
    require_same(RUNTIME_VERSION,api('version')['version'])
    listeners=[line for line in command(['lsof','-nP','-iTCP:11434','-sTCP:LISTEN','-Fp']).splitlines()
               if line.startswith('p')]
    if len(listeners)!=1 or not listeners[0][1:].isdigit():
        raise ValidationError('ambiguous local provider listener')
    pid=listeners[0][1:]
    process=command(['ps','-p',pid,'-o','lstart=,command='])
    if not process.endswith(str(BINARIES/'ollama')+' serve'):
        raise ValidationError('unexpected local provider process')
    shown=api('show',{'model':MODEL})
    require_same('Q8_0',shown['details']['quantization_level'])
    require_same('llamacpp',shown['details']['runner'])
    return {'endpoint':ENDPOINT,'version':RUNTIME_VERSION,'pid':pid,'process':process,
        'show_digest':digest_object(shown),'details':shown['details'],
        'routing':'literal loopback, proxies disabled, redirects denied, full local blob reference',
        'daemon_environment_attestation':'NOT_ESTABLISHED; startup log inspected, host/service trusted'}


def snapshot():
    blobs={name:hashed(path) for name,path in artifact_paths().items()}
    for name,value in blobs.items():
        require_same(name.replace('-',':',1),value['digest'])
    return {'schema':'myskills.local-runtime-identity.v2','model':MODEL,
        'model_digest':'sha256:'+MODEL_DIGEST,'model_blobs':blobs,
        'runtime_binaries':{name:hashed(path) for name,path in binary_paths().items()},
        'service':service(),'environment':environment(),
        'trust_boundary':'Observed local service, not cryptographic model attestation or hostile-host protection'}


class RuntimeGuard:
    """Hash all bytes at admission and completion; check file identity around each request."""
    def __init__(self, pin):
        self.pin=pin
        require_same(pin,snapshot())
        self.paths={**{'blob/'+k:v for k,v in artifact_paths().items()},
                    **{'runtime/'+k:v for k,v in binary_paths().items()}}
        self.stamps={k:stamp(p) for k,p in self.paths.items()}
        self.halted=False

    def check(self):
        if self.halted:
            raise ValidationError('runtime guard halted')
        require_same(self.pin['service'],service())
        require_same(self.pin['environment'],environment())
        require_same(self.stamps,{k:stamp(p) for k,p in self.paths.items()})

    def generate(self, request, retain_response):
        try:
            self.check()
            response=api('chat',request)
            retain_response(response)
            self.check()
            loaded=api('ps')['models']
            matching=[m for m in loaded if m.get('digest','').removeprefix('sha256:')==MODEL_DIGEST]
            if len(matching)!=1:
                raise ValidationError('loaded model differs from the runnable manifest pin')
            if response.get('model') not in (MODEL,MODEL+':latest'):
                raise ValidationError('response model differs from request')
            return response,matching[0]
        except Exception:
            self.halted=True
            raise

    def finish(self):
        try:
            self.check()
            require_same(self.pin,snapshot())
        except Exception:
            self.halted=True
            raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture',required=True,type=Path)
    args=parser.parse_args()
    value=snapshot()
    with args.capture.open('x') as destination:
        destination.write(json.dumps(value,sort_keys=True,indent=2)+'\n')
    print(digest_object(value))
