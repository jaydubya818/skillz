from copy import deepcopy
from pathlib import Path

import pytest

import json
from myskills.cohort_assessment import assess, verify_assessment, verify_bundle
from myskills.digest import digest_object
from myskills.manifest import ValidationError
from myskills.qualification import QualificationStore
from myskills.governance import GovernedRegistry

ROOT = Path(__file__).parents[1]
EXPECTED = [
    'figure-it-out', 'principle-sequence-verifiable-units', 'tdd',
    'thermo-nuclear-code-quality-review', 'api-and-interface-design',
    'deprecation-and-migration', 'frontend-ui-engineering', 'security-and-hardening',
    'ci-cd-and-automation', 'create-verification-skill',
]


@pytest.fixture(scope='module')
def assessment():
    return assess(ROOT)


def test_exact_retained_cohort_has_no_fabricated_behavioral_qualification(assessment):
    assert [r['binding']['skill_id'] for r in assessment['skills']] == EXPECTED
    assert assessment['deep_qualified'] == 0
    assert assessment['catalog_count'] == 92
    for report in assessment['skills']:
        assert report['behavioral_execution'] == 'NOT_RUN'
        assert report['qualification'] == 'NOT_EVALUATED'
        assert report['trust'] == 'UNTRUSTED'
        assert report['effective_permitted_effects'] == []
        assert report['execution_attempts'] == 0
        assert report['packaging']['status'] == 'PASS'
        assert report['packaging']['executable_resources'] == []
        assert all(c['status'] == 'NOT_RUN' for c in report['behavioral_cases'])
        assert report['boundaries']['unqualified_admission']['status'] == 'PASS'
        assert report['boundaries']['revoked_version']['status'] == 'PASS'
        assert report['boundaries']['body_tamper']['status'] == 'PASS'
        assert all(r['status'] == 'PASS' for r in report['boundaries']['untrusted_request_admission'])


def test_assessment_is_reproducible_and_independently_rechecked(assessment):
    assert assess(ROOT) == assessment
    assert verify_assessment(ROOT, assessment, assessment['evidence_digest'])


@pytest.mark.parametrize('tamper', ['promotion', 'binding', 'cohort', 'composition', 'myapps'])
def test_resealed_assessment_cannot_invent_evidence(assessment, tamper):
    bad = deepcopy(assessment)
    if tamper == 'promotion':
        bad['skills'][0]['behavioral_execution'] = 'PASS'
        bad['skills'][0]['qualification'] = 'DETERMINISTIC_TESTED'
    elif tamper == 'binding':
        bad['skills'][0]['binding']['digest'] = digest_object('other package')
    elif tamper == 'cohort':
        bad['skills'][0] = deepcopy(bad['skills'][1])
    elif tamper == 'composition':
        bad['composition']['status'] = 'PASS'
    else:
        bad['myapps']['ready_skills'] = [bad['skills'][0]['binding']]
    bad['evidence_digest'] = digest_object({k: v for k, v in bad.items() if k != 'evidence_digest'})
    with pytest.raises(ValidationError):
        verify_assessment(ROOT, bad, bad['evidence_digest'])


def test_assessment_is_not_accepted_as_qualification_evidence(assessment):
    store = QualificationStore(GovernedRegistry(), reviewers=['fixture-reviewer'])
    with pytest.raises(ValidationError, match='invalid evidence shape'):
        store.record('fixture-owner', assessment, authenticated_reviewer='fixture-reviewer', accepted_by='fixture-owner')


def test_actual_cohort_composition_cannot_claim_synthetic_success(assessment):
    composition = assessment['composition']
    assert composition['status'] == 'PARTIAL'
    assert composition['executed_stages'] == 0
    assert composition['publication'] == 'UNAUTHORIZED'
    assert composition['stage_failure_behavior'] == 'NOT_RUN'
    assert composition['admission_failure_stops']['status'] == 'PASS'
    assert composition['tampered_child']['status'] == 'PASS'
    assert composition['child_effect_escalation']['status'] == 'PASS'
    assert [s['skill']['skill_id'] for s in composition['proposal']['stages']] == [EXPECTED[i] for i in (0, 1, 2, 3, 9)]


def test_myapps_references_remain_ineligible_and_preserve_coverage_gaps(assessment):
    mapping = assessment['myapps']
    assert mapping['ready_skills'] == []
    assert len(mapping['candidates']) == 10
    assert all(not c['execution_eligible'] for c in mapping['candidates'])
    assert {c['capability'] for c in mapping['outside_cohort']} == {'performance', 'observability'}
    assert all(c['in_cohort'] is False for c in mapping['outside_cohort'])


@pytest.mark.parametrize('target', ['skill', 'myapps'])
def test_consumer_rejects_swapped_sidecar_even_with_valid_top_level_report(assessment, tmp_path, target):
    (tmp_path / 'skills').mkdir()
    (tmp_path / 'assessment.json').write_text(json.dumps(assessment))
    for item in assessment['skills']:
        (tmp_path / 'skills' / (item['binding']['skill_id'] + '.json')).write_text(json.dumps(item))
    (tmp_path / 'myapps.json').write_text(json.dumps(assessment['myapps']))
    assert verify_bundle(ROOT, tmp_path, assessment['evidence_digest'])
    if target == 'skill':
        modified = deepcopy(assessment['skills'][0])
        modified['behavioral_execution'] = 'PASS'
        (tmp_path / 'skills' / 'figure-it-out.json').write_text(json.dumps(modified))
    else:
        modified = deepcopy(assessment['myapps'])
        modified['ready_skills'] = [assessment['skills'][0]['binding']]
        (tmp_path / 'myapps.json').write_text(json.dumps(modified))
    with pytest.raises(ValidationError, match='differs from pinned bundle'):
        verify_bundle(ROOT, tmp_path, assessment['evidence_digest'])


@pytest.mark.parametrize('revision', ['main', 'f' * 40])
def test_assessment_requires_available_exact_source_objects(revision):
    from myskills.cohort_assessment import PLAN, verify_source
    plan = json.loads((ROOT / PLAN).read_text())
    plan['canonical_source_sha'] = revision
    with pytest.raises(ValidationError, match='source'):
        verify_source(ROOT, plan)


def test_shared_adversarial_input_is_bound_into_every_skill(assessment, monkeypatch):
    import myskills.cohort_assessment as module
    original = module._plan
    def changed(root, manifests):
        value = original(root, manifests)
        value['common_adversarial_cases'][0]['input'] += ' changed fixture'
        return value
    monkeypatch.setattr(module, '_plan', changed)
    updated = module.assess(ROOT)
    for before, after in zip(assessment['skills'], updated['skills']):
        assert before['corpus_digest'] != after['corpus_digest']
        assert before['evidence_digest'] != after['evidence_digest']
