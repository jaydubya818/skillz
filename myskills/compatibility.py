"""Inactive next-version contract. This is not accepted by the frozen live protocol."""
from copy import deepcopy
from .digest import digest_object
from .manifest import BINDING_SCHEMA, DIGEST, EFFECTS, ValidationError, array, obj, string, validate

WORK_SCHEMA = obj(
    schema=string(values=('myskills.work-proposal.v1',)), owner=string(), application=string(), work_id=string(),
    generation={'type': 'integer', 'minimum': 1}, workspace=string(), source_snapshot=string(DIGEST),
    skill=BINDING_SCHEMA, factory_version=string(DIGEST), execution_provider=string(values=('deterministic-fixture',)),
    harness=string(), model_route=string(values=('deterministic',)), effects=array(string(values=EFFECTS)),
    budget=obj(operations={'type': 'integer', 'minimum': 0}, paid_operations={'type': 'integer', 'minimum': 0}),
    expires_at={'type': 'integer', 'minimum': 0},
)
AUTHORITY_SCHEMA = obj(schema=string(values=('myskills.authority-fixture.v1',)),
    proposal_digest=string(DIGEST), owner=string(), publication={'type': 'boolean'},
    effects=array(string(values=EFFECTS)), expires_at={'type': 'integer', 'minimum': 0})

def work_proposal(selection, **context):
    if selection['state'] != 'SELECTED' or not selection['selected']:
        raise ValidationError('exact selection required')
    proposal = {'schema': 'myskills.work-proposal.v1', **deepcopy(context), 'skill': deepcopy(selection['selected'])}
    validate(proposal, WORK_SCHEMA)
    if proposal['budget']['paid_operations'] != 0:
        raise ValidationError('paid qualification disabled')
    return proposal

def validate_admission(proposal, authority, *, session, resolver, policy, now):
    with session.registry._lock:
        return _validate_admission(proposal, authority, session=session, resolver=resolver, policy=policy, now=now)

def _validate_admission(proposal, authority, *, session, resolver, policy, now):
    validate(proposal, WORK_SCHEMA)
    # Authority is an authenticated external fixture input. Nothing here creates it.
    validate(authority, AUTHORITY_SCHEMA)
    if authority['schema'] != 'myskills.authority-fixture.v1' or authority['owner'] != session.owner or proposal['owner'] != session.owner:
        raise ValidationError('authority owner mismatch')
    if authority['publication'] is not False or authority['proposal_digest'] != digest_object(proposal):
        raise ValidationError('authority binding mismatch')
    if type(authority['expires_at']) is not int or min(authority['expires_at'], proposal['expires_at']) <= now:
        raise ValidationError('authority expired')
    if proposal['harness'] != policy.harness or proposal['model_route'] != policy.model_route or proposal['budget']['paid_operations'] != 0:
        raise ValidationError('runtime route mismatch')
    graph = resolver.eligible(session, proposal['skill'], policy)
    if any(proposal['budget']['operations'] > m['resource_ceilings']['operations'] for m in graph):
        raise ValidationError('skill operation ceiling exceeded')
    root = next(m for m in graph if m['skill_id'] == proposal['skill']['skill_id'])
    if not set(proposal['effects']).issubset(set(root['permitted_effects']) & policy.allowed_effects & set(authority['effects'])):
        raise ValidationError('authority effect escalation')
    return {'proposal_digest': digest_object(proposal), 'skill': deepcopy(proposal['skill']),
            'dependencies': [dict(skill_id=m['skill_id'], version=m['version'], digest=m['digest']) for m in graph],
            'factory_version': proposal['factory_version'], 'publication': False, 'production_admission': False}

def relay_advertisement(manifest):
    if manifest['visibility']['scope'] != 'public':
        raise ValidationError('private skill advertisement forbidden')
    return {'schema': 'myskills.advertisement-proposal.v1', 'skill': {key: manifest[key] for key in ('skill_id', 'version', 'digest')},
            'capabilities': list(manifest['required_capabilities']), 'install_authority': False, 'work_authority': False,
            'relay_registration_extension': 'NOT_ACTIVATED'}
