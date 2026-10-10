"""Deterministic missing-row race oracle, separate from candidate claims."""
RACE = r'''
import json, pathlib, sqlite3, subprocess, sys, tempfile
with tempfile.TemporaryDirectory() as d:
 db=str(pathlib.Path(d)/'race.db')
 with sqlite3.connect(db) as c:
  c.execute('CREATE TABLE notes(owner TEXT,key TEXT,text TEXT,PRIMARY KEY(owner,key))')
 driver=r"""
import json, pathlib, sqlite3, sys, time
db,barrier,identity=sys.argv[1:]
real_connect=sqlite3.connect
class Cursor(sqlite3.Cursor):
 def fetchone(self):
  result=super().fetchone()
  if result is None and not self.connection.in_transaction:
   pathlib.Path(barrier,identity).touch()
   deadline=time.monotonic()+2
   while len(list(pathlib.Path(barrier).glob('ready-*')))<2:
    if time.monotonic()>deadline:raise RuntimeError('race barrier incomplete')
    time.sleep(.01)
  return result
class Connection(sqlite3.Connection):
 def execute(self,*a,**kw):return self.cursor(factory=Cursor).execute(*a,**kw)
 def cursor(self,*a,**kw):
  kw.setdefault('factory',Cursor)
  return super().cursor(*a,**kw)
def connect(*a,**kw):
 kw['factory']=Connection
 return real_connect(*a,**kw)
sqlite3.connect=connect
from api import handle
print(json.dumps(handle('owner-race',{'key':'race','text':'one'},db)))
"""
 children=[subprocess.Popen([sys.executable,'-c',driver,db,d,'ready-'+str(i)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for i in range(2)]
 results=[]
 for child in children:
  out,err=child.communicate(timeout=5)
  assert child.returncode==0,err
  results.append(json.loads(out))
 assert sorted(x['status'] for x in results)==[200,201],results
 assert all(x['text']=='one' for x in results),results
 with sqlite3.connect(db) as c:
  assert c.execute('SELECT owner,key,text FROM notes').fetchall()==[('owner-race','race','one')]
 print(json.dumps({'concurrent_replay':True,'durable_rows':1}))
'''
