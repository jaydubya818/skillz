from copy import deepcopy
import json
import pytest
from myskills.manifest import ValidationError
from qualification.custody_v2 import bundle, package, restore, permitted


def test_custody_roundtrip_and_mutation_rejection(tmp_path):
    a=tmp_path/'artifacts';w=tmp_path/'workflows'
    a.mkdir();w.mkdir()
    for d in (a,w):
        (d/'context.json').write_text('{"fixture":"synthetic"}')
        (d/'completion.json').write_text('{"all_results_admissible":false}')
    pin=package(a,w,tmp_path/'packed')
    bodies=[(tmp_path/'packed'/f'part-{i}.md').read_text() for i in range(len(pin['parts']))]
    value=restore(pin,bodies,tmp_path/'restored')
    assert value==bundle(a,w)
    with pytest.raises(ValidationError,match='changed'):
        restore(pin,[bodies[0]+'changed',*bodies[1:]],tmp_path/'bad')
    altered=deepcopy(pin);altered['bundle_digest']='sha256:'+'0'*64
    with pytest.raises(ValidationError,match='committed digest'):
        restore(altered,bodies,tmp_path/'bad-pin')


def test_custody_denies_arbitrary_paths_and_symlinks(tmp_path):
    for name in ('../secret','artifacts/../../secret','/etc/passwd',
                 'workflows/tdd--representative/12-response.json',
                 'artifacts/another-skill--representative/response.json'):
        assert not permitted(name)
    a=tmp_path/'a';w=tmp_path/'w';a.mkdir();w.mkdir()
    (a/'context.json').symlink_to(tmp_path/'outside')
    with pytest.raises(ValidationError,match='symlink'):
        bundle(a,w)
