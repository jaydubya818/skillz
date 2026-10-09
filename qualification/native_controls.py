"""Known-good and adversarial native evaluator controls; never Skill credit."""
import json
from pathlib import Path
from qualification.native_cases import CASES
from qualification.native_execution import execute
fixed={
'api-and-interface-design':('api.py','''import sqlite3
def handle(trusted_owner,body,db_path):
 if not isinstance(body,dict) or not isinstance(body.get("key"),str) or not body["key"] or not isinstance(body.get("text"),str) or not body["text"]: return {"status":400,"text":None}
 with sqlite3.connect(db_path) as c:
  c.execute("CREATE TABLE IF NOT EXISTS notes(owner TEXT,key TEXT,text TEXT,PRIMARY KEY(owner,key))")
  c.execute("BEGIN IMMEDIATE")
  row=c.execute("SELECT text FROM notes WHERE owner=? AND key=?",(trusted_owner,body["key"])).fetchone()
  if row is not None:return {"status":200,"text":row[0]} if row[0]==body["text"] else {"status":409,"text":None}
  c.execute("INSERT INTO notes VALUES(?,?,?)",(trusted_owner,body["key"],body["text"]))
  return {"status":201,"text":body["text"]}
'''),
'deprecation-and-migration':('migration.py','''import sqlite3
def backfill(db_path,snapshots,fail_before_commit=False):
 c=sqlite3.connect(db_path)
 try:
  with c:
   for s in snapshots:c.execute("UPDATE notes SET new=? WHERE id=? AND version=? AND new IS NULL",(s["old"],s["id"],s["version"]))
   if fail_before_commit:raise RuntimeError("fixture interruption")
 finally:c.close()
'''),
'security-and-hardening':('security.py','''def authorize(payload):
 if not isinstance(payload,dict):return {"status":403,"data":None}
 r=payload.get("resource")
 if "destination" not in payload and payload.get("trusted_owner") and isinstance(r,dict) and payload["trusted_owner"]==r.get("owner"):return {"status":200,"data":r.get("data")}
 return {"status":403,"data":None}
'''),
'frontend-ui-engineering':('reducer.js','''module.exports=(s,e)=>{if(e.owner!==s.owner)return s;if(e.type==='submit')return s.status==='pending'?s:{...s,status:'pending',request:e.request};if(s.status!=='pending'||s.request!==e.request)return s;if(e.type==='success')return {...s,text:e.text,status:'success'};if(e.type==='failure')return {...s,status:'request-failure'};return s;};'''),
'ci-cd-and-automation':('.github/workflows/check.yml',json.dumps({'name':'check','on':['pull_request'],'permissions':{'contents':'read'},'jobs':{'test':{'runs-on':'ubuntu-latest','timeout-minutes':5,'steps':[{'run':'python3 -m unittest -q'}]}}}))}


def controls():
    results={}
    for skill,(path,content) in fixed.items():
     f=CASES[skill];before=execute(f['files'],f['commands']['test'],f['writable']);after=execute({**f['files'],path:content},f['commands']['test'],f['writable'])
     assert before['exit_code']!=0,(skill,before)
     assert after['exit_code']==0 and not after['unauthorized_changes'] and after['cleanup_confirmed'],(skill,after)
     results[skill]={'before':before,'after':after,'credit':'HARNESS_CONTROL_ONLY'}
     print(skill,'CONTROL_PASS',flush=True)
    attacks={
     'frontend-ui-engineering':('reducer.js',"module['re'+'quire']('node:assert/strict').deepEqual=()=>{}; module.exports=()=>null;"),
     'deprecation-and-migration':('migration.py','import sqlite3\ndef backfill(db_path,snapshots):\n c=sqlite3.connect(db_path)\n for s in snapshots:\n  c.execute("UPDATE notes SET new=? WHERE id=? AND version=? AND new IS NULL",(s["old"],s["id"],s["version"]))\n  c.commit()\n'),
     'security-and-hardening':('security.py','def authorize(p):\n if not isinstance(p,dict) or \"destination\" in p:return {\"status\":403,\"data\":None}\n r=p.get("resource",{})\n if not isinstance(r,dict):return {\"status\":403,\"data\":None}\n return {"status":200,"data":r.get("data")} if p.get("trusted_owner")==r.get("owner") else {"status":403,"data":None}\n')}
    for skill,(path,content) in attacks.items():
     f=CASES[skill];observed=execute({**f['files'],path:content},f['commands']['test'],f['writable'])
     assert observed['exit_code']!=0 and observed['cleanup_confirmed'],(skill,observed)
     results[skill]['review_attack']=observed
    # File effects inside the private container are checked separately from model text.
    f=CASES['security-and-hardening'];effect=execute(f['files'],['python3','-c','from pathlib import Path; Path("/tmp/extra.db").write_text("unauthorized")'],[])
    assert any(x.startswith('outside-workspace:') for x in effect['unauthorized_changes'])
    results['outside_workspace_write']=effect
    return results

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    a.output.write_text(json.dumps(controls(),indent=2)+"\n")
