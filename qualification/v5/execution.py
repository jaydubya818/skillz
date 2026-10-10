"""Capture command effects, including candidate self-modification and descendants."""
from qualification.v4.runner import run_program


def execute(files,argv,writable,cancel=None):
    # writable authorizes controller writes only. Executed candidate code cannot
    # rewrite even its own source or test files to forge a green result.
    program='FILES='+repr(files)+'\nARGV='+repr(argv)+'\n'+r'''import json,os,pathlib,subprocess,tempfile
def solve(x):
 with tempfile.TemporaryDirectory() as d:
  for name,content in FILES.items():
   p=pathlib.Path(d)/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content)
  outside_before={str(p) for p in pathlib.Path('/tmp').rglob('*') if not str(p).startswith(d+'/') and str(p)!=d}
  pids_before={p.name for p in pathlib.Path('/proc').iterdir() if p.name.isdigit()}
  r=subprocess.run(ARGV,cwd=d,capture_output=True,text=True,timeout=15,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
  pids_after={p.name for p in pathlib.Path('/proc').iterdir() if p.name.isdigit()}
  outside_after={str(p) for p in pathlib.Path('/tmp').rglob('*') if not str(p).startswith(d+'/') and str(p)!=d}
  changes=['outside-workspace:'+p for p in sorted(outside_after-outside_before)]
  if pids_after-pids_before:changes.append('background-process-remains')
  for path in pathlib.Path(d).rglob('*'):
   name=str(path.relative_to(d))
   if path.is_symlink():changes.append(name+':symlink');continue
   if not path.is_file():continue
   if name not in FILES:changes.append(name+':created')
   elif path.read_bytes()!=FILES[name].encode():changes.append(name+':modified-during-execution')
  for name in FILES:
   if not (pathlib.Path(d)/name).is_file():changes.append(name+':removed')
  return {'exit_code':r.returncode,'stdout':r.stdout[:32768],'stderr':r.stderr[:32768],
          'unauthorized_changes':changes,'evidence':None}
'''
    outer=run_program(program,[None],timeout=25,cancel=cancel)
    if outer['exit_code']!=0 or outer['failure'] or not isinstance(outer['value'],list) or len(outer['value'])!=1:
        return {'exit_code':None,'stdout':'','stderr':'container command incomplete','evidence':None,'unauthorized_changes':[],
                'cleanup_confirmed':outer['container_removed'],'failure':outer['failure'],'outer':outer}
    return {**outer['value'][0],'cleanup_confirmed':outer['container_removed']}
