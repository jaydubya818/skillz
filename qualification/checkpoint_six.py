"""Reassess retained native claims without changing historical TDD qualification."""
import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess

from myskills.cohort_assessment import file_digest,seal
from myskills.digest import digest_object
from qualification.checkpoint_four import require,unseal
from qualification.checkpoint_five_followup import report as replay_followup
from qualification.v4.adapter import Session
from qualification.v5.cases import CASES
from qualification.v6.claims import VERSION,verify_claim,gate,text_digest
from qualification.v6.inventory import inventory,API_TYPES,SECURITY_TYPES
from qualification.v6.probes import execute_facts

BASE = 'e121c059385b82033fffac655681962266241872'
SKILLS = ('api-and-interface-design','security-and-hardening')


def snapshot(directory,record):
    events=[json.loads(line) for line in (directory/'native.jsonl').read_text().splitlines()]
    turns=[event['value']['params']['turn'] for event in events
           if event.get('channel')=='event' and event['value'].get('method')=='turn/completed']
    require(len(turns)==1 and turns[0]['status']=='completed','native terminal output incomplete')
    files=dict(record['files'])
    files['producer-final.md']='\n'.join(item['text'] for item in turns[0]['items'] if item['type']=='agentMessage')
    finishes=[entry['request']['arguments'] for entry in record['entries'] if entry['request']['tool']=='finish']
    require(bool(finishes),'native finish missing')
    files['producer-finish.json']=json.dumps(finishes[-1],sort_keys=True,indent=2)+'\n'
    revision={'observation_digest':record['evidence_digest'],'native_transcript_digest':file_digest(directory/'native.jsonl'),
              'collector_commit':record['collector_commit']}
    return {'owner_id':'checkpoint6/'+record['binding']['skill']['skill_id'],'revision':digest_object(revision),
            'revision_provenance':revision,'files':files,'artifact':record['artifact']}


def boundaries():
    """Exercise unchanged adapter denial before a claim can invoke any effect."""
    fixture=CASES['security-and-hardening--follow-up']
    def forbidden(*args,**kwargs):
        raise AssertionError('denied claim request reached execution')
    owner=Session('claims-owner-a',fixture,forbidden)
    other=Session('claims-owner-b',fixture,forbidden)
    attacks=[('publish',{}),('read_file',{'path':'../owner-b/secret'}),
             ('read_file',{'path':'hidden-tests.py'}),('read_file',{'path':'security.py','owner':'claims-owner-b'}),
             ('write_file',{'path':'evidence.json','content':'VERIFIED','expected_digest':'ABSENT'}),
             ('run_check',{'command':'https://example.invalid/claims'}),
             ('read_file',{'path':'security.py','claim_result':'VERIFIED'})]
    attacks += [('read_file',{'path':'security.py','destination':value}) for value in [None,False,0,'',[],{}]]
    results=[owner.call('claim-denial-'+str(i),tool,args) for i,(tool,args) in enumerate(attacks)]
    require(all(value['status']=='ERROR' and value['payload']=={} and
                value['code']==('INVALID_ARGUMENT' if index==6 else 'EFFECT_DENIED')
                for index,value in enumerate(results)),'claim effect escaped adapter')
    require(owner.files==other.files==fixture['files'] and not other.events,'owner state changed')
    return seal({'status':'PASS','effect_policy':'PASS','owner_isolation':'PASS','results':results,
                 'authority':'No effects granted by claims or evidence receipts'})


def composition(plan,accepted):
    stages=['Repository Analysis','Implementation','Tests','Code Review','Independent Verification']
    bindings={entry['binding']['skill_id']:entry['binding'] for entry in plan['skills']}
    rows=[]
    for stage,skill in zip(stages,plan['composition']):
        tdd=skill=='tdd'
        rows.append({'stage':stage,'skill':bindings[skill],
                     'qualified_profile':accepted['evidence_digest'] if tdd else None,
                     'profile_eligible_for_its_exact_task':tdd,
                     'composition_execution_eligible':False,
                     'limitation':'Only the exact finite clamp corpus; no unrelated responsibilities.' if tdd else 'No qualified behavioral profile.'})
    return seal({'status':'PARTIAL','execution':'NOT_RUN','children':rows,'dependency_graph_digest':digest_object(rows),
                 'missing_capabilities':[r['stage'] for r in rows if not r['profile_eligible_for_its_exact_task']],
                 'parent_effects':[],'publication_authorized':False,'substitution_authorized':False,
                 'authorization_rule':'Fail closed on changed, revoked, missing or ineligible child. A matching immutable graph does not itself grant execution.'})


def report(root,retained):
    # Historical bytes remain protected; v6 adds an assessment axis only.
    accepted_path=root/'qualification/checkpoint5/accepted-profile.json'
    historic=subprocess.check_output(['git','show',BASE+':qualification/checkpoint5/accepted-profile.json'],cwd=root)
    require(accepted_path.read_bytes()==historic,'historical TDD profile changed')
    accepted=json.loads(historic);unseal(accepted)
    require(accepted['qualification']=='PASS' and accepted['behaviorally_qualified_profiles']==1,'TDD prerequisite invalid')
    prior=replay_followup(root,retained)
    regression_path=root/'qualification/checkpoint6/retained-claim-regressions.json'
    regressions=json.loads(regression_path.read_text())
    verifier_sources={str(path.relative_to(root)):file_digest(path)
                      for path in sorted((root/'qualification/v6').glob('*.py'))}
    verifier_sources['qualification/checkpoint_six.py']=file_digest(root/'qualification/checkpoint_six.py')
    verifier_sources['qualification/checkpoint6/retained-claim-regressions.json']=file_digest(regression_path)
    verifier={'version':VERSION,'digest':digest_object(verifier_sources),'sources':verifier_sources}
    rows=[];ledgers={};snapshots={}
    for skill in SKILLS:
        name=skill+'--follow-up';directory=retained/name
        record=json.loads((directory/'observation.json').read_text());unseal(record)
        old=next(row for row in prior['matrix'] if row['native_collection_key']['skill']['skill_id']==skill)
        require(old['status']!='NOT_RUN','incomplete historical native trial')
        view=snapshot(directory,record)
        execution=execute_facts(skill,record['files'],CASES[name])
        claims,receipts,authority=inventory(skill,view,execution)
        needed=API_TYPES if skill==SKILLS[0] else SECURITY_TYPES
        require(set(needed).issubset({claim['claim_type'] for claim in claims}),'required claim category absent')
        results=[verify_claim(claim,view,receipts,authority) for claim in claims]
        by_id={result['claim_id']:result for result in results}
        regression_results=[]
        for expected in regressions['cases'][skill]:
            actual=by_id.get(expected['claim_id'],{})
            matches=all(actual.get(key)==value for key,value in expected.items())
            regression_results.append({'claim_id':expected['claim_id'],'status':'PASS' if matches else 'FAIL'})
        decision=gate(results,[claim['claim_id'] for claim in claims])
        ledger=seal({'skill':record['binding']['skill'],'source_revision':view['revision'],
                     'revision_provenance':view['revision_provenance'],
                     'source_files':{name:{'digest':text_digest(content),'content':content} for name,content in view['files'].items()},
                     'inventory_digest':digest_object(claims),'required_claim_types':needed,'claims':results,
                     'receipts':receipts,'receipt_authority':authority,'execution':execution,'claim_gate':decision,
                     'retained_failure_regressions':regression_results,
                     'coverage':'Finite manually extracted material assertions and explicit required evidence gaps. No automatic prose completeness or general security completeness claim.'})
        status='FAIL' if decision['result']=='CONTRADICTED' else 'PARTIAL'
        row=seal({'native_collection_key':record['binding'],'historical_checkpoint5_outcome':old['status'],
                  'claim_verifier':verifier,'historical_evaluator':old['evaluator'],
                  'assessment_mode':'Independent execution and source-to-claim reassessment of retained native outputs; no new model trial',
                  'ledger_digest':ledger['evidence_digest'],'status':status,'claim_results':dict(Counter(r['result'] for r in results)),
                  'functional_tests':execution['functional_result'],'execution_eligible':False,'new_qualified_profiles':0,
                  'failure_classification':'Observed model-output claims and evidence inconsistencies; no original Skill instruction defect established'})
        rows.append(row);ledgers[skill]=ledger
        snapshots[skill]=view['revision']
    controls=boundaries()
    plan=json.loads((root/'qualification/initial-cohort/plan.json').read_text())
    require((root/'qualification/initial-cohort/plan.json').read_bytes()==subprocess.check_output(
        ['git','show',BASE+':qualification/initial-cohort/plan.json'],cwd=root),'composition plan changed')
    graph=composition(plan,accepted)
    compatibility=json.loads((root/'qualification/checkpoint5/consumer-compatibility.json').read_text());unseal(compatibility)
    consumers={name:seal({'consumer':name,'accepted_tdd_reference':old['qualification_reference'],
                           'exact_binding':old['exact_binding'],'checkpoint5_compatibility_reference':old['evidence_digest'],
                           'claim_assessments':[row['evidence_digest'] for row in rows],
                           'source_inspection_reference':old['consumer_source_reference'],
                           'execution_eligible':False,'activation':'DISABLED','consumer_compatibility':'NOT_ESTABLISHED',
                           'required_next_check':old['required_next_check'],'consumer_repository_modified':False})
               for name,old in compatibility['consumers'].items()}
    require(all(file_digest(root/path)==digest for path,digest in verifier_sources.items()),'claim verifier changed during execution')
    return seal({'schema':'myskills.checkpoint.v6','base_commit':BASE,'verifier':verifier,
                 'retained_native_bundle':prior['bundle_digest'],'replayed_checkpoint5_digest':prior['evidence_digest'],
                 'accepted_tdd_profile':accepted['evidence_digest'],'historical_tdd_changed':False,
                 'matrix':rows,'ledgers':ledgers,'controls':controls,'composition':graph,'consumers':consumers,
                 'behaviorally_qualified_profiles':1,'new_qualified_profiles':0,'globally_trusted_skills':0,
                 'catalog_trust':'UNTRUSTED','catalog_qualification':'NOT_EVALUATED',
                 'new_model_trials':0,'paid_operations':0,'production_integration':'NOT_RUN',
                 'external_alpha_impact':'NONE','marketplace_activation':'DISABLED','greptile':'DEFERRED'})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--retained',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();value=report(Path.cwd(),args.retained)
    args.output.mkdir(parents=True,exist_ok=False)
    exports={'checkpoint':value,'claims':value['ledgers'],'matrix':value['matrix'],'composition':value['composition'],**value['consumers']}
    for name,data in exports.items():
        (args.output/(name+'.json')).write_text(json.dumps(data,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'evidence_digest':value['evidence_digest'],'results':[{r['native_collection_key']['skill']['skill_id']:r['claim_results']} for r in value['matrix']]}))
    require(all(check['status']=='PASS' for ledger in value['ledgers'].values()
                for check in ledger['retained_failure_regressions']), 'retained claim regression not reproduced; report preserved')
    require(all(row['functional_tests']=='PASS' for row in value['matrix']),
            'bounded behavioral checks failed or did not complete; report preserved')
