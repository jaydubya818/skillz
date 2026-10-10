"""Independently replay checkpoint 5 and export exact, inactive consumer references."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from myskills.cohort_assessment import assess,seal,file_digest
from myskills.digest import digest_object
from qualification.checkpoint_four import require,unseal
from qualification.custody_v5 import bundle,PIN
from qualification.v5.cases import CASES,TDD_CASES
from qualification.v5.probe import context,binding,prompt,POLICY
from qualification.v5.replay import replay_entries,native_complete
from qualification.v5.evaluate import evaluate
from qualification.evaluator_successor_v5 import evaluate as successor_evaluate,VERSION as SUCCESSOR
from qualification.v5.controls import controls
from qualification.workflow_probe import normalized


def report(root,retained,previous):
    pin=json.loads((root/PIN).read_text())
    require(digest_object(bundle(retained))==pin['bundle_digest'],'checkpoint5 custody changed')
    ctx=json.loads((retained/'context.json').read_text());require(ctx==context(root),'collector context changed')
    for path,digest in ctx['harness'].items():
        source=subprocess.check_output(['git','show',pin['collector_commit']+':'+path],cwd=root)
        require('sha256:'+sha256(source).hexdigest()==digest,'collector source differs: '+path)
    completion=json.loads((retained/'completion.json').read_text());unseal(completion)
    require(completion['cases']==list(TDD_CASES),'TDD corpus substituted or incomplete')
    review_path=root/'qualification/checkpoint5/output-review.json'
    review_pin=json.loads((root/'qualification/checkpoint5/output-review-pin.json').read_text())
    require(file_digest(review_path)==review_pin['file_digest'],'output review bytes changed')
    review=json.loads(review_path.read_text());unseal(review)
    require(review['evaluator_review']['version']==SUCCESSOR and review['evaluator_review']['source_digest']==file_digest(root/'qualification/evaluator_successor_v5.py'),'successor evaluator changed after review')
    require(review['evidence_digest']==review_pin['evidence_digest'] and review['collector_commit']==pin['collector_commit'] and review['completion_digest']==completion['evidence_digest'],'output review context differs')
    require(len(review['cases'])==len(TDD_CASES) and {r['case'] for r in review['cases']}==set(TDD_CASES),'review corpus incomplete')
    rows=[]
    for name in TDD_CASES:
        directory=retained/name;record=json.loads((directory/'observation.json').read_text());unseal(record)
        identity=binding(ctx,name)
        require(record['binding']==identity and record['collector_commit']==pin['collector_commit'] and record['execution_eligible'] is False,'trial binding differs')
        if (directory/'prompt.json').exists():require(json.loads((directory/'prompt.json').read_text())=={'policy':POLICY,'prompt':prompt(root,ctx,name)},'native prompt changed')
        session=replay_entries(CASES[name],record,directory)
        native=native_complete(directory,record,CASES[name])
        admissible=(completion['runtime_identity']=='STABLE' and completion['all_results_admissible'] is True and completion['halt'] is None
                    and record['generation']=='COMPLETED' and record.get('trial_identity')=='PRE_POST_CHECKED' and native)
        verdict=evaluate(CASES[name],session.files,record['entries'],session.artifact,session.finished) if admissible else {'status':'NOT_RUN','reason':'incomplete native trial'}
        if admissible:require(normalized(verdict)==normalized(record['verification']),'independent evaluation differs')
        frozen=verdict
        if admissible:verdict=successor_evaluate(CASES[name],session.files,record['entries'],session.artifact,session.finished)
        output_review=next(r for r in review['cases'] if r['case']==name)
        require(output_review['observation_digest']==record['evidence_digest'] and output_review['files_digest']==digest_object(record['files']),'output review candidate differs')
        status='NOT_RUN' if not admissible else 'PASS' if verdict['status']=='PASS' and output_review['verdict']=='PASS' else 'FAIL'
        evaluated_identity={**identity,'evaluator':{'version':SUCCESSOR,'digest':file_digest(root/'qualification/evaluator_successor_v5.py'),
                                                 'predecessor':identity['evaluator']}}
        rows.append(seal({'key':evaluated_identity,'native_collection_key':identity,'status':status,
                         'frozen_evaluation':normalized(frozen),'assessment_mode':'Independent reevaluation of authentic complete native captures; no model rerun or execution-policy change',
                         'verification':normalized(verdict),'review':output_review,'native_admissible':admissible,
                         'observation_digest':record['evidence_digest'],'bundle_digest':pin['bundle_digest'],
                         'execution_eligible':False,'catalog_trust':'UNTRUSTED','catalog_qualification':'NOT_EVALUATED'}))
    actual_controls=controls(root,previous)
    saved_controls=json.loads((retained/'controls.json').read_text());unseal(saved_controls)
    stable=lambda v:normalized({k:w for k,w in v.items() if k!='evidence_digest'})
    require(stable(actual_controls)==stable(saved_controls),'independent controls differ')
    static=assess(root)
    require(static['evidence_digest']==json.loads((root/'qualification/initial-cohort/assessment-pin.json').read_text())['evidence_digest'],'foundation catalog changed')
    passed=all(r['status']=='PASS' and r['native_admissible'] for r in rows) and actual_controls['status']=='PASS'
    common={k:v for k,v in rows[0]['key'].items() if k!='task_class'}
    profile=seal({'schema':'myskills.qualified-profile.v5','profile':'tdd-python-clamp-offline-v1',**common,
                  'task_class':{'name':'finite Python clamp TDD corpus','fixtures':{n:digest_object(CASES[n]) for n in TDD_CASES}},
                  'behavioral_candidate':'PASS' if passed else 'PARTIAL',
                  'qualification':'PENDING_VALIDATION' if passed else 'PARTIAL','case_evidence':[r['evidence_digest'] for r in rows],
                  'controls_evidence':saved_controls['evidence_digest'],'independent_review':review['evidence_digest'],
                  'scope':'Exact supplied finite fixtures and native dynamic-tool profile only; native automatic Skill discovery NOT_RUN',
                  'checkpoint_validation':'Require separate matching fresh-clone/hosted validation pin before checkpoint acceptance',
                  'global_trust':'UNTRUSTED','catalog_qualification':'NOT_EVALUATED','execution_eligible':False})
    compatibility=json.loads((root/'qualification/checkpoint4/native-compatibility.json').read_text())
    blockers={
        'MyApps':'No consumer harness equivalence established; can consume this exact inactive evidence reference only.',
        'MyFactory':'Codex version alone is insufficient. Its native shell/files and paid infrastructure differ from this profile.',
        'MissionControl':'Existing bridge task types do not provide this Python TDD execution profile.',
        'MyEve-Sofie-subagents':'Current gateway and historical DeepAgents tooling differ; consumer-specific qualification and authorization required.'}
    consumers={name:seal({'schema':'myskills.inactive-compatibility.v5','consumer':name,'profile_reference':profile['evidence_digest'],
                         'profile_qualification':profile['qualification'],'exact_profile':profile,'source_inspection_reference':compatibility['evidence_digest'],
                         'execution_eligible':False,'activation':'DISABLED','consumer_repository_modified':False,'blocker':reason}) for name,reason in blockers.items()}
    return seal({'schema':'myskills.checkpoint.v5','collector_commit':pin['collector_commit'],'bundle_digest':pin['bundle_digest'],
                 'verifier_digest':file_digest(root/'qualification/checkpoint_five.py'),'custody_verifier_digest':file_digest(root/'qualification/custody_v5.py'),
                 'completion':completion,'profile':profile,'matrix':rows,'consumers':consumers,'controls':saved_controls,
                 'behavioral_candidate_profiles':1 if passed else 0,'behaviorally_qualified_profiles':0,'globally_trusted_skills':0,'catalog_count':92,
                 'composition':'PARTIAL_NOT_RUN; missing eligible analysis, implementation, review and independent-verification children',
                 'paid_operations':0,'production_integration':'NOT_RUN','external_alpha_impact':'NONE','marketplace':'DISABLED','greptile':'DEFERRED'})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--retained',type=Path,required=True)
    p.add_argument('--previous',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();value=report(Path.cwd(),args.retained,args.previous);args.output.mkdir(parents=True,exist_ok=False)
    exports={'checkpoint':value,'profile':value['profile'],'matrix':value['matrix'],**value['consumers']}
    for name,record in exports.items():(args.output/(name+'.json')).write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'evidence_digest':value['evidence_digest'],'profile':value['profile']['qualification'],'behaviorally_qualified_profiles':value['behaviorally_qualified_profiles']}))
