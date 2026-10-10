"""Replay checkpoint-3 evidence and export scoped, non-activating decisions."""
import argparse
import json
from pathlib import Path
from myskills.cohort_assessment import assess,seal,file_digest
from myskills.digest import digest_object
from myskills.manifest import ValidationError
from qualification.native_probe import replay,harness
from qualification.workflow_probe import normalized
from qualification.native_cases import CASES,NATIVE_UNAVAILABLE
from qualification.native_controls import controls
from qualification.custody_v3 import bundle,PIN
from qualification.isolation_check import verify_isolation
from qualification.output_review import review


def decisions(static,trials,ctx,pin,output_review=None):
    output_review=output_review or {"findings":[],"qualification_approvals":[]}
    values=[]
    for spec in static['skills']:
        skill=spec['binding']['skill_id'];cases=[v for v in trials if v['binding']==spec['binding']]
        if len(cases)!=2:raise ValidationError('incomplete exact cohort observations')
        stable=all(v['runtime_admissible'] for v in cases)
        passes=stable and all(v['verification']['bounded_workflow']=='PASS' for v in cases)
        failed=stable and any(v['verification']['bounded_workflow']=='FAIL' for v in cases)
        gaps=[NATIVE_UNAVAILABLE[skill]] if skill in NATIVE_UNAVAILABLE else []
        findings=[f for f in output_review['findings'] if f['binding']==spec['binding']]
        for finding in findings:
            if not any(t['case']==finding['case'] and t['observation_digest']==finding['observation_digest'] for t in cases):raise ValidationError('output review binding mismatch')
        failed=failed or any(f['status']=='FAIL' for f in findings)
        approved=spec['binding'] in output_review['qualification_approvals']
        qualified=passes and not gaps and not failed and approved
        status='NARROW_BEHAVIORAL_PASS' if qualified else 'FAIL' if failed else 'PARTIAL'
        values.append(seal({'schema':'myskills.behavioral-decision.v3','binding':spec['binding'],
            'status':status,'scope':CASES[skill]['scope'],'scope_qualified':qualified,
            'full_skill_qualification':'NOT_ESTABLISHED','catalog_trust':'UNTRUSTED','catalog_qualification':'NOT_EVALUATED',
            'execution_eligible':False,'production_effects':[],'consumer_admission':'NOT_RUN',
            'trial_results':cases,'native_command_workflow_pair_pass':passes,'remaining_workflow_gates':gaps,
            'independent_output_review_findings':findings,'output_review_approved':approved,
            'provenance':spec['provenance'],'intended_capabilities':spec['task_specification']['myapps_capabilities'],
            'dependencies':spec['task_specification']['source_reference_bindings'],
            'dependency_execution':'NOT_RUN','runtime_digest':digest_object(ctx['runtime']),
            'harness_digest':digest_object(ctx['harness']),'fixture_digest':ctx['fixtures_digest'],
            'collector_commit':pin['collector_commit'],'measurement_normalization':'Unittest duration and ephemeral traceback directory only; original bytes remain in custody','evidence_bundle_digest':pin['bundle_digest'],
            'limits':['Two scoped cases do not establish general Skill reliability or inference determinism.',
                      'Native Python/Node/SQLite commands in the test adapter; Codex/Cursor provider workflows NOT_RUN.',
                      'No consumer execution grant or production integration.',
                      'Database fault checks cover the injected SQLite update failure, not process crash/power-loss recovery.',
                      'Only the retained API duplicate-race claim receives a supplemental concurrency check; broader concurrency and full syscall auditing NOT_RUN.']}))
    return values


def report(root,retained):
    pin=json.loads((root/PIN).read_text())
    if digest_object(bundle(retained))!=pin['bundle_digest']:raise ValidationError('checkpoint3 custody mismatch')
    trials=normalized(replay(root,retained,pin['collector_commit']))
    ctx=json.loads((retained/'context.json').read_text());completion=json.loads((retained/'completion.json').read_text())
    static=assess(root);expected=json.loads((root/'qualification/initial-cohort/assessment-pin.json').read_text())
    if static['evidence_digest']!=expected['evidence_digest']:raise ValidationError('foundation assessment changed')
    checked=controls();isolation=verify_isolation();output_review=review(root,retained)
    skills=decisions(static,trials,ctx,pin,output_review)
    refs=[{'binding':s['binding'],'status':s['status'],'scope':s['scope'],'scope_qualified':s['scope_qualified'],
           'catalog_trust':s['catalog_trust'],'execution_eligible':False,'permitted_effects':[],
           'decision_file':'skills/'+s['binding']['skill_id']+'.json','decision_digest':s['evidence_digest'],
           'runtime_digest':s['runtime_digest'],'harness_digest':s['harness_digest'],
           'evidence_bundle_digest':pin['bundle_digest'],'intended_capabilities':s['intended_capabilities']} for s in skills]
    consumers={name:{'schema':'myskills.consumer-compatibility.v3','consumer':name,'references':refs,
                    'activation':'DISABLED','ready_skills':[],'consumer_schema_validation':'NOT_RUN',
                    'consumer_changes':0,'production_execution':False} for name in
                    ['MyApps','MissionControl','MyEve-Sofie-subagents','Role-Packs','MyFactory']}
    consumers['MyApps']['outside_cohort']=static['myapps']['outside_cohort']
    consumers['MissionControl']['orchestration']='Owned by MissionControl; MySkills exports evidence references only'
    consumers['Role-Packs']['custody']='No persistent production owner Skill custody created'
    composition={**static['composition'],'status':'PARTIAL','execution':'NOT_RUN_INELIGIBLE_CHILDREN','executed_stages':0,
                 'publication':'UNAUTHORIZED','actual_stage_output_authentication':'NOT_RUN','actual_failure_stop':'NOT_RUN',
                 'protected_composition_verification':'NOT_RUN','reason':'Complete role eligibility is not established by narrow fixture passes.',
                 'missing_capabilities':[]}
    roles=['Repository Analysis','Implementation','Tests','Code Review','Independent Verification']
    for role,stage in zip(roles,composition['proposal']['stages']):
        s=next(s for s in skills if s['binding']==stage['skill'])
        if not s['scope_qualified']:
            composition['missing_capabilities'].append({'role':role,'binding':s['binding'],'status':s['status'],'gaps':s['remaining_workflow_gates']})
    return seal({'schema':'myskills.behavioral-checkpoint.v3','runtime_stability':completion['runtime_identity'],
        'runtime_completion':completion,'model_digest':ctx['runtime']['model_digest'],'runtime':ctx['runtime'],
        'harness':ctx['harness'],'harness_digest':digest_object(ctx['harness']),
        'replay_harness':harness(root),'replay_harness_digest':digest_object(harness(root)),
        'supplemental_output_review':output_review,
        'checkpoint_verifier_digest':file_digest(root/'qualification/checkpoint_three.py'),
        'evaluator_control_digest':file_digest(root/'qualification/native_controls.py'),
        'foundation_sha':static['foundation_sha'],'canonical_source_sha':static['canonical_source_sha'],
        'catalog_count':92,'manifest_count':92,'custody_pin':pin,'skills':skills,'trials':trials,
        'tool_trials_total':len(trials),'tool_trials_finished':sum(t['finished'] for t in trials),
        'native_command_workflows_passed':sum(t['verification']['bounded_workflow']=='PASS' for t in trials),
        'native_agent_provider_workflows':'NOT_RUN','narrow_behaviorally_qualified':sum(s['scope_qualified'] for s in skills),
        'controls':checked,'isolation':isolation,'composition':composition,'consumers':consumers,
        'original_evidence':'PRESERVED','failure_analysis':json.loads((root/'qualification/checkpoint3/failure-analysis.json').read_text()),
        'native_failure_analysis':json.loads((root/'qualification/checkpoint3/native-findings.json').read_text()),
        'docker_reconciliation':json.loads((root/'qualification/checkpoint3/reconciliation.json').read_text()),
        'paid_operations':0,'production_integration':'NOT_RUN','external_alpha_impact':'NONE','marketplace':'DISABLED',
        'automatic_promotion':'DISABLED','greptile':'DEFERRED'})


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--retained',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1];value=report(root,args.retained)
    args.output.mkdir(parents=True,exist_ok=True);(args.output/'skills').mkdir(exist_ok=True)
    for s in value['skills']:(args.output/'skills'/(s['binding']['skill_id']+'.json')).write_text(json.dumps(s,indent=2,sort_keys=True)+'\n')
    for name,consumer in value['consumers'].items():(args.output/(name+'.json')).write_text(json.dumps(consumer,indent=2,sort_keys=True)+'\n')
    (args.output/'checkpoint.json').write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'evidence_digest':value['evidence_digest'],'runtime':value['runtime_stability'],
        'finished':value['tool_trials_finished'],'native_command_workflows_passed':value['native_command_workflows_passed'],
        'qualified':value['narrow_behaviorally_qualified'],'skills':{s['binding']['skill_id']:s['status'] for s in value['skills']}}))

if __name__=='__main__':main()
