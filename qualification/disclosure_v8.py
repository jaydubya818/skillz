"""Prepare a reviewed public view without exporting original native transcripts."""
import argparse
import base64
from hashlib import sha256
import json
import lzma
from pathlib import Path
import re

from myskills.digest import canonical_bytes, digest_object
from qualification.checkpoint_four import require
from qualification.custody_v8 import MARKER, MAX_RAW, bundle

ORIGINAL = 'sha256:af12d52061c706aee5be94aa2d23e74b53d4d05ac262a44becd1f1e2a301974c'
VERSION = 'myskills.public-disclosure-view.v1'
CASES = ('api-and-interface-design--adversarial', 'api-and-interface-design--representative',
         'security-and-hardening--adversarial', 'security-and-hardening--representative')


def bytes_digest(raw):
    return 'sha256:'+sha256(raw).hexdigest()


def safe_digest(value):
    require(isinstance(value, str) and re.fullmatch(r'sha256:[0-9a-f]{64}', value), 'invalid public digest')
    return value


def scan(text):
    patterns = {
        'private-key': r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
        'provider-token': r'(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,}|AKIA[A-Z0-9]{16})',
        'credential-header': r'(?i)authorization["\s:]+(?:bearer|basic)\s+[A-Za-z0-9+/=._-]{12,}',
        'private-path': r'(?:/Users/[^/\s"\\]+|/home/[^/\s"\\]+|/private/(?:tmp|var)/|[A-Z]:\\Users\\)',
        'email': r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',
        'native-private-field': r'"(?:encrypted_content|reasoning_text|client_metadata|prompt_cache_key|threadId|turnId|installation_id|window_id)"\s*:',
    }
    return {name: len(re.findall(pattern, text)) for name, pattern in patterns.items() if re.search(pattern, text)}


def native_view(text, transport_text):
    records = [json.loads(line) for line in text.splitlines()]
    transport = json.loads(transport_text)
    require(transport['records'] == records, 'transport and native transcript differ')
    requests = [r for r in records if r['channel'] == 'provider']
    replies = {r['id']: r['value'] for r in records if r['channel'] == 'host_response'}
    calls = []
    for sequence, request in enumerate(requests):
        response = replies[request['id']]
        require(response['status'] == 200, 'non-success provider cannot be projected')
        raw = base64.b64decode(response['body'], validate=True).decode()
        events = [json.loads(line[6:]) for line in raw.splitlines() if line.startswith('data: {')]
        completed = [e['response'] for e in events if e.get('type') == 'response.completed']
        require(len(completed) == 1 and completed[0]['status'] == 'completed', 'incomplete provider response')
        from qualification.runtime_identity import MODEL
        require(completed[0]['model'] == request['value']['model'] == MODEL, 'model differs')
        functions = []
        for item in completed[0]['output']:
            if item['type'] != 'function_call':
                continue  # No reasoning, opaque payload, message, instruction, or event text is copied.
            require(item.get('namespace') == 'myskills', 'unreviewed tool namespace')
            require(item['name'] in ('read_file', 'write_file', 'run_check', 'finish'), 'unreviewed tool')
            functions.append({'call_id': item['call_id'], 'tool': item['name'],
                              'arguments': json.loads(item['arguments'])})
        calls.append({'sequence': sequence, 'model': MODEL, 'status': 'completed', 'function_calls': functions})
    turns = [r['value']['params']['turn']['status'] for r in records
             if r['channel'] == 'event' and r['value'].get('method') == 'turn/completed']
    require(turns == ['completed'], 'native terminal state differs')
    require(transport['cleanup_confirmed'] is True and transport['exit_code'] == 0 and
            transport['failure'] is None and transport['network'] == 'none' and transport['host_mounts'] == [],
            'transport boundary or completion differs')
    witness = {'schema': VERSION, 'original_native_digest': bytes_digest(text.encode()),
               'projection': 'Completed provider function calls only; raw provenance requires private custody review.',
               'provider_calls': calls, 'terminal_status': 'completed', 'raw_transcript_replay': False}
    summary = {'schema': VERSION, 'original_transport_digest': bytes_digest(transport_text.encode()),
               'image': safe_digest(transport['image']), 'cleanup_confirmed': True, 'exit_code': 0,
               'failure': None, 'network': 'none', 'host_mounts': [], 'raw_transcript_replay': False}
    return witness, summary


def prepare(package, native, output):
    require(not output.exists(), 'disclosure output already exists')
    require(not package.is_symlink() and not native.is_symlink(), 'symlink disclosure root')
    pin = json.loads((package/'pin.json').read_text())
    require(pin['bundle_digest'] == ORIGINAL and len(pin['parts']) == 8, 'unexpected original bundle')
    parts = []; part_rows = []
    for i in range(8):
        path = package/f'part-{i}.md'
        require(not path.is_symlink(), 'symlink disclosure part')
        body = path.read_text()
        require(pin['parts'][i]['index'] == i and digest_object(body) == pin['parts'][i]['body_digest'], 'part identity differs')
        matches = re.findall(r'```'+MARKER+r'\n([A-Za-z0-9+/=]+)\n```', body)
        require(len(matches) == 1 and len(matches[0]) <= 60000, 'invalid custody encoding')
        parts.append(matches[0])
        part_rows.append({'path': path.name, 'bytes': len(body.encode()), 'body_digest': digest_object(body),
                          'classification': 'PRIVATE_ORIGINAL_CONTAINS_COMPRESSED_SENSITIVE_RECORDS', 'publication': 'DENIED'})
    require(sum(row['bytes'] for row in part_rows) == 466548, 'original size differs')
    decoder = lzma.LZMADecompressor(memlimit=64000000)
    raw = decoder.decompress(base64.b64decode(''.join(parts), validate=True), max_length=MAX_RAW+1)
    require(len(raw) <= MAX_RAW and decoder.eof and not decoder.unused_data, 'invalid compressed stream')
    original = json.loads(raw)
    require(digest_object(original) == ORIGINAL and original == bundle(native), 'original custody differs')
    files = original['files']; public = {}; rows = []
    replacements = {}
    context = json.loads(files['context.json'])
    replacements['context.json'] = ('context-public.json', {
        'schema': VERSION, 'original_context_digest': bytes_digest(files['context.json'].encode()),
        'runtime_digest': digest_object(context['runtime']), 'model_digest': safe_digest(context['model_digest']),
        'harness_digest': digest_object(context['harness']), 'corpus_digest': digest_object(context['fixtures']),
        'private_runtime_details_withheld': True, 'raw_transcript_replay': False})
    for case in CASES:
        witness, summary = native_view(files[case+'/native.jsonl'], files[case+'/transport.json'])
        replacements[case+'/native.jsonl'] = (case+'/native-witness.json', witness)
        replacements[case+'/transport.json'] = (case+'/transport-public.json', summary)
    for name, content in sorted(files.items()):
        sensitive = name in replacements
        if sensitive:
            destination, view = replacements[name]
            result = json.dumps(view, sort_keys=True, indent=2)+'\n'
            classification = 'PRIVATE_HOST_METADATA' if name == 'context.json' else 'PRIVATE_NATIVE_REASONING_AND_SESSION_METADATA'
        else:
            require(name == 'completion.json' or name.endswith(('/prompt.json', '/observation.json')) or '/journal/' in name,
                    'unclassified original file')
            destination, result = name, content
            classification = 'PUBLIC_SKILL_AND_SYNTHETIC_TASK' if name.endswith('/prompt.json') else 'SYNTHETIC_FIXTURE_AND_EXECUTION_EVIDENCE'
        findings = scan(result)
        require(not findings, 'public output requires further review: '+name+' '+','.join(findings))
        public[destination] = result
        rows.append({'original_path': name, 'original_bytes': len(content.encode()), 'original_digest': bytes_digest(content.encode()),
                     'classification': classification, 'action': 'PROJECT' if sensitive else 'COPY_EXACT',
                     'public_path': destination, 'public_bytes': len(result.encode()), 'public_digest': bytes_digest(result.encode()),
                     'sensitive_original_withheld': sensitive, 'automated_scan_findings': findings})
    require(len(rows) == 144 and len(replacements) == 9, 'reviewed file inventory differs')
    manifest = {'schema': VERSION, 'original_bundle_digest': ORIGINAL, 'original_parts': part_rows,
                'files': rows, 'independent_review': 'PENDING', 'final_owner_approval': 'REQUIRED_BEFORE_UPLOAD',
                'raw_transcript_replay': False,
                'limitations': ['No credential-pattern match is not a guarantee of credential absence.',
                               '135 original records are retained exactly; nine files are distinct disclosure projections.',
                               'Public tool replay cannot reconstruct omitted raw native/provider content.',
                               'Original native provenance remains supported by private custody and local independent review.']}
    public['disclosure-manifest.json'] = json.dumps(manifest, sort_keys=True, indent=2)+'\n'
    value = {'schema': VERSION, 'files': public}
    encoded = base64.b64encode(lzma.compress(canonical_bytes(value), preset=6)).decode()
    chunks = [encoded[i:i+60000] for i in range(0, len(encoded), 60000)]
    output.mkdir(parents=True)
    (output/'view').mkdir()
    for name, content in public.items():
        path = output/'view'/name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(content)
    result = {'schema': VERSION, 'codec': 'xz-base64', 'original_bundle_digest': ORIGINAL,
              'bundle_digest': digest_object(value), 'parts': [], 'public_files': len(public),
              'publication': 'NOT_AUTHORIZED_PENDING_FINAL_OWNER_APPROVAL', 'raw_transcript_replay': False}
    for i, chunk in enumerate(chunks):
        body = ('Sanitized MySkills disclosure view. Original raw transcripts remain private.\n'
                +f'Part {i+1}/{len(chunks)}; {result["bundle_digest"]}\n\n```'+VERSION+'\n'+chunk+'\n```\n')
        (output/f'part-{i}.md').write_text(body)
        result['parts'].append({'index': i, 'bytes': len(body.encode()), 'body_digest': digest_object(body)})
    result['total_part_bytes'] = sum(p['bytes'] for p in result['parts'])
    (output/'pin.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('package', 'native', 'output'):
        parser.add_argument('--'+name, required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.package, args.native, args.output), sort_keys=True))
