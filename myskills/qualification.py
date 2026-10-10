"""Scoped, append-only evidence behind a trusted verifier/acceptance boundary."""
from copy import deepcopy
from datetime import datetime
from .digest import digest_object
from .governance import identity_key
from .manifest import QUALIFICATION, TRUST, ValidationError, binding
from .registry import Unavailable

CHECKS = ('contract', 'schema', 'deterministic', 'effects', 'adversarial', 'runtime', 'dependencies', 'security')
REPORT_FIELDS = {'schema', 'binding', 'status', 'trust', 'runtime', 'harness', 'policy_digest', 'corpus_digest',
                 'dependencies', 'results', 'author', 'reviewer', 'timestamp', 'limitations', 'evidence_digest'}

class QualificationStore:
    """Trusted backend service. Digests prove integrity, not reviewer authenticity.

    The adapter must authenticate reviewer and acceptance principals before record().
    Neither method nor its principals are exposed as owner/agent request fields.
    """
    def __init__(self, registry, *, reviewers=(), platform_acceptors=(), reviewer_limits=None):
        self.registry = registry
        self._reviewers = frozenset(reviewers)
        self._acceptors = frozenset(platform_acceptors)
        self._limits = deepcopy(reviewer_limits or {})
        self._records = {}
        self._revoked = set()

    def record(self, owner, report, *, authenticated_reviewer, accepted_by):
        r = self.registry
        with r._lock:
            if set(report) != REPORT_FIELDS or report['schema'] != 'myskills.qualification.v1':
                raise ValidationError('invalid evidence shape')
            if authenticated_reviewer not in self._reviewers or report['reviewer'] != authenticated_reviewer:
                raise ValidationError('reviewer not authorized')
            if not isinstance(report['author'], str) or not report['author'] or report['author'] == authenticated_reviewer:
                raise ValidationError('independent reviewer required')
            if report['status'] not in QUALIFICATION[1:-1] or report['trust'] not in TRUST:
                raise ValidationError('invalid qualification decision')
            limit = self._limits.get(authenticated_reviewer, {'statuses': ['STATIC_VALIDATED', 'DETERMINISTIC_TESTED'], 'trust': ['COMMUNITY', 'OWNER_PRIVATE']})
            if report['status'] not in limit['statuses'] or report['trust'] not in limit['trust']:
                raise ValidationError('reviewer qualification scope exceeded')
            if authenticated_reviewer == 'static-package-verifier' and (report['runtime'] != 'myskills-reference' or report['harness'] != 'myskills-reference'):
                raise ValidationError('static reviewer cannot qualify another runtime')
            if report['trust'] == 'PLATFORM_QUALIFIED' and (accepted_by not in self._acceptors or report['status'] not in ('SANDBOX_QUALIFIED', 'INTEGRATION_QUALIFIED', 'LIVE_QUALIFIED')):
                raise ValidationError('platform promotion requires independent sandbox qualification and acceptance')
            if report['trust'] != 'PLATFORM_QUALIFIED' and accepted_by != owner:
                raise ValidationError('owner acceptance required')
            m = r.assert_available(owner, report['binding'])
            if authenticated_reviewer == 'static-package-verifier':
                from .static_pack import validate_static_envelope
                validate_static_envelope(m)
            if report['trust'] == 'OWNER_PRIVATE' and m['visibility'] != {'scope': 'owner', 'subject': owner}:
                raise ValidationError('private qualification owner mismatch')
            if set(report['results']) != set(CHECKS) or any(value != 'PASS' for value in report['results'].values()):
                raise ValidationError('qualification checks incomplete')
            if not isinstance(report['limitations'], list) or not report['limitations'] or not all(isinstance(x, str) and x for x in report['limitations']):
                raise ValidationError('known limitations required')
            try:
                stamp = datetime.fromisoformat(report['timestamp'].replace('Z', '+00:00'))
                if stamp.tzinfo is None:
                    raise ValueError()
            except (ValueError, TypeError, AttributeError):
                raise ValidationError('timestamp must include timezone') from None
            from .manifest import DIGEST, validate, string
            for field in ('policy_digest', 'corpus_digest', 'evidence_digest'):
                validate(report[field], string(DIGEST), field)
            for field in ('runtime', 'harness'):
                validate(report[field], string(), field)
            if report['runtime'] not in m['harness_compatibility'] or report['harness'] not in m['harness_compatibility']:
                raise ValidationError('evidence runtime mismatch')
            expected_dependencies = [binding(item) for item in r.dependency_graph(owner, report['binding'], runtime=report['runtime'])]
            if report['dependencies'] != expected_dependencies:
                raise ValidationError('evidence dependency mismatch')
            expected = digest_object({k: v for k, v in report.items() if k != 'evidence_digest'})
            if report['evidence_digest'] != expected:
                raise ValidationError('evidence tampered')
            scope = '' if report['trust'] == 'PLATFORM_QUALIFIED' and m['visibility']['scope'] == 'public' else owner
            key = (scope, report['evidence_digest'])
            if key in self._records:
                if self._records[key] != report:
                    raise ValidationError('immutable evidence conflict')
                return report['evidence_digest']
            self._records[key] = deepcopy(report)
            r._event('qualification.recorded', {'visibility': {'scope': 'public' if not scope else 'owner', 'subject': scope}, 'binding': binding(m), 'evidence_digest': report['evidence_digest']})
            return report['evidence_digest']

    def evidence(self, owner, identity):
        with self.registry._lock:
            m = self.registry.exact(owner, *identity_key(identity))
            records = []
            for (scope, stored_digest), report in self._records.items():
                if scope not in ('', owner) or report.get('binding') != identity:
                    continue
                if set(report) != REPORT_FIELDS or stored_digest != report['evidence_digest'] or stored_digest != digest_object({k: v for k, v in report.items() if k != 'evidence_digest'}):
                    raise ValidationError('qualification store integrity failure')
                limit = self._limits.get(report['reviewer'], {'statuses': ['STATIC_VALIDATED', 'DETERMINISTIC_TESTED'], 'trust': ['COMMUNITY', 'OWNER_PRIVATE']})
                if report['reviewer'] not in self._reviewers or report['status'] not in limit['statuses'] or report['trust'] not in limit['trust']:
                    raise ValidationError('qualification reviewer scope failure')
                if report['reviewer'] == 'static-package-verifier':
                    from .static_pack import validate_static_envelope
                    validate_static_envelope(m)
                records.append(report)
            return deepcopy(records)


    def is_current(self, owner, identity, evidence_digest):
        with self.registry._lock:
            self.registry.assert_available(owner, identity)
            return evidence_digest not in self._revoked and any(report['evidence_digest'] == evidence_digest for report in self.evidence(owner, identity))

    def lookup(self, owner, identity, policy):
        with self.registry._lock:
            records = self.evidence(owner, identity)
            eligible = [report for report in records if report['evidence_digest'] == digest_object({k: v for k, v in report.items() if k != 'evidence_digest'}) and report['evidence_digest'] not in self._revoked and
                        all(report[field] == getattr(policy, field) for field in ('runtime', 'harness', 'policy_digest', 'corpus_digest'))]
            if not eligible:
                return None
            # Highest level is explicit evidence; equal-level conflicting trust fails closed.
            rank = max(QUALIFICATION.index(report['status']) for report in eligible)
            best = [report for report in eligible if QUALIFICATION.index(report['status']) == rank]
            if len({report['trust'] for report in best}) != 1:
                return None
            return deepcopy(sorted(best, key=lambda report: report['evidence_digest'])[0])

    def revoke(self, evidence_digest, *, authenticated_reviewer):
        with self.registry._lock:
            if authenticated_reviewer not in self._reviewers:
                raise ValidationError('reviewer not authorized')
            self._revoked.add(evidence_digest)


def seal_report(report):
    return {**deepcopy(report), 'evidence_digest': digest_object(report)}
