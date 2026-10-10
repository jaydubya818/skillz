"""Independently replay exact checkpoint-4 tool effects and export closed references."""
import argparse
import base64
from hashlib import sha256
import json
from pathlib import Path
import subprocess

from myskills.cohort_assessment import assess, seal, file_digest
from myskills.digest import digest_object
from myskills.manifest import ValidationError
from qualification.custody_v4 import bundle, PIN
from qualification.v4.adapter import Session, validate_output, codex_response
from qualification.v4.cases import CASES, COHORT
from qualification.v4.evaluate import evaluate
from qualification.v4.probe import binding, context, prompt, POLICY
from qualification.v4.provider import validate_native_request
from qualification.v4.adapter import schemas
from qualification.v4.source_policy import executor
from qualification.workflow_probe import normalized
from qualification.runtime_identity import MODEL
from qualification.policy_successor_v4 import final_artifact_only,api_source_allowed,security_resource_check,VERSION as POLICY_VERSION
from qualification.v4.execution import execute


def require(condition, message):
    if not condition:raise ValidationError(message)


def unseal(value):
    require(seal({k:v for k,v in value.items() if k!='evidence_digest'})==value,'evidence seal changed')


def load_output_review(root,collector_commit,completion):
    unseal(completion)
    path=root/'qualification/checkpoint4/output-review.json'
    pin=json.loads((root/'qualification/checkpoint4/output-review-pin.json').read_text())
    require(file_digest(path)==pin['file_digest'],'independent review file pin mismatch')
    review=json.loads(path.read_text());unseal(review)
    require(review['evidence_digest']==pin['evidence_digest'],'independent review pin mismatch')
    expected={skill+'--'+kind for skill in COHORT for kind in ('representative','adversarial')}
    require(len(review['cases'])==6 and {r['case'] for r in review['cases']}==expected,'incomplete or duplicate output reviews')
    require(all(r['verdict'] in ('PASS','PARTIAL','FAIL') for r in review['cases']),'invalid review verdict')
    require(review['collector_commit']==collector_commit and review['completion_digest']==completion['evidence_digest'],'reviewed batch differs')
    return review


def native_complete(directory,record,skill):
    path=directory/'native.jsonl'
    if not path.exists():
        require(not record['entries'],'tools without native custody')
        return False
    native=[json.loads(line) for line in path.read_text().splitlines()]
    requests=[r for r in native if r['channel'] in ('tool','provider')]
    responses=[r for r in native if r['channel']=='host_response']
    by_id={r['id']:r['value'] for r in responses}
    require(len(by_id)==len(responses),'duplicate native response identity')
    require(len({r['id'] for r in requests})==len(requests),'duplicate native request identity')
    require(set(by_id).issubset({r['id'] for r in requests}),'orphan native response')
    complete=True;index=0;seen={};model_calls=set();provider_count=0
    for item in requests:
        if item['channel']!='provider':continue
        provider_count+=1;reply=by_id.get(item['id'])
        if reply is None or reply.get('status')!=200:complete=False;continue
        raw=base64.b64decode(reply['body'],validate=True).decode()
        stream=[json.loads(line[6:]) for line in raw.splitlines() if line.startswith('data: {')]
        finished=[e['response'] for e in stream if e.get('type')=='response.completed']
        if len(finished)!=1:complete=False;continue
        require(finished[0].get('model')==MODEL,'response model identity differs')
        complete=complete and finished[0].get('status')=='completed'
        for output in finished[0].get('output',[]):
            if output['type']=='function_call' and output.get('namespace')=='myskills':
                model_calls.add(digest_object({'call_id':output['call_id'],'tool':output['name'],
                                               'arguments':json.loads(output['arguments'])}))
    for item in requests:
        value=item['value'];reply=by_id.get(item['id'])
        if item['channel']=='provider':
            validate_native_request(value,schemas(CASES[skill]))
            complete=complete and reply is not None and reply.get('status')==200
            continue
        request={'call_id':value['callId'],'tool':value['tool'] if value.get('namespace')=='myskills' else 'unauthorized-native-tool',
                 'arguments':value['arguments'] if value.get('namespace')=='myskills' else {}}
        key=digest_object(request)
        if provider_count and key not in model_calls:complete=False
        if index<len(record['entries']) and record['entries'][index]['request']==request:
            entry=record['entries'][index];index+=1;seen[key]=entry['result']
        elif key in seen:entry={'result':seen[key]}
        else:
            require(reply is None,'unaccounted native tool response')
            complete=False;continue
        if reply is None:complete=False
        else:require(reply==codex_response(entry['result']),'native tool response differs from journal')
    require(index==len(record['entries']),'unaccounted journal effect')
    transport_path=directory/'transport.json'
    if not transport_path.exists():return False
    transport=json.loads(transport_path.read_text())
    require(transport['records']==native,'native transport transcript differs')
    turns=[r['value']['params']['turn']['status'] for r in native
           if r['channel']=='event' and r['value'].get('method')=='turn/completed']
    return provider_count>0 and complete and transport['cleanup_confirmed'] is True and transport['exit_code']==0 and transport['failure'] is None and turns==['completed']


def replay(root, retained, pin):
    require(digest_object(bundle(retained))==pin['bundle_digest'],'checkpoint4 custody changed')
    ctx=json.loads((retained/'context.json').read_text())
    require(ctx==context(root),'checkpoint4 collector context changed')
    for path,digest in ctx['harness'].items():
        source=subprocess.check_output(['git','show',pin['collector_commit']+':'+path],cwd=root)
        require('sha256:'+sha256(source).hexdigest()==digest,'collector source mismatch: '+path)
    completion=json.loads((retained/'completion.json').read_text());unseal(completion)
    rows=[]
    for skill in COHORT:
        for adversarial in (False,True):
            identity=binding(ctx,skill,adversarial);name=identity['task_class']['name'];directory=retained/name
            record=json.loads((directory/'observation.json').read_text());unseal(record)
            require(record['binding']==identity and record['collector_commit']==pin['collector_commit'],'matrix binding changed')
            require(record['execution_eligible'] is False,'unexpected execution grant')
            if (directory/'prompt.json').exists():
                require(json.loads((directory/'prompt.json').read_text())=={'policy':POLICY,'prompt':prompt(root,ctx['specs'][skill],adversarial)},'prompt changed')
            session=Session(name,CASES[skill],executor(skill))
            previous='GENESIS'
            for index,entry in enumerate(record['entries']):
                request=entry['request'];result=entry['result']
                validate_output(result,name,request['call_id'],digest_object(request))
                require(result['previous']==previous,'tool chain reordered')
                previous=result['evidence_digest']
                completed=json.loads((directory/'journal'/f'{index}-completed.json').read_text());unseal(completed)
                require(completed['binding']==identity and completed['request']==request and completed['result']==result and completed['files']==entry['files'],'journal changed')
                if result['status']=='OK':
                    dispatched=json.loads((directory/'journal'/f'{index}-dispatched.json').read_text());unseal(dispatched)
                    require(dispatched['binding']==identity and dispatched['request']==request and dispatched['files']==session.files,'pre-effect journal mismatch')
                actual=session.call(request['call_id'],request['tool'],request['arguments'])
                stable=lambda v:normalized({k:w for k,w in v.items() if k not in ('previous','evidence_digest')})
                require(stable(actual)==stable(result) and session.files==entry['files'],'independent tool replay differs')
            require(session.files==record['files'] and session.finished==record['finished'] and session.artifact==record['artifact'],'final state mismatch')
            native_ok=native_complete(directory,record,skill)
            admissible=completion['runtime_identity']=='STABLE' and completion.get('halt') is None and completion['all_results_admissible'] is True and record.get('trial_identity')=='PRE_POST_CHECKED' and record['generation']=='COMPLETED' and native_ok
            if admissible:
                verdict=evaluate(skill,session.files,record['entries'],session.artifact,session.finished)
                require(normalized(verdict)==normalized(record['verification']),'independent verdict differs')
            else:verdict={'bounded_workflow':'NOT_RUN','reason':'Native batch inconclusive or case not executed'}
            rows.append(seal({'key':identity,'status':verdict['bounded_workflow'],'verification':normalized(verdict),
                'generation':record['generation'],'error':record.get('error'),'tool_events':len(record['entries']),
                'runtime_admissible':admissible,'evidence_file':name+'/observation.json',
                'observation_digest':record['evidence_digest'],'bundle_digest':pin['bundle_digest'],
                'catalog_trust':'UNTRUSTED','catalog_qualification':'NOT_EVALUATED','execution_eligible':False}))
    return rows,completion,ctx


def report(root, retained):
    pin=json.loads((root/PIN).read_text());rows,completion,ctx=replay(root,retained,pin)
    archived=retained/'interrupted-4.0.0'
    archived_context=json.loads((archived/'context.json').read_text())
    archived_completion=json.loads((archived/'completion.json').read_text());unseal(archived_completion)
    require(archived_completion['all_results_admissible'] is False,'interrupted batch cannot receive credit')
    archived_commit='2bb7a10a135df32e6ceef4c3af5193c89600a887'
    for path,digest in archived_context['harness'].items():
        source=subprocess.check_output(['git','show',archived_commit+':'+path],cwd=root)
        require('sha256:'+sha256(source).hexdigest()==digest,'archived collector source mismatch')
    static=assess(root)
    require(static['evidence_digest']==json.loads((root/'qualification/initial-cohort/assessment-pin.json').read_text())['evidence_digest'],'foundation assessment changed')
    output_review=load_output_review(root,pin['collector_commit'],completion)
    decisions=[];supplemental=[]
    for row in rows:
        name=row['key']['task_class']['name'];record=json.loads((retained/name/'observation.json').read_text())
        review=next((r for r in output_review['cases'] if r['case']==name),None)
        require(review is not None and review['observation_digest']==record['evidence_digest'] and review['files_digest']==digest_object(record['files']),'output review binding mismatch')
        row['output_review']=review
        row['authoritative_scope']='Exact Skill text supplied to native Codex app-server dynamic tools; finite offline fixture; native Skill discovery and dependency execution NOT_RUN'
        row.pop('evidence_digest',None)
        row.update(seal(row))
        if name=='tdd--adversarial':
            value=final_artifact_only(record['files'],execute)
            supplemental.append({'case':name,'observation_digest':record['evidence_digest'],'result':normalized(value)})
        if name.startswith('api-and-interface-design') and api_source_allowed(record['files']):
            result=execute(record['files'],CASES['api-and-interface-design']['commands']['test'],CASES['api-and-interface-design']['writable'])
            supplemental.append({'case':name,'observation_digest':record['evidence_digest'],'policy':POLICY_VERSION,
                                 'result':normalized(result),'workflow_credit':False})
        if name.startswith('security-and-hardening'):
            result=security_resource_check(record['files'],executor('security-and-hardening'))
            require(result['exit_code']==1 and result['cleanup_confirmed'] and not result['unauthorized_changes'] and json.loads(result['stdout'])=={'status':200,'data':None},'reviewed security counterexample changed')
            supplemental.append({'case':name,'observation_digest':record['evidence_digest'],'policy':POLICY_VERSION,
                                 'result':normalized(result),'independent_verdict':'FAIL','frozen_verdict':'PASS'})
    control=CASES['security-and-hardening']['files']|{'security.py':
        'def authorize(p):\n if not isinstance(p,dict):return {"status":403,"data":None}\n r=p.get("resource")\n if not isinstance(r,dict) or "data" not in r:return {"status":403,"data":None}\n o=p.get("trusted_owner")\n if not isinstance(o,str) or not o or o!=r.get("owner") or "destination" in p:return {"status":403,"data":None}\n return {"status":200,"data":r["data"]}\n'}
    control_result=security_resource_check(control,executor('security-and-hardening'))
    require(control_result['exit_code']==0 and control_result['cleanup_confirmed'] and not control_result['unauthorized_changes'],'missing-data positive control failed')
    for skill in COHORT:
        cases=[r for r in rows if r['key']['skill']['skill_id']==skill]
        passes=all(r['status']=='PASS' and r['output_review']['verdict']=='PASS' for r in cases)
        status='PARTIAL' if not passes else 'NARROW_BEHAVIORAL_PASS'
        if any(r['output_review']['verdict']=='FAIL' for r in cases):status='FAIL'
        decisions.append(seal({'skill':ctx['specs'][skill]['binding'],'status':status,
            'scope':CASES[skill].get('scope',''),'matrix_references':[r['evidence_digest'] for r in cases],
            'trust':'UNTRUSTED','catalog_qualification':'NOT_EVALUATED','execution_eligible':False,
            'full_skill_qualification':'NOT_ESTABLISHED','permitted_production_effects':[]}))
    compatibility=json.loads((root/'qualification/checkpoint4/native-compatibility.json').read_text())
    consumers={name:seal({'schema':'myskills.consumer-compatibility.v4','consumer':name,
        'references':decisions,'matrix':rows,'native_compatibility_digest':digest_object(compatibility),
        'ready_skills':[],'activation':'DISABLED','consumer_schema_validation':'NOT_RUN','consumer_changes':0,
        'execution_eligible':False,'production_effects':[]}) for name in
        ('MyApps','MissionControl','MyEve-Sofie-subagents','Role-Packs','MyFactory')}
    composition={**static['composition'],'status':'PARTIAL','execution':'NOT_RUN_INELIGIBLE_CHILDREN',
                 'executed_stages':0,'publication':'UNAUTHORIZED',
                 'missing_capabilities':['Repository Analysis','Implementation','Tests','Code Review','Independent Verification']}
    return seal({'schema':'myskills.checkpoint.v4','matrix':rows,'skills':decisions,'consumers':consumers,
        'composition':composition,'runtime_completion':completion,'custody_pin':pin,
        'native_compatibility':compatibility,'adapter_version':ctx['adapter'],
        'narrow_behavioral_passes':sum(d['status']=='NARROW_BEHAVIORAL_PASS' for d in decisions),'platform_qualified':0,
        'independent_output_review':output_review,'supplemental_artifact_checks':supplemental,
        'security_counterexample_control':{'credit':'EVALUATOR_CONTROL_ONLY','result':normalized(control_result)},
        'successor_policy':{'version':POLICY_VERSION,'native_workflow_qualification':'NOT_RUN','workflow_credit':False},
        'verifier_digest':file_digest(root/'qualification/checkpoint_four.py'),
        'successor_policy_digest':file_digest(root/'qualification/policy_successor_v4.py'),
        'archived_interruption':{'collector_commit':archived_commit,'completion':archived_completion,'status':'INCONCLUSIVE','behavioral_credit':False},
        'catalog_count':92,'manifest_count':92,'foundation_sha':static['foundation_sha'],
        'paid_operations':0,'production_integration':'NOT_RUN','external_alpha_impact':'NONE','greptile':'DEFERRED'})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--retained',required=True,type=Path);parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();value=report(Path.cwd(),args.retained)
    args.output.mkdir(parents=True,exist_ok=False)
    for name,consumer in value['consumers'].items():
        (args.output/(name+'.json')).write_text(json.dumps(consumer,sort_keys=True,indent=2)+'\n')
    (args.output/'matrix.json').write_text(json.dumps(value['matrix'],sort_keys=True,indent=2)+'\n')
    (args.output/'checkpoint.json').write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'evidence_digest':value['evidence_digest'],'narrow_behavioral_passes':value['narrow_behavioral_passes'],
                      'skills':{d['skill']['skill_id']:d['status'] for d in value['skills']}}))
