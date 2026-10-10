from copy import deepcopy
from pathlib import Path

import pytest

from myskills.composition import composition_proposal, verify_fixture_candidate
from myskills.digest import digest_object
from myskills.governance import RegistryAdmin
from myskills.manifest import ValidationError
from myskills.reference_journey import prepare_fixture, run_journey
from myskills.registry import Unavailable


def test_composed_journey_retains_every_binding_and_separate_publication():
    report = run_journey(Path(__file__).parents[1])
    assert len(report['canonical_unqualified_denials']) == 5
    result = report['synthetic_reference_result']
    assert result['status'] == 'PASS' and result['attempts'] == 1
    assert len(result['proof']['skills']) == 5
    assert result['proof']['composition_digest'] == result['composition']['digest']
    assert result['proof']['candidate_digest'] == digest_object(result['candidate'])
    assert result['admission']['proposal_digest'] == digest_object(result['proposal'])
    assert result['admission']['composition_digest'] == result['composition']['digest']
    assert result['admission']['stages'] == result['proof']['skills']
    assert not result['publication'] and not result['production_admission']
    assert report['failure_recovery']['producer_crash']['status'] == 'UNKNOWN'
    assert report['failure_recovery']['stage_failure']['handoffs'] == 1
    assert report['deep_qualified_catalog_skills'] == 0


def test_second_owner_cannot_discover_resolve_read_evidence_or_run_composition():
    fixture, comp, work, auth, qualifications = prepare_fixture()
    fixture.run(work['owner'], comp, work, auth, now=1)
    foreign = 'fixture-owner-b'
    skill = comp['stages'][0]['skill']
    assert fixture.store.registry.search(foreign, '') == []
    assert fixture.resolver.resolve(foreign, 'repository-analysis', fixture.policy)['state'] == 'NO_ELIGIBLE_SKILL'
    for operation in (
        lambda: fixture.store.registry.exact(foreign, **skill),
        lambda: qualifications.evidence(foreign, skill),
        lambda: fixture.store.session(foreign).install(skill),
        lambda: fixture.read(foreign, work['application'], work['work_id'], work['generation']),
        lambda: fixture.run(foreign, comp, work, auth, now=1),
    ):
        with pytest.raises(Unavailable):
            operation()


def test_composition_cannot_expand_authority_or_substitute_digests():
    fixture, comp, work, auth, _ = prepare_fixture()
    tampered = deepcopy(comp)
    tampered['stages'][1]['skill']['digest'] = digest_object('substitution')
    with pytest.raises(ValidationError, match='digest mismatch'):
        fixture.run(work['owner'], tampered, work, auth, now=1)
    stages = deepcopy(comp['stages'])
    stages[1]['effects'] = ['merge.execute']
    with pytest.raises(ValidationError, match='child effect'):
        composition_proposal(work['owner'], stages)
    changed = deepcopy(work)
    changed['effects'] = ['merge.execute']
    changed_auth = {**auth, 'proposal_digest': digest_object(changed)}
    with pytest.raises(ValidationError, match='no execution authority'):
        fixture.run(work['owner'], comp, changed, changed_auth, now=1)
    with pytest.raises(ValidationError, match='authority'):
        fixture.run(work['owner'], comp, work, {**auth, 'publication': True}, now=1)


@pytest.mark.parametrize('change', ['revoked', 'disabled', 'evidence-revoked'])
def test_component_denial_after_work_creation_stops_before_candidate(change):
    fixture, comp, work, auth, qualifications = prepare_fixture()
    child = comp['stages'][2]['skill']
    if change == 'revoked':
        RegistryAdmin(fixture.store.registry).transition(work['owner'], child, 'revoked')
    elif change == 'disabled':
        session = fixture.store.session(work['owner'])
        installed = next(i for i in session.installed() if i['binding'] == child)
        session.set_enabled(child['skill_id'], False, installed['revision'])
    else:
        evidence = qualifications.evidence(work['owner'], child)[0]
        qualifications.revoke(evidence['evidence_digest'], authenticated_reviewer='static-package-verifier')
    with pytest.raises(ValidationError):
        fixture.run(work['owner'], comp, work, auth, now=1)
    with pytest.raises(Unavailable):
        fixture.read(work['owner'], work['application'], work['work_id'], work['generation'])


def test_unknown_replay_is_retained_and_changed_retry_rejected():
    fixture, comp, work, auth, _ = prepare_fixture()
    first = fixture.run(work['owner'], comp, work, auth, now=1, fault='producer_crash')
    assert first['status'] == 'UNKNOWN'
    assert fixture.run(work['owner'], comp, work, auth, now=2, fault='producer_crash') == first
    with pytest.raises(ValidationError, match='already bound'):
        fixture.run(work['owner'], comp, work, auth, now=2)
    first['candidate']['handoffs'].clear()
    retained = fixture.read(work['owner'], work['application'], work['work_id'], work['generation'])
    assert len(retained['candidate']['handoffs']) == 1 and retained['attempts'] == 1


def test_revocation_between_handoffs_stops_without_substitution(monkeypatch):
    import myskills.composition as module
    fixture, comp, work, auth, _ = prepare_fixture()
    original = module._handoff
    def revoke_after_first(stage, previous, source):
        handoff = original(stage, previous, source)
        if stage['stage_id'] == comp['stages'][0]['stage_id']:
            RegistryAdmin(fixture.store.registry).transition(work['owner'], comp['stages'][1]['skill'], 'revoked')
        return handoff
    monkeypatch.setattr(module, '_handoff', revoke_after_first)
    result = fixture.run(work['owner'], comp, work, auth, now=1)
    assert result['status'] == 'FAIL' and result['proof'] is None
    assert len(result['candidate']['handoffs']) == 1


@pytest.mark.parametrize('tamper', ['root-skill', 'budget', 'effects'])
def test_verifier_rechecks_full_work_binding_and_fixture_envelope(tamper):
    fixture, comp, work, auth, _ = prepare_fixture()
    result = fixture.run(work['owner'], comp, work, auth, now=1)
    if tamper == 'root-skill':
        work['skill'] = comp['stages'][1]['skill']
    elif tamper == 'budget':
        work['budget']['operations'] = 1
    else:
        work['effects'] = ['merge.execute']
    result['candidate']['work_digest'] = digest_object(work)
    with pytest.raises(ValidationError):
        verify_fixture_candidate(comp, work, result['candidate'])


@pytest.mark.parametrize('tamper', ['output', 'skill', 'order', 'missing', 'extra'])
def test_independent_fixture_verifier_rejects_bad_candidate(tamper):
    fixture, comp, work, auth, _ = prepare_fixture()
    result = fixture.run(work['owner'], comp, work, auth, now=1)
    candidate = result['candidate']
    if tamper == 'output':
        candidate['handoffs'][0]['output'] = 'producer claims success'
    elif tamper == 'skill':
        candidate['handoffs'][0]['skill']['digest'] = digest_object('other')
    elif tamper == 'order':
        candidate['handoffs'].reverse()
    elif tamper == 'missing':
        candidate['handoffs'].pop()
    else:
        candidate['publication'] = True
    with pytest.raises(ValidationError):
        verify_fixture_candidate(comp, work, candidate)
