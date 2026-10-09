"""Inactive composition contract and deterministic handoff fixture, never an executor."""
from copy import deepcopy

from .compatibility import AUTHORITY_SCHEMA, WORK_SCHEMA, validate_admission
from .digest import digest_object
from .manifest import BINDING_SCHEMA, DIGEST, EFFECTS, ID, ValidationError, array, obj, string, validate
from .registry import Unavailable

HANDOFF = 'myskills.fixture-handoff.v1'
STAGE_SCHEMA = obj(stage_id=string(ID), skill=BINDING_SCHEMA, input_format=string(values=(HANDOFF,)),
                   output_format=string(values=(HANDOFF,)), effects=array(string(values=EFFECTS)))
COMPOSITION_SCHEMA = obj(schema=string(values=('myskills.composition-proposal.v1',)), owner=string(),
                         stages=array(STAGE_SCHEMA), effects=array(string(values=EFFECTS)),
                         failure_policy=string(values=('stop',)), digest=string(DIGEST))
COMPOSED_WORK_SCHEMA = obj(**WORK_SCHEMA['properties'], composition_digest=string(DIGEST))
FAULTS = (None, 'stage_failure', 'producer_crash', 'verifier_failure', 'dependency_unavailable')


def composition_proposal(owner, stages, effects=()):
    """Stages are caller-selected exact identities; this creates no approval."""
    composition = {'schema': 'myskills.composition-proposal.v1', 'owner': owner,
                   'stages': deepcopy(stages), 'effects': list(effects), 'failure_policy': 'stop'}
    composition['digest'] = digest_object(composition)
    validate_composition(composition)
    return composition


def validate_composition(composition):
    validate(composition, COMPOSITION_SCHEMA)
    stages = composition['stages']
    if not 1 <= len(stages) <= 8 or len({s['stage_id'] for s in stages}) != len(stages):
        raise ValidationError('composition requires one to eight unique stages')
    if len({s['skill']['skill_id'] for s in stages}) != len(stages):
        raise ValidationError('repeated skill requires a separate reviewed composition')
    if composition['digest'] != digest_object({k: v for k, v in composition.items() if k != 'digest'}):
        raise ValidationError('composition digest mismatch')
    for stage in stages:
        if not set(stage['effects']).issubset(composition['effects']):
            raise ValidationError('child effect escalation')
    return composition


def composed_work(proposal, composition):
    validate(proposal, WORK_SCHEMA)
    validate_composition(composition)
    if proposal['owner'] != composition['owner'] or proposal['skill'] != composition['stages'][0]['skill']:
        raise ValidationError('composition Work binding mismatch')
    return {**deepcopy(proposal), 'composition_digest': composition['digest']}


def validate_fixture_work(composition, proposal):
    validate_composition(composition)
    validate(proposal, COMPOSED_WORK_SCHEMA)
    if (proposal['owner'] != composition['owner'] or proposal['composition_digest'] != composition['digest'] or
        proposal['skill'] != composition['stages'][0]['skill']):
        raise ValidationError('composition Work binding mismatch')
    if composition['effects'] or proposal['effects'] or any(proposal['budget'].values()):
        raise ValidationError('fixture has no execution authority')


def _handoff(stage, prior_digest, source_snapshot):
    # Fixed fixture data. No Skill text, tools, models, commands or user code run.
    return {'schema': HANDOFF, 'stage_id': stage['stage_id'], 'skill': deepcopy(stage['skill']),
            'input_digest': prior_digest, 'source_snapshot': source_snapshot,
            'output': 'synthetic contract candidate', 'effects': []}


def verify_fixture_candidate(composition, proposal, candidate):
    """Separate verifier rechecks every handoff and exact identity, with no repair."""
    validate_fixture_work(composition, proposal)
    if set(candidate) != {'composition_digest', 'work_digest', 'handoffs'}:
        raise ValidationError('candidate fields invalid')
    if candidate['composition_digest'] != composition['digest'] or candidate['work_digest'] != digest_object(proposal):
        raise ValidationError('candidate binding mismatch')
    if len(candidate['handoffs']) != len(composition['stages']):
        raise ValidationError('incomplete candidate')
    previous = proposal['source_snapshot']
    for stage, handoff in zip(composition['stages'], candidate['handoffs']):
        if handoff != _handoff(stage, previous, proposal['source_snapshot']):
            raise ValidationError('handoff mismatch')
        previous = digest_object(handoff)
    return {'schema': 'myskills.fixture-proof.v1', 'composition_digest': composition['digest'],
            'work_digest': digest_object(proposal), 'candidate_digest': digest_object(candidate),
            'skills': [deepcopy(s['skill']) for s in composition['stages']], 'verdict': 'PASS',
            'scope': 'synthetic handoff contract only', 'publication': False}


class ComposedFixture:
    """Ephemeral owner-partitioned journal for contract tests, not a second Work fabric.

    Authority is supplied by the trusted harness. No method mints authority, executes
    Skill instructions, resumes a crash, publishes, or accesses external providers.
    """
    def __init__(self, owner_store, resolver, policy):
        self.store, self.resolver, self.policy = owner_store, resolver, policy
        self._records = {}

    def read(self, owner, application, work_id, generation):
        with self.store.registry._lock:
            record = self._records.get((owner, application, work_id, generation))
            if record is None:
                raise Unavailable()
            return deepcopy(record)

    def run(self, owner, composition, proposal, authority, *, now, fault=None):
        with self.store.registry._lock:
            validate_composition(composition)
            validate(proposal, COMPOSED_WORK_SCHEMA)
            if fault not in FAULTS:
                raise ValidationError('unknown fixture fault')
            if owner != composition['owner'] or owner != proposal['owner']:
                raise Unavailable()
            validate_fixture_work(composition, proposal)
            validate(authority, AUTHORITY_SCHEMA)
            if authority.get('proposal_digest') != digest_object(proposal):
                raise ValidationError('composition authority mismatch')
            key = (owner, proposal['application'], proposal['work_id'], proposal['generation'])
            request_digest = digest_object({'composition': composition, 'proposal': proposal, 'authority': authority, 'fault': fault})
            retained = self._records.get(key)
            if retained is not None:
                if retained['request_digest'] != request_digest:
                    raise ValidationError('Work identity already bound; reconcile retained result')
                return deepcopy(retained)
            session = self.store.session(owner)
            base = {k: v for k, v in proposal.items() if k != 'composition_digest'}
            base_authority = {**authority, 'proposal_digest': digest_object(base)}
            admitted = validate_admission(base, base_authority, session=session, resolver=self.resolver,
                                          policy=self.policy, now=now)
            for stage in composition['stages']:
                graph = self.resolver.eligible(session, stage['skill'], self.policy)
                if any(m['permitted_effects'] or any(m['resource_ceilings'].values()) for m in graph):
                    raise ValidationError('fixture component exceeds zero-effect envelope')
            admitted = {**admitted, 'schema': 'myskills.composed-admission-fixture.v1',
                        'base_contract_digest': admitted['proposal_digest'],
                        'proposal_digest': digest_object(proposal), 'composition_digest': composition['digest'],
                        'stages': [deepcopy(stage['skill']) for stage in composition['stages']]}
            candidate = {'composition_digest': composition['digest'], 'work_digest': digest_object(proposal), 'handoffs': []}
            record = {'request_digest': request_digest, 'proposal': deepcopy(proposal), 'composition': deepcopy(composition),
                      'admission': admitted, 'status': 'RUNNING', 'candidate': candidate, 'proof': None,
                      'publication': False, 'production_admission': False, 'attempts': 1, 'paid_operations': 0}
            self._records[key] = record
            previous = proposal['source_snapshot']
            for index, stage in enumerate(composition['stages']):
                # Recheck every stage at its handoff; never substitute a missing child.
                try:
                    self.resolver.eligible(session, stage['skill'], self.policy)
                    if index == 1 and fault == 'dependency_unavailable':
                        raise Unavailable()
                except ValidationError:
                    record['status'] = 'FAIL'
                    record['reason'] = 'exact component unavailable at handoff'
                    break
                if index == 1 and fault in ('stage_failure', 'producer_crash'):
                    record['status'] = 'UNKNOWN' if fault == 'producer_crash' else 'FAIL'
                    record['reason'] = fault
                    break
                handoff = _handoff(stage, previous, proposal['source_snapshot'])
                candidate['handoffs'].append(handoff)
                previous = digest_object(handoff)
            else:
                if fault == 'verifier_failure':
                    record['status'] = 'FAIL'
                    record['reason'] = 'independent fixture verifier unavailable; no accepted proof'
                else:
                    record['proof'] = verify_fixture_candidate(composition, proposal, candidate)
                    record['status'] = 'PASS'
            return deepcopy(record)
