from copy import deepcopy
from pathlib import Path
import pytest
from myskills.catalog import build_catalog
from myskills.governance import GovernedRegistry, RegistryAdmin, permission_diff
from myskills.manifest import ValidationError, binding
from myskills.registry import Unavailable

@pytest.fixture
def manifest():
    return deepcopy(build_catalog(Path(__file__).parents[1])['skills'][0])

def test_revocation_denies_new_use_without_erasing_history(manifest):
    r = GovernedRegistry([manifest])
    admin = RegistryAdmin(r)
    identity = binding(manifest)
    admin.transition('owner-a', identity, 'revoked')
    admin.transition('owner-a', identity, 'revoked')
    assert len(r._events) == 1
    assert r.exact('owner-a', **identity) == manifest
    with pytest.raises(Unavailable):
        r.assert_available('owner-a', identity)
    with pytest.raises(ValidationError):
        admin.transition('owner-a', identity, 'published')

def test_publisher_revocation_and_immutable_add(manifest):
    r = GovernedRegistry([manifest])
    admin = RegistryAdmin(r)
    admin.revoke_publisher(manifest['publisher']['publisher_id'])
    with pytest.raises(Unavailable):
        r.assert_available('owner-a', binding(manifest))
    changed = deepcopy(manifest)
    changed['description'] = 'new bytes must be a new version'
    with pytest.raises(ValidationError, match='duplicate'):
        admin.add(changed)

def test_update_diff_surfaces_security_and_retains_old_identity(manifest):
    new = deepcopy(manifest)
    new['version'] = '1.0.0'
    new['digest'] = 'sha256:' + '1'*64
    new['permitted_effects'] = ['network.request']
    new['prohibited_effects'].remove('network.request')
    new['network_requirements'] = {'mode': 'allowlist', 'hosts': ['example.invalid']}
    r = GovernedRegistry([manifest, new])
    update = r.updates('owner-a', binding(manifest))[0]
    assert update == permission_diff(manifest, new)
    assert update['requires_review'] and not update['automatic_update']
    assert 'network_requirements' in update['security_changes']
    RegistryAdmin(r).transition('owner-a', binding(new), 'revoked')
    assert r.updates('owner-a', binding(manifest)) == []
    assert r.exact('owner-a', **binding(manifest)) == manifest

def test_no_self_qualification_transition(manifest):
    r = GovernedRegistry([manifest])
    with pytest.raises(ValidationError, match='evidence'):
        RegistryAdmin(r).transition('owner-a', binding(manifest), 'qualified')

def test_revoked_child_blocks_installation_and_update_candidate(manifest):
    child, successor = deepcopy(manifest), deepcopy(manifest)
    child['skill_id'] = 'synthetic-child'
    successor['version'], successor['digest'] = '1.0.0', 'sha256:' + '2'*64
    successor['dependencies'] = [{'dependency_id': child['skill_id'], 'type': 'skill', 'version': child['version'],
        'digest': child['digest'], 'provider': '', 'required_capabilities': [], 'authentication': 'none',
        'network_hosts': [], 'data_exposed': [], 'effects': [], 'required': True, 'runtimes': ['codex'], 'qualification': 'NOT_EVALUATED'}]
    r = GovernedRegistry([manifest, successor, child])
    RegistryAdmin(r).transition('owner-a', binding(child), 'revoked')
    with pytest.raises(Unavailable):
        r.assert_available('owner-a', binding(successor), installing=True)
    assert r.updates('owner-a', binding(manifest)) == []

def test_private_lifecycle_audit_is_owner_bound(manifest):
    records = []
    for owner in ('owner-a', 'owner-b'):
        m = deepcopy(manifest)
        m['visibility'] = {'scope': 'owner', 'subject': owner}
        records.append(m)
    r = GovernedRegistry(records)
    for owner in ('owner-a', 'owner-b'):
        RegistryAdmin(r).transition(owner, binding(manifest), 'revoked')
    assert r._events[0]['subject'] != r._events[1]['subject']
