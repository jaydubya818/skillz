from pathlib import Path
import pytest
from myskills.application import Application
from myskills.catalog import build_catalog
from myskills.governance import GovernedRegistry, RegistryAdmin
from myskills.manifest import ValidationError, binding

def test_ui_and_agent_actions_share_one_owner_registry():
    r = GovernedRegistry(build_catalog(Path(__file__).parents[1])['skills'])
    app = Application(r)
    m = app.execute('search', {'query':'API contracts'})[0]
    item = app.execute('install', {'identity':binding(m)})
    assert app.execute('installed', {}) == [item]
    assert app.execute('detail', {'identity':binding(m)})['installation'] == item
    RegistryAdmin(r).transition(app.owner, binding(m), 'revoked')
    with pytest.raises(ValidationError):
        app.execute('enable', {'skill_id':m['skill_id'], 'enabled':True, 'expected_revision':item['revision']})
    assert app.execute('detail', {'identity':binding(m)})['lifecycle'] == 'revoked'
    for action in ('execute','publish','revoke_publisher','record_qualification'):
        with pytest.raises(ValidationError):
            app.execute(action,{})
    with pytest.raises(TypeError):
        app.execute('search',{'owner':'someone-else'})

def test_private_draft_action_does_not_return_mutable_store_references():
    app = Application(GovernedRegistry())
    app.execute('draft', {'skill_id':'private-test','version':'1.0.0','description':'Synthetic','instructions':'Review synthetic data'})
    listed=app.execute('my_skills',{})
    listed[0]['manifest']['trust']='PLATFORM_QUALIFIED'
    assert app.execute('my_skills',{})[0]['manifest']['trust']=='OWNER_PRIVATE'

def test_detail_never_controls_another_version_or_calls_revoked_evidence_current():
    app = Application(GovernedRegistry())
    def qualify(version):
        draft = app.execute('draft', {'skill_id':'private-test','version':version,'description':'Synthetic','instructions':'Review synthetic data'})
        app.execute('validate', {'identity':draft['binding']})
        app.execute('qualify', {'identity':draft['binding']})
        return draft['binding']
    first, second = qualify('1.0.0'), qualify('2.0.0')
    app.execute('accept_install', {'identity':first})
    detail = app.execute('detail', {'identity':second})
    assert detail['installation'] is None
    assert detail['other_installation']['binding'] == first
    evidence_digest = detail['current_evidence'][0]
    app.qualifications.revoke(evidence_digest, authenticated_reviewer='static-package-verifier')
    assert app.execute('detail', {'identity':second})['current_evidence'] == []
    assert app.execute('my_skills', {})[1]['state'] == 'qualification revoked'

def test_private_cards_reflect_exact_current_installation_after_update_and_uninstall():
    app = Application(GovernedRegistry())
    versions = []
    for version in ('1.0.0', '2.0.0'):
        identity = app.draft('private-test', version, 'Synthetic', 'Review synthetic data')['binding']
        app.validate(identity)
        app.qualify(identity)
        versions.append(identity)
    installed = app.accept_install(versions[0])
    review = app.session.review_update('private-test', versions[1], installed['revision'])
    updated = app.session.update('private-test', versions[1], installed['revision'], review['decision_digest'])
    assert [item['state'] for item in app.my_skills()] == ['qualified', 'installed']
    app.session.uninstall('private-test', updated['revision'])
    assert [item['state'] for item in app.my_skills()] == ['qualified', 'qualified']
