from copy import deepcopy
from pathlib import Path
import pytest
from myskills.catalog import build_catalog
from myskills.registry import Registry, Unavailable
from myskills.manifest import ValidationError

@pytest.fixture
def manifest():
    return deepcopy(build_catalog(Path(__file__).parents[1])['skills'][0])

def test_owner_private_denial_is_generic_across_reads(manifest):
    manifest['visibility'] = {'scope': 'owner', 'subject': 'owner-a'}
    manifest['trust'] = 'OWNER_PRIVATE'
    registry = Registry([manifest])
    assert len(registry.enumerate('owner-a')) == 1
    assert registry.enumerate('owner-b') == registry.search('owner-b', manifest['name']) == []
    for skill_id in (manifest['skill_id'], 'missing'):
        with pytest.raises(Unavailable, match='^skill unavailable$'):
            registry.exact('owner-b', skill_id, manifest['version'])

def test_immutable_identity_and_defensive_reads(manifest):
    with pytest.raises(ValidationError, match='duplicate'):
        Registry([manifest, manifest])
    registry = Registry([manifest])
    manifest['description'] = 'mutated caller'
    item = registry.enumerate('owner-a')[0]
    assert item['description'] != 'mutated caller'
    item['trust'] = 'PLATFORM_QUALIFIED'
    assert registry.enumerate('owner-a')[0]['trust'] == 'UNTRUSTED'
    with pytest.raises(Unavailable):
        registry.exact('owner-a', item['skill_id'], 'latest')

def test_search_filters_before_results(manifest):
    registry = Registry([manifest])
    assert registry.search('owner-a', runtime='codex', trust='UNTRUSTED')
    assert not registry.search('owner-a', trust='PLATFORM_QUALIFIED')
    with pytest.raises(ValidationError):
        registry.search('owner-a', unsafe=True)

def dependency(m):
    return {'dependency_id': m['skill_id'], 'type': 'skill', 'version': m['version'], 'digest': m['digest'],
            'provider': '', 'required_capabilities': [], 'authentication': 'none', 'network_hosts': [],
            'data_exposed': [], 'effects': [], 'required': True, 'runtimes': ['codex'], 'qualification': 'NOT_EVALUATED'}

def test_exact_dependency_cycle_missing_and_revoked(manifest):
    from myskills.manifest import binding
    child = deepcopy(manifest)
    child['skill_id'] = 'child'
    manifest['dependencies'] = [dependency(child)]
    child['dependencies'] = [dependency(manifest)]
    with pytest.raises(ValidationError, match='cycle'):
        Registry([manifest, child]).dependency_graph('owner-a', binding(manifest), runtime='codex')
    with pytest.raises(Unavailable):
        Registry([manifest]).dependency_graph('owner-a', binding(manifest), runtime='codex')
    child['dependencies'] = []
    child['lifecycle'] = 'revoked'
    with pytest.raises(ValidationError, match='revoked'):
        Registry([manifest, child]).dependency_graph('owner-a', binding(manifest), runtime='codex')

@pytest.mark.parametrize('reverse', [False, True])
def test_diamond_dependency_checks_every_parent_envelope(manifest, reverse):
    from myskills.manifest import binding
    shared, child = deepcopy(manifest), deepcopy(manifest)
    shared['skill_id'], child['skill_id'] = 'shared', 'child'
    for m in (manifest, shared):
        m['permitted_effects'] = ['tests.execute']
        m['prohibited_effects'].remove('tests.execute')
    child['dependencies'] = [dependency(shared)]
    manifest['dependencies'] = [dependency(shared), dependency(child)]
    if reverse:
        manifest['dependencies'].reverse()
    with pytest.raises(ValidationError, match='effect escalation'):
        Registry([manifest, shared, child]).dependency_graph('owner-a', binding(manifest), runtime='codex')
