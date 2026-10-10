"""Replay source-supported native outputs; qualification still needs review."""
import argparse
import json
from pathlib import Path
import subprocess
from hashlib import sha256
from myskills.cohort_assessment import seal,file_digest
from myskills.digest import digest_object
from qualification.checkpoint_four import require,unseal
from qualification.checkpoint_six import boundaries,composition
from qualification.v5.replay import native_complete,replay_entries
from qualification.v7.probe import context,binding,prompt
from qualification.v7.cases import CASES,POLICY,SNAPSHOTS
from qualification.v7.evaluate import assess
from qualification.v7.evaluate import authenticated_facts
from qualification.v5.policy import executor,allowed
from qualification.v5.evaluate import clean
from qualification.workflow_probe import normalized

BASE='3c975f3df6cfd973d5d42b45c64565c1171dcdc8'


def transcript_digest(directory,record):
    path=directory/'native.jsonl'
    if not path.exists():
        require(record['generation']!='COMPLETED','completed capture lacks native transcript')
        return None
    return file_digest(path)


def evaluator_controls(root):
    controls=json.loads((root/'qualification/checkpoint7/evaluator-counterexamples.json').read_text());unseal(controls)
    rows=[]
    for skill,case in controls['fixtures'].items():
        fixture=CASES[skill+'--representative'];run=executor(skill)
        original=run(fixture['files'],fixture['commands']['test'],fixture['writable'])
        observed=authenticated_facts(skill,original)
        require(observed is not None and all(observed.values()) and original['exit_code']==0,'positive evaluator control failed')
        files={**fixture['files'],case['path']:case['candidate']}
        require(allowed(skill,files),'counterexample no longer reaches the qualified runtime')
        result=run(files,fixture['commands']['test'],fixture['writable'])
        require(clean(result) and type(result['exit_code']) is int and result['exit_code']!=0,'shared-process verifier regression escaped')
        rows.append({'skill':skill,'positive':normalized(original),'counterexample':normalized(result),'status':'PASS'})
    return seal({'status':'PASS','fixture_digest':controls['evidence_digest'],'results':rows,'native_model_credit':False})


def case_status(complete,evaluation,review,adverse):
    if not complete:return 'PARTIAL'
    return 'PASS' if evaluation=='PASS' and review=='PASS' and adverse is None else 'FAIL'


def report(root,retained,previous,initial=None):
    from qualification.custody_v5 import bundle
    from qualification.custody_v7 import bundle as native_bundle
    context_fn,binding_fn,prompt_fn,cases=context,binding,prompt,CASES
    record_path=root/'qualification/checkpoint7'
    prior_native_digest=None
    if initial is not None:
        from qualification.v7r1.probe import context as context_fn,binding as binding_fn,prompt as prompt_fn
        from qualification.v7r1.cases import CASES as cases,INPUTS
        from qualification.custody_v7r1 import bundle as successor_bundle
        initial_pin=json.loads((record_path/'evidence-pin.json').read_text())
        prior_native_digest=digest_object(native_bundle(initial))
        require(prior_native_digest==initial_pin['bundle_digest'],'feedback predecessor custody changed')
        unseal(INPUTS)
        for skill,item in INPUTS['initial_cases'].items():
            old=json.loads((initial/item['case']/'observation.json').read_text());unseal(old)
            require(old['generation']=='COMPLETED' and old['binding']['skill']['skill_id']==skill,'unestablished successor starting source')
            require(item=={'case':skill+'--representative','observation_digest':old['evidence_digest'],
                           'binding':old['binding'],'files':old['files']},'feedback input source changed')
        native_bundle=successor_bundle;record_path=record_path/'followup'
    prior_pin=json.loads((root/'qualification/checkpoint5/followup-evidence-pin.json').read_text())
    require(digest_object(bundle(previous))==prior_pin['bundle_digest']==SNAPSHOTS['origin_bundle'],'prior evidence custody changed')
    unseal(SNAPSHOTS)
    for skill,item in SNAPSHOTS['skills'].items():
        old=json.loads((previous/(skill+'--follow-up')/'observation.json').read_text());unseal(old)
        require(item=={'observation_digest':old['evidence_digest'],'collector_commit':old['collector_commit'],
                       'binding':old['binding'],'files':old['files']},'correction inputs differ from retained source')
    expected=context_fn(root);ctx=json.loads((retained/'context.json').read_text())
    require(ctx==expected,'native context differs from current frozen source')
    native_pin=json.loads((record_path/'evidence-pin.json').read_text())
    require(digest_object(native_bundle(retained))==native_pin['bundle_digest'],'checkpoint7 native custody changed')
    completion=json.loads((retained/'completion.json').read_text());unseal(completion)
    require(completion['cases']==list(cases),'native cohort differs')
    admitted=completion['runtime_identity']=='STABLE' and completion['all_results_admissible'] is True and completion['halt'] is None
    review=json.loads((record_path/'output-review.json').read_text());unseal(review)
    review_pin=json.loads((record_path/'output-review-pin.json').read_text())
    require(file_digest(record_path/'output-review.json')==review_pin['review_file_digest'],'independent output review differs')
    require(review_pin['context_digest']==digest_object(ctx) and review_pin['completion_digest']==completion['evidence_digest'], 'review batch binding differs')
    require(set(review['cases'])==set(review_pin['case_observations'])==set(cases),'review case set differs')
    for path,digest in review_pin['verifier_sources'].items():require(file_digest(root/path)==digest,'reviewed verifier source changed')
    required_sources={**ctx['harness'],**ctx['claim_verifier'],
                      'qualification/evaluator_successor_v5.py':ctx['historical_evaluator_digest']}
    require(all(review_pin['verifier_sources'].get(path)==digest for path,digest in required_sources.items()),'review omits qualification dependency')
    require(all(path in review_pin['verifier_sources'] for path in ('qualification/checkpoint_seven.py','qualification/checkpoint_six.py','qualification/custody_v5.py','qualification/custody_v7.py','qualification/checkpoint7/evaluator-counterexamples.json','qualification/checkpoint7/hosted-counterexample.json')),'report review binding missing')
    if initial is not None:require('qualification/custody_v7r1.py' in review_pin['verifier_sources'],'successor custody source pin missing')
    accepted_path='qualification/checkpoint5/accepted-profile.json'
    for path in (accepted_path,'qualification/initial-cohort/plan.json','qualification/checkpoint5/consumer-compatibility.json'):
        require((root/path).read_bytes()==subprocess.check_output(['git','show',BASE+':'+path],cwd=root),'historical qualification or dependency graph changed')
    accepted=json.loads((root/accepted_path).read_text());unseal(accepted)
    adverse=json.loads((root/'qualification/checkpoint7/hosted-counterexample.json').read_text());unseal(adverse)
    require(adverse['result']=='CONTRADICTED' and adverse['qualification_credit'] is False,'invalid adverse evidence')
    rows=[]
    for name,fixture in cases.items():
        directory=retained/name;record=json.loads((directory/'observation.json').read_text());unseal(record)
        require(record['binding']==binding_fn(ctx,name) and record['execution_eligible'] is False,'native profile binding changed')
        commit=record['collector_commit']
        require(commit==review_pin['collector_commit']==native_pin['collector_commit'],'collector commit differs')
        require(record['evidence_digest']==review_pin['case_observations'][name],'review observation differs')
        for path,digest in required_sources.items():
            raw=subprocess.check_output(['git','show',commit+':'+path],cwd=root)
            require('sha256:'+sha256(raw).hexdigest()==digest,'collector source does not match committed identity')
        trial_complete=admitted and record['generation']=='COMPLETED' and record.get('trial_identity')=='PRE_POST_CHECKED'
        native_ok=native_complete(directory,record,fixture)
        if trial_complete:require(native_ok,'native completion mismatch')
        if trial_complete:
            require(json.loads((directory/'prompt.json').read_text())=={'policy':POLICY,'prompt':prompt_fn(root,ctx,name)},'native Skill prompt changed')
            replay_entries(fixture,record,directory)
            evaluated=assess(fixture,record)
            require(evaluated==record['verification'],'independent profile evaluation differs')
        else:evaluated={'status':'NOT_RUN','reason':'incomplete batch; no credit'}
        opinion=review['cases'][name]
        transcript=transcript_digest(directory,record)
        require(opinion['observation_digest']==record['evidence_digest'] and opinion['native_transcript_digest']==transcript,'output review binding differs')
        counter=adverse['affected_observations'].get(record['evidence_digest'])
        if counter:
            require(counter['source_digest']==digest_object(record['files']['api.py']) and counter['binding_digest']==digest_object(record['binding']),'counterevidence source mismatch')
        status=case_status(trial_complete,evaluated['status'],opinion['status'],counter)
        rows.append(seal({'binding':record['binding'],'observation_digest':record['evidence_digest'],'native_transcript_digest':transcript,'generation':record['generation'],
                          'collector_commit':commit,'evaluation':evaluated,'captured_verification':record.get('verification'),
                          'batch_admission':'ADMITTED' if admitted else 'WITHHELD','adverse_evidence':adverse['evidence_digest'] if counter else None,'output_review':opinion,'status':status,'execution_eligible':False}))
    profiles={}
    for skill in SNAPSHOTS['skills']:
        children=[r for r in rows if r['binding']['skill']['skill_id']==skill]
        status='PASS' if all(r['status']=='PASS' for r in children) else 'PARTIAL' if any(r['status']=='PARTIAL' for r in children) else 'FAIL'
        profiles[skill]=seal({'profile':skill+('-review-assisted-offline-v1' if initial is not None else '-source-supported-offline-v1'),'status':status,'bindings':[r['binding'] for r in children],
                              'case_evidence':[r['evidence_digest'] for r in children],'scope':'Exact representative and adversarial correction fixtures only; protected synthetic gateway integration, no real provider or released consumer qualification.',
                              'reviewer_feedback_assistance':initial is not None,'starting_native_bundle':prior_native_digest,
                              'acceptance':'PENDING_FRESH_HOSTED_VALIDATION' if status=='PASS' else 'NOT_QUALIFIED',
                              'execution_eligible':False,'global_trust':'UNTRUSTED'})
    graph=composition(json.loads((root/'qualification/initial-cohort/plan.json').read_text()),accepted)
    prior=json.loads((root/'qualification/checkpoint5/consumer-compatibility.json').read_text());unseal(prior)
    consumers={name:seal({'consumer':name,'accepted_tdd_reference':old['qualification_reference'],'exact_tdd_binding':old['exact_binding'],
                          'api_security_profile_references':{skill:p['evidence_digest'] for skill,p in profiles.items()},
                          'api_security_bindings':{skill:p['bindings'] for skill,p in profiles.items()},
                          'activation':'DISABLED','execution_eligible':False,'consumer_compatibility':'NOT_ESTABLISHED',
                          'source_inspection_reference':old['consumer_source_reference'],'required_next_check':old['required_next_check'],
                          'consumer_repository_modified':False}) for name,old in prior['consumers'].items()}
    return seal({'schema':'myskills.checkpoint.v7','base_commit':BASE,'context_digest':digest_object(ctx),'completion':completion,
                 'retained_hosted_counterexample':adverse,'matrix':rows,'profiles':profiles,'composition':graph,'consumers':consumers,'controls':boundaries(),'evaluator_controls':evaluator_controls(root),
                 'accepted_tdd_profile':accepted['evidence_digest'],'historical_tdd_changed':False,
                 'new_profile_candidates':sum(p['status']=='PASS' for p in profiles.values()),'accepted_behavioral_profiles':1,
                 'acceptance_rule':'New PASS candidates need a separate matching fresh-clone and hosted validation receipt before acceptance.',
                 'globally_trusted_skills':0,'catalog_trust':'UNTRUSTED','catalog_qualification':'NOT_EVALUATED',
                 'paid_operations':0,'production_integration':'NOT_RUN','external_alpha_impact':'NONE','marketplace_activation':'DISABLED','greptile':'DEFERRED'})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--retained',type=Path,required=True);parser.add_argument('--previous',type=Path,required=True);parser.add_argument('--initial',type=Path);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();value=report(Path.cwd(),args.retained,args.previous,args.initial);args.output.mkdir(parents=True,exist_ok=False)
    exports={'checkpoint':value,'matrix':value['matrix'],'profiles':value['profiles'],'composition':value['composition'],**value['consumers']}
    for name,data in exports.items():(args.output/(name+'.json')).write_text(json.dumps(data,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'evidence_digest':value['evidence_digest'],'profiles':{k:v['status'] for k,v in value['profiles'].items()}}))
