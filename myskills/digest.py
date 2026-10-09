"""Content identity includes every package byte, path, executable bit, and declaration."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import stat
from .manifest import ValidationError

EXCLUDED_DIRECTORIES = frozenset(('.git', '__pycache__', '.artifacts', '.pytest_cache', 'node_modules'))

def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode('ascii')

def digest_object(value):
    return 'sha256:' + hashlib.sha256(canonical_bytes(value)).hexdigest()

def package_files(root: Path):
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ValidationError('package root must be a real directory')
    files = []
    def visit(directory):
        for path in sorted(directory.iterdir()):
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode):
                raise ValidationError('symlinks are not package content')
            if path.is_dir():
                if path.name not in EXCLUDED_DIRECTORIES:
                    visit(path)
            elif stat.S_ISREG(info.st_mode):
                if path.name == '.DS_Store' or path.suffix == '.pyc':
                    continue
                files.append({'path': path.relative_to(root).as_posix(), 'executable': bool(info.st_mode & 0o111),
                              'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
            else:
                raise ValidationError('special files are not package content')
    visit(root)
    if not any(item['path'] == 'SKILL.md' for item in files):
        raise ValidationError('missing SKILL.md')
    return sorted(files, key=lambda item: item['path'])

def package_digest(root, manifest):
    declaration = {k: v for k, v in manifest.items() if k != 'digest'}
    return digest_object({'algorithm': 'myskills.package.v1', 'manifest': declaration, 'files': package_files(root)})

def verify_package(root, manifest):
    if package_digest(root, manifest) != manifest['digest']:
        raise ValidationError('package digest mismatch')
