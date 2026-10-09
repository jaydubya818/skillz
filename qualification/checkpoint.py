"""Assemble independently rechecked, non-promoting cohort decisions."""
import argparse
import json
from pathlib import Path

from myskills.cohort_assessment import assess, file_digest, seal
from myskills.digest import digest_object
from myskills.manifest import ValidationError
from qualification.isolation_check import verify_isolation
from qualification.local_probe import replay

PIN_DIRECTORY = Path('qualification/initial-cohort')


def behavioral_status(attempts):
    verified = any(a['model_execution'] == 'COMPLETED' and
                   a['artifact_verification'] == 'COMPLETED' for a in attempts)
    return 'PARTIAL' if verified else 'NOT_RUN'


def checkpoint(root, observations):
    pin = json.loads((root/PIN_DIRECTORY/'observations-pin.json').read_text())
    replays = replay(root,observations,pin['bundle_digest'],pin['collector_commit'])
    static = assess(root)
    assessment_pin = json.loads((root/PIN_DIRECTORY/'assessment-pin.json').read_text())
    if static['evidence_digest'] != assessment_pin['evidence_digest']:
        raise ValidationError('assessment differs from reviewed pin')
    isolation = verify_isolation()
    decisions = []
    for item in static['skills']:
        skill_id = item['binding']['skill_id']
        attempts = []
        for kind in ('representative','adversarial'):
            name = skill_id + '--' + kind
            observation = json.loads((observations/name/'observation.json').read_text())
            attempts.append({'kind':kind,'binding':observation['binding'],
                'model_execution':observation['model_execution'],
                'artifact_verification':observation['artifact_verification'],
                'runtime_identity':('VERIFIED' if observation['artifact_verification']=='COMPLETED' else
                    'UNVERIFIED' if observation['model_execution']=='COMPLETED' else 'NOT_RUN'),
                'error':observation.get('error'),
                'artifact_oracle':observation.get('observations',{}).get('artifact_oracle','NOT_RUN'),
                'effect_request_check':observation.get('observations',{}).get('effect_request_check','NOT_RUN'),
                'observation_digest':observation['evidence_digest'], 'file':name+'/observation.json'})
        decisions.append(seal({'schema':'myskills.cohort-decision.v1',
            'evidence_kind':'BOUNDED_PARTIAL_OBSERVATIONS_NOT_QUALIFICATION',
            'binding':item['binding'],'provenance':item['provenance'],
            'capabilities':item['task_specification']['myapps_capabilities'],
            'intended_capability':item['task_specification']['intended_capability'],
            'current_permitted_effects':[],
            'test_adapter_effects':['synthetic.artifact.produce','offline.container.evaluate'],
            'behavioral_qualification':behavioral_status(attempts),
            'catalog_qualification':'NOT_EVALUATED','trust':'UNTRUSTED','execution_eligible':False,
            'full_workflow':'NOT_RUN','native_harness_compatibility':'NOT_RUN',
            'packaging':'PASS','assessment_digest':item['evidence_digest'],
            'observations_bundle_digest':pin['bundle_digest'],'attempts':attempts,
            'dependency_bindings':item['task_specification']['source_reference_bindings'],
            'dependency_execution':'NOT_RUN',
            'scope':json.loads((observations/(skill_id+'--representative')/'observation.json').read_text())['scope']}))
    composition = static['composition']
    return seal({'schema':'myskills.initial-qualification-checkpoint.v1',
        'evidence_kind':'BOUNDED_PARTIAL_OBSERVATIONS_NOT_QUALIFICATION',
        'foundation_sha':static['foundation_sha'],'canonical_source_sha':static['canonical_source_sha'],
        'assessment_digest':static['evidence_digest'],'observations_pin':pin,
        'checkpoint_verifier_digest':file_digest(root/'qualification/checkpoint.py'),
        'replay_verifier_digest':file_digest(root/'qualification/local_probe.py'),
        'runtime_drift':json.loads((root/PIN_DIRECTORY/'model-drift.json').read_text()),
        'interrupted_attempt':json.loads((root/PIN_DIRECTORY/'interruption.json').read_text()),
        'runtime':json.loads((observations/'runtime.json').read_text()),
        'catalog_count':92,'manifest_count':92,'deep_qualified':0,
        'skills':decisions,'composition':composition,'isolation':isolation,'replays':replays,
        'myapps':{'ready_skills':[], 'candidates':[
            {'binding':s['binding'],'capabilities':s['capabilities'],'execution_eligible':False,
             'behavioral_qualification':s['behavioral_qualification'],'trust':s['trust'],
             'decision_file':'skills/'+s['binding']['skill_id']+'.json','decision_digest':s['evidence_digest']}
            for s in decisions], 'outside_cohort':static['myapps']['outside_cohort']},
        'paid_operations':0,'production_integration':'NOT_RUN','external_alpha_impact':'NONE',
        'publication':'UNAUTHORIZED',
        'limitations':[
            'All normal platform admissions remain denied; test-only observations grant no authority.',
            'Artifact predicates do not establish the full Skill workflows or native agent compatibility.',
            'Replaying retained bytes is deterministic verification, not deterministic model inference.',
            'Container controls do not establish kernel escape resistance or audit every attempted syscall.',
            'Hashes bind retained observations, not cryptographic model authorship.',
            'No qualified-member software composition can run until its child qualification gates pass.']})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--observations',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    report=checkpoint(root,args.observations)
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'skills').mkdir(exist_ok=True)
    for item in report['skills']:
        (args.output/'skills'/(item['binding']['skill_id']+'.json')).write_text(json.dumps(item,indent=2,sort_keys=True)+'\n')
    (args.output/'checkpoint.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    (args.output/'myapps.json').write_text(json.dumps(report['myapps'],indent=2,sort_keys=True)+'\n')
    print(json.dumps({'deep_qualified':report['deep_qualified'],'composition':report['composition']['status'],
        'replayed_attempts':len([r for r in report['replays'] if r['replay']=='PASS']),
        'artifact_passes':len([r for r in report['replays'] if r.get('artifact_oracle')=='PASS']),
        'artifact_failures':len([r for r in report['replays'] if r.get('artifact_oracle')=='FAIL']),
        'evidence_digest':report['evidence_digest']}))


if __name__=='__main__':
    main()
