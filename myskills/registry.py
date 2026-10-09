"""Owner-filtered exact catalog reads. Callers supply an authenticated owner context."""
from __future__ import annotations

from copy import deepcopy
from .manifest import ValidationError, validate_manifest

class Unavailable(ValidationError):
    def __init__(self):
        super().__init__('skill unavailable')

class Registry:
    """In-process reference store; never expose this object directly to untrusted code.

    Public and owner records have separate indexes. Filtering happens before lookup,
    counting or ranking. A future network adapter must derive owner from authentication.
    """
    def __init__(self, manifests=()):
        self._public = {}
        self._owners = {}
        for manifest in manifests:
            self._add(manifest)

    def _add(self, manifest):
        validate_manifest(manifest)
        visibility = manifest['visibility']
        if visibility['scope'] not in ('public', 'owner'):
            raise ValidationError('sharing scope not implemented')
        partition = self._public if visibility['scope'] == 'public' else self._owners.setdefault(visibility['subject'], {})
        key = (manifest['skill_id'], manifest['version'])
        if key in partition:
            raise ValidationError('duplicate immutable identity')
        partition[key] = deepcopy(manifest)

    def _visible(self, owner):
        if not isinstance(owner, str) or not owner:
            raise Unavailable()
        # Public IDs and private IDs cannot shadow one another within a scope.
        return [*self._public.values(), *self._owners.get(owner, {}).values()]

    def enumerate(self, owner):
        return deepcopy(sorted(self._visible(owner), key=lambda m: (m['skill_id'], m['version'], m['digest'])))

    def search(self, owner, query='', **filters):
        allowed = {'trust', 'category', 'publisher', 'capability', 'runtime', 'qualification'}
        if set(filters) - allowed:
            raise ValidationError('unknown search filter')
        result = []
        words = query.lower().split()
        for m in self._visible(owner):
            terms = ' '.join([m['name'], m['description'], m['publisher']['display_name'], *m['categories'], *m['tags'], *m['aliases'], *m['required_capabilities']]).lower()
            fields = {'trust': [m['trust']], 'category': m['categories'], 'publisher': [m['publisher']['publisher_id']],
                      'capability': m['required_capabilities'], 'runtime': m['harness_compatibility'], 'qualification': [m['qualification']['status']]}
            if all(word in terms for word in words) and all(value in fields[key] for key, value in filters.items()):
                result.append(deepcopy(m))
        return sorted(result, key=lambda m: (m['skill_id'], m['version']))

    def exact(self, owner, skill_id, version, digest=None):
        matches = [m for m in self._visible(owner) if m['skill_id'] == skill_id and m['version'] == version and (digest is None or m['digest'] == digest)]
        if len(matches) != 1:
            raise Unavailable()
        return deepcopy(matches[0])

    def dependency_graph(self, owner, identity, *, runtime, available=(), max_nodes=64):
        """Resolve the complete exact graph without installing or invoking anything."""
        resolved, visiting = {}, set()
        def visit(identity, parent=None):
            key = (identity['skill_id'], identity['version'], identity['digest'])
            if key in visiting:
                raise ValidationError('dependency cycle')
            m = self.exact(owner, *key)
            if m['lifecycle'] == 'revoked' or m['qualification']['status'] == 'REVOKED':
                raise ValidationError('revoked dependency')
            if runtime not in m['harness_compatibility']:
                raise ValidationError('incompatible dependency runtime')
            if parent and not set(m['permitted_effects']).issubset(parent['permitted_effects']):
                raise ValidationError('dependency effect escalation')
            if parent and m['trust'] != parent['trust']:
                raise ValidationError('dependency trust mismatch')
            if key in resolved:
                return
            if len(resolved) + len(visiting) >= max_nodes:
                raise ValidationError('dependency graph limit')
            visiting.add(key)
            for dependency in m['dependencies']:
                if dependency['type'] == 'skill':
                    visit({'skill_id': dependency['dependency_id'], 'version': dependency['version'], 'digest': dependency['digest']}, m)
                elif dependency['required'] and (dependency['dependency_id'], dependency['version'], dependency['digest']) not in available:
                    raise ValidationError('required dependency unavailable')
            visiting.remove(key)
            resolved[key] = m
        visit(identity)
        return deepcopy(list(resolved.values()))
