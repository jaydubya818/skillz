from pathlib import Path
from copy import deepcopy
from myskills.cohort_assessment import assess
from qualification.checkpoint_three import decisions
from qualification.native_probe import context
from myskills.manifest import ValidationError
import pytest


def test_infrastructure_and_unstable_batches_cannot_grant_behavioral_qualification():
    root=Path(__file__).parents[1];static=assess(root);ctx=context(root)
    trials=[{'binding':s['binding'],'runtime_admissible':False,'verification':{'bounded_workflow':'PASS'}} for s in static['skills'] for _ in range(2)]
    pin={'collector_commit':'0'*40,'bundle_digest':'sha256:'+'0'*64}
    result=decisions(static,trials,ctx,pin)
    assert len(result)==10 and all(s['status']=='PARTIAL' and not s['scope_qualified'] and not s['execution_eligible'] for s in result)
    for t in trials:t['runtime_admissible']=True
    result=decisions(static,trials,ctx,pin)
    assert all(s['status']=='PARTIAL' for s in result if s['remaining_workflow_gates'])
    assert all(not s['scope_qualified'] for s in result)
    assert all(not s['execution_eligible'] and s['catalog_trust']=='UNTRUSTED' for s in result)
    next(t for t in trials if t['binding']['skill_id']=='tdd')['verification']['bounded_workflow']='FAIL'
    assert next(s for s in decisions(static,trials,ctx,pin) if s['binding']['skill_id']=='tdd')['status']=='FAIL'


def test_supplemental_failure_overrides_pair_pass_and_rejects_mismatched_evidence():
    root=Path(__file__).parents[1];static=assess(root);ctx=context(root)
    trials=[{'binding':s['binding'],'case':s['binding']['skill_id']+'--'+kind,
             'observation_digest':'sha256:'+str(index)*64,'runtime_admissible':True,
             'verification':{'bounded_workflow':'PASS'}} for s in static['skills']
            for index,kind in enumerate(('representative','adversarial'))]
    pin={'collector_commit':'0'*40,'bundle_digest':'sha256:'+'0'*64}
    selected=next(t for t in trials if t['case']=='api-and-interface-design--representative')
    finding={**{k:selected[k] for k in ('binding','case','observation_digest')},'status':'FAIL'}
    review={'findings':[finding],'qualification_approvals':[selected['binding']]}
    decision=next(s for s in decisions(static,trials,ctx,pin,review) if s['binding']==selected['binding'])
    assert decision['native_command_workflow_pair_pass'] and not decision['scope_qualified'] and decision['status']=='FAIL'
    review['findings'][0]['observation_digest']='sha256:'+'f'*64
    with pytest.raises(ValidationError,match='output review binding mismatch'):
        decisions(static,trials,ctx,pin,review)
