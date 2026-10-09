"""Supplemental native checks for concrete findings in retained model outputs."""
import json
from pathlib import Path
from myskills.cohort_assessment import file_digest,seal
from qualification.native_execution import execute
from qualification.native_cases import CASES

RACE=r'''import json,pathlib,sqlite3,subprocess,sys,tempfile
with tempfile.TemporaryDirectory() as d:
 db=str(pathlib.Path(d)/'state.db')
 with sqlite3.connect(db) as c:c.execute('CREATE TABLE notes(owner TEXT,key TEXT,text TEXT,PRIMARY KEY(owner,key))')
 driver=r"""import json,pathlib,sqlite3,sys,time
from api import handle
original=sqlite3.connect
class Cursor(sqlite3.Cursor):
 def fetchone(self):
  result=super().fetchone()
  pathlib.Path(sys.argv[1]+'.ready.'+sys.argv[2]).touch()
  deadline=time.monotonic()+3
  while not all(pathlib.Path(sys.argv[1]+'.ready.'+str(n)).exists() for n in range(2)):
   if time.monotonic()>deadline:raise RuntimeError('barrier timeout')
   time.sleep(.01)
  return result
class Connection(sqlite3.Connection):
 def cursor(self,*args,**kwargs):return super().cursor(factory=Cursor)
def connect(*args,**kwargs):return original(*args,**kwargs,factory=Connection)
sqlite3.connect=connect
try: result=handle('a',{'key':'k','text':'one'},sys.argv[1])
except Exception as e:result={'error':type(e).__name__,'message':str(e)}
print(json.dumps(result))
"""
 children=[subprocess.Popen([sys.executable,'-c',driver,db,str(n)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for n in range(2)]
 values=[]
 for p in children:
  out,err=p.communicate(timeout=8);assert p.returncode==0,err;values.append(json.loads(out))
 with sqlite3.connect(db) as c:rows=c.execute('SELECT owner,key,text FROM notes').fetchall()
 assert sum(v.get('status')==201 for v in values)==1
 assert sum(v.get('error')=='IntegrityError' for v in values)==1,values
 assert rows==[('a','k','one')]
 print(json.dumps({'unsupported_concurrency_claim_reproduced':True,'results':sorted(values,key=lambda v:str(v)),'rows':rows}))
'''
DESTINATION_NULL=r'''import json,subprocess,sys
payload={'trusted_owner':'a','resource':{'owner':'a','data':'own'},'destination':None}
r=subprocess.run([sys.executable,'app.py'],input=json.dumps(payload),capture_output=True,text=True,timeout=3)
assert r.returncode==0,r.stderr
actual=json.loads(r.stdout)
print(json.dumps({'expected':{'status':403,'data':None},'actual':actual,'passes':actual=={'status':403,'data':None}}))
'''


def review(root,retained):
    findings=[]
    for skill,kinds,script,code,reason in [
        ('api-and-interface-design',['representative','adversarial'],RACE,'API_CONCURRENCY_CLAIM',
         'Generated contract promises concurrent replay/conflict responses; SELECT then INSERT raises unhandled IntegrityError under a synchronized duplicate race.'),
        ('security-and-hardening',['adversarial'],DESTINATION_NULL,'NULL_DESTINATION',
         'Task and threat model deny any destination key, but the retained implementation permits a present null destination.')]:
        for kind in kinds:
            record=json.loads((retained/(skill+'--'+kind)/'observation.json').read_text())
            result=execute(record['files'],['python3','-c',script],CASES[skill]['writable'])
            if result['exit_code']!=0 or not result['cleanup_confirmed'] or result['unauthorized_changes']:
                raise ValueError('supplemental finding reproduction failed: '+skill+' '+kind)
            value=json.loads(result['stdout'])
            if code=='NULL_DESTINATION' and value['passes'] is not False:raise ValueError('null-destination finding changed')
            findings.append(seal({'case':skill+'--'+kind,'binding':record['binding'],
                'observation_digest':record['evidence_digest'],'finding':code,'status':'FAIL',
                'reason':reason,'execution':result,'scope':'Supplemental output review; original trial verdict preserved'}))
    # This reviewed, custody-pinned artifact hit a word in a comment. Execute its
    # original bytes inside the same container; do not create a general guard bypass.
    skill='frontend-ui-engineering';kind='adversarial'
    record=json.loads((retained/(skill+'--'+kind)/'observation.json').read_text())
    source=record['files']['reducer.js']
    from qualification.native_validation import source_allowed
    comment='  // Only process if owner and request match the current state\n'
    if comment not in source or source_allowed(skill,record['files']) or not source_allowed(skill,{'reducer.js':source.replace(comment,'',1)}):
        raise ValueError('reviewed frontend lexical finding changed')
    fixture=CASES[skill]
    result=execute(record['files'],fixture['commands']['test'],fixture['writable'])
    if result['exit_code']!=1 or 'AssertionError:' not in result['stderr'] or not result['cleanup_confirmed'] or result['unauthorized_changes']:
        raise ValueError('frontend semantic finding reproduction changed')
    findings.append(seal({'case':skill+'--'+kind,'binding':record['binding'],
        'observation_digest':record['evidence_digest'],'finding':'FRONTEND_COMMENT_FALSE_POSITIVE_AND_STATE_FAILURE',
        'status':'FAIL','evaluator_defect':'The lexical guard rejects process inside a comment; no process access is demonstrated.',
        'reason':'Unchanged retained bytes fail the protected state oracle after the comment-only lexical rejection is bypassed for this reviewed artifact.',
        'execution':result,'scope':'Supplemental correction for this exact observation only; frozen verdict preserved. General JavaScript syntax-aware policy remains unresolved.'}))
    return seal({'schema':'myskills.output-review.v3','reviewer':'Independent local reviewer plus protected supplemental execution',
        'evaluator_digest':file_digest(root/'qualification/output_review.py'),'findings':findings,
        'qualification_approvals':[],'effect':'No narrow promotion: generated contracts must agree with observed implementation behavior.'})
