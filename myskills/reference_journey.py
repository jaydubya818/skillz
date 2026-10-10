"""No-provider fixture connecting catalog, owner state, resolution and Work contracts."""
import json
from pathlib import Path

from .builder import PrivateBuilder, REFERENCE_CORPUS, REFERENCE_POLICY
from .catalog import build_catalog
from .compatibility import work_proposal
from .composition import ComposedFixture, HANDOFF, composed_work, composition_proposal
from .digest import digest_object, verify_package
from .governance import GovernedRegistry
from .manifest import ValidationError, binding
from .owner import OwnerStore
from .qualification import QualificationStore
from .resolver import ResolutionPolicy, Resolver

COHORT = (
    ('repository-analysis', 'figure-it-out'),
    ('implementation', 'principle-sequence-verifiable-units'),
    ('tests', 'tdd'),
    ('code-review', 'thermo-nuclear-code-quality-review'),
    ('independent-verification', 'create-verification-skill'),
)


def prepare_fixture():
    registry = GovernedRegistry()
    owners = OwnerStore(registry)
    qualifications = QualificationStore(registry, reviewers=['static-package-verifier'])
    builder = PrivateBuilder(owners, qualifications)
    session = owners.session('fixture-owner-a')
    stages = []
    for stage_id, _ in COHORT:
        identity = builder.draft(session.owner, skill_id='fixture-' + stage_id, version='1.0.0',
            description='Synthetic ' + stage_id, instructions='Inspect static fixture metadata only. No instruction execution.')['binding']
        builder.validate(session.owner, identity)
        builder.qualify(session.owner, identity)
        installed = builder.accept_install(session.owner, identity)
        session.set_enabled(identity['skill_id'], True, installed['revision'])
        stages.append({'stage_id': stage_id, 'skill': identity, 'input_format': HANDOFF, 'output_format': HANDOFF, 'effects': []})
    policy = ResolutionPolicy('myskills-reference', 'myskills-reference', REFERENCE_POLICY, REFERENCE_CORPUS,
        frozenset(), frozenset(), frozenset({'OWNER_PRIVATE'}), runtime_features=frozenset({'static-package-only'}))
    resolver = Resolver(owners, qualifications)
    selection = resolver.resolve(session.owner, 'repository-analysis', policy)
    composition = composition_proposal(session.owner, stages)
    proposal = work_proposal(selection, owner=session.owner, application='fixture-app', work_id='fixture-work', generation=1,
        workspace='fixture-workspace', source_snapshot=digest_object('synthetic source snapshot'),
        factory_version=digest_object('inactive synthetic factory'), execution_provider='deterministic-fixture',
        harness=policy.harness, model_route='deterministic', effects=[], budget={'operations': 0, 'paid_operations': 0}, expires_at=100)
    proposal = composed_work(proposal, composition)
    authority = {'schema': 'myskills.authority-fixture.v1', 'proposal_digest': digest_object(proposal),
                 'owner': session.owner, 'publication': False, 'effects': [], 'expires_at': 100}
    return ComposedFixture(owners, resolver, policy), composition, proposal, authority, qualifications


def run_journey(root):
    catalog = build_catalog(root)
    if catalog['failures']:
        raise ValidationError('catalog inventory failed')
    registry = GovernedRegistry(catalog['skills'])
    owners = OwnerStore(registry)
    session = owners.session('fixture-catalog-owner')
    actual_stages = []
    for stage_id, skill_id in COHORT:
        manifest = next(m for m in catalog['skills'] if m['skill_id'] == skill_id)
        verify_package(root / 'skills' / skill_id, manifest)
        identity = binding(manifest)
        installed = session.install(identity)
        session.set_enabled(skill_id, True, installed['revision'])
        actual_stages.append({'stage_id': stage_id, 'skill': identity, 'input_format': HANDOFF, 'output_format': HANDOFF, 'effects': []})
    actual = composition_proposal(session.owner, actual_stages)
    policy = ResolutionPolicy('codex', 'codex', digest_object('unqualified policy'), digest_object('unqualified corpus'),
                              frozenset(), frozenset(), frozenset({'COMMUNITY'}))
    resolver = Resolver(owners)
    denied = []
    for stage in actual['stages']:
        try:
            resolver.eligible(session, stage['skill'], policy)
        except ValidationError:
            denied.append(stage['skill'])
        else:
            raise ValidationError('unqualified canonical component was eligible')
    fixture, composition, proposal, authority, _ = prepare_fixture()
    success = fixture.run(proposal['owner'], composition, proposal, authority, now=1)
    failures = {}
    for fault in ('stage_failure', 'producer_crash', 'verifier_failure', 'dependency_unavailable'):
        fault_fixture, comp, work, auth, _ = prepare_fixture()
        result = fault_fixture.run(work['owner'], comp, work, auth, now=1, fault=fault)
        replay = fault_fixture.run(work['owner'], comp, work, auth, now=2, fault=fault)
        if result != replay or result['attempts'] != 1 or result['proof'] is not None:
            raise ValidationError('failure recovery minted a replacement result')
        failures[fault] = {'status': result['status'], 'handoffs': len(result['candidate']['handoffs']), 'attempts': result['attempts']}
    return {'scope': 'inactive deterministic compatibility contract; no real Skill instructions executed',
            'canonical_composition': actual, 'canonical_unqualified_denials': denied,
            'synthetic_reference_result': success, 'failure_recovery': failures,
            'deep_qualified_catalog_skills': 0, 'production_mutations': 0, 'paid_operations': 0,
            'publication': False, 'external_alpha_changes': 0}


if __name__ == '__main__':
    print(json.dumps(run_journey(Path(__file__).resolve().parents[1]), indent=2, sort_keys=True))
