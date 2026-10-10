"""Supplement original executable checks with bounded contention evidence."""
from qualification.v7.checks import API as HISTORICAL_API, SECURITY
from qualification.v8.sqlite_probe import LOCK_PROBE, RACE_PROBE, PLAIN_WORKER

_FINAL = "print(json.dumps({'suite':'api-and-interface-design','facts':facts},sort_keys=True))\nassert all(facts.values()),facts\n"
assert HISTORICAL_API.count(_FINAL) == 1
API = HISTORICAL_API.replace(_FINAL, '') + LOCK_PROBE + r'''
reader_cases=[locked_reader_case(mode) for mode in ['DELETE','WAL']]
reader_ok=all(case['reader_present_at_sql'] and case['outcome']['error'] is None
 and case['outcome']['response']=={'status':201,'text':'one'}
 and case['rows']==[('a','k','one'),('legacy','keep','old')]
 and case['final_mode']==case['mode'].lower()
 and not any(sql.strip().upper().startswith('PRAGMA JOURNAL_MODE=') for sql in case['outcome']['statements'])
 for case in reader_cases)
''' + RACE_PROBE + '\nworker='+repr(PLAIN_WORKER)+r'''
paired=[paired_case(texts) for texts in [['one','one'],['one','two']] for _ in range(4)]
pair_ok=True
for case in paired:
 outcomes=case['outcomes']
 okay=case['participants']==2 and all(o['error'] is None for o in outcomes)
 if okay:
  responses=[o['response'] for o in outcomes]
  expected=[200,201] if case['texts'][0]==case['texts'][1] else [201,409]
  winners=[r for r in responses if r['status']==201]
  okay=sorted(r['status'] for r in responses)==expected and len(winners)==1 and case['rows']==[('a','k',winners[0]['text'])]
 pair_ok=pair_ok and okay
facts['api.concurrency']=facts['api.concurrency'] and reader_ok and pair_ok
facts['api.coverage']=all(facts.values())
''' + _FINAL
