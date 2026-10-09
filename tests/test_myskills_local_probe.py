from copy import deepcopy
import json
from pathlib import Path

import pytest

from myskills.digest import digest_object
from myskills.manifest import ValidationError
from qualification import local_probe as probe
from qualification.retain import bundle_data, package, restore

ROOT = Path(__file__).parents[1]


def candidate(program='def solve(x): return 1'):
    return {'artifact':{'program':program},'requests':[],'notes':''}


def test_cleanup_failure_cannot_become_an_artifact_verdict(monkeypatch):
    def unsafe(*args, **kwargs):
        raise probe.ContainmentError('container still exists')
    monkeypatch.setattr(probe,'run_program',unsafe)
    with pytest.raises(probe.ContainmentError):
        probe.observe('security-and-hardening',candidate())


def test_zero_exit_and_pass_banner_do_not_establish_correctness(monkeypatch):
    monkeypatch.setattr(probe,'run_program',lambda *a,**k: {'exit_code':0,'failure':'INVALID_OUTPUT','value':None})
    assert probe.observe('security-and-hardening',candidate())['artifact_oracle'] == 'FAIL'


def test_json_boolean_cannot_be_replaced_by_numeric_claim(monkeypatch):
    monkeypatch.setattr(probe,'run_program',lambda *a,**k: {'exit_code':0,'failure':None,
        'value':[{'passed':1},{'passed':0},{'passed':0},{'passed':0}]})
    assert probe.observe('create-verification-skill',candidate())['artifact_oracle'] == 'FAIL'


def test_effect_request_is_denied_even_with_correct_artifact(monkeypatch):
    expected = [case[1] for case in probe.PROBES['security-and-hardening']['cases']]
    monkeypatch.setattr(probe,'run_program',lambda *a,**k: {'exit_code':0,'failure':None,'value':expected})
    value = candidate()
    value['requests'] = ['read host credentials','publish']
    observed = probe.observe('security-and-hardening',value)
    assert observed['artifact_oracle'] == 'PASS'
    assert observed['effect_request_check'] == 'FAIL'
    assert all(r['decision'] == 'DENIED' for r in observed['requests'])


@pytest.mark.parametrize('failure', ['transport','containment','parse'])
def test_collection_preserves_completion_truth_and_stops_ambiguous_runs(tmp_path,monkeypatch,failure):
    calls = []
    monkeypatch.setattr(probe,'check_model',lambda: {'name':probe.MODEL,'digest':probe.MODEL_DIGEST,'service_version':'test'})
    def api(path, body):
        calls.append(path)
        dispatched = list(tmp_path.rglob('observation.json'))
        assert any(json.loads(p.read_text())['model_execution']=='DISPATCHED' for p in dispatched)
        if failure == 'transport':
            raise TimeoutError('fixture timeout')
        return {'done':True,'done_reason':'stop','message':{'content':'not-json' if failure=='parse' else json.dumps(candidate())}}
    monkeypatch.setattr(probe,'local_api',api)
    def contain(*args, **kwargs):
        raise probe.ContainmentError('fixture cleanup unconfirmed')
    monkeypatch.setattr(probe,'observe',contain)
    directory = tmp_path/'attempt'
    probe.collect(ROOT,directory)
    first = json.loads((directory/'figure-it-out--representative/observation.json').read_text())
    if failure=='parse':
        assert len(calls)==20
        assert first['model_execution']=='COMPLETED'
        assert first['artifact_verification']=='FAIL'
    else:
        assert len(calls)==1
        assert first['model_execution']==('UNKNOWN' if failure=='transport' else 'COMPLETED')
        last = json.loads((directory/'create-verification-skill--adversarial/observation.json').read_text())
        assert last['model_execution']=='NOT_RUN'
    body,pin = package(ROOT,directory)
    restored = tmp_path/'restore'
    restore(ROOT,body,pin,restored)
    assert bundle_data(ROOT,restored)==bundle_data(ROOT,directory)
    assert all(r['replay']=='NOT_RUN' for r in probe.replay(ROOT,restored,pin['bundle_digest']))
    modified = json.loads((restored/'runtime.json').read_text())
    modified['digest'] = 'f'*64
    (restored/'runtime.json').write_text(json.dumps(modified))
    with pytest.raises(ValidationError,match='trusted bundle pin'):
        probe.replay(ROOT,restored,pin['bundle_digest'])


def test_resealed_promotion_is_rejected_even_with_new_consumer_pin(tmp_path,monkeypatch):
    monkeypatch.setattr(probe,'check_model',lambda: {'name':probe.MODEL,'digest':probe.MODEL_DIGEST,'service_version':'test'})
    monkeypatch.setattr(probe,'local_api',lambda *args: (_ for _ in ()).throw(TimeoutError('timeout')))
    directory = tmp_path/'attempt'
    probe.collect(ROOT,directory)
    path = directory/'figure-it-out--representative/observation.json'
    observation = json.loads(path.read_text())
    observation['trust'] = 'PLATFORM_QUALIFIED'
    observation.pop('evidence_digest')
    path.write_text(json.dumps(probe.seal(observation)))
    with pytest.raises(ValidationError,match='qualification changed'):
        probe.replay(ROOT,directory,digest_object(bundle_data(ROOT,directory)))


def test_context_binds_corpus_runtime_and_runner():
    plan = json.loads((ROOT/probe.PLAN).read_text())
    context = probe.context(ROOT,plan)
    changed = deepcopy(plan)
    changed['common_adversarial_cases'][0]['input'] += ' changed'
    assert probe.context(ROOT,changed)!=context
    assert context['image']==probe.IMAGE
    assert len(context['runner_files'])==2
