from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from pathlib import Path
import pytest
from myskills.catalog import build_catalog
from myskills.governance import GovernedRegistry, RegistryAdmin
from myskills.owner import OwnerStore
from myskills.manifest import binding, ValidationError
from myskills.registry import Unavailable

@pytest.fixture
def setup():
    m = deepcopy(build_catalog(Path(__file__).parents[1])['skills'][0])
    r = GovernedRegistry([m])
    store = OwnerStore(r)
    return m, r, store.session('owner-a'), store.session('owner-b')

def test_install_is_idempotent_disabled_and_owner_scoped(setup):
    m, r, a, b = setup
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: a.install(binding(m)), range(20)))
    assert all(result == results[0] for result in results)
    assert len(a.installed()) == 1 and b.installed() == []
    item = results[0]
    assert not item['enabled'] and 'authority' not in item
    with pytest.raises(Unavailable):
        b.set_enabled(m['skill_id'], True, item['revision'])
    enabled = a.set_enabled(m['skill_id'], True, item['revision'])
    with pytest.raises(ValidationError, match='stale'):
        a.uninstall(m['skill_id'], item['revision'])
    a.uninstall(m['skill_id'], enabled['revision'])
    assert a.installed() == []

def test_foreign_private_install_has_same_denial_as_missing(setup):
    m, r, a, b = setup
    m['skill_id'] = 'private-synthetic'
    m['visibility'] = {'scope': 'owner', 'subject': 'owner-a'}
    m['trust'] = 'OWNER_PRIVATE'
    RegistryAdmin(r).add(m)
    assert a.install(binding(m))
    for identity in (binding(m), {**binding(m), 'skill_id': 'absent'}):
        with pytest.raises(Unavailable, match='^skill unavailable$'):
            b.install(identity)
    assert r.search('owner-b', 'private-synthetic') == []

def test_update_requires_exact_review_and_revocation_wins(setup):
    m, r, a, b = setup
    old = a.install(binding(m))
    new = deepcopy(m)
    new['version'], new['digest'] = '1.0.0', 'sha256:' + 'a'*64
    new['secret_requirements'] = [{'name': 'example', 'purpose': 'synthetic test', 'authentication': 'credential_handle'}]
    RegistryAdmin(r).add(new)
    review = a.review_update(m['skill_id'], binding(new), old['revision'])
    assert review['diff']['requires_review']
    with pytest.raises(ValidationError, match='decision mismatch'):
        a.update(m['skill_id'], binding(new), old['revision'], 'wrong')
    RegistryAdmin(r).transition('owner-a', binding(new), 'revoked')
    with pytest.raises(Unavailable):
        a.update(m['skill_id'], binding(new), old['revision'], review['decision_digest'])
    assert a.installed() == [old]
    assert r.exact('owner-a', **old['binding']) == m

def test_successful_update_preserves_historical_version(setup):
    m, r, a, _ = setup
    old = a.install(binding(m))
    new = deepcopy(m)
    new['version'], new['digest'] = '1.0.0', 'sha256:' + 'a'*64
    RegistryAdmin(r).add(new)
    review = a.review_update(m['skill_id'], binding(new), old['revision'])
    result = a.update(m['skill_id'], binding(new), old['revision'], review['decision_digest'])
    assert result['binding'] == binding(new) and not result['enabled']
    assert r.exact('owner-a', **binding(m)) == m
    assert r.enumerate('owner-a') == [m, new]
