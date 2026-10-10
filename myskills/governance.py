"""Serialized governance decisions around immutable catalog records.

Administrator methods are a trusted server boundary, never agent-callable tools.
The reference implementation is in-memory; production persistence is not enabled.
"""
from __future__ import annotations
from copy import deepcopy
from threading import RLock
from .manifest import ValidationError, binding
from .registry import Registry, Unavailable

TRANSITIONS = {'draft': {'qualified', 'revoked'}, 'qualified': {'published', 'deprecated', 'revoked'},
               'published': {'deprecated', 'revoked'}, 'deprecated': {'revoked'}, 'revoked': set()}
SECURITY_FIELDS = ('required_capabilities', 'permitted_effects', 'prohibited_effects', 'scope_constraints',
                   'network_requirements', 'secret_requirements', 'runtime_requirements', 'harness_compatibility',
                   'model_policy_requirements', 'verification_requirements', 'resource_ceilings',
                   'dependencies', 'trust', 'qualification', 'publisher', 'provenance')

def identity_key(identity):
    from .manifest import BINDING_SCHEMA, validate
    validate(identity, BINDING_SCHEMA)
    return (identity['skill_id'], identity['version'], identity['digest'])

def permission_diff(old, new):
    if old['skill_id'] != new['skill_id']:
        raise ValidationError('updates must retain skill identity')
    changes = {field: {'before': deepcopy(old[field]), 'after': deepcopy(new[field])}
               for field in SECURITY_FIELDS if old[field] != new[field]}
    return {'from': binding(old), 'to': binding(new), 'security_changes': changes,
            'requires_review': bool(changes), 'automatic_update': False}

class GovernedRegistry(Registry):
    def __init__(self, manifests=()):
        self._lock = RLock()
        self._states = {}
        self._revoked_publishers = set()
        self._revoked_dependencies = set()
        self._events = []
        self.resolution_enabled = True
        self.installation_enabled = True
        self.private_resolution_enabled = True
        super().__init__(manifests)

    def enumerate(self, owner):
        with self._lock:
            return super().enumerate(owner)

    def search(self, owner, query='', **filters):
        with self._lock:
            return super().search(owner, query, **filters)

    def exact(self, owner, skill_id, version, digest=None):
        with self._lock:
            return super().exact(owner, skill_id, version, digest)

    def _event(self, kind, subject):
        self._events.append({'sequence': len(self._events) + 1, 'kind': kind, 'subject': deepcopy(subject)})

    def _scope_key(self, manifest):
        return (manifest['visibility']['subject'], *identity_key(binding(manifest)))

    def lifecycle(self, owner, identity):
        with self._lock:
            m = self.exact(owner, *identity_key(identity))
            return self._states.get(self._scope_key(m), m['lifecycle'])

    def assert_available(self, owner, identity, *, installing=False):
        with self._lock:
            if installing and not self.installation_enabled:
                raise Unavailable()
            active, checked = set(), {}
            def visit(identity):
                key = identity_key(identity)
                if key in active or len(active) + len(checked) >= 64:
                    raise Unavailable()
                if key in checked:
                    return checked[key]
                m = self.exact(owner, *key)
                if self.lifecycle(owner, identity) == 'revoked' or m['qualification']['status'] == 'REVOKED':
                    raise Unavailable()
                if m['publisher']['publisher_id'] in self._revoked_publishers:
                    raise Unavailable()
                active.add(key)
                for dep in m['dependencies']:
                    if dep['dependency_id'] in self._revoked_dependencies:
                        raise Unavailable()
                    if dep['type'] == 'skill' and dep['required']:
                        visit({'skill_id': dep['dependency_id'], 'version': dep['version'], 'digest': dep['digest']})
                active.remove(key)
                checked[key] = m
                return m
            return visit(identity)

    def dependency_graph(self, owner, identity, **kwargs):
        with self._lock:
            graph = super().dependency_graph(owner, identity, **kwargs)
            for m in graph:
                self.assert_available(owner, binding(m))
            return graph

    def updates(self, owner, identity):
        with self._lock:
            current = self.exact(owner, *identity_key(identity))
            result = []
            for m in self._visible(owner):
                if m['skill_id'] == current['skill_id'] and m['version'] != current['version'] and m['visibility'] == current['visibility']:
                    try:
                        self.assert_available(owner, binding(m), installing=True)
                    except Unavailable:
                        continue
                    result.append(permission_diff(current, m))
            return sorted(result, key=lambda item: item['to']['version'])

class RegistryAdmin:
    """Trusted operator API. Not exposed through owner or conversational actions."""
    def __init__(self, registry):
        self.registry = registry

    def add(self, manifest):
        r = self.registry
        with r._lock:
            r._add(manifest)
            r._event('version.recorded', {'visibility': manifest['visibility'], 'binding': binding(manifest)})

    def transition(self, owner, identity, state):
        r = self.registry
        with r._lock:
            m = r.exact(owner, *identity_key(identity))
            current = r.lifecycle(owner, identity)
            if current == state:
                return
            if state not in TRANSITIONS.get(current, set()):
                raise ValidationError('invalid lifecycle transition')
            if state == 'qualified':
                raise ValidationError('qualification requires scoped evidence')
            r._states[r._scope_key(m)] = state
            r._event('lifecycle.' + state, {'visibility': m['visibility'], 'binding': identity})

    def revoke_publisher(self, publisher_id):
        r = self.registry
        with r._lock:
            if publisher_id not in r._revoked_publishers:
                r._revoked_publishers.add(publisher_id)
                r._event('publisher.revoked', {'publisher_id': publisher_id})

    def revoke_dependency(self, dependency_id):
        r = self.registry
        with r._lock:
            if dependency_id not in r._revoked_dependencies:
                r._revoked_dependencies.add(dependency_id)
                r._event('dependency.revoked', {'dependency_id': dependency_id})
