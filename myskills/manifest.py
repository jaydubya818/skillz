"""Closed, versioned manifest contract; standard-library validation and JSON schema."""
from __future__ import annotations

import json
import re

TRUST = ('PLATFORM_QUALIFIED', 'OWNER_PRIVATE', 'VERIFIED_PUBLISHER', 'COMMUNITY', 'UNTRUSTED')
QUALIFICATION = ('NOT_EVALUATED', 'STATIC_VALIDATED', 'DETERMINISTIC_TESTED', 'SANDBOX_QUALIFIED', 'INTEGRATION_QUALIFIED', 'LIVE_QUALIFIED', 'REVOKED')
LIFECYCLE = ('draft', 'qualified', 'published', 'deprecated', 'revoked')
EFFECTS = tuple('workspace.read repository.read files.read evidence.read web.read connector.read candidate.create candidate.modify tests.execute build.execute analysis.persist network.request message.send email.send external_api.write branch.push pull_request.create pull_request.modify review.submit merge.execute deployment.create deployment.promote infrastructure.modify secrets.use owner_computer.use credential.rotate billing.modify identity.modify'.split())
ID = r'^[a-z0-9]+(?:-[a-z0-9]+)*$'
VERSION = r'^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-[a-zA-Z0-9.-]+)?(?:\+[a-zA-Z0-9.-]+)?$'
DIGEST = r'^sha256:[a-f0-9]{64}$'
CAPABILITY = r'^[a-z][a-z0-9-]*(?:\.[a-z][a-z0-9-]*)+$'

class ValidationError(ValueError):
    """Untrusted input failed the governance contract."""

def string(pattern=None, values=None, empty=False):
    result = {'type': 'string', 'minLength': 0 if empty else 1, 'maxLength': 4096}
    if pattern:
        result['pattern'] = pattern
    if values:
        result['enum'] = list(values)
    return result

def array(items=None):
    return {'type': 'array', 'items': items or string(), 'uniqueItems': True, 'maxItems': 1000}

def obj(**properties):
    return {'type': 'object', 'properties': properties, 'required': list(properties), 'additionalProperties': False}

BINDING_SCHEMA = obj(skill_id=string(ID), version=string(VERSION), digest=string(DIGEST))
DEPENDENCY_SCHEMA = obj(
    dependency_id=string(r'^[a-z0-9]+(?:[.-][a-z0-9]+)*$'), type=string(values=('skill', 'runtime', 'mcp', 'service', 'application')),
    version=string(), digest=string(empty=True), provider=string(empty=True),
    required_capabilities=array(string(CAPABILITY)), authentication=string(values=('none', 'owner_grant', 'credential_handle')),
    network_hosts=array(), data_exposed=array(), effects=array(string(values=EFFECTS)),
    required={'type': 'boolean'}, runtimes=array(), qualification=string(values=QUALIFICATION),
)
SCHEMA = obj(
    schema=string(values=('myskills.manifest.v1',)), skill_id=string(ID), version=string(VERSION), digest=string(DIGEST),
    name=string(), description=string(), publisher=obj(publisher_id=string(ID), display_name=string()),
    provenance=obj(kind=string(values=('original', 'vendored', 'adapted', 'owner-private')),
                   source=string(), revision=string(), reference=string(), license=string(), license_references=array()),
    visibility=obj(scope=string(values=('public', 'owner', 'team', 'organization')), subject=string(empty=True)),
    trust=string(values=TRUST), lifecycle=string(values=LIFECYCLE),
    inputs=array(obj(name=string(), format=string(), required={'type': 'boolean'})),
    outputs=array(obj(name=string(), format=string(), required={'type': 'boolean'})),
    required_capabilities=array(string(CAPABILITY)), permitted_effects=array(string(values=EFFECTS)),
    prohibited_effects=array(string(values=EFFECTS)), scope_constraints=obj(repository_paths=array(), file_paths=array()),
    network_requirements=obj(mode=string(values=('deny', 'allowlist')), hosts=array()),
    secret_requirements=array(obj(name=string(ID), purpose=string(), authentication=string(values=('credential_handle',)))),
    runtime_requirements=array(), harness_compatibility=array(), model_policy_requirements=array(),
    verification_requirements=array(), resource_ceilings=obj(seconds={'type': 'integer', 'minimum': 0}, operations={'type': 'integer', 'minimum': 0}),
    compatibility_requirements=array(), dependencies=array(DEPENDENCY_SCHEMA),
    qualification=obj(status=string(values=QUALIFICATION), evidence=array(string(DIGEST))),
    metadata_status=string(values=('UNREVIEWED', 'REVIEWED')), categories=array(), tags=array(), aliases=array(string(ID)),
)
SCHEMA.update({'$schema': 'https://json-schema.org/draft/2020-12/schema', 'title': 'SkillManifest v1'})

def validate(value, schema, path='$'):
    expected = schema['type']
    types = {'object': dict, 'array': list, 'string': str, 'integer': int, 'boolean': bool}
    if type(value) is not types[expected]:
        raise ValidationError(f'{path}: expected {expected}')
    if 'enum' in schema and value not in schema['enum']:
        raise ValidationError(f'{path}: unknown value')
    if expected == 'object':
        if set(value) != set(schema['required']):
            raise ValidationError(f'{path}: missing or unknown fields')
        for key, item in value.items():
            validate(item, schema['properties'][key], f'{path}.{key}')
    elif expected == 'array':
        if len(value) > schema['maxItems'] or len({json.dumps(v, sort_keys=True) for v in value}) != len(value):
            raise ValidationError(f'{path}: duplicate or too many entries')
        for index, item in enumerate(value):
            validate(item, schema['items'], f'{path}[{index}]')
    elif expected == 'string':
        if not schema['minLength'] <= len(value) <= schema['maxLength'] or ('pattern' in schema and not re.fullmatch(schema['pattern'], value)):
            raise ValidationError(f'{path}: invalid string')
        if any(ord(c) < 32 and c not in '\n\t' for c in value):
            raise ValidationError(f'{path}: control characters')
    elif expected == 'integer' and value < schema['minimum']:
        raise ValidationError(f'{path}: below minimum')

def validate_manifest(manifest):
    validate(manifest, SCHEMA)
    visibility = manifest['visibility']
    if (visibility['scope'] == 'public') != (visibility['subject'] == ''):
        raise ValidationError('visibility subject mismatch')
    if manifest['trust'] == 'OWNER_PRIVATE' and visibility['scope'] != 'owner':
        raise ValidationError('owner-private trust requires owner scope')
    if set(manifest['permitted_effects']) & set(manifest['prohibited_effects']):
        raise ValidationError('effect both requested and prohibited')
    network = manifest['network_requirements']
    if (network['mode'] == 'deny' and network['hosts']) or (network['mode'] == 'allowlist' and not network['hosts']):
        raise ValidationError('network mode mismatch')
    for host in network['hosts']:
        if not re.fullmatch(r'[a-z0-9]+(?:[.-][a-z0-9]+)*', host):
            raise ValidationError('network host must be an exact hostname')
    for dependency in manifest['dependencies']:
        if dependency['type'] == 'skill':
            if not re.fullmatch(ID, dependency['dependency_id']) or not re.fullmatch(VERSION, dependency['version']) or not re.fullmatch(DIGEST, dependency['digest']):
                raise ValidationError('skill dependencies must pin version and digest')
    return manifest

def binding(manifest):
    return {key: manifest[key] for key in ('skill_id', 'version', 'digest')}
