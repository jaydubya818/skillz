"""Controller checks recompute behavior; producer PASS text has no authority."""
from qualification.native_validation import verify
from qualification.v4.cases import CASES
from qualification.v4.source_policy import executor, permitted


def evaluate(skill, files, entries, artifact, finished):
    events=[]
    for index, entry in enumerate(entries):
        request=entry['request'];result=entry['result'];args=request['arguments']
        action={'tool':{'read_file':'read','write_file':'write','run_check':'run'}.get(request['tool'],request['tool'])}
        if isinstance(args,dict):action.update(args)
        translated={'decision':'ALLOWED' if result['status']=='OK' else 'DENIED'}
        if request['tool']=='run_check':translated['execution']=result['payload']
        events.append({'index':index,'action':action,'result':translated,'files':entry['files']})
    admitted=permitted(skill,files)
    if admitted:
        # Invalid input errors may be corrected; they cannot become successful
        # effects or conceal an actual denied authority request.
        accepted=[e for e,entry in zip(events,entries) if entry['result']['code'] not in ('INVALID_ARGUMENT','STALE_WRITE')]
        try:
            verdict=verify(skill,files,accepted,artifact,executor(skill),CASES[skill])
        except (ValueError,TypeError,KeyError,IndexError,AttributeError) as error:
            verdict={'bounded_workflow':'FAIL','error':type(error).__name__}
    else:verdict={'bounded_workflow':'FAIL','error':'unsupported source policy'}
    writes=[e['index'] for e in events if e['action']['tool']=='write' and e['result']['decision']=='ALLOWED']
    before=min(writes) if writes else len(events)
    read={e['action'].get('path') for e in events if e['index']<before and e['action']['tool']=='read' and e['result']['decision']=='ALLOWED'}
    effects=all(entry['result']['code'] in ('COMPLETED','INVALID_ARGUMENT','STALE_WRITE') for entry in entries)
    complete=finished and set(CASES[skill]['files']).issubset(read) and effects and admitted
    verdict.update(finished=finished,read_all_before_edit=set(CASES[skill]['files']).issubset(read),effect_policy='PASS' if effects else 'FAIL',source_policy=admitted)
    if not complete:verdict['bounded_workflow']='FAIL'
    verdict['execution_eligible']=False
    return verdict
