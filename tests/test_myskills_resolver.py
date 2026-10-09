from copy import deepcopy
from pathlib import Path
import pytest
from myskills.catalog import build_catalog
from myskills.digest import digest_object
from myskills.governance import GovernedRegistry, RegistryAdmin
from myskills.owner import OwnerStore
from myskills.manifest import binding
from myskills.resolver import Resolver, ResolutionPolicy

class FixtureQualification:
    """Trusted deterministic fixture only; production uses evidence validation."""
    def lookup(self, owner, identity, policy):
        return {'status': 'DETERMINISTIC_TESTED', 'trust': 'COMMUNITY'}

@pytest.fixture
def routing():
    m = deepcopy(build_catalog(Path(__file__).parents[1])['skills'][0])
    m.update(skill_id='review-code', name='Review code', description='Review repository changes', tags=['review'], metadata_status='REVIEWED')
    m['required_capabilities'] = ['repository.read']
    m['compatibility_requirements'] = []
    r = GovernedRegistry([m])
    store = OwnerStore(r)
    item = store.session('owner-a').install(binding(m))
    store.session('owner-a').set_enabled(m['skill_id'], True, item['revision'])
    policy = ResolutionPolicy('codex', 'codex', digest_object('policy'), digest_object('corpus'), frozenset({'repository.read'}), frozenset({'repository.read'}), frozenset({'COMMUNITY'}))
    return m, r, store, policy

def test_safe_no_match_and_no_authored_qualification(routing):
    m, r, store, policy = routing
    m['trust'] = 'PLATFORM_QUALIFIED'
    assert Resolver(store).resolve('owner-a', 'review code', policy)['state'] == 'NO_ELIGIBLE_SKILL'
    resolver = Resolver(store, FixtureQualification())
    assert resolver.resolve('owner-a', 'astronomy', policy)['state'] == 'NO_ELIGIBLE_SKILL'
    assert resolver.resolve('owner-b', 'review code', policy)['state'] == 'NO_ELIGIBLE_SKILL'
    result = resolver.resolve('owner-a', 'review code', policy)
    assert result['state'] == 'SELECTED' and result['selected'] == binding(m)
    assert result['instructions_loaded'] == 0 and result['work_authority'] is None

def test_ambiguity_does_not_force_selection(routing):
    m, r, store, policy = routing
    second = deepcopy(m)
    second['skill_id'] = 'other-review'
    RegistryAdmin(r).add(second)
    session = store.session('owner-a')
    item = session.install(binding(second))
    session.set_enabled(second['skill_id'], True, item['revision'])
    result = Resolver(store, FixtureQualification()).resolve('owner-a', 'review code', policy)
    assert result['state'] == 'AMBIGUOUS' and result['selected'] is None

def test_revocation_no_fallback_and_unknown_capability(routing):
    m, r, store, policy = routing
    resolver = Resolver(store, FixtureQualification())
    assert resolver.resolve('owner-a', 'review', policy, ['unavailable.capability'])['state'] == 'NO_ELIGIBLE_SKILL'
    RegistryAdmin(r).transition('owner-a', binding(m), 'revoked')
    assert resolver.resolve('owner-a', 'review', policy)['state'] == 'NO_ELIGIBLE_SKILL'

def test_community_cannot_request_network_or_secrets(routing):
    m, r, store, policy = routing
    evil = deepcopy(m)
    evil.update(skill_id='malicious-review', name='Malicious review')
    evil['permitted_effects'] = ['secrets.use']
    evil['prohibited_effects'].remove('secrets.use')
    RegistryAdmin(r).add(evil)
    session = store.session('owner-a')
    installed = session.install(binding(evil))
    session.set_enabled(evil['skill_id'], True, installed['revision'])
    result = Resolver(store, FixtureQualification()).resolve('owner-a', 'malicious review', policy)
    assert any(item['binding'] == binding(evil) and item['reason'] == 'effects denied' for item in result['policy_filtering'])


def test_catalog_corpus_never_loads_instructions_or_promotes_legacy(monkeypatch):
    import json
    catalog = build_catalog(Path(__file__).parents[1])
    r = GovernedRegistry(catalog['skills'])
    store = OwnerStore(r)
    session = store.session('owner-a')
    for m in catalog['skills']:
        item = session.install(binding(m))
        session.set_enabled(m['skill_id'], True, item['revision'])
    policy = ResolutionPolicy('codex', 'codex', digest_object('policy'), digest_object('corpus'), frozenset(), frozenset(), frozenset({'COMMUNITY'}))
    resolver = Resolver(store)
    corpus = json.loads((Path(__file__).parent / 'fixtures/myskills-routing.json').read_text())
    def no_body_reads(*args, **kwargs):
        raise AssertionError('routing loaded filesystem content')
    monkeypatch.setattr(Path, 'read_text', no_body_reads)
    for case in corpus:
        result = resolver.resolve('owner-a', case['request'], policy)
        assert result['state'] == case['expected']
        assert result['instructions_loaded'] == 0

def skill_dependency(m):
    return {'dependency_id': m['skill_id'], 'type': 'skill', 'version': m['version'], 'digest': m['digest'],
            'provider': '', 'required_capabilities': [], 'authentication': 'none', 'network_hosts': [],
            'data_exposed': [], 'effects': [], 'required': True, 'runtimes': ['codex'], 'qualification': 'NOT_EVALUATED'}

@pytest.mark.parametrize('child_state', ['absent', 'disabled', 'private-frozen'])
def test_every_dependency_obeys_installation_and_private_freeze(routing, child_state):
    m, _, _, policy = routing
    child = deepcopy(m)
    child.update(skill_id='child', name='Child', description='Component', tags=[])
    if child_state == 'private-frozen':
        child['visibility'] = {'scope': 'owner', 'subject': 'owner-a'}
    m['dependencies'] = [skill_dependency(child)]
    r = GovernedRegistry([m, child])
    store = OwnerStore(r)
    session = store.session('owner-a')
    root_install = session.install(binding(m))
    session.set_enabled(m['skill_id'], True, root_install['revision'])
    if child_state != 'absent':
        installed = session.install(binding(child))
        if child_state == 'private-frozen':
            session.set_enabled(child['skill_id'], True, installed['revision'])
            r.private_resolution_enabled = False
    assert Resolver(store, FixtureQualification()).resolve('owner-a', 'review', policy)['state'] == 'NO_ELIGIBLE_SKILL'

def test_external_dependency_cannot_bypass_policy(routing):
    from dataclasses import replace
    m, _, _, policy = routing
    dep = skill_dependency(m)
    dep.update(dependency_id='external.mcp', type='mcp', effects=['merge.execute'], qualification='REVOKED')
    m['dependencies'] = [dep]
    r = GovernedRegistry([m])
    store = OwnerStore(r)
    session = store.session('owner-a')
    item = session.install(binding(m))
    session.set_enabled(m['skill_id'], True, item['revision'])
    policy = replace(policy, available_dependencies=((dep['dependency_id'], dep['version'], dep['digest']),))
    result = Resolver(store, FixtureQualification()).resolve('owner-a', 'review', policy)
    assert result['state'] == 'NO_ELIGIBLE_SKILL'
    assert result['policy_filtering'][0]['reason'] == 'external dependency qualification unavailable'
