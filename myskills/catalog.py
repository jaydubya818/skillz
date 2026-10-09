"""Inventory existing portable packages without executing their instructions."""
from __future__ import annotations

import json
from pathlib import Path
import re
from .digest import digest_object, package_digest, package_files
from .manifest import EFFECTS, ID, ValidationError, validate_manifest

RUNTIMES = ['agent-skills', 'claude-code', 'codex', 'cursor']

def frontmatter(text):
    match = re.match(r'^---\n(.*?)\n---(?:\n|$)', text, re.S)
    if not match:
        raise ValidationError('missing portable frontmatter')
    # This is an explicit parser for the repository's scalar/metadata subset,
    # not a general YAML loader. Unsupported syntax fails instead of guessing.
    fields, metadata = {}, {}
    lines = match[1].splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        index += 1
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        nested = line.startswith('  ')
        target = metadata if nested else fields
        pair = re.fullmatch(r'(?:  )?([a-z][a-z0-9-]*):\s*(.*)', line)
        if not pair:
            raise ValidationError('unsupported frontmatter syntax')
        key, value = pair.groups()
        if key in target:
            raise ValidationError('duplicate frontmatter key')
        if key == 'metadata' and not nested:
            if value:
                raise ValidationError('metadata must be a mapping')
            fields[key] = metadata
            continue
        if nested and 'metadata' not in fields:
            raise ValidationError('unexpected nested frontmatter')
        if value in ('>', '>-', '|', '|-'):
            continuation = []
            while index < len(lines) and lines[index].startswith('  '):
                continuation.append(lines[index].strip())
                index += 1
            value = (' ' if value.startswith('>') else '\n').join(continuation)
        elif value.startswith('"'):
            value = json.loads(value)
        elif value.startswith("'") and value.endswith("'"):
            value = value[1:-1].replace("''", "'")
        elif value.startswith(('[', '{', '&', '*', '!')):
            raise ValidationError('unsupported frontmatter scalar')
        target[key] = value
    if not re.fullmatch(ID, fields.get('name', '')) or not fields.get('description'):
        raise ValidationError('invalid portable name or description')
    return fields

def provenance(root, skill_id, fields):
    for path in sorted((root / 'vendor').glob('*.json')):
        vendor = json.loads(path.read_text())
        if skill_id in vendor.get('imported', []):
            license_refs = [f'skills/{skill_id}/LICENSE'] if (root / 'skills' / skill_id / 'LICENSE').is_file() else ['LICENSES.md']
            return {'kind': 'adapted' if vendor.get('integration_mode') == 'curated-rewrite' else 'vendored',
                    'source': vendor['upstream'], 'revision': vendor['commit'], 'reference': path.relative_to(root).as_posix(),
                    'license': vendor.get('license', fields.get('license', 'UNSPECIFIED')), 'license_references': license_refs}
    metadata = fields.get('metadata', {})
    sources = {
        'before-and-after': 'https://github.com/vercel-labs/before-and-after',
        'greploop': 'https://github.com/greptileai/skills',
        'greploop-apps': 'https://github.com/greptileai/skills',
        'unslop': 'https://github.com/cursor/plugins/tree/main/pstack',
        'new-feature': 'https://github.com/michaelshimeles/skills',
        'code-structure': 'https://github.com/michaelshimeles/skills',
        'evidence-driven-testing': 'https://github.com/michaelshimeles/skills',
        'mission-control-delivery': 'https://github.com/jaydubya818/skillz',
    }
    return {'kind': 'adapted',
            'source': sources.get(skill_id, metadata.get('source', 'UNKNOWN_REQUIRES_REVIEW')),
            'revision': metadata.get('source-commit', 'SEE_GIT_HISTORY'), 'reference': 'LICENSES.md',
            'license': fields.get('license', 'UNSPECIFIED'),
            'license_references': [f'skills/{skill_id}/LICENSE'] if (root / 'skills' / skill_id / 'LICENSE').exists() else ['LICENSES.md']}

SIGNALS = {
    'network.request': r'\b(?:https?://|network|fetch|curl|MCP)\b',
    'secrets.use': r'\b(?:credentials?|secrets?|tokens?|API key)\b',
    'tests.execute': r'\b(?:pytest|npm test|tests?|verification)\b',
    'branch.push': r'\b(?:git push|push|publish|publication)\b',
    'external_api.write': r'\b(?:deploy|send|upload|API mutation)\b',
    'owner_computer.use': r'\b(?:desktop|computer|screen recording)\b',
    'repository.read': r'\b(?:repository|repo|code|git)\b',
    'candidate.modify': r'\b(?:implement|modify|edit|write|migration)\b',
}

def inventory_signals(path):
    files = package_files(path)
    text = '\n'.join((path / item['path']).read_text(errors='replace') for item in files if Path(item['path']).suffix in ('.md', '.py', '.sh', '.mjs', '.json', '.yaml'))
    return {'effect_candidates': sorted(effect for effect, pattern in SIGNALS.items() if re.search(pattern, text, re.I)),
            'skill_reference_candidates': sorted(set(re.findall(r'\.\./([a-z0-9-]+)/', text))),
            'external_hosts': sorted(set(re.findall(r'https?://([a-zA-Z0-9.-]+)', text))),
            'executable_helpers': [item['path'] for item in files if Path(item['path']).suffix in ('.py', '.sh', '.mjs', '.js', '.ts')],
            'assessment': 'LEXICAL_ONLY_REQUIRES_REVIEW'}

def legacy_manifest(root, path):
    files = package_files(path)
    fields = frontmatter((path / 'SKILL.md').read_text())
    if fields['name'] != path.name:
        raise ValidationError('directory/name mismatch')
    metadata = fields.get('metadata', {})
    tags = sorted(set(metadata.get('capabilities', '').split(',')) - {''})
    source = provenance(root, path.name, fields)
    for reference in source['license_references'] + [source['reference']]:
        if not (root / reference).is_file():
            raise ValidationError('missing provenance/license reference')
    m = {
        'schema': 'myskills.manifest.v1', 'skill_id': path.name,
        'version': '0.0.0+legacy.' + digest_object(files)[7:23], 'digest': 'sha256:' + '0'*64,
        'name': path.name.replace('-', ' ').capitalize(), 'description': fields['description'],
        'publisher': {'publisher_id': 'skillz-collection', 'display_name': 'Skillz collection; see upstream attribution'},
        'provenance': source, 'visibility': {'scope': 'public', 'subject': ''},
        'trust': 'UNTRUSTED', 'lifecycle': 'draft', 'inputs': [], 'outputs': [],
        'required_capabilities': [], 'permitted_effects': [], 'prohibited_effects': list(EFFECTS),
        'scope_constraints': {'repository_paths': [], 'file_paths': []},
        'network_requirements': {'mode': 'deny', 'hosts': []}, 'secret_requirements': [],
        'runtime_requirements': [], 'harness_compatibility': RUNTIMES.copy(), 'model_policy_requirements': [],
        'verification_requirements': ['manifest-review', 'dependency-review', 'runtime-qualification', 'independent-review'],
        'resource_ceilings': {'seconds': 0, 'operations': 0},
        'compatibility_requirements': [fields.get('compatibility', 'Required host capabilities have not been evaluated.')],
        'dependencies': [], 'qualification': {'status': 'NOT_EVALUATED', 'evidence': []},
        'metadata_status': 'UNREVIEWED', 'categories': tags, 'tags': tags, 'aliases': [],
    }
    m['digest'] = package_digest(path, m)
    return validate_manifest(m)

def build_catalog(root):
    root = Path(root)
    skills, failures, signals, seen = [], [], {}, set()
    for path in sorted((root / 'skills').iterdir()):
        if not path.is_dir():
            continue
        try:
            manifest = legacy_manifest(root, path)
            if manifest['skill_id'] in seen:
                raise ValidationError('duplicate skill ID')
            seen.add(manifest['skill_id'])
            skills.append(manifest)
            signals[path.name] = inventory_signals(path)
        except (ValidationError, ValueError, OSError) as error:
            failures.append({'path': 'skills/' + path.name, 'error': str(error)})
    overlaps = []
    for index, a in enumerate(skills):
        words_a = set(re.findall(r'[a-z]{4,}', a['description'].lower()))
        for b in skills[index + 1:]:
            words_b = set(re.findall(r'[a-z]{4,}', b['description'].lower()))
            similarity = len(words_a & words_b) / max(1, len(words_a | words_b))
            if similarity >= .35:
                overlaps.append({'skills': [a['skill_id'], b['skill_id']], 'classification': 'REVIEW_REQUIRED', 'lexical_similarity': round(similarity, 3)})
    return {'schema': 'myskills.catalog.v1', 'skills': skills, 'failures': failures, 'inventory_signals': signals, 'overlap_candidates': overlaps}
