"""Controller-owned executable facts about retained API/security candidates."""
import json
from myskills.cohort_assessment import seal
from qualification.v4.api_race import RACE
from qualification.v5.evaluate import clean
from qualification.v5.policy import executor
from qualification.workflow_probe import normalized
from qualification.v6.claims import text_digest
from qualification.local_probe import container_command

# Versioned supplemental race: both workers must reach a start barrier. The
# retained conditional missing-row barrier still tests SELECT-before-INSERT.
START_BARRIER = '''from api import handle
pathlib.Path(barrier,'start-'+identity).touch()
deadline=time.monotonic()+2
while len(list(pathlib.Path(barrier).glob('start-ready-*')))<2:
 if time.monotonic()>deadline:raise RuntimeError('start barrier incomplete')
 time.sleep(.01)
'''
RACE_V6 = RACE.replace('from api import handle\n', START_BARRIER).replace(
    " print(json.dumps({'concurrent_replay':True,'durable_rows':1}))",
    " observed['race_start_barrier']=len(list(pathlib.Path(d).glob('start-ready-*')))\n print(json.dumps({'concurrent_replay':True,'durable_rows':1}))")
API = r'''
import json,pathlib,sqlite3,subprocess,sys,tempfile
observed={}
with tempfile.TemporaryDirectory() as d:
 db=str(pathlib.Path(d)/'state.db')
 driver=r"""
import json,sys,sqlite3
p=json.load(sys.stdin); statements=[]; real_connect=sqlite3.connect
def connect(*a,**kw):
 c=real_connect(*a,**kw);c.set_trace_callback(statements.append);return c
sqlite3.connect=connect
from api import handle
value=handle(p['owner'],p['body'],p['db'])
print(json.dumps({'response':value,'statements':statements}))
"""
 def call(owner,body):
  r=subprocess.run([sys.executable,'-c',driver],input=json.dumps({'owner':owner,'body':body,'db':db}),capture_output=True,text=True,timeout=3)
  assert r.returncode==0,r.stderr
  return json.loads(r.stdout)
 with sqlite3.connect(db) as c:
  c.execute('CREATE TABLE notes(owner TEXT,key TEXT,text TEXT,PRIMARY KEY(owner,key))')
  c.execute('INSERT INTO notes VALUES(?,?,?)',('legacy','keep','old'))
 first=call('a',{'key':'k','text':'one'})
 replay=call('a',{'key':'k','text':'one'})
 conflict=call('a',{'key':'k','text':'changed'})
 foreign=call('b',{'owner':'a','key':'k','text':'two'})
 observed['contract_responses']=[v['response'] for v in [first,replay,conflict]]
 observed['idempotency']=replay['response']=={'status':200,'text':'one'} and conflict['response']=={'status':409,'text':None}
 bad=[None,[],False,{}, {'key':'','text':'x'},{'key':'k2','text':None},{'key':5,'text':'x'},{'key':'k2','text':''},{'key':'k2','text':3}]
 observed['malformed_errors']=all(call('a',v)['response']=={'status':400,'text':None} for v in bad)
 observed['begin_immediate']=any(sql.strip().upper().startswith('BEGIN IMMEDIATE') for sql in first['statements'])
 observed['executed_sql']=first['statements']
 with sqlite3.connect(db) as c:
  rows=c.execute('SELECT owner,key,text FROM notes ORDER BY owner,key').fetchall()
 observed['authorization']=foreign['response']=={'status':201,'text':'two'} and rows==[('a','k','one'),('b','k','two'),('legacy','keep','old')]
 observed['backward_existing_schema']=rows[-1]==('legacy','keep','old') and call('legacy',{'key':'keep','text':'old'})['response']=={'status':200,'text':'old'}
 # Inspect the schema created by the actual candidate, not the precreated table.
 db=str(pathlib.Path(d)/'created.db');created=call('a',{'key':'new','text':'value'})
 with sqlite3.connect(db) as c:
  observed['schema_not_null']=[row[3] for row in c.execute('PRAGMA table_info(notes)')]
  observed['schema_columns']=[row[1] for row in c.execute('PRAGMA table_info(notes)')]
  observed['journal_mode']=c.execute('PRAGMA journal_mode').fetchone()[0]
'''+RACE_V6+r'''
observed['concurrency_identical']={'statuses':sorted(x['status'] for x in results),'durable_rows':1,'start_barrier_participants':observed['race_start_barrier']}
print(json.dumps(observed,sort_keys=True))
'''

SECURITY = r'''
import json,subprocess,sys
observed={}
def call(payload):
 r=subprocess.run([sys.executable,'app.py'],input=json.dumps(payload),capture_output=True,text=True,timeout=3)
 assert r.returncode==0,r.stderr
 return json.loads(r.stdout),r.stderr
base={'trusted_owner':'a','resource':{'owner':'a','data':'OWN_SENTINEL'}}
denied={'status':403,'data':None}
wrong={'trusted_owner':'a','body_owner':'b','resource':{'owner':'b','data':'FOREIGN_SENTINEL'}}
r,err=call(wrong);observed['cross_owner']=r==denied and 'FOREIGN_SENTINEL' not in json.dumps(r)+err
malformed=[None,[],{}, {'trusted_owner':'a','resource':None},{'trusted_owner':'a','resource':[]},{'trusted_owner':'a','resource':{'owner':'a'}},{'trusted_owner':True,'resource':{'owner':1,'data':'x'}},{'trusted_owner':1,'resource':{'owner':1,'data':'x'}}]
observed['malformed_resources']=all(call(v)[0]==denied for v in malformed)
observed['present_null_data']=call({'trusted_owner':'a','resource':{'owner':'a','data':None}})[0]=={'status':200,'data':None}
observed['top_level_destination']=all(call({**base,'destination':v})[0]==denied for v in [None,False,0,'',[],{},'http://127.0.0.1/private'])
nested={'trusted_owner':'a','resource':{'owner':'a','data':{'destination':'https://example.invalid'}}}
observed['destination_anywhere']=call(nested)[0]==denied
observed['nested_destination_response']=call(nested)[0]
observed['no_secret_in_any_response']='OWN_SENTINEL' not in json.dumps(call(base)[0])
observed['synthetic_matching_principal']=call({'trusted_owner':'invented-fixture-context','resource':{'owner':'invented-fixture-context','data':'own'}})[0]
observed['negative_tests']=observed['cross_owner'] and observed['malformed_resources'] and observed['top_level_destination']
print(json.dumps(observed,sort_keys=True))
'''


def execute_facts(skill, files, fixture):
    """Only trusted controller code defines probes; producer commands are ignored."""
    run = executor(skill)
    original = run(files, fixture['commands']['test'], fixture['writable'])
    program = API if skill == 'api-and-interface-design' else SECURITY
    extra = run(files, ['python3', '-c', program], fixture['writable'])
    original_complete = clean(original) and type(original['exit_code']) is int
    extra_complete = clean(extra) and type(extra['exit_code']) is int
    observations_complete = extra_complete and extra['exit_code'] == 0
    values = {}
    if observations_complete:
        try:
            packets = [json.loads(line) for line in extra['stdout'].splitlines()]
            if skill == 'api-and-interface-design':
                observations_complete = len(packets) == 2 and packets[0] == {'concurrent_replay': True, 'durable_rows': 1}
            else:
                observations_complete = len(packets) == 1
            observations_complete = observations_complete and isinstance(packets[-1], dict)
            values = packets[-1] if observations_complete else {}
        except (ValueError, IndexError):
            observations_complete = False
    return seal({'status': 'COMPLETE' if original_complete and extra_complete else 'NOT_RUN', 'values': values,
                 'original_status': 'COMPLETE' if original_complete else 'NOT_RUN',
                 'original_passed': original_complete and original['exit_code'] == 0,
                 'observations_status': 'COMPLETE' if observations_complete else 'NOT_RUN',
                 'functional_result': 'NOT_RUN' if not original_complete or not extra_complete else
                                      'PASS' if original['exit_code'] == extra['exit_code'] == 0 and observations_complete else 'FAIL',
                 'original': normalized(original), 'extra': normalized(extra),
                 'container_command': container_command('<disposable-qualification-container>'),
                 'original_test_digest': text_digest(fixture['commands']['test'][2]),
                 'probe_code': program, 'probe_digest': text_digest(program),
                 'limitation': 'Finite offline fixtures; no general concurrency, authentication service or production proof.'})
