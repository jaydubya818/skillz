"""One action service for the local UI and conversational clients."""
from copy import deepcopy
from .builder import PrivateBuilder
from .owner import OwnerStore
from .qualification import QualificationStore
from .manifest import ValidationError, binding

class Application:
    def __init__(self, registry, owner='local-prototype-owner'):
        self.registry = registry
        self.owner = owner
        self.store = OwnerStore(registry)
        self.session = self.store.session(owner)
        self.qualifications = QualificationStore(registry, reviewers=['static-package-verifier'])
        self.builder = PrivateBuilder(self.store, self.qualifications)

    def execute(self, action, params):
        if not isinstance(params, dict):
            raise ValidationError('parameters must be an object')
        methods = {
            'search': self.search, 'detail': self.detail, 'installed': self.session.installed,
            'install': self.session.install, 'enable': self.session.set_enabled,
            'uninstall': self.session.uninstall, 'updates': self.updates,
            'review_update': self.session.review_update, 'update': self.session.update,
            'my_skills': self.my_skills, 'draft': self.draft, 'validate': self.validate,
            'qualify': self.qualify, 'accept_install': self.accept_install,
        }
        if action not in methods:
            raise ValidationError('action unavailable')
        return methods[action](**params)

    def search(self, query=''):
        if not isinstance(query, str) or len(query) > 1024:
            raise ValidationError('search is too long')
        return self.registry.search(self.owner, query)

    def detail(self, identity):
        m = self.registry.exact(self.owner, **identity)
        installed = next((item for item in self.session.installed() if item['binding']['skill_id'] == identity['skill_id']), None)
        evidence = self.qualifications.evidence(self.owner, identity)
        current = [report['evidence_digest'] for report in evidence if self._evidence_current(identity, report['evidence_digest'])]
        return {'manifest': m, 'lifecycle': self.registry.lifecycle(self.owner, identity),
                'evidence': evidence, 'current_evidence': current,
                'installation': installed if installed and installed['binding'] == identity else None,
                'other_installation': installed if installed and installed['binding'] != identity else None}

    def _evidence_current(self, identity, evidence_digest):
        try:
            return self.qualifications.is_current(self.owner, identity, evidence_digest)
        except ValidationError:
            return False


    def updates(self):
        return [{'installation': item, 'versions': self.registry.updates(self.owner, item['binding'])}
                for item in self.session.installed() if self.registry.updates(self.owner, item['binding'])]

    def my_skills(self):
        with self.registry._lock:
            records = []
            installed = [entry['binding'] for entry in self.session.installed()]
            for (owner, _, _), item in self.builder._drafts.items():
                if owner != self.owner:
                    continue
                state = item['state']
                if state in ('qualified', 'installed'):
                    identity = binding(item['manifest'])
                    state = 'installed' if identity in installed else 'qualified'
                    if not self._evidence_current(identity, item['evidence']['evidence_digest']):
                        state = 'qualification revoked'
                records.append({'manifest': item['manifest'], 'state': state})
            return deepcopy(records)

    def draft(self, skill_id, version, description, instructions):
        return self.builder.draft(self.owner, skill_id=skill_id, version=version, description=description, instructions=instructions)

    def validate(self, identity):
        return self.builder.validate(self.owner, identity)

    def qualify(self, identity):
        return self.builder.qualify(self.owner, identity)

    def accept_install(self, identity):
        return self.builder.accept_install(self.owner, identity)
