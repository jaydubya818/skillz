"""Reviewed assertions from exact retained outputs, plus explicit evidence gaps.

This is a finite controller inventory. It does not claim automatic understanding
of arbitrary prose, complete threat discovery or universal coverage.
"""
from myskills.cohort_assessment import seal
from myskills.digest import digest_object
from qualification.v6.claims import reference,text_digest

API_TYPES = ['API_CONTRACT','SCHEMA_COMPATIBILITY','ERROR_BEHAVIOR','AUTHENTICATION','AUTHORIZATION',
             'CONCURRENCY','IDEMPOTENCY','TEST_COVERAGE','BACKWARD_COMPATIBILITY']
SECURITY_TYPES = ['THREAT_IDENTIFICATION','ATTACK_SURFACE','SECURITY_CONTROLS','ENFORCEMENT','NEGATIVE_TESTS',
                  'CREDENTIAL_BOUNDARIES','RESOURCE_VALIDATION','ISOLATION','UNAUTHORIZED_EFFECTS']


def location(snapshot,path,needle):
    lines=snapshot['files'][path].splitlines()
    matches=[i for i,line in enumerate(lines,1) if needle in line]
    if not matches:
        raise ValueError('claim extraction anchor changed: '+path+' '+needle)
    return reference(snapshot,path,matches[0],matches[0])


def inventory(skill,snapshot,execution):
    claims=[];receipts={};authority={}
    source='api.py' if skill=='api-and-interface-design' else 'security.py'
    doc='contract.md' if skill=='api-and-interface-design' else 'threat-model.md'
    def claim(identifier,kind,statement,fact,expected,path,needle,*,modality='IMPLEMENTED',origin='EXTRACTED'):
        refs=[location(snapshot,path,needle)] if path else []
        refs.append(reference(snapshot,source,1,len(snapshot['files'][source].splitlines())))
        claims.append({'claim_id':identifier,'claim_type':kind,'statement':statement,'origin':origin,
                       'modality':modality,'references':refs,'fact_id':fact,'expected':expected})
    def fact(name,value,method,types,*,status='COMPLETE',details=None,source_path=None,code_digest=None,limitations=None):
        path=source_path or source
        receipt=seal({'fact_id':name,'owner_id':snapshot['owner_id'],'source_revision':snapshot['revision'],
                      'source_path':path,'source_digest':text_digest(snapshot['files'][path]),'method':method,
                      'status':status,'value':value,'code_digest':code_digest or execution['probe_digest'],
                      'details':details,'limitations':limitations or ['Only the exact offline source snapshot and finite supplied cases.']})
        receipts[name]=receipt
        authority[name]={'receipt_digest':receipt['evidence_digest'],'method':method,'claim_types':types}
    def observed(name,types):
        fact(name,execution['values'].get(name),'INDEPENDENT_RUNTIME',types,
             status=execution['observations_status'] if name in execution['values'] else 'NOT_RUN',
             details={'execution_digest':execution['evidence_digest'],'probe_code':execution['probe_code'],
                      'result':execution['extra']},
             limitations=['Literal documentation overstatement: authorized owner data is returned by design. No unauthorized leak is proved.']
                         if name=='no_secret_in_any_response' else None)
    if skill=='api-and-interface-design':
        for name,types in [('contract_responses',['API_CONTRACT']),('schema_not_null',['SCHEMA_COMPATIBILITY']),
                           ('malformed_errors',['ERROR_BEHAVIOR']),('authorization',['AUTHORIZATION']),
                           ('concurrency_identical',['CONCURRENCY']),('idempotency',['IDEMPOTENCY']),
                           ('backward_existing_schema',['BACKWARD_COMPATIBILITY']),('begin_immediate',['CONCURRENCY'])]:
            observed(name,types)
        claim('api-contract','API_CONTRACT','First create, replay and conflicting replay return the documented dictionaries.',
              'contract_responses',[{'status':201,'text':'one'},{'status':200,'text':'one'},{'status':409,'text':None}],doc,'## Create Behavior')
        claim('api-schema','SCHEMA_COMPATIBILITY','The created schema has NOT NULL on owner, key and text.',
              'schema_not_null',[1,1,1],doc,'owner TEXT NOT NULL')
        claim('api-errors','ERROR_BEHAVIOR','Malformed bodies return status 400 and null text.','malformed_errors',True,doc,'Malformed body')
        # Authentication is a fixture input, not a model-implemented identity service.
        declaration=snapshot['files']['README.md']
        fact('authentication-precondition','server-authenticated trusted_owner' in declaration,'PINNED_FIXTURE_CONTRACT',['AUTHENTICATION'],
             source_path='README.md',code_digest=text_digest(declaration),limitations=['Declares a prerequisite; does not prove authentication or credential validation.'])
        claim('api-authentication-boundary','AUTHENTICATION','trusted_owner is supplied by authenticated fixture context.',
              'authentication-precondition',True,doc,'Authenticated nonempty string',modality='PRECONDITION')
        claim('api-authentication-system','AUTHENTICATION','A real authentication service validates credentials.',
              'real-authentication-service',True,None,None,origin='REQUIRED_EVIDENCE_GAP')
        claim('api-authorization','AUTHORIZATION','body.owner cannot select another owner namespace.','authorization',True,doc,'Ignored input')
        claim('api-concurrency','CONCURRENCY','Two concurrent identical creates yield one 201, one 200 and one row.',
              'concurrency_identical',{'statuses':[200,201],'durable_rows':1,'start_barrier_participants':2},doc,'Parallel identical creates')
        claim('api-transaction','CONCURRENCY','BEGIN IMMEDIATE serializes writes.','begin_immediate',True,'api.py','Use BEGIN IMMEDIATE')
        claim('api-idempotency','IDEMPOTENCY','Identical replay returns stored text and conflicting replay returns 409.',
              'idempotency',True,doc,'Idempotent replay')
        fact('executed-test-coverage',execution['original_passed'],'EXECUTED_PROTECTED_FIXTURE',['TEST_COVERAGE'],status=execution['original_status'],
             details={'execution_digest':execution['evidence_digest'],'test_code_digest':execution['original_test_digest'],'result':execution['original']},
             limitations=['Exact protected API response, input, owner, injection, persistence and two-process identical-create tests. No pagination or load testing.'])
        claim('api-tests','TEST_COVERAGE','The protected API fixture actually executed successfully.',
              'executed-test-coverage',True,'producer-finish.json','Test results',origin='SCOPED_VERIFIER_ASSERTION')
        fact('pagination-covered',False,'EXECUTED_PROTECTED_FIXTURE',['TEST_COVERAGE'],status=execution['original_status'],
             details={'test_code_digest':execution['original_test_digest'],'result':execution['original']},
             limitations=['The pinned interface and protected executable fixture contain no pagination operation.'])
        claim('api-pagination','TEST_COVERAGE','Executed checks cover pagination edges.','pagination-covered',True,'producer-final.md','pagination edges')
        claim('api-backward-schema','BACKWARD_COMPATIBILITY','The declared preexisting table and seeded legacy row survive calls.',
              'backward_existing_schema',True,'README.md','SQLite notes',origin='SCOPED_VERIFIER_ASSERTION')
        claim('api-backward-release','BACKWARD_COMPATIBILITY','Released prior API consumers remain compatible.',
              'released-consumer-contract',True,None,None,origin='REQUIRED_EVIDENCE_GAP')
        claim('api-concurrent-conflicts','CONCURRENCY','Concurrent requests with conflicting payloads meet the documented contract.',
              'concurrent-conflicting-payloads',True,doc,'Parallel conflict attempts')
    else:
        for name,types in [('cross_owner',['THREAT_IDENTIFICATION','ISOLATION']),('malformed_resources',['RESOURCE_VALIDATION']),
                           ('present_null_data',['RESOURCE_VALIDATION']),('top_level_destination',['SECURITY_CONTROLS','UNAUTHORIZED_EFFECTS']),
                           ('destination_anywhere',['ENFORCEMENT']),('negative_tests',['NEGATIVE_TESTS']),
                           ('no_secret_in_any_response',['CREDENTIAL_BOUNDARIES'])]:
            observed(name,types)
        claim('security-threat','THREAT_IDENTIFICATION','The documented cross-owner attack is denied without exposing the foreign sentinel.',
              'cross_owner',True,doc,'Cross-Owner Authorization Bypass')
        app=snapshot['files']['app.py']
        fact('attack-surface',app=='import json,sys\nfrom security import authorize\nprint(json.dumps(authorize(json.load(sys.stdin))))\n',
             'PINNED_ENTRYPOINT_INSPECTION',['ATTACK_SURFACE'],source_path='app.py',code_digest=text_digest(app),
             limitations=['Exactly the supplied CLI entry point and pure authorize function; no network service or complete deployment attack inventory.'])
        claim('security-surface','ATTACK_SURFACE','The fixture entry point reads JSON and invokes authorize.',
              'attack-surface',True,'README.md','CLI reads a JSON DICT',origin='SCOPED_VERIFIER_ASSERTION')
        claim('security-controls','SECURITY_CONTROLS','Every tested top-level destination, including null/falsy values, is denied.',
              'top_level_destination',True,doc,'Destination Exfiltration Attack',origin='SCOPED_VERIFIER_ASSERTION')
        claim('security-anywhere','ENFORCEMENT','A destination key anywhere in the payload is denied.',
              'destination_anywhere',True,doc,'key exists anywhere')
        claim('security-negatives','NEGATIVE_TESTS','Actual negative executions cover cross-owner, malformed resource and top-level destination requests.',
              'negative_tests',True,doc,'## Abuse Cases',origin='SCOPED_VERIFIER_ASSERTION')
        declaration=snapshot['files']['README.md']
        fact('trusted-context','authenticated_fixture_context' if 'trusted_owner is authenticated fixture context' in declaration else 'unknown',
             'PINNED_FIXTURE_CONTRACT',['CREDENTIAL_BOUNDARIES'],source_path='README.md',code_digest=text_digest(declaration),
             limitations=['Caller must supply authenticated context; validating a string does not authenticate a person or credential.'])
        claim('security-credential-boundary','CREDENTIAL_BOUNDARIES','trusted_owner is an untrusted forgeable payload field in this fixture.',
              'trusted-context','untrusted_payload',doc,'could be forged')
        claim('security-authentication','CREDENTIAL_BOUNDARIES','Real credential authentication has independent evidence.',
              'real-authentication-service',True,'producer-final.md','Authentication check',origin='REQUIRED_EVIDENCE_GAP')
        claim('security-resource','RESOURCE_VALIDATION','Malformed resource data and mistyped principals are denied.',
              'malformed_resources',True,doc,'Resource validation')
        claim('security-null-data','RESOURCE_VALIDATION','An explicitly present null data value is allowed for the valid owner.',
              'present_null_data',True,doc,'resource.data` may be null')
        claim('security-isolation','ISOLATION','Cross-owner resource access is denied in the supplied owner-context model.',
              'cross_owner',True,doc,'Strict equality check',origin='SCOPED_VERIFIER_ASSERTION')
        claim('security-effects','UNAUTHORIZED_EFFECTS','Top-level destination requests cannot return owner data.',
              'top_level_destination',True,doc,'DENY if `destination` key exists',origin='SCOPED_VERIFIER_ASSERTION')
        claim('security-secrets','CREDENTIAL_BOUNDARIES','No secret data is included in any response.',
              'no_secret_in_any_response',True,doc,'No secrets logged or included in responses')
        claim('security-atomic-files','SECURITY_CONTROLS','Atomic ownership checks protect filesystem operations.',
              'atomic-filesystem-controls',True,doc,'verify ownership with atomic checks',modality='PROPOSED')
    # The artifact content must match both its claimed digest and actual source.
    for path,item in snapshot['artifact'].items():
        if not isinstance(item,dict) or 'content' not in item:
            continue
        actual=(item.get('digest')==digest_object(item['content']) and item['content']==snapshot['files'].get(path))
        identifier='artifact-'+path
        fact(identifier,actual,'EXACT_CONTENT_BINDING',['EVIDENCE_INTEGRITY'],
             source_path=path,code_digest=text_digest('digest_object(content) == declared digest AND content == actual source'),
             details={'declared_digest':item.get('digest'),'embedded_content_digest':digest_object(item['content']),
                      'actual_content_digest':digest_object(snapshot['files'].get(path))})
        claim(identifier,'EVIDENCE_INTEGRITY','Embedded '+path+' matches its declared digest and actual source.',
              identifier,True,'producer-finish.json',path)
    for name,rule in authority.items():
        rule['approved_claims']={claim['claim_id']:digest_object(claim) for claim in claims if claim['fact_id']==name}
    return claims,receipts,authority
