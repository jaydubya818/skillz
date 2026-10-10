"""Successor bounded runner adds cancellable dispatch; legacy runner stays frozen."""
import json, os, selectors, subprocess, time, uuid
from myskills.manifest import ValidationError
from qualification.local_probe import container_command, ContainmentError, MAX_OUTPUT, IMAGE

def run_program(program, inputs, *, timeout=10, cancel=None):
    """Candidate process emits data. Only the host oracle decides correctness."""
    if not isinstance(program, str) or len(program.encode()) > 32768:
        raise ValidationError('invalid or oversized program')
    payload = json.dumps({'program':program,'inputs':inputs}, allow_nan=False).encode()
    if len(payload) > 262144:
        raise ValidationError('oversized fixture input')
    name = 'myskills-qual-' + uuid.uuid4().hex
    process = subprocess.Popen(container_command(name), stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    streams = {'stdout':bytearray(), 'stderr':bytearray()}
    remaining = memoryview(payload)
    reason = None
    deadline = time.monotonic() + timeout
    try:
        with selectors.DefaultSelector() as selector:
            for pipe, event, label in ((process.stdin,selectors.EVENT_WRITE,'stdin'),
                (process.stdout,selectors.EVENT_READ,'stdout'),(process.stderr,selectors.EVENT_READ,'stderr')):
                os.set_blocking(pipe.fileno(), False)
                selector.register(pipe, event, label)
            while selector.get_map():
                if cancel is not None and cancel.is_set():
                    reason = 'CANCELLED'
                    break
                if time.monotonic() >= deadline:
                    reason = 'TIMEOUT'
                    break
                for key, _ in selector.select(min(0.1, max(0,deadline-time.monotonic()))):
                    if key.data == 'stdin':
                        try:
                            written = os.write(key.fd, remaining[:4096])
                            remaining = remaining[written:]
                        except BrokenPipeError:
                            remaining = memoryview(b'')
                        if not remaining:
                            selector.unregister(key.fileobj)
                            key.fileobj.close()
                    else:
                        data = os.read(key.fd, 4096)
                        if not data:
                            selector.unregister(key.fileobj)
                            key.fileobj.close()
                        else:
                            streams[key.data].extend(data)
                            if sum(map(len,streams.values())) > MAX_OUTPUT:
                                reason = 'OUTPUT_LIMIT'
                if reason:
                    break
        if reason:
            process.kill()
        process.wait(timeout=5)
    finally:
        try:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
        finally:
            try:
                for pipe in (process.stdin, process.stdout, process.stderr):
                    if not pipe.closed: pipe.close()
            finally:
                try:
                    subprocess.run(['docker','rm','-f',name], capture_output=True, timeout=10)
                    absent = subprocess.run(['docker','container','inspect',name], capture_output=True, timeout=10)
                    if absent.returncode != 1 or not any(s in absent.stderr for s in (b'No such container', b'No such object')):
                        raise ContainmentError('container removal not confirmed: ' + name)
                except (OSError, subprocess.TimeoutExpired) as error:
                    raise ContainmentError('container cleanup unavailable: ' + name) from error
    stdout = bytes(streams['stdout'][:MAX_OUTPUT]).decode(errors='replace')
    stderr = bytes(streams['stderr'][:MAX_OUTPUT]).decode(errors='replace')
    value = None
    if not reason and process.returncode == 0:
        try:
            value = json.loads(stdout)
        except (ValueError, RecursionError):
            reason = 'INVALID_OUTPUT'
    return {'exit_code':process.returncode,'failure':reason,'stdout':stdout,'stderr':stderr,
            'value':value,'container_removed':True,'image':IMAGE}
