from pathlib import Path
import pytest
from qualification.custody_v3 import package,restore,permitted


def test_native_custody_round_trip_and_changed_part(tmp_path):
    source=tmp_path/'source';source.mkdir();(source/'context.json').write_text('{}')
    case=source/'tdd--representative';case.mkdir();(case/'19-response.json').write_text('{"done":true}')
    out=tmp_path/'packed';pin=package(source,out)
    bodies=[(out/f'part-{p["index"]}.md').read_text() for p in pin['parts']]
    restore(pin,bodies,tmp_path/'restored')
    assert (tmp_path/'restored/tdd--representative/19-response.json').read_bytes()==(case/'19-response.json').read_bytes()
    with pytest.raises(ValueError):restore(pin,[bodies[0]+'changed'],tmp_path/'bad')
    with pytest.raises(ValueError):restore(pin,bodies,tmp_path/'restored')


def test_native_custody_rejects_unbounded_or_escaping_paths(tmp_path):
    for path in ['../outside','tdd--representative/20-response.json','fake--representative/0-request.json','tdd--repeat/0-request.json']:
        assert not permitted(path)
    root=tmp_path/'source';root.mkdir();(root/'context.json').symlink_to('/etc/hosts')
    with pytest.raises(ValueError,match='symlink'):package(root,tmp_path/'out')
