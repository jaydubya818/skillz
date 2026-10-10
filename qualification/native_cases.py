"""Versioned, finite repository workflows for the retained ten-Skill cohort."""
from copy import deepcopy
from qualification.workflow_cases import CASES as PRIOR

CASES=deepcopy(PRIOR)
CASES['tdd']['task']=CASES['tdd']['task'].replace('No helper, import-time code or main block.', 'No helper or import-time side effects. An optional if __name__ == "__main__": unittest.main() guard is supported.')
CASES['principle-sequence-verifiable-units']['task']=CASES['principle-sequence-verifiable-units']['task'].replace('No helper, import-time code or main block.', 'No helper or import-time side effects. An optional if __name__ == "__main__": unittest.main() guard is supported.')
# Planning and review outputs retain their deliberately narrow scope. They do not
# cover the full multi-phase/delegated workflows named in their canonical Skills.
CASES['figure-it-out']['scope']='Read-only parser investigation and planning'
CASES['principle-sequence-verifiable-units']['scope']='Stop ordered Python edits at a failing first-unit dependency gate'
CASES['tdd']['scope']='Python clamp bug fix with executable red-before-edit/green regression'
CASES['thermo-nuclear-code-quality-review']['scope']='Read-only Python fallback-defect review with executed counterexample'
CASES['create-verification-skill']['scope']='Generate and drive a single-feature count CLI verification Skill'
CASES['create-verification-skill']['writable'] += ['.agents/skills/verify/features/README.md','.agents/skills/verify/features/count.md']
CASES['create-verification-skill']['task'] += ' Also generate the feature-map README index and count.md with H2 Sub-features, How to get to it (user POV), Driving it with Python, and Gotchas. Name the actual count CLI command, expected state, and preserve evidence.json during cleanup.'

# Each protected command is materialized in a disposable, credential-free
# container. Candidate modules run in child interpreters; parent checks inspect
# returned values AND the actual SQLite state, never producer PASS text.
API_TEST=r'''import json, pathlib, sqlite3, subprocess, sys, tempfile
with tempfile.TemporaryDirectory() as d:
 db=str(pathlib.Path(d)/'state.db')
 def call(owner,body):
  driver='import json,sys; from api import handle; p=json.load(sys.stdin); print(json.dumps(handle(p["owner"],p["body"],p["db"])))'
  r=subprocess.run([sys.executable,'-c',driver],input=json.dumps({'owner':owner,'body':body,'db':db}),capture_output=True,text=True,timeout=3)
  assert r.returncode==0,r.stderr
  return json.loads(r.stdout)
 assert call('a',{'key':'k','text':'one'})=={'status':201,'text':'one'}
 assert call('a',{'key':'k','text':'one'})=={'status':200,'text':'one'}
 assert call('a',{'key':'k','text':'changed'})=={'status':409,'text':None}
 assert call('b',{'key':'k','text':'two','owner':'a'})=={'status':201,'text':'two'}
 assert call('a',{'key':'k2','text':None})=={'status':400,'text':None}
 assert call('a',{'key':'','text':'bad'})=={'status':400,'text':None}
 assert call('a',[])=={'status':400,'text':None}
 owner="tenant' OR 1=1 --";key="k'";text="x'); DROP TABLE notes; --"
 assert call(owner,{'key':key,'text':text})=={'status':201,'text':text}
 assert call(owner,{'key':key,'text':text})=={'status':200,'text':text}
 with sqlite3.connect(db) as c:
  assert c.execute('select owner,key,text from notes order by owner,key').fetchall()==[('a','k','one'),('b','k','two'),(owner,key,text)]
 print(json.dumps({'checks':10,'durable_rows':3,'reopened_processes':9}))
'''
MIGRATION_TEST=r'''import json, pathlib, sqlite3, subprocess, sys, tempfile
with tempfile.TemporaryDirectory() as d:
 db=str(pathlib.Path(d)/'state.db')
 with sqlite3.connect(db) as c:
  c.execute('create table notes(id integer primary key,old text,new text,version integer)')
  c.executemany('insert into notes values(?,?,?,?)',[(1,'latest',None,2),(2,'ready',None,1),(3,'legacy','newer',1),(4,'fourth',None,1)])
 snapshots=[{'id':1,'old':'stale','version':1},{'id':2,'old':'ready','version':1},{'id':3,'old':'legacy','version':1},{'id':4,'old':'fourth','version':1}]
 def run():
  driver='import json,sys; from migration import backfill; p=json.load(sys.stdin); backfill(p["db"],p["snapshots"])'
  return subprocess.run([sys.executable,'-c',driver],input=json.dumps({'db':db,'snapshots':snapshots}),capture_output=True,text=True,timeout=3)
 def rows():
  with sqlite3.connect(db) as c:return c.execute('select * from notes order by id').fetchall()
 before=rows()
 with sqlite3.connect(db) as c:c.execute("CREATE TRIGGER qualification_fault AFTER UPDATE ON notes WHEN NEW.id=4 BEGIN SELECT RAISE(ABORT,'QUALIFICATION_UPDATE_ABORT'); END")
 failed=run()
 assert failed.returncode!=0 and 'QUALIFICATION_UPDATE_ABORT' in failed.stderr
 assert rows()==before,'failed transaction leaked writes'
 with sqlite3.connect(db) as c:
  assert c.execute("select name from sqlite_master where type='trigger'").fetchall()==[('qualification_fault',)]
  c.execute('DROP TRIGGER qualification_fault')
 good=run();assert good.returncode==0,good.stderr
 expected=[(1,'latest',None,2),(2,'ready','ready',1),(3,'legacy','newer',1),(4,'fourth','fourth',1)]
 assert rows()==expected
 assert run().returncode==0 and rows()==expected
 print(json.dumps({'checks':5,'rows':rows(),'sqlite_update_fault_recovery':True}))
'''
SECURITY_TEST=r'''import json, subprocess, sys
cases=[({'trusted_owner':'a','body_owner':'b','resource':{'owner':'b','data':'PRIVATE_B'}},{'status':403,'data':None}),({'trusted_owner':'a','resource':{'owner':'a','data':'own'}},{'status':200,'data':'own'}),({'trusted_owner':'a','resource':{'owner':'a','data':'own'},'destination':'http://127.0.0.1/private'},{'status':403,'data':None}),({'trusted_owner':'a','resource':{}},{'status':403,'data':None}),({'trusted_owner':'a','resource':{'owner':'a','data':'own'},'destination':'http://[::1]/private'},{'status':403,'data':None})]
cases += [(p,{'status':403,'data':None}) for p in [[],None,{}, {'trusted_owner':'','resource':{'owner':'','data':'private'}},{'resource':{'data':'private'}},{'trusted_owner':'a','resource':[]},{'trusted_owner':'a','resource':None}]]
for payload,expected in cases:
 r=subprocess.run([sys.executable,'app.py'],input=json.dumps(payload),capture_output=True,text=True,timeout=3)
 assert r.returncode==0,r.stderr
 assert json.loads(r.stdout)==expected
 assert 'PRIVATE_B' not in r.stdout+r.stderr
print(json.dumps({'checks':len(cases),'secret_leaks':0}))
'''
FRONTEND_TEST=r'''import json, subprocess
original={'owner':'a','request':2,'text':'draft','status':'pending'}
cases=[(original,{'type':'success','owner':'b','request':2,'text':'foreign'},original),(original,{'type':'success','owner':'a','request':1,'text':'stale'},original),(original,{'type':'submit','owner':'a','request':3},original),(original,{'type':'failure','owner':'a','request':2},{**original,'status':'request-failure'}),(original,{'type':'success','owner':'a','request':2,'text':'saved'},{**original,'status':'success','text':'saved'}),({**original,'status':'idle'},{'type':'submit','owner':'a','request':3},{**original,'request':3})]
for state,event,expected in cases:
 driver='const fs=require("node:fs");const p=JSON.parse(fs.readFileSync(0,"utf8"));const reduce=require("./reducer.js");console.log(JSON.stringify(reduce(p.state,p.event)));'
 r=subprocess.run(['node','-e',driver],input=json.dumps({'state':state,'event':event}),capture_output=True,text=True,timeout=3)
 assert r.returncode==0,r.stderr
 assert json.loads(r.stdout)==expected,r.stdout
print(json.dumps({'checks':6,'browser':'NOT_RUN'}))
'''
CI_TEST=r'''import json,subprocess,sys,pathlib,tempfile
p=json.loads(pathlib.Path('.github/workflows/check.yml').read_text())
assert p=={'name':'check','on':['pull_request'],'permissions':{'contents':'read'},'jobs':{'test':{'runs-on':'ubuntu-latest','timeout-minutes':5,'steps':[{'run':'python3 -m unittest -q'}]}}}
# Execute the exact permitted command on actual good and bad repositories.
for fail,expected in [(False,0),(True,1)]:
 with tempfile.TemporaryDirectory() as d:
  pathlib.Path(d,'test_check.py').write_text('import unittest\nclass Check(unittest.TestCase):\n def test_gate(self): self.assertTrue('+str(not fail)+')\n')
  r=subprocess.run(['python3','-m','unittest','-q'],cwd=d,capture_output=True,text=True,timeout=3)
  assert r.returncode==expected,r.stderr
print(json.dumps({'checks':3,'hosted_generated_workflow':'NOT_RUN','local_failure_propagation':True}))
'''
CASES.update({
 'api-and-interface-design':{
  'scope':'SQLite-backed local API contract, durable replay and owner separation',
  'files':{'api.py':'def handle(trusted_owner, body, db_path):\n return {"status":201,"text":body.get("text")}\n','README.md':'Local Python API with server-authenticated trusted_owner; body is untrusted. No external callers. SQLite notes(owner TEXT,key TEXT,text TEXT,PRIMARY KEY(owner,key)); persistent replay cache is this table. Schema created IF NOT EXISTS by handle. Inputs/outputs are Python dicts, not objects. No pagination in this interface.'},
  'writable':['api.py','contract.md'], 'commands':{'test':['python3','-c',API_TEST]},
  'task':'Read README and api.py. Write contract.md before implementation. Implement handle(trusted_owner,body,db_path) using Python sqlite3, parameterized statements and transaction-safe unique owner/key. body.key and body.text must be nonempty strings; malformed body returns {"status":400,"text":null}. Ignore body.owner. First create returns 201 and stored text; identical replay returns 200 and the ORIGINAL stored text; changed text for same owner/key returns 409 and null text. Create notes schema if needed. Preserve records across calls from new processes. Run test and report observed evidence and untested concurrency. Only import sqlite3; module contains imports and function definitions, no import-time side effects or dunder access.'},
 'deprecation-and-migration':{
  'scope':'SQLite conditional backfill with transaction rollback and retry',
  'files':{'migration.py':'def backfill(db_path, snapshots):\n pass\n','README.md':'SQLite table notes(id INTEGER PRIMARY KEY,old TEXT,new TEXT,version INTEGER) already expanded. Old readers consume old; new readers prefer new then old. Keep old and existing non-null new values. No contract/drop phase authorized. Snapshots are list[dict] with id,old,version, bounded to four records. SQLite version can be inspected with doctor.'},
  'writable':['migration.py','migration-plan.md'],'commands':{'doctor':['python3','-c','import sqlite3; print(sqlite3.sqlite_version)'],'test':['python3','-c',MIGRATION_TEST]},
  'task':'Read current code and README; run doctor. Write migration-plan.md with retained readers, expand/migrate phase, rollback/retry and no removal authorization. Implement backfill(db_path,snapshots) with sqlite3. For each snapshot DICT update new from snapshot["old"] only WHERE id matches, version equals snapshot["version"] AND new IS NULL. Parameterize SQL. One transaction; SQLite may raise an error during an update. Roll back all writes and propagate the error. The evaluator injects an actual database update fault before retry. Close the connection. Repeated runs must preserve data. Run test and report. Only import sqlite3; imports and function definitions only, no module side effects or dunder access.'},
 'security-and-hardening':{
  'scope':'CLI resource-read authorization and explicit destination denial',
  'files':{'security.py':'def authorize(payload):\n return {"status":200,"data":payload["resource"].get("data")}\n','app.py':'import json,sys\nfrom security import authorize\nprint(json.dumps(authorize(json.load(sys.stdin))))\n','README.md':'CLI reads a JSON DICT. trusted_owner is authenticated fixture context; body_owner, destination and resource data are untrusted. resource is {owner,data}. Assets are owner data. No network fetch is supported.'},
  'writable':['security.py','threat-model.md'],'commands':{'test':['python3','-c',SECURITY_TEST]},
  'task':'Read all files. Write threat-model.md with actor, owner-data asset, untrusted body_owner, cross-owner and destination abuse cases before fixing. Implement authorize(payload) as a pure function. Return {status:200,data:resource.data} only for a nonempty authenticated trusted_owner matching resource.owner and no destination key. All other inputs, malformed resources, and any destination request return {status:403,data:null}. Actual payload/resource values are DICTS; use dictionary access. Do not log secret data. Run test against the actual CLI and report evidence and scope. No imports, dunder access or module side effects in security.py.'},
 'frontend-ui-engineering':{
  'scope':'JavaScript note-editor state transitions; browser workflow remains unavailable',
  'files':{'reducer.js':'module.exports=(state,event)=>({...state,...event});\n','README.md':'CommonJS reducer(state,event) returns state directly. State {owner,request,text,status}; status idle,pending,success,request-failure. The repository has no browser dependency in this pinned runtime. Do not claim browser, layout or accessibility checks.'},
  'writable':['reducer.js','ui-evidence.md'],'commands':{'test':['python3','-c',FRONTEND_TEST]},
  'task':'Read source and README. Fix reducer.js. submit on non-pending state with matching owner sets pending and request; pending duplicate submit does nothing. success/failure only applies for matching owner and request while pending. success sets status success and event text; failure sets request-failure and preserves draft. Every unmatched event preserves state. Return state directly, never {state:...}. Run native Node test, write ui-evidence.md listing browser/accessibility NOT_RUN and exact tested states. No imports, require, filesystem, network, process/global access in candidate JS. Browser-dependent full workflow cannot qualify in this runtime.'},
 'ci-cd-and-automation':{
  'scope':'GitHub workflow configuration and native local failure propagation',
  'files':{'README.md':'Python3 stdlib unittest project. No dependencies or credentials. Check command: python3 -m unittest -q. Existing action policy: no external actions in fixture; checkout/hosted dispatch unavailable here. JSON is accepted as a YAML subset. Publishing and branch protection changes are unauthorized.','test_check.py':'import unittest\nclass Check(unittest.TestCase):\n def test_example(self): self.assertTrue(True)\n'},
  'writable':['.github/workflows/check.yml','ci-evidence.md'],'commands':{'baseline':['python3','-m','unittest','-q'],'test':['python3','-c',CI_TEST]},
  'task':'Read the repo and run baseline. Generate .github/workflows/check.yml as JSON YAML subset exactly: name check; on [pull_request]; permissions {contents:read}; jobs.test with runs-on ubuntu-latest, timeout-minutes 5, steps [{run:"python3 -m unittest -q"}]. No secrets, interpolation, external actions, continue-on-error or publication. Run test for configuration and real pass/fail command propagation. Write ci-evidence.md with hosted generated-workflow execution NOT_RUN. Do not mistake a local command for a hosted run.'}
})

NATIVE_UNAVAILABLE={'figure-it-out':'Required multi-phase dependency workflows and complete implementation trail not executed',
 'thermo-nuclear-code-quality-review':'Broad structural audit and layered report not established by one defect',
 'frontend-ui-engineering':'Pinned image has no browser; rendered interaction/accessibility NOT_RUN',
 'ci-cd-and-automation':'Generated workflow hosted dispatch/fork behavior NOT_RUN',
 'create-verification-skill':'Generated helper executable packaging and complete feature-map workflow require independent inspection'}
