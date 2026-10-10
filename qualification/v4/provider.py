"""Explicit local-only provider boundary. No provider discovery or paid fallback."""
import base64
import json
import http.client
from pathlib import Path
import socket
import threading
import time

from myskills.manifest import ValidationError
from qualification.runtime_identity import MODEL, MODEL_DIGEST, api


def wire_schema(value):
    result = {k: v for k, v in value.items() if k != 'maxLength'}
    if result.get('type') == 'object':
        result['properties'] = {k: wire_schema(v) for k, v in result.get('properties', {}).items()}
    return result


def validate_native_request(request, specs):
    """Pin Codex's observed schema codec; the host still enforces logical limits."""
    builtin = json.loads(Path(__file__).with_name('native-builtin.json').read_text())
    functions = [{'type': 'function', 'name': s['name'], 'description': s['description'],
                  'strict': False, 'parameters': wire_schema(s['inputSchema'])}
                 for s in sorted(specs, key=lambda s: s['name'])]
    expected = [builtin, {'type': 'namespace', 'name': 'myskills',
                         'description': 'Tools in the myskills namespace.', 'tools': functions}]
    if request.get('model') != MODEL or request.get('tools') != expected:
        raise ValidationError('unreviewed native model or advertised tool contract')
    if request.get('store') is not False or request.get('stream') is not True:
        raise ValidationError('native persistence/stream contract changed')
    # request_user_input is advertised by this binary but never granted. The
    # guest rejects every non-dynamic server RPC; network and shell are absent.


class LocalResponses:
    def __init__(self, guard):
        self.guard = guard
        self.calls = 0

    def __call__(self, request, specs, *, deadline, cancel):
        validate_native_request(request, specs)
        self.calls += 1
        if self.calls > 32:
            raise ValidationError('provider call limit')
        self.guard.check()
        result=[];done=threading.Event()
        connection=http.client.HTTPConnection('127.0.0.1',11434,timeout=90)
        def receive():
            try:
                if cancel.is_set() or time.monotonic()>=deadline:
                    raise TimeoutError('provider admission deadline')
                connection.request('POST','/v1/responses',body=json.dumps(request,allow_nan=False).encode(),
                                   headers={'Content-Type':'application/json'})
                response=connection.getresponse()
                result.append((response.status,response.getheader('Content-Type','application/json'),response.read(2_000_001)))
            except Exception as error:result.append(error)
            finally:connection.close();done.set()
        worker=threading.Thread(target=receive,daemon=True);worker.start()
        while not done.wait(.05):
            if cancel.is_set() or time.monotonic()>=deadline:
                # Disconnect is not proof that the daemon stopped inference.
                # Collector retains UNKNOWN, halts, and starts no further trial.
                if connection.sock is not None:
                    try:connection.sock.shutdown(socket.SHUT_RDWR)
                    except OSError:pass
                connection.close()
                raise TimeoutError('provider cancellation/deadline; inference outcome UNKNOWN')
        if isinstance(result[0],Exception):raise result[0]
        status,content_type,raw=result[0]
        if cancel.is_set() or time.monotonic()>=deadline:
            raise TimeoutError('provider completion past deadline; inference outcome UNKNOWN')
        self.guard.check()
        if len(raw) > 2_000_000:
            raise ValidationError('provider response limit')
        if status == 200:
            matching = [m for m in api('ps')['models']
                        if m.get('digest', '').removeprefix('sha256:') == MODEL_DIGEST]
            if len(matching) != 1:
                raise ValidationError('loaded native model identity changed')
        return {'status': status, 'content_type': content_type, 'body': base64.b64encode(raw).decode()}
