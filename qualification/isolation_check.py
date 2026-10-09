"""Exercise concrete confinement controls; not an OS sandbox security audit."""
import json
from qualification.local_probe import ContainmentError, IMAGE, run_program

PROGRAM = '''def solve(x):
 import os,pathlib,socket
 result={"uid":os.getuid(),"credential_present":any(os.environ.get(k) for k in ("GITHUB_TOKEN","OPENAI_API_KEY","AWS_SECRET_ACCESS_KEY"))}
 try:
  pathlib.Path("/outside").write_text("x")
  result["root_write"]="ALLOWED"
 except OSError as e: result["root_write"]=e.errno
 for label,address in (("egress",("1.1.1.1",443)),("host_model",("127.0.0.1",11434))):
  try:
   s=socket.create_connection(address,timeout=0.5); s.close(); result[label]="CONNECTED"
  except OSError as e: result[label]=e.errno
 result["owner_a_state"]=pathlib.Path("/tmp/owner-a-state").exists()
 if x=="owner-a": pathlib.Path("/tmp/owner-a-state").write_text("synthetic owner A")
 return result
'''


def verify_isolation():
    first = run_program(PROGRAM,['owner-a'])
    second = run_program(PROGRAM,['owner-b'])
    for value in (first,second):
        if value['failure'] or value['exit_code'] != 0 or not value['container_removed']:
            raise ContainmentError('isolation probe failed')
        actual = value['value'][0]
        if (actual['uid'] != 65534 or actual['credential_present'] or actual['root_write'] != 30 or
            actual['egress'] != 101 or actual['host_model'] != 111 or actual['owner_a_state']):
            raise ContainmentError('isolation expectation did not hold')
    forged = run_program('print("PASS")\nraise SystemExit(0)',[None])
    hanging = run_program('def solve(x):\n while True: pass',[None],timeout=2)
    flooding = run_program('def solve(x):\n while True: print("x"*4096)',[None])
    if forged['failure'] != 'INVALID_OUTPUT' or hanging['failure'] != 'TIMEOUT' or flooding['failure'] != 'OUTPUT_LIMIT':
        raise ContainmentError('host verifier accepted a forged or unbounded response')
    return {'status':'PASS','image':IMAGE,'owner_a':first,'owner_b':second,
            'forged_pass_rejected':True,'timeout_removed':hanging['container_removed'],
            'output_limit_removed':flooding['container_removed'],
            'scope':'Offline container fixture controls; kernel escape and syscall audit NOT_RUN.'}


if __name__=='__main__':
    print(json.dumps(verify_isolation(),indent=2,sort_keys=True))
