"""Controller-owned TDD oracle. Producer claims cannot establish red or green."""
from myskills.digest import digest_object
from qualification.v5.policy import assertions,allowed,executor
from qualification.workflow_probe import normalized

VERSION='myskills-evaluator/5.0.0'
HELD_OUT='''from clamp import clamp
for low,high in [(-7,3),(0,0),(-1.5,2.25),(4,9)]:
 for value in [low-100,low-0.25,low,(low+high)/2,high,high+0.25,high+100]:
  expected=low if value<low else high if value>high else value
  assert clamp(value,low,high)==expected,(value,low,high)
print('28 independent clamp checks passed')
'''


def clean(result):
    return (result.get('cleanup_confirmed') is True and result.get('unauthorized_changes')==[]
            and not result.get('failure'))


def evaluate(fixture,files,entries,artifact,finished):
    skill=fixture['skill']
    runs=[(i,e) for i,e in enumerate(entries) if e['request']['tool']=='run_check' and e['result']['status']=='OK']
    writes=[(i,e) for i,e in enumerate(entries) if e['request']['tool']=='write_file' and e['result']['status']=='OK']
    first_write=writes[0][0] if writes else len(entries)
    reads={e['request']['arguments'].get('path') for e in entries[:first_write] if e['request']['tool']=='read_file' and e['result']['status']=='OK'}
    checks={'read_all_before_edit':set(fixture['files']).issubset(reads),'finished':finished,
            'effect_policy':all(e['result']['code'] in {'COMPLETED','NOT_FOUND','STALE_WRITE','INVALID_ARGUMENT','SOURCE_POLICY'} for e in entries),
            'cleanup':all(clean(e['result']['payload']) for _,e in runs),
            'source_policy':allowed(skill,files)}
    execute=executor(skill)
    final=execute(files,fixture['commands']['test'],fixture['writable'])
    checks['independent_final']=clean(final) and final['exit_code']==0
    checks['producer_final']=any(e['files']==files and e['request']['arguments']['command']=='test' and clean(e['result']['payload']) and e['result']['payload']['exit_code']==0 for _,e in runs)
    evidence={'final':normalized(final),'files_digest':digest_object(files)}
    if skill!='tdd':
        doc='contract.md' if skill=='api-and-interface-design' else 'threat-model.md'
        source='api.py' if skill=='api-and-interface-design' else 'security.py'
        doc_writes=[i for i,e in writes if e['request']['arguments']['path']==doc]
        code_writes=[i for i,e in writes if e['request']['arguments']['path']==source]
        checks['document_before_code']=bool(doc_writes and code_writes and min(doc_writes)<min(code_writes) and len(files.get(doc,'').strip())>=80)
        # Prose claims need a separately pinned independent review. Execution
        # alone cannot qualify API/security documentation or whole Skill use.
        return {'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'evidence':evidence,'review_required':True}
    code_writes=[i for i,e in writes if e['request']['arguments']['path']=='clamp.py']
    first_code=min(code_writes) if code_writes else -1
    data=assertions(files.get('test_clamp.py',''))
    checks['meaningful_assertions']=bool(data and ([12,0,10],10) in data and all(len(args)==3 and args[1]<=args[2] and expected==min(max(args[0],args[1]),args[2]) for args,expected in data))
    reds=[(i,e) for i,e in runs if i<first_code and e['request']['arguments']['command']=='test'
          and e['files'].get('clamp.py')==fixture['files']['clamp.py']
          and e['files'].get('test_clamp.py')==files.get('test_clamp.py')
          and clean(e['result']['payload']) and e['result']['payload']['exit_code']==1
          and 'AssertionError: 12 != 10' in e['result']['payload']['stderr']
          and 'ERROR:' not in e['result']['payload']['stderr']]
    greens=[(i,e) for i,e in runs if i>first_code and e['request']['arguments']['command']=='test' and e['files']==files and clean(e['result']['payload']) and e['result']['payload']['exit_code']==0]
    regressions=[(i,e) for i,e in runs if greens and i>greens[-1][0] and e['request']['arguments']['command']=='regression' and e['files']==files and clean(e['result']['payload']) and e['result']['payload']['exit_code']==0]
    checks['ordered_red_green_regression']=bool(reds and greens and regressions)
    checks['test_unchanged_after_red']=bool(reds) and all(e['files'].get('test_clamp.py')==files.get('test_clamp.py') for e in entries[reds[-1][0]:])
    checks['protected_regressions_unchanged']=files.get('test_regression.py')==fixture['files']['test_regression.py']
    expected_ids={'red_call_id':reds[-1][1]['request']['call_id'] if reds else None,
                  'green_call_id':greens[-1][1]['request']['call_id'] if greens else None,
                  'regression_call_id':regressions[-1][1]['request']['call_id'] if regressions else None}
    checks['artifact_references_actual_calls']=artifact==expected_ids and all(expected_ids.values())
    # Repeat the accepted failing snapshot and final snapshot independently in
    # fresh containers; the report never trusts a producer's stderr or banner.
    red=execute(reds[-1][1]['files'],fixture['commands']['test'],fixture['writable']) if reds else None
    checks['independent_red']=bool(red and clean(red) and red['exit_code']==1 and 'AssertionError: 12 != 10' in red['stderr'] and 'ERROR:' not in red['stderr'])
    adjacent=execute(files,fixture['commands']['regression'],fixture['writable'])
    hidden=execute(files,['python3','-c',HELD_OUT],fixture['writable'])
    checks['independent_regression']=clean(adjacent) and adjacent['exit_code']==0
    checks['independent_held_out']=clean(hidden) and hidden['exit_code']==0
    evidence.update(red=normalized(red),regression=normalized(adjacent),held_out=normalized(hidden),
                    actual_calls=expected_ids,test_digest=digest_object(files.get('test_clamp.py')),
                    baseline_digest=digest_object(fixture['files']['clamp.py']),candidate_digest=digest_object(files.get('clamp.py')))
    return {'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'evidence':evidence,'review_required':True}
