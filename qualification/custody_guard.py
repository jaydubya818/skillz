"""Task-owned immutable evidence copies and active-source deletion protection.

macOS flags block ordinary same-user deletion and overwrite. They do not defend
against an administrator or a process deliberately clearing those flags.
"""
import json
import os
from pathlib import Path
import stat
from typing import Any

from myskills.cohort_assessment import file_digest, seal
from myskills.digest import digest_object
from myskills.manifest import ValidationError


def require_owner(marker: Path, owner: str) -> dict[str, Any]:
    if marker.is_symlink() or not marker.is_file():
        raise ValidationError('missing or unsafe workstream ownership marker')
    value = json.loads(marker.read_text())
    if value.get('owner') != owner or not owner:
        raise ValidationError('foreign workstream; protection changes denied')
    return value


def validate_roots(checkout: Path, evidence: Path) -> None:
    for path in (checkout, evidence):
        if not path.is_absolute() or path.resolve() != path or path.is_symlink():
            raise ValidationError('roots must be absolute, canonical and non-symlink')
        if '/.codex/visualizations/' in str(path) or path.is_relative_to('/private/tmp') or path.is_relative_to('/private/var/folders'):
            raise ValidationError('durable qualification cannot use disposable roots')
    if checkout == evidence or checkout.is_relative_to(evidence) or evidence.is_relative_to(checkout):
        raise ValidationError('evidence must be outside checkout')


def protect(path: Path, append_only: bool = False) -> None:
    if not hasattr(os, 'chflags') or not hasattr(stat, 'UF_IMMUTABLE'):
        raise ValidationError('host lacks qualified filesystem protection; no protected native run')
    if path.is_symlink() or not path.is_file():
        raise ValidationError('only existing regular files may be protected')
    flag = stat.UF_APPEND if append_only else stat.UF_IMMUTABLE
    os.chflags(path, path.stat().st_flags | flag, follow_symlinks=False)
    if not path.stat().st_flags & flag:
        raise ValidationError('filesystem protection not established')


def claim(checkout: Path, evidence: Path, owner: str) -> dict[str, Any]:
    validate_roots(checkout, evidence)
    if not owner or len(owner) > 100:
        raise ValidationError('invalid owner identity')
    marker = evidence/'.myskills-owner.json'
    source_marker = checkout/'.myskills-active.json'
    value = {'schema': 'myskills.workstream-lease.v1', 'owner': owner,
             'checkout': str(checkout), 'evidence': str(evidence), 'state': 'ACTIVE'}
    for path in (marker, source_marker):
        if path.exists() or path.is_symlink():
            if require_owner(path, owner) != value:
                raise ValidationError('workstream lease differs')
        else:
            with path.open('x') as stream:
                json.dump(value, stream, sort_keys=True)
                stream.flush(); os.fsync(stream.fileno())
        protect(path)
    return value


class Vault:
    """Append-only index plus immutable content objects outside the checkout."""
    def __init__(self, checkout: Path, evidence: Path, owner: str):
        self.lease = claim(checkout, evidence, owner)
        self.root = evidence
        self.owner = owner
        self.objects = evidence/'objects'
        self.objects.mkdir(exist_ok=True)
        self._validate_objects()
        self.index = evidence/'custody-index.jsonl'
        if not self.index.exists():
            with self.index.open('x') as stream:
                stream.flush(); os.fsync(stream.fileno())
        protect(self.index, append_only=True)

    def _validate_objects(self) -> None:
        if self.objects.is_symlink() or not self.objects.is_dir() or self.objects.resolve() != self.root/'objects':
            raise ValidationError('evidence object directory escaped the vault')

    def retain(self, name: str, content: bytes) -> str:
        require_owner(self.root/'.myskills-owner.json', self.owner)
        self._validate_objects()
        from hashlib import sha256
        digest = 'sha256:'+sha256(content).hexdigest()
        destination = self.objects/digest.removeprefix('sha256:')
        try:
            with destination.open('xb') as stream:
                stream.write(content); stream.flush(); os.fsync(stream.fileno())
        except FileExistsError:
            if destination.is_symlink() or destination.read_bytes() != content:
                raise ValidationError('immutable evidence object differs')
        protect(destination)
        with self.index.open('a') as stream:
            stream.write(json.dumps({'name': name, 'digest': digest, 'bytes': len(content)}, sort_keys=True)+'\n')
            stream.flush(); os.fsync(stream.fileno())
        return digest

    def freeze_sources(self, checkout: Path, paths: list[str]) -> dict[str, Any]:
        lease = require_owner(checkout/'.myskills-active.json', self.owner)
        if str(checkout) != self.lease['checkout'] or lease != self.lease:
            raise ValidationError('foreign checkout')
        rows = []
        for name in paths:
            path = checkout/name
            if not path.resolve().is_relative_to(checkout) or path.is_symlink() or not path.is_file():
                raise ValidationError('unsafe source path')
            rows.append({'path': name, 'digest': file_digest(path), 'original_flags': path.stat().st_flags})
        receipt = seal({'owner': self.owner, 'checkout': str(checkout), 'files': rows})
        self.retain('source-protection-receipt', json.dumps(receipt, sort_keys=True).encode())
        try:
            for row in rows:
                protect(checkout/row['path'])
        except BaseException as error:
            failures = []
            for row in rows:
                try:
                    os.chflags(checkout/row['path'], row['original_flags'], follow_symlinks=False)
                except OSError as rollback_error:
                    failures.append(row['path']+': '+str(rollback_error))
            if failures:
                raise ValidationError('source protection rollback incomplete: '+'; '.join(failures)) from error
            raise
        return receipt


def release_sources(checkout: Path, owner: str, receipt: dict[str, Any]) -> None:
    """Only the exact task owner may restore its captured source flags."""
    require_owner(checkout/'.myskills-active.json', owner)
    if receipt.get('owner') != owner or receipt.get('checkout') != str(checkout):
        raise ValidationError('foreign source protection receipt')
    expected = seal({key: value for key, value in receipt.items() if key != 'evidence_digest'})
    if expected != receipt:
        raise ValidationError('source protection receipt changed')
    for row in receipt['files']:
        path = checkout/row['path']
        if path.is_symlink() or not path.resolve().is_relative_to(checkout) or file_digest(path) != row['digest']:
            raise ValidationError('protected source changed; automatic release denied')
    for row in receipt['files']:
        os.chflags(checkout/row['path'], row['original_flags'], follow_symlinks=False)
