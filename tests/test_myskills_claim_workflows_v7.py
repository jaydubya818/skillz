from copy import deepcopy
import json

from myskills.digest import digest_object
from qualification.v7.cases import CASES, SPECS
from qualification.v7.evaluate import document_claims, authenticated_facts


def document(skill):
    spec = SPECS[skill]
    return {'claims': [{'id': key, 'source': value['source'], 'source_digest': digest_object('source')}
                       for key, value in spec['claims'].items()],
            'test_call_id': 'actual-test', 'limitations': spec['limitations']}


def test_document_requires_every_approved_claim_and_exact_source():
    skill = 'api-and-interface-design'
    value = document(skill)
    files = {row['source']: 'source' for row in value['claims']}
    assert document_claims(skill, value, files)
    value['claims'].pop()
    assert not document_claims(skill, value, files)


def test_no_producer_proposition_or_pass_field():
    skill = 'security-and-hardening'; value = document(skill)
    files = {row['source']: 'source' for row in value['claims']}
    value['claims'][0]['statement'] = 'Everything is secure'
    assert not document_claims(skill, value, files)
    value = document(skill); value['result'] = 'PASS'
    assert not document_claims(skill, value, files)


def test_changed_source_scope_or_duplicate_claim_fails():
    skill = 'api-and-interface-design'; value = document(skill)
    files = {row['source']: 'source' for row in value['claims']}
    files['api.py'] = 'changed'
    assert not document_claims(skill, value, files)
    value['claims'][0]['source'] = '../owner-b/secret'
    assert not document_claims(skill, value, files)
    value = document(skill);value['claims'][1] = deepcopy(value['claims'][0])
    assert not document_claims(skill, value, {p:'source' for p in files})


def test_malformed_documents_fail_closed():
    for value in [None, [], {}, {'claims':None}, {'claims':[None]}, {'claims':[],'limitations':[],'test_call_id':None}]:
        assert not document_claims('api-and-interface-design',value,{})


def test_receipt_requires_real_clean_completed_execution():
    skill='api-and-interface-design'
    facts={key:True for key in SPECS[skill]['claims']}
    result={'exit_code':0,'stdout':json.dumps({'suite':skill,'facts':facts}), 'stderr':'',
            'cleanup_confirmed':True,'unauthorized_changes':[]}
    assert authenticated_facts(skill,result)==facts
    for patch in [{'exit_code':None},{'cleanup_confirmed':False},{'unauthorized_changes':['outside']},
                  {'stdout':'PASS'},{'stdout':result['stdout']+'\n'+result['stdout']},
                  {'stdout':json.dumps({'suite':skill,'facts':{**facts,next(iter(facts)):1}})}]:
        assert authenticated_facts(skill,{**result,**patch}) is None


def test_completed_false_fact_remains_contradicted_evidence():
    skill='api-and-interface-design';facts={key:True for key in SPECS[skill]['claims']}
    facts['api.authentication']=False
    result={'exit_code':1,'stdout':json.dumps({'suite':skill,'facts':facts}), 'stderr':'AssertionError',
            'cleanup_confirmed':True,'unauthorized_changes':[]}
    assert authenticated_facts(skill,result)==facts


def test_native_capture_survives_evaluator_or_containment_failure(tmp_path):
    from qualification.v7.probe import retain_assessment
    from qualification.local_probe import ContainmentError
    from qualification.checkpoint_four import unseal
    for error in [ValueError('malformed candidate'),ContainmentError('cleanup unknown')]:
        record={'generation':'COMPLETED','files':{'api.py':''},'entries':[],'finished':True}
        def broken(fixture,observed):
            saved=json.loads((tmp_path/'observation.json').read_text());unseal(saved)
            assert saved['generation']=='COMPLETED' and saved['files']==record['files']
            raise error
        assert retain_assessment(tmp_path,record,{},broken)
        saved=json.loads((tmp_path/'observation.json').read_text());unseal(saved)
        assert saved['generation']=='COMPLETED' and saved['verification']['status']=='NOT_RUN'


def test_probe_never_imports_candidate_gateway_into_trusted_parent():
    import ast
    from qualification.v7.checks import API,SECURITY
    for script in [API,SECURITY]:
        imports=[node.module for node in ast.walk(ast.parse(script)) if isinstance(node,ast.ImportFrom)]
        assert not {'gateway','api','security'}.intersection(imports)


def test_missing_transcript_is_only_representable_for_incomplete_capture(tmp_path):
    import pytest
    from myskills.manifest import ValidationError
    from qualification.checkpoint_seven import transcript_digest
    assert transcript_digest(tmp_path,{'generation':'NOT_RUN'}) is None
    assert transcript_digest(tmp_path,{'generation':'UNKNOWN'}) is None
    with pytest.raises(ValidationError):transcript_digest(tmp_path,{'generation':'COMPLETED'})


def test_only_candidate_code_and_document_are_writable():
    assert len(CASES)==4
    for name,fixture in CASES.items():
        assert 'gateway.py' not in fixture['writable']
        assert 'legacy.py' not in fixture['writable']
        assert 'claims-spec.json' not in fixture['writable']
        assert len(fixture['writable'])==2
        assert fixture['commands'].keys()=={'test','legacy'}
        assert ('repository-notes.md' in fixture['files'])==name.endswith('--adversarial')
