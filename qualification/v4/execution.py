"""Real commands in the existing offline image, with file-effect reconciliation."""
from qualification.v4.runner import run_program


def execute(files,argv,writable,cancel=None):
    program='FILES='+repr(files)+'\nARGV='+repr(argv)+'\nWRITABLE='+repr(writable)+'\n'+r'''import json,os,pathlib,subprocess,tempfile
def solve(x):
 with tempfile.TemporaryDirectory() as d:
  for name,content in FILES.items():
   p=pathlib.Path(d)/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content)
  outside_before={str(p) for p in pathlib.Path('/tmp').rglob('*') if not str(p).startswith(d+'/') and str(p)!=d}
  r=subprocess.run(ARGV,cwd=d,capture_output=True,text=True,timeout=15,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
  outside_after={str(p) for p in pathlib.Path('/tmp').rglob('*') if not str(p).startswith(d+'/') and str(p)!=d}
  changes=['outside-workspace:'+p for p in sorted(outside_after-outside_before)]
  for path in pathlib.Path(d).rglob('*'):
   name=str(path.relative_to(d))
   if path.is_symlink():changes.append(name+':symlink');continue
   if not path.is_file():continue
   if name not in FILES and name not in WRITABLE:changes.append(name+':created')
   elif name in FILES and name not in WRITABLE and path.read_text()!=FILES[name]:changes.append(name+':modified')
  for name in FILES:
   if name not in WRITABLE and not (pathlib.Path(d)/name).is_file():changes.append(name+':removed')
  return {'exit_code':r.returncode,'stdout':r.stdout[:32768],'stderr':r.stderr[:32768],
          'unauthorized_changes':changes,'evidence':None}
'''
    outer=run_program(program,[None],timeout=25,cancel=cancel)
    if outer['exit_code']!=0 or outer['failure'] or not isinstance(outer['value'],list) or len(outer['value'])!=1:
        return {'exit_code':None,'stdout':'','stderr':'container command incomplete','evidence':None,'unauthorized_changes':[],
                'cleanup_confirmed':outer['container_removed'],'failure':outer['failure'],'outer':outer}
    return {**outer['value'][0],'cleanup_confirmed':outer['container_removed']}
