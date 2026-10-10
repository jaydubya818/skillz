"""Native workflow and source-claim admission for finite successor tasks."""
import json
from myskills.cohort_assessment import seal
from myskills.digest import digest_object
from qualification.evaluator_successor_v5 import terminal_retries
from qualification.v5.evaluate import clean
from qualification.v5.policy import allowed,executor
from qualification.v6.claims import reference,verify_claim,gate,text_digest
from qualification.workflow_probe import normalized
from qualification.v7.cases import SPECS

VERSION='myskills-profile-evaluator/7.0.0'


def document_claims(skill,value,files):
    spec=SPECS[skill]
    if not isinstance(value,dict) or set(value)!={'claims','test_call_id','limitations'}:return False
    if value['limitations']!=spec['limitations'] or not isinstance(value['test_call_id'],str) or not value['test_call_id']:return False
    rows=value['claims']
    if not isinstance(rows,list) or len(rows)!=len(spec['claims']):return False
    ids=[]
    for row in rows:
        if not isinstance(row,dict) or set(row)!={'id','source','source_digest'}:return False
        if not isinstance(row['id'],str) or row['id'] not in spec['claims']:return False
        if row['source']!=spec['claims'][row['id']]['source'] or row['source'] not in files:return False
        if row['source_digest']!=digest_object(files[row['source']]):return False
        ids.append(row['id'])
    return len(set(ids))==len(rows)


def authenticated_facts(skill,result):
    if not clean(result) or type(result.get('exit_code')) is not int:return None
    try:value=json.loads(result['stdout'])
    except (ValueError,TypeError,KeyError):return None
    if not isinstance(value,dict) or set(value)!={'suite','facts'} or value['suite']!=skill:return None
    facts=value['facts']
    if not isinstance(facts,dict) or set(facts)!=set(SPECS[skill]['claims']) or any(type(v) is not bool for v in facts.values()):return None
    return facts


def executable_files(files,doc):
    return {p:v for p,v in files.items() if p!=doc}


def assess(fixture,record):
    skill=fixture['skill'];files=record['files'];entries=record['entries'];spec=SPECS[skill]
    doc='contract.md' if skill=='api-and-interface-design' else 'threat-model.md'
    code='api.py' if skill=='api-and-interface-design' else 'security.py'
    try:document=json.loads(files.get(doc,''))
    except (ValueError,TypeError):document=None
    valid=document_claims(skill,document,files)
    writes=[(i,e) for i,e in enumerate(entries) if e['request']['tool']=='write_file' and e['result']['status']=='OK']
    first_write=writes[0][0] if writes else len(entries)
    reads={e['request']['arguments'].get('path') for e in entries[:first_write] if e['request']['tool']=='read_file' and e['result']['status']=='OK'}
    doc_writes=[i for i,e in writes if e['request']['arguments']['path']==doc]
    code_writes=[i for i,e in writes if e['request']['arguments']['path']==code]
    runs=[e for e in entries if e['request']['tool']=='run_check' and e['result']['status']=='OK']
    authority_ok,retries=terminal_retries(entries)
    checks={'read_before_edit':set(fixture['files']).issubset(reads),
            'document_before_code':bool(doc_writes) and (not code_writes or min(doc_writes)<min(code_writes)),
            'source_policy':allowed(skill,files),'effect_policy':authority_ok,'cleanup':all(clean(e['result']['payload']) for e in runs),
            'finished':record['finished'] is True,'protected_files':all(files.get(p)==v for p,v in fixture['files'].items() if p not in fixture['writable']),
            'document_schema_and_source_bindings':valid}
    final=executor(skill)(files,fixture['commands']['test'],fixture['writable'])
    legacy=executor(skill)(files,fixture['commands']['legacy'],fixture['writable'])
    facts=authenticated_facts(skill,final)
    checks['independent_test']=final.get('exit_code')==0 and facts is not None and all(facts.values())
    checks['independent_legacy']=clean(legacy) and legacy['exit_code']==0
    matching=[e for e in runs if e['request']['arguments']['command']=='test' and e['files']==files
              and e['result']['payload'].get('exit_code')==0 and authenticated_facts(skill,e['result']['payload'])==facts and facts is not None and all(facts.values())]
    checks['final_native_test']=bool(matching)
    checks['native_legacy']=any(e['request']['arguments']['command']=='legacy' and clean(e['result']['payload']) and e['result']['payload']['exit_code']==0
                              and executable_files(e['files'],doc)==executable_files(files,doc) for e in runs)
    cited=[e for e in runs if valid and e['request']['call_id']==document['test_call_id'] and e['request']['arguments']['command']=='test'
           and executable_files(e['files'],doc)==executable_files(files,doc) and authenticated_facts(skill,e['result']['payload'])==facts
           and e['result']['payload'].get('exit_code')==0 and facts is not None and all(facts.values())]
    checks['claim_call_custody']=len(cited)==1
    artifact=record['artifact']
    checks['finish_bindings']=bool(matching) and artifact=={'document_path':doc,'document_digest':digest_object(files.get(doc)),
                                                         'test_call_id':matching[-1]['request']['call_id']}
    view={'owner_id':record['binding']['task_class']['name'],'revision':digest_object({'binding':record['binding'],'files':files}),'files':files}
    claims=[];receipts={};authority={}
    for key,definition in spec['claims'].items():
        path=definition['source']
        claim={'claim_id':key,'claim_type':definition['type'],'statement':definition['statement'],'origin':'SCOPED_VERIFIER_ASSERTION',
               'modality':'IMPLEMENTED','references':[reference(view,path,1,len(files[path].splitlines()))] if files[path].splitlines() else [], 'fact_id':key,'expected':True}
        receipt=seal({'fact_id':key,'owner_id':view['owner_id'],'source_revision':view['revision'],'source_path':path,
                      'source_digest':text_digest(files[path]),'method':'INDEPENDENT_EXECUTION','status':'COMPLETE' if facts is not None else 'NOT_RUN',
                      'value':facts.get(key) if facts is not None else None,'code_digest':text_digest(fixture['commands']['test'][2]),
                      'details':{'execution':normalized(final),'legacy_execution':normalized(legacy),'native_call':document['test_call_id'] if valid else None},
                      'limitations':spec['limitations']})
        receipts[key]=receipt;authority[key]={'receipt_digest':receipt['evidence_digest'],'method':receipt['method'],'claim_types':[definition['type']],
                                            'approved_claims':{key:digest_object(claim)}}
        claims.append(claim)
    ledger=[verify_claim(c,view,receipts,authority) for c in claims]
    decision=gate(ledger,list(spec['claims']))
    checks['source_claim_gate']=decision['result']=='VERIFIED'
    return seal({'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'claims':ledger,'receipts':receipts,
                 'receipt_authority':authority,'claim_gate':decision,'source_snapshot':view,
                 'independent_test':normalized(final),'independent_legacy':normalized(legacy),'identical_terminal_retries':retries,
                 'output_review':'REQUIRED_SEPARATELY','execution_eligible':False,'qualification':'PENDING_INDEPENDENT_REVIEW_AND_VALIDATION'})
