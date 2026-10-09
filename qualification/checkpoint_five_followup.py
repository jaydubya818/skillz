"""Diagnostic API/security reruns after accepted TDD; no extra profile promotion."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from myskills.cohort_assessment import file_digest,seal
from myskills.digest import digest_object
from qualification.checkpoint_four import require,unseal
from qualification.custody_v5 import bundle
from qualification.v5.cases import CASES
from qualification.v5.probe import context,binding,prompt,POLICY
from qualification.v5.replay import replay_entries,native_complete
from qualification.v5.evaluate import evaluate
from qualification.evaluator_successor_v5 import evaluate as successor_evaluate,VERSION
from qualification.workflow_probe import normalized

NAMES=['api-and-interface-design--follow-up','security-and-hardening--follow-up']


def report(root,retained):
    folder=root/'qualification/checkpoint5';pin=json.loads((folder/'followup-evidence-pin.json').read_text())
    require(digest_object(bundle(retained))==pin['bundle_digest'],'follow-up custody differs')
    ctx=json.loads((retained/'context.json').read_text());require(ctx==context(root),'follow-up source context differs')
    for path,digest in ctx['harness'].items():
        source=subprocess.check_output(['git','show',pin['collector_commit']+':'+path],cwd=root)
        require('sha256:'+sha256(source).hexdigest()==digest,'follow-up collector differs')
    accepted=json.loads((folder/'accepted-profile.json').read_text());unseal(accepted)
    require(accepted['qualification']=='PASS' and accepted['evidence_digest']==pin['accepted_tdd_profile'],'TDD prerequisite missing or changed')
    completion=json.loads((retained/'completion.json').read_text());unseal(completion)
    require(completion['cases']==NAMES,'follow-up case substitution')
    review_path=folder/'followup-review.json';review_pin=json.loads((folder/'followup-review-pin.json').read_text())
    require(file_digest(review_path)==review_pin['file_digest'],'follow-up review bytes differ')
    review=json.loads(review_path.read_text());unseal(review)
    require(review['evidence_digest']==review_pin['evidence_digest'] and review['completion_digest']==completion['evidence_digest'] and review['collector_commit']==pin['collector_commit'],'follow-up review identity differs')
    require(review['evaluator_digest']==file_digest(root/'qualification/evaluator_successor_v5.py'),'follow-up evaluator review differs')
    require(len(review['cases'])==2 and {v['case'] for v in review['cases']}==set(NAMES),'follow-up review incomplete')
    rows=[]
    for name in NAMES:
        directory=retained/name;record=json.loads((directory/'observation.json').read_text());unseal(record)
        identity=binding(ctx,name)
        require(record['binding']==identity and record['collector_commit']==pin['collector_commit'] and record['execution_eligible'] is False,'follow-up binding differs')
        if (directory/'prompt.json').exists():require(json.loads((directory/'prompt.json').read_text())=={'policy':POLICY,'prompt':prompt(root,ctx,name)},'follow-up prompt changed')
        session=replay_entries(CASES[name],record,directory)
        admissible=(completion['runtime_identity']=='STABLE' and completion['all_results_admissible'] is True and completion['halt'] is None
                    and record['generation']=='COMPLETED' and record.get('trial_identity')=='PRE_POST_CHECKED' and native_complete(directory,record,CASES[name]))
        frozen=evaluate(CASES[name],session.files,record['entries'],session.artifact,session.finished) if admissible else {'status':'NOT_RUN'}
        if admissible:require(normalized(frozen)==normalized(record['verification']),'follow-up frozen evaluation differs')
        verdict=successor_evaluate(CASES[name],session.files,record['entries'],session.artifact,session.finished) if admissible else frozen
        reviewed=next(v for v in review['cases'] if v['case']==name)
        require(reviewed['observation_digest']==record['evidence_digest'] and reviewed['files_digest']==digest_object(record['files']),'follow-up reviewed files differ')
        status='NOT_RUN' if not admissible else 'PASS' if verdict['status']=='PASS' and reviewed['verdict']=='PASS' else 'FAIL'
        rows.append(seal({'native_collection_key':identity,'evaluator':{'version':VERSION,'digest':file_digest(root/'qualification/evaluator_successor_v5.py')},
                          'status':status,'frozen_evaluation':normalized(frozen),'verification':normalized(verdict),'review':reviewed,
                          'observation_digest':record['evidence_digest'],'execution_eligible':False,'profile_qualification':'PARTIAL_ADDITIONAL_COVERAGE_REQUIRED'}))
    return seal({'schema':'myskills.followup.v5','accepted_tdd_profile':accepted['evidence_digest'],'collector_commit':pin['collector_commit'],
                 'bundle_digest':pin['bundle_digest'],'completion':completion,'matrix':rows,'new_qualified_profiles':0,
                 'verifier_digest':file_digest(root/'qualification/checkpoint_five_followup.py'),
                 'scope':'Affected corrected API/security fixtures only; diagnostics do not constitute the complete qualification corpus or consumer eligibility',
                 'paid_operations':0,'production_integration':'NOT_RUN','external_alpha_impact':'NONE'})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--retained',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();value=report(Path.cwd(),args.retained);args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'followup.json').write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'evidence_digest':value['evidence_digest'],'cases':[v['status'] for v in value['matrix']]}))
