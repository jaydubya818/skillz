"""Executable negative tests for the static, no-effect private-package contract."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from .digest import package_digest
from .manifest import ValidationError, validate_manifest

def validate_static_envelope(manifest):
    validate_manifest(manifest)
    if (manifest['visibility']['scope'] != 'owner' or manifest['trust'] != 'OWNER_PRIVATE' or
        manifest['permitted_effects'] or manifest['secret_requirements'] or manifest['dependencies'] or
        manifest['network_requirements'] != {'mode': 'deny', 'hosts': []} or any(manifest['resource_ceilings'].values()) or
        manifest['harness_compatibility'] != ['myskills-reference'] or manifest['runtime_requirements'] != ['static-package-only'] or
        manifest['model_policy_requirements'] != ['deterministic']):
        raise ValidationError('static reviewer envelope exceeded')

def run_static_pack(manifest, body):
    validate_static_envelope(manifest)
    validate_manifest(manifest)
    results = {'schema': 'PASS'}
    if manifest['visibility']['scope'] != 'owner' or manifest['trust'] != 'OWNER_PRIVATE':
        raise ValidationError('private contract required')
    results['contract'] = 'PASS'
    if manifest['permitted_effects'] or manifest['secret_requirements'] or manifest['network_requirements'] != {'mode': 'deny', 'hosts': []} or any(manifest['resource_ceilings'].values()):
        raise ValidationError('static qualification cannot grant effects')
    results['effects'] = 'PASS'
    if manifest['dependencies']:
        raise ValidationError('external dependencies unsupported by static pack')
    results['dependencies'] = 'PASS'
    if manifest['harness_compatibility'] != ['myskills-reference'] or manifest['runtime_requirements'] != ['static-package-only'] or manifest['model_policy_requirements'] != ['deterministic']:
        raise ValidationError('static runtime mismatch')
    results['runtime'] = 'PASS'
    with TemporaryDirectory(prefix='myskills-static-pack-') as directory:
        root = Path(directory)
        (root / 'SKILL.md').write_text(body)
        digest = package_digest(root, manifest)
        if digest != manifest['digest'] or package_digest(root, manifest) != digest:
            raise ValidationError('static package digest mismatch')
        results['deterministic'] = 'PASS'
        (root / 'SKILL.md').write_text(body + '\nTampered instruction\n')
        if package_digest(root, manifest) == digest:
            raise ValidationError('tampering was not detected')
    invalid = deepcopy(manifest)
    invalid['authority'] = 'all'
    try:
        validate_manifest(invalid)
    except ValidationError:
        results['adversarial'] = 'PASS'
    else:
        raise ValidationError('authority field accepted')
    invalid = deepcopy(manifest)
    invalid['secret_requirements'] = [{'name': 'key', 'value': 'fixture-only'}]
    try:
        validate_manifest(invalid)
    except ValidationError:
        results['security'] = 'PASS'
    else:
        raise ValidationError('credential value accepted')
    return results
