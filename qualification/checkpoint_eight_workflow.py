"""Strict replay of the versioned, explicitly assisted checkpoint-8 profiles."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from typing import Any

from myskills.cohort_assessment import file_digest, seal
from myskills.digest import digest_object
from qualification.behavior_v2 import save
from qualification.checkpoint_four import require, unseal
from qualification.checkpoint_six import composition
from qualification.custody_v8 import bundle
from qualification.history_v8 import BASE, unchanged
from qualification.replay_v8 import replay_entries
from qualification.v5.replay import native_complete
from qualification.v8.cases import INPUTS, POLICY
from qualification.workflow_correction_v8 import CASES
from qualification.v8.controls import adapter_controls, verifier_controls
from qualification.v8.evaluate import assess
from qualification.workflow_correction_v8 import binding, context, prompt


REPORT_SOURCES = (
    'qualification/checkpoint_eight_workflow.py', 'qualification/workflow_correction_v8.py', 'qualification/checkpoint_eight_successor.py', 'qualification/checkpoint_eight.py', 'qualification/replay_v8.py',
    'qualification/history_v8.py', 'qualification/checkpoint_six.py',
    'qualification/runtime_successor_v8.py', 'qualification/successor_probe_v8.py', 'qualification/recovery_probe_v8.py', 'qualification/custody_guard.py',
    'qualification/custody_v8.py', 'qualification/custody_v7r1.py',
)


def source_bindings(root: Path, ctx: dict[str, Any]) -> dict[str, str]:
    return {**ctx['harness'], **ctx['claim_verifier'],
            'qualification/evaluator_successor_v5.py': ctx['historical_evaluator_digest'],
            **{name: file_digest(root/name) for name in REPORT_SOURCES}}


def verify_starting_source(root: Path, previous: Path) -> str:
    from qualification.custody_v7r1 import bundle as old_bundle
    pin = json.loads((root/'qualification/checkpoint7/followup/evidence-pin.json').read_text())
    digest = digest_object(old_bundle(previous))
    require(digest == pin['bundle_digest'] == INPUTS['bundle_digest'], 'starting source custody changed')
    unseal(INPUTS)
    for skill, item in INPUTS['skills'].items():
        old = json.loads((previous/(skill+'--representative')/'observation.json').read_text())
        unseal(old)
        require(old['generation'] == 'COMPLETED', 'starting source was not a completed native observation')
        require(item == {'observation_digest': old['evidence_digest'], 'binding': old['binding'],
                         'collector_commit': old['collector_commit'], 'files': old['files']}, 'starting source binding differs')
    return digest


def report(root: Path, retained: Path, previous: Path, output: Path) -> dict[str, Any]:
    (output/'assessments').mkdir(exist_ok=False)
    previous_digest = verify_starting_source(root, previous)
    historical = unchanged(root)
    ctx = json.loads((retained/'context.json').read_text())
    require(ctx == context(root), 'native context differs from frozen source')
    location = root/'qualification/checkpoint8/workflow-correction'
    pin = json.loads((location/'evidence-pin.json').read_text())
    require(digest_object(bundle(retained)) == pin['bundle_digest'], 'native custody changed')
    completion = json.loads((retained/'completion.json').read_text())
    unseal(completion)
    require(completion['cases'] == list(CASES), 'native cohort differs')
    admitted = completion['runtime_identity'] == 'STABLE' and completion['all_results_admissible'] is True and completion['halt'] is None
    review = json.loads((location/'output-review.json').read_text())
    unseal(review)
    review_pin = json.loads((location/'output-review-pin.json').read_text())
    require(file_digest(location/'output-review.json') == review_pin['review_file_digest'], 'output review changed')
    require(review_pin['context_digest'] == digest_object(ctx)
            and review_pin['completion_digest'] == completion['evidence_digest'], 'review batch binding differs')
    require(set(review['cases']) == set(review_pin['case_observations']) == set(CASES), 'review case set differs')
    require(review_pin['verifier_sources'] == source_bindings(root, ctx), 'reviewed verifier source differs or is incomplete')
    collector = pin['collector_commit']
    require(collector == review_pin['collector_commit'], 'collector review differs')
    for path, digest in {**ctx['harness'], **ctx['claim_verifier']}.items():
        raw = subprocess.check_output(['git', 'show', collector+':'+path], cwd=root)
        require('sha256:'+sha256(raw).hexdigest() == digest, 'collector source differs from committed identity')
    controls = verifier_controls(root, CASES)
    save(output/'specific-verifier-controls.json', controls)
    effects = adapter_controls(CASES['security-and-hardening--representative'])
    save(output/'effect-controls.json', effects)
    require(controls['status'] == effects['status'] == 'PASS', 'specific negative control failed; raw evidence retained')
    rows = []
    for name, fixture in CASES.items():
        directory = retained/name
        record = json.loads((directory/'observation.json').read_text())
        unseal(record)
        require(record['binding'] == binding(ctx, name) and record['execution_eligible'] is False, 'native profile binding changed')
        require(record['collector_commit'] == collector, 'collector commit differs')
        require(record['evidence_digest'] == review_pin['case_observations'][name], 'review observation differs')
        native_ok = native_complete(directory, record, fixture)
        complete = admitted and record['generation'] == 'COMPLETED' and record.get('trial_identity') == 'PRE_POST_CHECKED'
        if complete:
            require(native_ok, 'native completion mismatch')
            require(json.loads((directory/'prompt.json').read_text()) == {'policy': POLICY, 'prompt': prompt(root, ctx, name)}, 'native prompt changed')
            replay_entries(fixture, record, directory, output/'replay-journal')
            evaluated = assess(fixture, record)
            save(output/'assessments'/(name+'.json'), evaluated)
            require(evaluated == record['verification'], 'independent profile evaluation differs; actual assessment retained')
        else:
            evaluated = {'status': 'NOT_RUN', 'reason': 'incomplete batch; no credit'}
        opinion = review['cases'][name]
        transcript = file_digest(directory/'native.jsonl') if (directory/'native.jsonl').exists() else None
        require(opinion['observation_digest'] == record['evidence_digest']
                and opinion['native_transcript_digest'] == transcript, 'output review binding differs')
        status = 'PARTIAL' if not complete else 'PASS' if evaluated['status'] == opinion['status'] == 'PASS' else 'FAIL'
        rows.append(seal({'binding': record['binding'], 'observation_digest': record['evidence_digest'],
                          'native_transcript_digest': transcript, 'collector_commit': collector,
                          'generation': record['generation'], 'batch_admission': 'ADMITTED' if admitted else 'WITHHELD',
                          'evaluation': evaluated, 'output_review': opinion, 'status': status, 'execution_eligible': False}))
    profiles = {}
    for skill in INPUTS['skills']:
        children = [row for row in rows if row['binding']['skill']['skill_id'] == skill]
        status = 'PASS' if all(row['status'] == 'PASS' for row in children) else 'PARTIAL' if any(row['status'] == 'PARTIAL' for row in children) else 'FAIL'
        profiles[skill] = seal({'profile': skill+'-literal-edit-assisted-runtime8.2-offline-v1', 'status': status,
                               'bindings': [row['binding'] for row in children], 'case_evidence': [row['evidence_digest'] for row in children],
                               'scope': 'Exact representative and adversarial fixtures only. Explicit reviewed plan and source correction assistance; no general design or security capability claim.',
                               'starting_native_bundle': previous_digest, 'reviewer_feedback_assistance': True,
                               'acceptance': 'PENDING_FRESH_HOSTED_VALIDATION' if status == 'PASS' else 'NOT_QUALIFIED',
                               'execution_eligible': False, 'global_trust': 'UNTRUSTED'})
    accepted = json.loads((root/'qualification/checkpoint5/accepted-profile.json').read_text())
    unseal(accepted)
    prior = json.loads((root/'qualification/checkpoint5/consumer-compatibility.json').read_text())
    unseal(prior)
    consumers = {name: seal({'consumer': name, 'accepted_tdd_reference': old['qualification_reference'],
                             'exact_tdd_binding': old['exact_binding'],
                             'api_security_profile_references': {skill: value['evidence_digest'] for skill, value in profiles.items()},
                             'api_security_bindings': {skill: value['bindings'] for skill, value in profiles.items()},
                             'activation': 'DISABLED', 'execution_eligible': False, 'consumer_compatibility': 'NOT_ESTABLISHED',
                             'source_inspection_reference': old['consumer_source_reference'],
                             'required_next_check': old['required_next_check'], 'consumer_repository_modified': False})
                 for name, old in prior['consumers'].items()}
    return seal({'schema': 'myskills.checkpoint.v8.2.1-assisted-edit', 'base_commit': BASE, 'context_digest': digest_object(ctx),
                 'completion': completion, 'bundle_digest': pin['bundle_digest'], 'matrix': rows, 'profiles': profiles,
                 'specific_verifier_controls': controls, 'effect_controls': effects,
                 'composition': composition(json.loads((root/'qualification/initial-cohort/plan.json').read_text()), accepted),
                 'consumers': consumers, 'historical_files_digest': digest_object(historical),
                 'accepted_tdd_profile': accepted['evidence_digest'], 'historical_tdd_changed': False,
                 'new_profile_candidates': sum(value['status'] == 'PASS' for value in profiles.values()),
                 'accepted_behavioral_profiles': 1,
                 'acceptance_rule': 'New candidates require a separate matching fresh-clone and hosted validation receipt. C7 acceptance hold and historical verdicts remain unchanged.',
                 'globally_trusted_skills': 0, 'catalog_trust': 'UNTRUSTED', 'catalog_qualification': 'NOT_EVALUATED',
                 'paid_operations': 0, 'production_integration': 'NOT_RUN', 'external_alpha_impact': 'NONE',
                 'marketplace_activation': 'DISABLED', 'greptile': 'DEFERRED'})


def run(root: Path, retained: Path, previous: Path, output: Path) -> dict[str, Any]:
    from qualification.v7 import evaluate as historical_evaluator
    from qualification.v8 import controls as specific_controls
    output.mkdir(parents=True, exist_ok=False)
    observations: list[dict[str, Any]] = []
    original_evaluator = historical_evaluator.executor
    original_controls = specific_controls.executor

    def observed(factory: Any, phase: str) -> Any:
        def make(skill: str) -> Any:
            execute = factory(skill)
            def capture(*args: Any, **kwargs: Any) -> dict[str, Any]:
                row = {'phase': phase, 'skill': skill, 'args': args, 'kwargs': kwargs, 'state': 'DISPATCHED'}
                observations.append(row)
                save(output/'executions.json', seal({'executions': observations}))
                try:
                    result = execute(*args, **kwargs)
                except Exception as error:
                    row.update(state='RAISED', error=type(error).__name__+': '+str(error))
                    save(output/'executions.json', seal({'executions': observations}))
                    raise
                row.update(state='RETURNED', result=result)
                save(output/'executions.json', seal({'executions': observations}))
                return result
            return capture
        return make

    historical_evaluator.executor = observed(original_evaluator, 'independent-profile')
    specific_controls.executor = observed(original_controls, 'specific-controls')
    try:
        value = report(root, retained, previous, output)
    except Exception as error:
        save(output/'failure.json', seal({'status': 'FAIL', 'error': type(error).__name__+': '+str(error), 'qualification_credit': False}))
        raise
    finally:
        historical_evaluator.executor = original_evaluator
        specific_controls.executor = original_controls
    exports = {'checkpoint': value, 'matrix': value['matrix'], 'profiles': value['profiles'],
               'composition': value['composition'], **value['consumers']}
    for name, data in exports.items():
        save(output/(name+'.json'), data)
    return value


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('retained', 'previous', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    value = run(Path.cwd(), args.retained, args.previous, args.output)
    print(json.dumps({'evidence_digest': value['evidence_digest'], 'profiles': {key: row['status'] for key, row in value['profiles'].items()}}))
