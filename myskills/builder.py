"""Deterministic private authoring prototype, scoped to static package qualification."""
from copy import deepcopy
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from .catalog import legacy_manifest
from .digest import digest_object, package_digest
from .governance import RegistryAdmin
from .manifest import ValidationError, binding, validate_manifest
from .qualification import CHECKS, seal_report
from .registry import Unavailable

REFERENCE_POLICY = digest_object({'mode': 'static-package-only', 'effects': [], 'model': 'none', 'version': 1})
REFERENCE_CORPUS = digest_object({'checks': CHECKS, 'scope': 'static-private-package', 'version': 1})

class PrivateBuilder:
    def __init__(self, owner_store, qualifications):
        self.store = owner_store
        self.qualifications = qualifications
        self._drafts = {}

    def draft(self, owner, *, skill_id, version, description, instructions):
        self.store.session(owner)
        if not isinstance(instructions, str) or not 1 <= len(instructions) <= 32000:
            raise ValidationError('instructions must contain 1 to 32000 characters')
        if re.search(r'ignore (?:all |previous |the )?(?:instructions|policy|authority)|(?:sk-|ghp_)[a-zA-Z0-9]{20,}', instructions, re.I):
            raise ValidationError('instructions require security review')
        # Validate IDs before using them as filesystem paths.
        from .manifest import ID, VERSION, validate, string
        validate(skill_id, string(ID))
        validate(version, string(VERSION))
        validate(description, string())
        import json
        body = f'---\nname: {skill_id}\ndescription: {json.dumps(description)}\n---\n\n{instructions}\n'
        with TemporaryDirectory(prefix='myskills-draft-') as directory:
            root = Path(directory)
            path = root / 'skills' / skill_id
            path.mkdir(parents=True)
            (root / 'LICENSES.md').write_text('Owner-private synthetic/reference custody; no redistribution grant.\n')
            (path / 'SKILL.md').write_text(body)
            m = legacy_manifest(root, path)
            m.update(version=version, name=skill_id.replace('-', ' ').capitalize(),
                     visibility={'scope': 'owner', 'subject': owner}, trust='OWNER_PRIVATE', metadata_status='REVIEWED',
                     publisher={'publisher_id': 'owner-private', 'display_name': 'Private owner'},
                     provenance={'kind': 'owner-private', 'source': 'owner-authored', 'revision': version, 'reference': 'SKILL.md',
                                 'license': 'PRIVATE_NO_REDISTRIBUTION', 'license_references': []},
                     harness_compatibility=['myskills-reference'], runtime_requirements=['static-package-only'],
                     compatibility_requirements=[], model_policy_requirements=['deterministic'],
                     verification_requirements=list(CHECKS))
            m['digest'] = package_digest(path, m)
        validate_manifest(m)
        with self.store.registry._lock:
            key = (owner, skill_id, version)
            if key in self._drafts and self._drafts[key]['manifest'] != m:
                raise ValidationError('draft version already exists; create a successor')
            self._drafts.setdefault(key, {'manifest': deepcopy(m), 'state': 'draft', 'body': body})
        return {'binding': binding(m), 'manifest': m, 'state': 'draft', 'qualification_scope': 'static-package-only'}

    def _draft(self, owner, identity):
        key = (owner, identity['skill_id'], identity['version'])
        item = self._drafts.get(key)
        if not item or binding(item['manifest']) != identity:
            raise Unavailable()
        return item

    def validate(self, owner, identity):
        with self.store.registry._lock:
            item = self._draft(owner, identity)
            validate_manifest(item['manifest'])
            if item['state'] == 'draft':
                item['state'] = 'validated'
            return {'binding': identity, 'state': item['state'], 'limitations': ['No instruction execution or behavioral qualification.']}

    def qualify(self, owner, identity):
        with self.store.registry._lock:
            item = self._draft(owner, identity)
            if item['state'] not in ('validated', 'qualified', 'installed'):
                raise ValidationError('validate draft first')
            if item['state'] in ('qualified', 'installed'):
                if not self.qualifications.is_current(owner, identity, item['evidence']['evidence_digest']):
                    raise ValidationError('qualification revoked or unavailable')
                return deepcopy(item['evidence'])
            m = item['manifest']
            # Exercise actual deterministic boundaries; never execute the instructions.
            validate_manifest(m)
            with TemporaryDirectory(prefix='myskills-check-') as directory:
                path = Path(directory)
                (path / 'SKILL.md').write_text(item['body'])
                if package_digest(path, m) != m['digest']:
                    raise ValidationError('draft bytes changed')
            if m['permitted_effects'] or m['dependencies'] or m['secret_requirements'] or m['network_requirements']['mode'] != 'deny':
                raise ValidationError('reference qualification supports no effects or dependencies')
            if m['visibility'] != {'scope': 'owner', 'subject': owner}:
                raise Unavailable()
            from .static_pack import run_static_pack
            results = run_static_pack(m, item['body'])
            try:
                existing = self.store.registry.exact(owner, **identity)
                if existing != m:
                    raise ValidationError('private version collision')
            except Unavailable:
                RegistryAdmin(self.store.registry).add(m)
            report = seal_report({'schema': 'myskills.qualification.v1', 'binding': identity,
                'status': 'DETERMINISTIC_TESTED', 'trust': 'OWNER_PRIVATE', 'runtime': 'myskills-reference',
                'harness': 'myskills-reference', 'policy_digest': REFERENCE_POLICY, 'corpus_digest': REFERENCE_CORPUS,
                'dependencies': [identity], 'results': results,
                'author': 'private-author', 'reviewer': 'static-package-verifier', 'timestamp': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
                'limitations': ['Static package contract only; no instruction execution, models, network, production compatibility or behavioral safety established.']})
            self.qualifications.record(owner, report, authenticated_reviewer='static-package-verifier', accepted_by=owner)
            item.update(state='qualified', evidence=report)
            return deepcopy(report)

    def accept_install(self, owner, identity):
        with self.store.registry._lock:
            item = self._draft(owner, identity)
            if item['state'] not in ('qualified', 'installed'):
                raise ValidationError('qualify draft first')
            if not self.qualifications.is_current(owner, identity, item['evidence']['evidence_digest']):
                raise ValidationError('qualification revoked or unavailable')
            installed = self.store.session(owner).install(identity)
            item['state'] = 'installed'
            return installed

    def source(self, owner, identity):
        with self.store.registry._lock:
            return self._draft(owner, identity)['body']
