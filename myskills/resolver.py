"""Metadata-first selection. A selected binding is a proposal, never Work authority."""
from __future__ import annotations
from dataclasses import dataclass
import re
from .manifest import EFFECTS, QUALIFICATION, ValidationError, binding
from .registry import Unavailable

PRIVATE_EFFECTS = frozenset('workspace.read repository.read files.read evidence.read candidate.create candidate.modify tests.execute build.execute analysis.persist'.split())
TRUST_CEILINGS = {'UNTRUSTED': frozenset(), 'COMMUNITY': PRIVATE_EFFECTS,
                  'OWNER_PRIVATE': PRIVATE_EFFECTS, 'VERIFIED_PUBLISHER': PRIVATE_EFFECTS,
                  'PLATFORM_QUALIFIED': frozenset(EFFECTS)}

@dataclass(frozen=True)
class ResolutionPolicy:
    runtime: str
    harness: str
    policy_digest: str
    corpus_digest: str
    allowed_effects: frozenset[str]
    available_capabilities: frozenset[str]
    allowed_trust: frozenset[str]
    model_route: str = 'deterministic'
    minimum_qualification: str = 'DETERMINISTIC_TESTED'
    available_dependencies: tuple = ()
    runtime_features: frozenset[str] = frozenset()
    network_hosts: frozenset[str] = frozenset()
    secret_names: frozenset[str] = frozenset()

class NoQualification:
    def lookup(self, owner, identity, policy):
        return None

class Resolver:
    def __init__(self, owner_store, qualifications=None):
        self.store = owner_store
        self.qualifications = qualifications or NoQualification()

    def eligible(self, session, identity, policy):
        r = self.store.registry
        if not r.resolution_enabled:
            raise ValidationError('resolution disabled')
        m = r.assert_available(session.owner, identity)
        if m['visibility']['scope'] == 'owner' and not r.private_resolution_enabled:
            raise ValidationError('private resolution disabled')
        graph = r.dependency_graph(session.owner, identity, runtime=policy.runtime, available=policy.available_dependencies)
        installed = {item['binding']['skill_id']: item for item in session.installed()}
        for component in graph:
            installation = installed.get(component['skill_id'])
            if not installation or not installation['enabled'] or installation['binding'] != binding(component):
                raise ValidationError('exact dependency installation disabled or unavailable')
            if component['visibility']['scope'] == 'owner' and not r.private_resolution_enabled:
                raise ValidationError('private resolution disabled')
            if any(dep['type'] != 'skill' for dep in component['dependencies']):
                raise ValidationError('external dependency qualification unavailable')
            if component['metadata_status'] != 'REVIEWED':
                raise ValidationError('metadata not reviewed')
            if policy.harness not in component['harness_compatibility']:
                raise ValidationError('harness incompatible')
            if not set(component['required_capabilities']).issubset(policy.available_capabilities):
                raise ValidationError('capability unavailable')
            if not set(component['runtime_requirements'] + component['compatibility_requirements']).issubset(policy.runtime_features):
                raise ValidationError('runtime requirements unavailable')
            if not set(component['network_requirements']['hosts']).issubset(policy.network_hosts):
                raise ValidationError('network host denied')
            if not {item['name'] for item in component['secret_requirements']}.issubset(policy.secret_names):
                raise ValidationError('secret requirement denied')
            if component['model_policy_requirements'] and policy.model_route not in component['model_policy_requirements']:
                raise ValidationError('model route incompatible')
            qualification = self.qualifications.lookup(session.owner, binding(component), policy)
            if not qualification or qualification['status'] == 'REVOKED':
                raise ValidationError('qualification unavailable')
            if qualification['status'] not in QUALIFICATION or policy.minimum_qualification not in QUALIFICATION[:-1]:
                raise ValidationError('qualification level invalid')
            if QUALIFICATION.index(qualification['status']) < QUALIFICATION.index(policy.minimum_qualification):
                raise ValidationError('qualification insufficient')
            trust = qualification['trust']
            if trust not in policy.allowed_trust or trust == 'UNTRUSTED':
                raise ValidationError('trust denied')
            requested = set(component['permitted_effects'])
            if not requested.issubset(policy.allowed_effects & TRUST_CEILINGS.get(trust, frozenset())):
                raise ValidationError('effects denied')
            if requested & set(component['prohibited_effects']):
                raise ValidationError('effects prohibited')
            if component['network_requirements']['mode'] != 'deny' and 'network.request' not in requested:
                raise ValidationError('undeclared network effect')
            if component['secret_requirements'] and 'secrets.use' not in requested:
                raise ValidationError('undeclared secret effect')
        return graph

    def resolve(self, owner, objective, policy, requested_capabilities=()):
        if not isinstance(objective, str) or len(objective) > 4096:
            raise ValidationError('invalid objective')
        session = self.store.session(owner)
        r = self.store.registry
        with r._lock:
            candidates, denied = [], []
            tokens = set(re.findall(r'[a-z0-9-]+', objective.lower())) - {'the', 'a', 'an', 'this', 'please', 'my', 'for', 'to'}
            for install in session.installed():
                if not install['enabled']:
                    continue
                identity = install['binding']
                score = 0
                try:
                    m = r.exact(owner, **identity)
                    words = set(re.findall(r'[a-z0-9-]+', ' '.join([m['name'], m['description'], *m['tags'], *m['aliases']]).lower()))
                    score = len(tokens & words)
                    if not score or not set(requested_capabilities).issubset(m['required_capabilities']):
                        continue
                    graph = self.eligible(session, identity, policy)
                    candidates.append({'binding': identity, 'score': score, 'dependencies': [binding(item) for item in graph],
                                       'reason': 'Installed, enabled, exact scoped qualification and policy checks passed.'})
                except ValidationError as error:
                    denied.append({'binding': identity, 'reason': str(error), 'score': score})
            candidates.sort(key=lambda item: (-item['score'], item['binding']['skill_id'], item['binding']['version']))
            if not candidates or max((item['score'] for item in denied), default=0) >= candidates[0]['score']:
                state = 'NO_ELIGIBLE_SKILL'
            elif len(candidates) > 1 and candidates[0]['score'] == candidates[1]['score']:
                state = 'AMBIGUOUS'
            else:
                state = 'SELECTED'
            return {'state': state, 'selected': candidates[0]['binding'] if state == 'SELECTED' else None,
                    'alternatives': candidates, 'policy_filtering': denied, 'instructions_loaded': 0, 'work_authority': None}
