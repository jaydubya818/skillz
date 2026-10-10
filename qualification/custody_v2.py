"""Bounded, digest-pinned custody of synthetic checkpoint-2 transcripts."""
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

MARKER='myskills-checkpoint2-bundle-v1'
MAX_RAW=16_000_000
MAX_CHUNKS=20
PIN=Path('qualification/checkpoint2/evidence-pin.json')


def permitted(name):
    from qualification.workflow_cases import CASES
    from qualification.probe_cases import PROBES
    parts=name.split('/')
    if len(parts)==2:
        return parts[0] in ('artifacts','workflows') and parts[1] in ('context.json','completion.json')
    if len(parts)!=3:return False
    section,case,file=parts
    suffixes=('representative','adversarial','repeat') if section=='artifacts' else ('representative','adversarial')
    skills=PROBES if section=='artifacts' else CASES if section=='workflows' else {}
    if not any(case==skill+'--'+kind for skill in skills for kind in suffixes):return False
    if section=='artifacts':return file in ('request.json','response.json','observation.json')
    return file=='observation.json' or bool(re.fullmatch(r'(?:[0-9]|1[01])-(?:request|response)\.json',file))


def bundle(artifacts,workflows):
    files={}
    for section,directory in [('artifacts',artifacts),('workflows',workflows)]:
        if directory.is_symlink():raise ValidationError('evidence root symlink denied')
        for path in directory.rglob('*'):
            if path.is_symlink():raise ValidationError('evidence symlink denied')
            if path.is_file():
                name=section+'/'+str(path.relative_to(directory))
                if not permitted(name):raise ValidationError('unexpected evidence path')
                files[name]=path.read_text()
    value={'schema':MARKER,'files':files}
    if len(canonical_bytes(value))>MAX_RAW:raise ValidationError('evidence exceeds bound')
    return value


def package(artifacts,workflows,output):
    value=bundle(artifacts,workflows)
    encoded=base64.b64encode(gzip.compress(canonical_bytes(value),mtime=0)).decode('ascii')
    chunks=[encoded[i:i+60000] for i in range(0,len(encoded),60000)]
    if len(chunks)>MAX_CHUNKS:raise ValidationError('too many custody chunks')
    output.mkdir(parents=True,exist_ok=False)
    pin={'schema':MARKER,'bundle_digest':digest_object(value),'parts':[],
         'evidence_kind':'SYNTHETIC_PARTIAL_BEHAVIOR_NOT_AN_EXECUTION_GRANT'}
    for index,chunk in enumerate(chunks):
        body=('Checkpoint 2 synthetic behavioral evidence. Catalog trust remains UNTRUSTED. '
              'The committed pin authenticates these bytes; no model-authorship attestation is claimed.\n\n'
              +f'Part {index+1}/{len(chunks)}; {pin["bundle_digest"]}\n\n'
              +'```'+MARKER+'\n'+chunk+'\n```\n')
        (output/f'part-{index}.md').write_text(body)
        pin['parts'].append({'index':index,'body_digest':digest_object(body)})
    (output/'pin.json').write_text(json.dumps(pin,indent=2)+'\n')
    return pin


def restore(pin,bodies,destination):
    if destination.exists():raise ValidationError('restore destination exists')
    if pin.get('schema')!=MARKER or pin.get('evidence_kind')!='SYNTHETIC_PARTIAL_BEHAVIOR_NOT_AN_EXECUTION_GRANT':
        raise ValidationError('unsupported custody pin')
    if not 1<=len(bodies)<=MAX_CHUNKS or len(pin['parts'])!=len(bodies):raise ValidationError('incomplete custody parts')
    chunks=[]
    for index,(part,body) in enumerate(zip(pin['parts'],bodies)):
        if part['index']!=index or digest_object(body)!=part['body_digest']:raise ValidationError('custody part changed or reordered')
        found=re.findall(r'```'+MARKER+r'\n([A-Za-z0-9+/=]+)\n```',body)
        if len(found)!=1 or len(found[0])>60000:raise ValidationError('invalid custody encoding')
        chunks.append(found[0])
    with gzip.GzipFile(fileobj=BytesIO(base64.b64decode(''.join(chunks),validate=True))) as stream:
        raw=stream.read(MAX_RAW+1)
    if len(raw)>MAX_RAW:raise ValidationError('expanded evidence exceeds bound')
    value=json.loads(raw)
    if digest_object(value)!=pin['bundle_digest'] or value.get('schema')!=MARKER or set(value)!={'schema','files'}:
        raise ValidationError('custody bundle does not match committed digest')
    if not isinstance(value['files'],dict) or not value['files'] or any(not permitted(k) or not isinstance(v,str) for k,v in value['files'].items()):
        raise ValidationError('invalid evidence paths or content')
    destination.mkdir(parents=True)
    for name,content in value['files'].items():
        path=destination/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(content)
    return value


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--restore',required=True,type=Path)
    parser.add_argument('--pin',type=Path,default=PIN)
    args=parser.parse_args()
    pin=json.loads(args.pin.read_text());bodies=[]
    for part in pin['parts']:
        identifier=part['comment_id']
        if type(identifier) is not int or identifier<=0:raise ValidationError('invalid comment identity')
        response=subprocess.run(['gh','api',f'repos/jaydubya818/skillz/issues/comments/{identifier}'],
                                capture_output=True,text=True,check=True,timeout=30)
        bodies.append(json.loads(response.stdout)['body'])
    restore(pin,bodies,args.restore)
    print(pin['bundle_digest'])
