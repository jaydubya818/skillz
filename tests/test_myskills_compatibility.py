from copy import deepcopy
import pytest
from myskills.compatibility import work_proposal, validate_admission, relay_advertisement
from myskills.digest import digest_object
from myskills.manifest import ValidationError
from myskills.builder import PrivateBuilder, REFERENCE_POLICY, REFERENCE_CORPUS
from myskills.governance import GovernedRegistry, RegistryAdmin
from myskills.owner import OwnerStore
from myskills.qualification import QualificationStore
from myskills.resolver import ResolutionPolicy, Resolver

def prepared():
    r = GovernedRegistry()
    owners = OwnerStore(r)
    q = QualificationStore(r, reviewers=['static-package-verifier'])
    b = PrivateBuilder(owners, q)
    identity = b.draft('owner-a', skill_id='fixture-check', version='1.0.0', description='Check fixture', instructions='Review synthetic fixture')['binding']
    b.validate('owner-a', identity)
    b.qualify('owner-a', identity)
    installed = b.accept_install('owner-a', identity)
    session = owners.session('owner-a')
    session.set_enabled(identity['skill_id'], True, installed['revision'])
    policy = ResolutionPolicy('myskills-reference', 'myskills-reference', REFERENCE_POLICY, REFERENCE_CORPUS,
        frozenset(), frozenset(), frozenset({'OWNER_PRIVATE'}), runtime_features=frozenset({'static-package-only'}))
    resolver = Resolver(owners, q)
    selection = resolver.resolve('owner-a', 'check fixture', policy)
    proposal = work_proposal(selection, owner='owner-a', application='fixture-app', work_id='fixture-work', generation=1,
        workspace='fixture-workspace', source_snapshot=digest_object('fixture-source'), factory_version=digest_object('fixture-factory'),
        execution_provider='deterministic-fixture', harness=policy.harness, model_route='deterministic', effects=[],
        budget={'operations': 0, 'paid_operations': 0}, expires_at=100)
    authority = {'schema': 'myskills.authority-fixture.v1', 'proposal_digest': digest_object(proposal), 'owner': 'owner-a',
                 'publication': False, 'effects': [], 'expires_at': 100}
    return r, session, resolver, policy, proposal, authority

def test_future_binding_requires_exact_separate_authority():
    r, session, resolver, policy, work, authority = prepared()
    admitted = validate_admission(work, authority, session=session, resolver=resolver, policy=policy, now=1)
    assert admitted['skill'] == work['skill'] and not admitted['production_admission']
    assert not admitted['publication']
    for field in ('owner', 'application', 'work_id', 'generation', 'workspace', 'source_snapshot', 'factory_version', 'expires_at'):
        changed = deepcopy(work)
        changed[field] = 2 if type(changed[field]) is int else digest_object('wrong') if field in ('source_snapshot', 'factory_version') else 'other'
        with pytest.raises(ValidationError):
            validate_admission(changed, authority, session=session, resolver=resolver, policy=policy, now=1)
    with pytest.raises(ValidationError):
        validate_admission(work, authority, session=session, resolver=resolver, policy=policy, now=100)
    RegistryAdmin(r).transition('owner-a', work['skill'], 'revoked')
    with pytest.raises(ValidationError):
        validate_admission(work, authority, session=session, resolver=resolver, policy=policy, now=1)

def test_private_advertisement_and_skill_substitution_denied():
    r, session, resolver, policy, work, authority = prepared()
    with pytest.raises(ValidationError):
        relay_advertisement(r.exact('owner-a', **work['skill']))
    changed = deepcopy(work)
    changed['skill']['digest'] = digest_object('substitution')
    with pytest.raises(ValidationError):
        validate_admission(changed, authority, session=session, resolver=resolver, policy=policy, now=1)


def test_static_skill_cannot_receive_execution_budget():
    _, session, resolver, policy, work, authority = prepared()
    work['budget']['operations'] = 1
    authority['proposal_digest'] = digest_object(work)
    with pytest.raises(ValidationError, match='ceiling'):
        validate_admission(work, authority, session=session, resolver=resolver, policy=policy, now=1)
