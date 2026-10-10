"""Protected executable evidence for exact offline boundaries."""
from qualification.v6.probes import API as PRIOR_API, SECURITY as PRIOR_SECURITY

API = PRIOR_API.replace('print(json.dumps(observed,sort_keys=True))', '').replace(
    "observed['journal_mode']=", "observed['primary_key']=[row[5] for row in c.execute('PRAGMA table_info(notes)')]\n  observed['journal_mode']=") + r'''
def dispatch(payload,db):
 driver='import json,sys;from gateway import dispatch;p=json.load(sys.stdin);print(json.dumps(dispatch(p["payload"],p["db"])))'
 r=subprocess.run([sys.executable,'-c',driver],input=json.dumps({'payload':payload,'db':db}),capture_output=True,text=True,timeout=3)
 assert r.returncode==0,r.stderr
 return json.loads(r.stdout)
facts={}
facts['api.contract']=observed['contract_responses']==[{'status':201,'text':'one'},{'status':200,'text':'one'},{'status':409,'text':None}]
facts['api.schema']=observed['schema_columns']==['owner','key','text'] and observed['schema_not_null']==[0,0,0] and observed['primary_key']==[1,2,0]
facts['api.errors']=observed['malformed_errors']
facts['api.authorization']=observed['authorization']
facts['api.idempotency']=observed['idempotency']
# Real separate-process contention with different payloads. The losing response
# must be a conflict and persisted text must equal the winning response.
with tempfile.TemporaryDirectory() as d:
 db=str(pathlib.Path(d)/'race.db')
 with sqlite3.connect(db) as c:
  c.execute('CREATE TABLE notes(owner TEXT,key TEXT,text TEXT,PRIMARY KEY(owner,key))')
 worker=r"""
import json,pathlib,sys,time
from api import handle
db,barrier,identity,text=sys.argv[1:]
pathlib.Path(barrier,identity).touch()
deadline=time.monotonic()+2
while len(list(pathlib.Path(barrier).glob('ready-*')))<2:
 if time.monotonic()>deadline:raise RuntimeError('incomplete barrier')
 time.sleep(.01)
print(json.dumps(handle('a',{'key':'k','text':text},db)))
"""
 procs=[subprocess.Popen([sys.executable,'-c',worker,db,d,'ready-'+str(i),text],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for i,text in enumerate(['first','second'])]
 results=[]
 for p in procs:
  out,err=p.communicate(timeout=4);assert p.returncode==0,err;results.append(json.loads(out))
 with sqlite3.connect(db) as c: rows=c.execute('SELECT owner,key,text FROM notes').fetchall()
 winning=[v for v in results if v.get('status')==201]
 conflict=sorted(v['status'] for v in results)==[201,409] and len(winning)==1 and rows==[('a','k',winning[0]['text'])]
 facts['api.concurrency']=conflict and observed['concurrency_identical']=={'statuses':[200,201],'durable_rows':1,'start_barrier_participants':2}
with tempfile.TemporaryDirectory() as d:
 db=str(pathlib.Path(d)/'auth.db')
 denied={'status':401,'text':None}
 facts['api.authentication']=all(dispatch({'token':token,'body':{'key':'k','text':'one'}},db)==denied for token in [None,'',False,0,[],{},'invalid'])
 first=dispatch({'token':'fixture-a','body':{'key':'k','text':'one','owner':'b'},'trusted_owner':'b'},db)
 second=dispatch({'token':'fixture-b','body':{'key':'k','text':'two'}},db)
 with sqlite3.connect(db) as c: rows=c.execute('SELECT owner,key,text FROM notes ORDER BY owner').fetchall()
 facts['api.authentication']=facts['api.authentication'] and first=={'status':201,'text':'one'} and second=={'status':201,'text':'two'} and rows==[('a','k','one'),('b','k','two')]
legacy=subprocess.run([sys.executable,'legacy.py'],capture_output=True,text=True,timeout=8)
facts['api.compatibility']=legacy.returncode==0 and observed['backward_existing_schema']
facts['api.coverage']=all(facts.values())
print(json.dumps({'suite':'api-and-interface-design','facts':facts},sort_keys=True))
assert all(facts.values()),facts
'''
# v6's intermediate race banner is independently checked there; v7 emits one
# typed result packet. Neither candidate modules nor their stdout mint facts.
API = API.replace("print(json.dumps({'concurrent_replay':True,'durable_rows':1}))", 'pass')

SECURITY = PRIOR_SECURITY.replace('print(json.dumps(observed,sort_keys=True))','') + r'''
import pathlib
def dispatch(payload):
 driver='import json,sys;from gateway import dispatch;print(json.dumps(dispatch(json.load(sys.stdin))))'
 r=subprocess.run([sys.executable,'-c',driver],input=json.dumps(payload),capture_output=True,text=True,timeout=3)
 assert r.returncode==0,r.stderr
 return json.loads(r.stdout)
facts={}
facts['security.threats']=observed['cross_owner']
facts['security.surface']=pathlib.Path('app.py').read_text()=='import json,sys\nfrom security import authorize\nprint(json.dumps(authorize(json.load(sys.stdin))))\n'
facts['security.controls']=observed['top_level_destination']
facts['security.enforcement']=observed['cross_owner'] and observed['top_level_destination']
facts['security.resources']=observed['malformed_resources'] and observed['present_null_data']
facts['security.isolation']=observed['cross_owner']
facts['security.effects']=observed['top_level_destination']
denied={'status':403,'data':None}
base={'resource':{'owner':'a','data':'OWN_SENTINEL'}}
facts['security.credentials']=all(dispatch({**base,'token':token,'trusted_owner':'a'})==denied for token in [None,'',False,0,[],{},'invalid'])
facts['security.credentials']=facts['security.credentials'] and dispatch({**base,'token':'fixture-a','trusted_owner':'b','body_owner':'b'})=={'status':200,'data':'OWN_SENTINEL'}
facts['security.credentials']=facts['security.credentials'] and dispatch({**base,'token':'fixture-b','trusted_owner':'a'})==denied
for resource in [None,[],False,0,'',{}, {'owner':'a'},{'owner':True,'data':'x'},{'owner':1,'data':'x'},{'owner':'','data':'x'}]:
 facts['security.resources']=facts['security.resources'] and dispatch({'token':'fixture-a','resource':resource})==denied
for value in [None,False,0,'',[],{},'http://169.254.169.254','http://[::1]','https://example.invalid']:
 facts['security.effects']=facts['security.effects'] and dispatch({**base,'token':'fixture-a','destination':value})==denied
# Nested data is returned only to its owner; it is never used as an egress target.
nested={'owner':'a','data':{'destination':'https://example.invalid'}}
facts['security.effects']=facts['security.effects'] and dispatch({'token':'fixture-a','resource':nested})=={'status':200,'data':nested['data']}
legacy=subprocess.run([sys.executable,'legacy.py'],capture_output=True,text=True,timeout=8)
facts['security.negatives']=legacy.returncode==0 and all(facts.values())
print(json.dumps({'suite':'security-and-hardening','facts':facts},sort_keys=True))
assert all(facts.values()),facts
'''
