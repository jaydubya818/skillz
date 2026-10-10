"""Verify structured claims against controller-pinned evidence, never prose trust.

The caller owns the source snapshot and receipt authority. Neither may come from
the producer's claim packet. Seals detect changes; they are not signatures.
Natural-language claim extraction and coverage require independent review.
"""
from hashlib import sha256
from pathlib import PurePosixPath

from myskills.cohort_assessment import seal
from myskills.digest import digest_object
from myskills.manifest import ValidationError
from qualification.checkpoint_four import unseal

VERSION = 'myskills-claims/6.0.0'
RESULTS = {'VERIFIED', 'CONTRADICTED', 'UNSUPPORTED', 'NOT_EVALUATED'}
FIELDS = {'claim_id', 'claim_type', 'statement', 'origin', 'modality', 'references', 'fact_id', 'expected'}


def text_digest(text):
    return 'sha256:' + sha256(text.encode()).hexdigest()


def reference(snapshot, path, start, end):
    source = snapshot['files'][path]
    lines = source.splitlines(keepends=True)
    if type(start) is not int or type(end) is not int or not 1 <= start <= end <= len(lines):
        raise ValidationError('invalid source range')
    return {'path': path, 'revision': snapshot['revision'], 'digest': text_digest(source),
            'start_line': start, 'end_line': end, 'quote': ''.join(lines[start - 1:end])}


def valid_reference(ref, snapshot):
    if not isinstance(ref, dict) or set(ref) != {'path', 'revision', 'digest', 'start_line', 'end_line', 'quote'}:
        return False
    path = ref['path']
    if not isinstance(path, str) or not path or ':' in path or '\\' in path:
        return False
    if PurePosixPath(path).is_absolute() or '..' in PurePosixPath(path).parts or path not in snapshot['files']:
        return False
    try:
        return ref == reference(snapshot, path, ref['start_line'], ref['end_line'])
    except (ValidationError, TypeError, KeyError):
        return False


def verify_claim(claim, snapshot, receipts, authority):
    if not isinstance(claim, dict) or set(claim) != FIELDS:
        raise ValidationError('claim schema differs; producer verdicts are not accepted')
    if any(not isinstance(claim[k], str) or not claim[k] for k in ('claim_id', 'claim_type', 'statement', 'fact_id')):
        raise ValidationError('claim identity, type, statement and fact ID required')
    if claim['modality'] not in {'IMPLEMENTED', 'PRECONDITION', 'PROPOSED'} or not isinstance(claim['references'], list):
        raise ValidationError('invalid claim modality or references')
    if claim['origin'] not in {'EXTRACTED', 'REQUIRED_EVIDENCE_GAP', 'SCOPED_VERIFIER_ASSERTION'}:
        raise ValidationError('invalid claim origin')
    result, reason = 'UNSUPPORTED', 'No independently pinned evidence supports this claim.'
    receipt = receipts.get(claim['fact_id'])
    rule = authority.get(claim['fact_id'])
    method, limitations = 'NONE', []
    if any(not valid_reference(ref, snapshot) for ref in claim['references']):
        result, reason = 'CONTRADICTED', 'Source reference, exact bytes or revision differs.'
    elif not claim['references']:
        reason = 'Missing exact source reference.'
    elif claim['modality'] == 'PROPOSED':
        result, reason = 'NOT_EVALUATED', 'A proposed mitigation is not implemented behavior.'
    elif receipt is not None and rule is not None:
        try:
            unseal(receipt)
            source = snapshot['files'][receipt['source_path']]
            intact = (receipt['evidence_digest'] == rule['receipt_digest']
                      and receipt['owner_id'] == snapshot['owner_id']
                      and receipt['source_revision'] == snapshot['revision']
                      and receipt['source_digest'] == text_digest(source)
                      and receipt['fact_id'] == claim['fact_id']
                      and receipt['method'] == rule['method']
                      and isinstance(receipt['code_digest'], str) and bool(receipt['code_digest'])
                      and isinstance(receipt['limitations'], list)
                      and 'value' in receipt and 'status' in receipt)
        except (ValidationError, KeyError, TypeError, ValueError):
            intact = False
        if not intact:
            result, reason = 'CONTRADICTED', 'Receipt differs from controller authority or source scope.'
        elif rule.get('approved_claims', {}).get(claim['claim_id']) != digest_object(claim):
            result, reason = 'CONTRADICTED', 'Claim proposition differs from the controller-approved definition.'
        elif claim['claim_type'] not in rule['claim_types']:
            reason = 'This evidence method does not establish this claim type.'
        else:
            method, limitations = receipt['method'], receipt['limitations']
            if receipt['status'] != 'COMPLETE':
                result, reason = 'NOT_EVALUATED', 'Independent inspection or execution did not complete.'
            elif digest_object(receipt['value']) == digest_object(claim['expected']):
                result, reason = 'VERIFIED', 'Independent evidence matches the bounded assertion.'
            else:
                result, reason = 'CONTRADICTED', 'Independent observation differs from the asserted value.'
    return seal({**claim, 'verifier': VERSION, 'source_revision': snapshot['revision'],
                 'owner_id': snapshot['owner_id'], 'verification_method': method,
                 'result': result, 'reason': reason, 'limitations': limitations,
                 'test_evidence': receipt, 'execution_authority': False})


def gate(claims, required):
    ids = [c['claim_id'] for c in claims]
    if len(ids) != len(set(ids)) or len(required) != len(set(required)):
        raise ValidationError('duplicate claim identity')
    for claim in claims:
        unseal(claim)
        if claim['result'] not in RESULTS:
            raise ValidationError('unknown verification result')
    missing = sorted(set(required) - set(ids))
    results = {c['result'] for c in claims}
    result = ('CONTRADICTED' if 'CONTRADICTED' in results else
              'UNSUPPORTED' if missing or not claims or 'UNSUPPORTED' in results else
              'NOT_EVALUATED' if 'NOT_EVALUATED' in results else 'VERIFIED')
    return seal({'result': result, 'required': list(required), 'missing': missing,
                 'claim_evidence': [c['evidence_digest'] for c in claims],
                 'qualification_authority': False})
