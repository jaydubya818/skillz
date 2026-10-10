"""Retain bounded synthetic probe transcripts in a pinned PR evidence comment."""
import argparse
import base64
import gzip
from io import BytesIO
import json
from pathlib import Path
import re
import subprocess

from myskills.digest import canonical_bytes, digest_object
from myskills.manifest import ValidationError

MAX_BUNDLE = 4_000_000
MARKER = 'myskills-local-probe-bundle-v1'


def allowed_files(root):
    plan = json.loads((root/'qualification/initial-cohort/plan.json').read_text())
    names = {'runtime.json','context.json'}
    for spec in plan['skills']:
        for kind in ('representative','adversarial'):
            prefix = spec['binding']['skill_id'] + '--' + kind + '/'
            names.update(prefix + name for name in ('request.json','observation.json'))
            names.add(prefix + 'response.json')
    return names


def bundle_data(root, directory):
    allowed = allowed_files(root)
    files = {str(p.relative_to(directory)):p.read_text() for p in directory.rglob('*') if p.is_file()}
    if not set(files).issubset(allowed) or allowed.difference(files).difference(
        name for name in allowed if name.endswith('/response.json')):
        raise ValidationError('unexpected or missing evidence files')
    for name in files:
        if (directory/name).is_symlink():
            raise ValidationError('evidence symlink forbidden')
    data = {'schema':MARKER,'files':files}
    if len(canonical_bytes(data)) > MAX_BUNDLE:
        raise ValidationError('evidence bundle too large')
    return data


def package(root, directory):
    data = bundle_data(root,directory)
    digest = digest_object(data)
    encoded = base64.b64encode(gzip.compress(canonical_bytes(data),mtime=0)).decode('ascii')
    body = ('Retained synthetic local-model observations for the initial MySkills cohort. '
            'All Skills remain UNTRUSTED. These are bounded PARTIAL observations, not qualification grants. '
            'The committed pin authenticates the exact bytes; replay does not prove model authorship.\n\n'
            + digest + '\n\n<details><summary>Machine-readable evidence, gzip + base64</summary>\n\n'
            + '```' + MARKER + '\n' + encoded + '\n```\n</details>\n')
    if len(body.encode()) > 65000:
        raise ValidationError('evidence exceeds one bounded PR comment')
    return body, {'schema':'myskills.local-probe-pin.v1','bundle_digest':digest,
                  'evidence_kind':'BOUNDED_PARTIAL_OBSERVATIONS_NOT_QUALIFICATION'}


def restore(root, body, pin, destination):
    if destination.exists():
        raise ValidationError('restore destination exists')
    if pin.get('schema') != 'myskills.local-probe-pin.v1' or pin.get('evidence_kind') != 'BOUNDED_PARTIAL_OBSERVATIONS_NOT_QUALIFICATION':
        raise ValidationError('unsupported observation pin')
    blocks = re.findall(r'```' + MARKER + r'\n([A-Za-z0-9+/=]+)\n```',body)
    if len(blocks) != 1 or len(blocks[0]) > 65000:
        raise ValidationError('invalid retained evidence comment')
    with gzip.GzipFile(fileobj=BytesIO(base64.b64decode(blocks[0],validate=True))) as archive:
        raw = archive.read(MAX_BUNDLE + 1)
    if len(raw) > MAX_BUNDLE:
        raise ValidationError('expanded evidence exceeds bound')
    data = json.loads(raw)
    if digest_object(data) != pin['bundle_digest'] or data.get('schema') != MARKER or set(data) != {'schema','files'}:
        raise ValidationError('retained evidence does not match committed pin')
    if not isinstance(data['files'],dict) or not set(data['files']).issubset(allowed_files(root)):
        raise ValidationError('invalid evidence paths')
    if any(not isinstance(value,str) for value in data['files'].values()):
        raise ValidationError('invalid evidence values')
    destination.mkdir(parents=True)
    for name, value in data['files'].items():
        path = destination/name
        path.parent.mkdir(exist_ok=True)
        path.write_text(value)
    if bundle_data(root,destination) != data:
        raise ValidationError('restored evidence differs')
    return pin['bundle_digest']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package',type=Path)
    parser.add_argument('--restore',type=Path)
    parser.add_argument('--comment',type=Path)
    parser.add_argument('--pin',required=True,type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if bool(args.package) == bool(args.restore):
        parser.error('choose exactly one --package or --restore')
    if args.package:
        if not args.comment:
            parser.error('--package requires --comment')
        body,pin = package(root,args.package)
        args.comment.write_text(body)
        args.pin.write_text(json.dumps(pin,indent=2,sort_keys=True)+'\n')
    else:
        pin = json.loads(args.pin.read_text())
        if args.comment:
            body = args.comment.read_text()
        else:
            comment_id = pin.get('github_comment_id')
            if type(comment_id) is not int or comment_id <= 0:
                raise ValidationError('a pinned GitHub comment ID is required')
            body = subprocess.check_output(['gh','api',
                'repos/jaydubya818/skillz/issues/comments/' + str(comment_id),'--jq','.body'],timeout=30).decode()
        print(restore(root,body,pin,args.restore))


if __name__ == '__main__':
    main()
