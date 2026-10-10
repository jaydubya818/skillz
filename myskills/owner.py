"""Authenticated-owner reference sessions; installation never creates authority."""
from copy import deepcopy
from .digest import digest_object
from .governance import identity_key, permission_diff
from .manifest import ValidationError, binding
from .registry import Unavailable

class OwnerStore:
    def __init__(self, registry):
        self.registry = registry
        self._installations = {}
        self._revision = {}

    def session(self, authenticated_owner):
        if not isinstance(authenticated_owner, str) or not authenticated_owner:
            raise Unavailable()
        return OwnerSession(self, authenticated_owner)

class OwnerSession:
    """Obtain this only after authentication. Owner is fixed for this session."""
    def __init__(self, store, owner):
        self._store, self.owner = store, owner
        self.registry = store.registry

    def _records(self):
        return self._store._installations.setdefault(self.owner, {})

    def _next_revision(self, skill_id):
        key = (self.owner, skill_id)
        revision = self._store._revision.get(key, 0) + 1
        self._store._revision[key] = revision
        return revision

    def installed(self):
        with self.registry._lock:
            return deepcopy(sorted(self._records().values(), key=lambda item: item['binding']['skill_id']))

    def install(self, identity):
        with self.registry._lock:
            m = self.registry.assert_available(self.owner, identity, installing=True)
            existing = self._records().get(m['skill_id'])
            if existing:
                if existing['binding'] != identity:
                    raise ValidationError('use reviewed update for another version')
                return deepcopy(existing)
            item = {'binding': binding(m), 'enabled': False, 'revision': self._next_revision(m['skill_id'])}
            self._records()[m['skill_id']] = item
            return deepcopy(item)

    def _installed(self, skill_id, expected_revision):
        item = self._records().get(skill_id)
        if not item:
            raise Unavailable()
        if item['revision'] != expected_revision:
            raise ValidationError('stale installation decision')
        return item

    def set_enabled(self, skill_id, enabled, expected_revision):
        if type(enabled) is not bool:
            raise ValidationError('enabled must be boolean')
        with self.registry._lock:
            item = self._installed(skill_id, expected_revision)
            if enabled:
                self.registry.assert_available(self.owner, item['binding'])
            if item['enabled'] != enabled:
                item['enabled'] = enabled
                item['revision'] = self._next_revision(skill_id)
            return deepcopy(item)

    def uninstall(self, skill_id, expected_revision):
        with self.registry._lock:
            if skill_id not in self._records():
                return
            self._installed(skill_id, expected_revision)
            del self._records()[skill_id]
            self._next_revision(skill_id)

    def review_update(self, skill_id, target, expected_revision):
        with self.registry._lock:
            item = self._installed(skill_id, expected_revision)
            old = self.registry.exact(self.owner, **item['binding'])
            new = self.registry.assert_available(self.owner, target, installing=True)
            if old['visibility'] != new['visibility'] or old['publisher'] != new['publisher']:
                raise ValidationError('update origin mismatch')
            review = {'revision': item['revision'], 'diff': permission_diff(old, new)}
            return {**review, 'decision_digest': digest_object(review)}

    def update(self, skill_id, target, expected_revision, decision_digest):
        with self.registry._lock:
            review = self.review_update(skill_id, target, expected_revision)
            if review['decision_digest'] != decision_digest:
                raise ValidationError('update decision mismatch')
            item = self._installed(skill_id, expected_revision)
            if item['binding'] == target:
                return deepcopy(item)
            # New versions begin disabled; existing Work retains its old binding.
            item.update(binding=deepcopy(target), enabled=False, revision=self._next_revision(skill_id))
            return deepcopy(item)
