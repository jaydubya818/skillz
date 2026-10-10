"""Real SQLite contention with an existing reader, without injected SQL errors."""

LOCK_PROBE = r'''
import json,pathlib,sqlite3,subprocess,sys,tempfile,time
worker=r"""
import json,pathlib,sqlite3,sys
real_connect=sqlite3.connect
statements=[]
def connect(*args,**kwargs):
 c=real_connect(*args,**kwargs)
 def trace(statement):
  statements.append(statement)
  upper=statement.strip().upper()
  if upper.startswith(('PRAGMA JOURNAL_MODE=', 'BEGIN', 'INSERT')):
   pathlib.Path(sys.argv[2]).touch()
 c.set_trace_callback(trace)
 return c
sqlite3.connect=connect
from api import handle
try:
 value={'response':handle('a',{'key':'k','text':'one'},sys.argv[1]),'error':None}
except Exception as error:
 value={'response':None,'error':{'class':type(error).__name__,'message':str(error),'sqlite_errorname':getattr(error,'sqlite_errorname',None)}}
value['statements']=statements
print(json.dumps(value))
"""
def locked_reader_case(mode):
 with tempfile.TemporaryDirectory() as temporary:
  directory=pathlib.Path(temporary);db=str(directory/'state.db');marker=directory/'entered-sql'
  with sqlite3.connect(db) as seed:
   assert seed.execute('PRAGMA journal_mode='+mode).fetchone()[0]==mode.lower()
   seed.execute('CREATE TABLE notes(owner TEXT,key TEXT,text TEXT,PRIMARY KEY(owner,key))')
   seed.execute('INSERT INTO notes VALUES(?,?,?)',('legacy','keep','old'))
  reader=sqlite3.connect(db)
  child=None
  try:
   reader.execute('BEGIN');assert reader.execute('SELECT * FROM notes').fetchall()==[('legacy','keep','old')]
   child=subprocess.Popen([sys.executable,'-c',worker,db,str(marker)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
   deadline=time.monotonic()+3
   while not marker.exists():
    if child.poll() is not None or time.monotonic()>deadline:raise RuntimeError('candidate did not reach controlled SQL boundary')
    time.sleep(.005)
   # A real reader remains open across the candidate SQL operation. No SQL
   # exception, result, timeout or dependency failure is injected by this probe.
   time.sleep(.15)
   reader.rollback()
   stdout,stderr=child.communicate(timeout=3)
   assert child.returncode==0 and not stderr,(child.returncode,stderr)
   observed=json.loads(stdout)
  finally:
   reader.close()
   if child is not None and child.poll() is None:
    child.kill();child.communicate()
  with sqlite3.connect(db) as verify:
   rows=verify.execute('SELECT owner,key,text FROM notes ORDER BY owner,key').fetchall()
   final_mode=verify.execute('PRAGMA journal_mode').fetchone()[0]
  return {'mode':mode,'reader_present_at_sql':True,'outcome':observed,'rows':rows,'final_mode':final_mode}
'''

REPRODUCTION = LOCK_PROBE + "\nprint(json.dumps({'cases':[locked_reader_case('DELETE') for _ in range(2)]},sort_keys=True))\n"

RACE_PROBE = r'''
import json,pathlib,sqlite3,subprocess,sys,tempfile
worker=r"""
import json,pathlib,sqlite3,sys,time
real_connect=sqlite3.connect
statements=[];entered=False
def connect(*args,**kwargs):
 c=real_connect(*args,**kwargs)
 def trace(statement):
  global entered
  statements.append(statement)
  upper=statement.strip().upper()
  if not entered and upper.startswith(('PRAGMA JOURNAL_MODE=', 'BEGIN', 'INSERT')):
   entered=True
   pathlib.Path(sys.argv[2],sys.argv[3]).touch()
   deadline=time.monotonic()+2
   while len(list(pathlib.Path(sys.argv[2]).glob('ready-*')))!=2:
    if time.monotonic()>deadline:break
    time.sleep(.005)
 c.set_trace_callback(trace)
 return c
sqlite3.connect=connect
from api import handle
try:
 value={'response':handle('a',{'key':'k','text':sys.argv[4]},sys.argv[1]),'error':None}
except Exception as error:
 value={'response':None,'error':{'class':type(error).__name__,'message':str(error),'sqlite_errorname':getattr(error,'sqlite_errorname',None)}}
value['statements']=statements
print(json.dumps(value))
"""
def paired_case(texts):
 with tempfile.TemporaryDirectory() as temporary:
  path=pathlib.Path(temporary);db=str(path/'state.db')
  with sqlite3.connect(db) as seed:
   seed.execute('CREATE TABLE notes(owner TEXT,key TEXT,text TEXT,PRIMARY KEY(owner,key))')
  processes=[]
  try:
   for i,text in enumerate(texts):
    processes.append(subprocess.Popen([sys.executable,'-c',worker,db,temporary,'ready-'+str(i),text],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True))
   results=[]
   for child in processes:
    stdout,stderr=child.communicate(timeout=4)
    assert child.returncode==0 and not stderr,(child.returncode,stderr)
    results.append(json.loads(stdout))
  finally:
   for child in processes:
    if child.poll() is None:child.kill();child.communicate()
  with sqlite3.connect(db) as verify:rows=verify.execute('SELECT owner,key,text FROM notes').fetchall()
  return {'participants':len(list(path.glob('ready-*'))),'texts':texts,'outcomes':results,'rows':rows}
'''
PAIRED_REPRODUCTION = RACE_PROBE + "\nprint(json.dumps({'cases':[paired_case(['one','two']) for _ in range(2)]},sort_keys=True))\n"

PLAIN_WORKER = r'''
import json,pathlib,sys,time
from api import handle
pathlib.Path(sys.argv[2],sys.argv[3]).touch()
deadline=time.monotonic()+2
while len(list(pathlib.Path(sys.argv[2]).glob('ready-*')))!=2:
 if time.monotonic()>deadline:raise RuntimeError('pair start barrier incomplete')
 time.sleep(.001)
try:
 value={'response':handle('a',{'key':'k','text':sys.argv[4]},sys.argv[1]),'error':None}
except Exception as error:
 value={'response':None,'error':{'class':type(error).__name__,'message':str(error),'sqlite_errorname':getattr(error,'sqlite_errorname',None)}}
print(json.dumps(value))
'''
BOUNDED_REPRODUCTION = RACE_PROBE + '\nworker='+repr(PLAIN_WORKER)+"\nprint(json.dumps({'cases':[paired_case(['one','two']) for _ in range(24)]},sort_keys=True))\n"
