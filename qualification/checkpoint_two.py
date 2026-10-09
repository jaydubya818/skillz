"""Recheck both qualification layers and export non-promoting consumer references."""
import argparse
import json
from pathlib import Path

from myskills.cohort_assessment import assess, seal, file_digest
from myskills.digest import digest_object
from myskills.manifest import ValidationError
from qualification import behavior_v2, workflow_probe
from qualification.custody_v2 import PIN, bundle
from qualification.isolation_check import verify_isolation


def report(root, retained):
    pin=json.loads((root/PIN).read_text())
    if digest_object(bundle(retained/'artifacts',retained/'workflows'))!=pin['bundle_digest']:
        raise ValidationError('checkpoint 2 evidence differs from committed custody pin')
    artifacts=behavior_v2.replay(root,retained/'artifacts',pin['artifact_collector_commit'])
    workflows=workflow_probe.replay(root,retained/'workflows',pin['workflow_collector_commit'])
    workflow_completion=json.loads((retained/'workflows/completion.json').read_text())
    static=assess(root)
    expected=json.loads((root/'qualification/initial-cohort/assessment-pin.json').read_text())
    if static['evidence_digest']!=expected['evidence_digest']:
        raise ValidationError('foundation assessment changed')
    isolation=verify_isolation()
    artifact_context=json.loads((retained/'artifacts/context.json').read_text())
    decisions=[]
    for result in artifacts:
        skill=result['binding']['skill_id']
        spec=next(s for s in static['skills'] if s['binding']['skill_id']==skill)
        tools=[w for w in workflows if w['binding']==result['binding']]
        used_tools=any(w['tool_steps'] for w in tools)
        failed=any(a['artifact_oracle']=='FAIL' or a['effect_request_check']=='FAIL' for a in result['attempts']) or any(w['runtime_admissible'] and w['verification']['bounded_workflow']=='FAIL' for w in tools)
        decisions.append(seal({'schema':'myskills.behavioral-decision.v2','binding':result['binding'],
            'provenance':spec['provenance'],'capabilities':spec['task_specification']['myapps_capabilities'],
            'intended_capability':spec['task_specification']['intended_capability'],
            'dependencies':spec['task_specification']['source_reference_bindings'],
            'dependency_execution':'NOT_RUN','current_permitted_effects':[],
            'behavioral_status':'FAIL' if failed else 'PARTIAL','trust':'UNTRUSTED',
            'catalog_qualification':'NOT_EVALUATED','execution_eligible':False,
            'layer_a':{'package_loading':'PASS','manifest_integrity':'PASS','digest_binding':'PASS',
                'static_dependency_resolution':'PASS','authority_admission':'DENIED_AS_REQUIRED',
                'tool_restrictions':'PASS_TEST_SCOPE','container_isolation':'PASS_TEST_SCOPE',
                'revocation':'PASS_ADMISSION_SCOPE','custody':'PASS_PINNED_BYTES',
                'result_identity':'PASS_OBSERVED_RUNTIME','model_authorship_attestation':'NOT_ESTABLISHED'},
            'layer_b':{'artifact_experiment':result,'tool_fixtures':tools,
                'tool_selection':'OBSERVED_UNVERIFIED_BATCH' if used_tools and not workflow_completion['all_results_admissible'] else 'SEE_CASE_VERDICTS' if used_tools else 'NOT_RUN',
                'failure_handling':'SEE_CASE_VERDICTS_WITH_RUNTIME_LIMITS' if used_tools else 'NOT_RUN',
                'model_repeat_output_equal':result['repeat_output_equal'],
                'general_inference_determinism':'NOT_ESTABLISHED','full_skill_workflow':'NOT_RUN',
                'native_harness_compatibility':'NOT_RUN'},
            'evidence_bundle_digest':pin['bundle_digest'],
            'runtime_digest':digest_object(artifact_context['runtime']),
            'artifact_harness_digest':digest_object(artifact_context['harness']),
            'limitations':['Passing infrastructure does not qualify Skill behavior.',
                'Behavioral FAIL means a retained scoped case failed; it does not attribute root cause to Skill instructions.',
                'Passing a bounded tool fixture does not establish all dependencies, runtime portability or production quality.']}))
    refs=[{'binding':s['binding'],'capabilities':s['capabilities'],'behavioral_status':s['behavioral_status'],
           'trust':s['trust'],'execution_eligible':False,'permitted_effects':[],
           'decision_file':'skills/'+s['binding']['skill_id']+'.json','decision_digest':s['evidence_digest'],
           'runtime_digest':s['runtime_digest'],'artifact_harness_digest':s['artifact_harness_digest'],
           'evidence_bundle_digest':pin['bundle_digest']} for s in decisions]
    myapps={'schema':'myskills.myapps-compatibility.v2','consumer_context':'Owner reports Checkpoint I complete; independent review pending',
        'ready_skills':[],'references':refs,'outside_cohort':static['myapps']['outside_cohort'],
        'consumer_schema_validation':'NOT_RUN','consumer_changes':0,'activation':'DISABLED',
        'architecture_limit':'figure-it-out supplies analysis evidence, not a qualified application architecture Skill',
        'required_gaps':['Durable API concurrency/recovery','Disposable database crash/restart migration',
            'Browser/keyboard/accessibility checks','Security boundary and leakage audit',
            'Hosted generated workflow failure propagation','Full dependency and native runtime qualification']}
    mission={'schema':'myskills.missioncontrol-compatibility.v1','consumer_changes':0,
        'consumer_schema_validation':'NOT_RUN','execution_eligible':False,'ready_skills':[],
        'references':refs,'surfaces':{name:{'contract':'Exact binding plus decision/evidence digest, effect ceiling and runtime compatibility; admission denied until consumer validates qualification',
                                        'activation':'DISABLED'} for name in
            ['EngineeringRolePacks','SpecializedAgents','MultiAgentCompositions','FactoryWorkOrders','IndependentVerification','EnterpriseQualityContracts']},
        'orchestration':'Owned by MissionControl; MySkills exports package and evidence references only'}
    return seal({'schema':'myskills.behavioral-checkpoint.v2','runtime_identity':workflow_completion['runtime_identity'],
        'artifact_runtime_identity':'STABLE_OBSERVED_BATCH','workflow_completion':workflow_completion,
        'runtime':json.loads((retained/'artifacts/context.json').read_text())['runtime'],
        'harness':json.loads((retained/'artifacts/context.json').read_text())['harness'],
        'workflow_harness':json.loads((retained/'workflows/context.json').read_text())['harness'],
        'checkpoint_verifier_digest':file_digest(root/'qualification/checkpoint_two.py'),
        'custody_pin':pin,'foundation_sha':static['foundation_sha'],'canonical_source_sha':static['canonical_source_sha'],
        'original_failures':'PRESERVED','failure_analysis':json.loads((root/'qualification/checkpoint2/failure-analysis.json').read_text()),
        'migration_investigation':json.loads((root/'qualification/checkpoint2/migration-investigation.json').read_text()),
        'container_interruption':json.loads((root/'qualification/checkpoint2/container-interruption.json').read_text()),
        'catalog_count':92,'manifest_count':92,'skills_evaluated':len(decisions),'behaviorally_qualified':0,
        'skills':decisions,'isolation':isolation,'composition':{**static['composition'],
            'status':'PARTIAL','execution':'NOT_RUN_INELIGIBLE_CHILDREN','executed_stages':0,
            'reason':'Every child remains behaviorally unqualified; artifact evidence does not authorize composed execution.',
            'actual_stage_output_authentication':'NOT_RUN','actual_failure_stop':'NOT_RUN',
            'protected_composition_verification':'NOT_RUN','publication':'UNAUTHORIZED'},
        'myapps':myapps,'missioncontrol':mission,'paid_operations':0,'production_integration':'NOT_RUN',
        'external_alpha_impact':'NONE','marketplace':'DISABLED','automatic_promotion':'DISABLED',
        'limits':['Only the completed artifact batch has stable observed runtime identity; the interrupted tool batch receives no qualification credit.',
                  'Runtime observations assume a trusted local host and service.',
                  'Hashes authenticate retained bytes, not cryptographic model authorship.',
                  'Five individual tool fixtures do not establish five-stage composition execution.',
                  'No consumer schema, live production integration or application readiness is established.']})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--retained',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    value=report(root,args.retained)
    args.output.mkdir(parents=True,exist_ok=True);(args.output/'skills').mkdir(exist_ok=True)
    for item in value['skills']:
        (args.output/'skills'/(item['binding']['skill_id']+'.json')).write_text(json.dumps(item,indent=2,sort_keys=True)+'\n')
    for name,data in [('checkpoint',value),('myapps',value['myapps']),('missioncontrol',value['missioncontrol'])]:
        (args.output/(name+'.json')).write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'evidence_digest':value['evidence_digest'],'evaluated':len(value['skills']),
        'qualified':0,'skills':{s['binding']['skill_id']:s['behavioral_status'] for s in value['skills']}}))


if __name__=='__main__':main()
