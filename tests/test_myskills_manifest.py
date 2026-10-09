from pathlib import Path
import copy
import pytest
from myskills.manifest import validate_manifest, ValidationError
from myskills.catalog import build_catalog
from myskills.digest import package_digest

ROOT = Path(__file__).parents[1]

def test_all_canonical_skills_are_indexed_reproducibly():
    catalog = build_catalog(ROOT)
    assert catalog == build_catalog(ROOT)
    assert not catalog['failures']
    assert len(catalog['skills']) == len(list((ROOT / 'skills').glob('*/SKILL.md')))
    assert all(m['trust'] == 'UNTRUSTED' and m['qualification']['status'] == 'NOT_EVALUATED' for m in catalog['skills'])

def test_digest_binds_bytes_paths_modes_and_metadata(tmp_path):
    skill = tmp_path / 'demo'
    skill.mkdir()
    (skill / 'SKILL.md').write_text('example')
    manifest = {'schema': 'test', 'effects': []}
    original = package_digest(skill, manifest)
    assert original == package_digest(skill, dict(reversed(list(manifest.items()))))
    (skill / 'helper.sh').write_text('echo example')
    added = package_digest(skill, manifest)
    assert original != added
    (skill / 'helper.sh').chmod(0o755)
    assert added != package_digest(skill, manifest)
    assert original != package_digest(skill, {**manifest, 'effects': ['network.request']})
    (skill / 'link').symlink_to('/etc/passwd')
    with pytest.raises(ValidationError):
        package_digest(skill, manifest)

@pytest.mark.parametrize('field,value', [('trust','TRUST_ME'),('version','latest'),('permitted_effects',['magic.all']),('required_capabilities',['all']),('secret_requirements',['actual-secret-value']),('unexpected',True)])
def test_manifest_rejects_invalid_security_metadata(field, value):
    manifest = copy.deepcopy(build_catalog(ROOT)['skills'][0])
    manifest[field] = value
    with pytest.raises(ValidationError):
        validate_manifest(manifest)

def test_generated_catalog_and_schema_are_current():
    import json
    from myskills.manifest import SCHEMA
    assert json.loads((ROOT / 'catalog/myskills.json').read_text()) == build_catalog(ROOT)
    assert json.loads((ROOT / 'catalog/skill-manifest.schema.json').read_text()) == SCHEMA

def test_invalid_legacy_metadata_is_an_inventory_failure(tmp_path):
    skill = tmp_path / 'skills' / 'broken'
    skill.mkdir(parents=True)
    (skill / 'SKILL.md').write_text('---\nname: broken\ndescription: example\nmetadata: malformed\n---\n')
    report = build_catalog(tmp_path)
    assert not report['skills']
    assert report['failures'] == [{'path': 'skills/broken', 'error': 'metadata must be a mapping'}]

def test_core_provenance_preserves_known_upstreams():
    skills = {m['skill_id']: m for m in build_catalog(ROOT)['skills']}
    assert skills['before-and-after']['provenance']['source'].endswith('vercel-labs/before-and-after')
    assert skills['greploop']['provenance']['source'].endswith('greptileai/skills')
    assert skills['unslop']['provenance']['source'].endswith('cursor/plugins/tree/main/pstack')

def test_export_is_reproducible_and_excludes_unhashed_artifacts(tmp_path):
    from io import BytesIO
    from zipfile import ZipFile
    import shutil
    from myskills.package import export_package
    source = ROOT / 'skills' / 'api-and-interface-design'
    skill = tmp_path / source.name
    shutil.copytree(source, skill)
    m = next(m for m in build_catalog(ROOT)['skills'] if m['skill_id'] == source.name)
    (skill / '.artifacts').mkdir()
    (skill / '.artifacts' / 'evil.py').write_text('raise Exception()')
    first = export_package(skill, m)
    assert first == export_package(skill, m)
    with ZipFile(BytesIO(first)) as archive:
        assert not any('.artifacts' in name for name in archive.namelist())
        assert 'skill/LICENSE' in archive.namelist()
    (skill / 'SKILL.md').write_text('tampered')
    with pytest.raises(ValidationError, match='mismatch'):
        export_package(skill, m)
