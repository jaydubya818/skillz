"""5.0.1 reevaluation of retained native captures; execution authority is unchanged.

An identical terminal acknowledgement can be retried with a new call ID. Adapter
4.0.1 correctly closes dispatch; its empty SESSION_CLOSED result is not a new
effect. The original evaluator result and exact native evidence remain retained.
"""
from copy import deepcopy
from qualification.v5.evaluate import evaluate as frozen_evaluate

VERSION='myskills-evaluator/5.0.1'
RECOVERABLE={'COMPLETED','NOT_FOUND','STALE_WRITE','INVALID_ARGUMENT','SOURCE_POLICY'}


def terminal_retries(entries):
    """Accept only an identical no-effect finish suffix, never post-close tools."""
    terminal=None;duplicates=[]
    for index,entry in enumerate(entries):
        request=entry['request'];result=entry['result']
        if terminal is None:
            if result['code'] not in RECOVERABLE:return False,[]
            if request['tool']=='finish' and result['status']=='OK' and result['code']=='COMPLETED':terminal=entry
            continue
        if not (request['tool']=='finish' and request['arguments']==terminal['request']['arguments']
                and result['code']=='SESSION_CLOSED' and result['status']=='ERROR' and result['payload']=={}
                and entry['files']==terminal['files']):return False,[]
        duplicates.append(index)
    return True,duplicates


def evaluate(fixture,files,entries,artifact,finished):
    frozen=frozen_evaluate(fixture,files,entries,artifact,finished)
    verdict=deepcopy(frozen);effects,retries=terminal_retries(entries)
    verdict['checks']['effect_policy']=effects
    verdict['status']='PASS' if all(verdict['checks'].values()) else 'FAIL'
    verdict['evaluation_successor']={'version':VERSION,'frozen_version':'myskills-evaluator/5.0.0',
                                   'frozen_status':frozen['status'],'identical_terminal_retry_indices':retries,
                                   'new_model_execution':False,'execution_policy_changed':False}
    return verdict
