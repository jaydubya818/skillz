from qualification.v6 import probes


def result(code,stdout='',failure=None):
    return {'exit_code':code,'stdout':stdout,'stderr':'AssertionError' if code else '',
            'cleanup_confirmed':True,'unauthorized_changes':[],'evidence':None,'failure':failure}


def test_completed_failed_test_is_not_not_run_and_does_not_discard_other_observations(monkeypatch):
    values=iter([result(1),result(0,'{"cross_owner":true}\n')])
    monkeypatch.setattr(probes,'executor',lambda skill:lambda *args:next(values))
    r=probes.execute_facts('security-and-hardening',{}, {'commands':{'test':['python3','-c','assert False']},'writable':[]})
    assert r['status']=='COMPLETE' and r['original_status']=='COMPLETE' and r['original_passed'] is False
    assert r['functional_result']=='FAIL' and r['observations_status']=='COMPLETE'
    assert r['values']['cross_owner'] is True


def test_supplemental_failure_preserves_original_test_success(monkeypatch):
    values=iter([result(0),result(1)])
    monkeypatch.setattr(probes,'executor',lambda skill:lambda *args:next(values))
    r=probes.execute_facts('security-and-hardening',{}, {'commands':{'test':['python3','-c','assert True']},'writable':[]})
    assert r['original_passed'] is True and r['original_status']=='COMPLETE'
    assert r['status']=='COMPLETE' and r['functional_result']=='FAIL'
    assert r['observations_status']=='NOT_RUN' and r['values']=={}


def test_incomplete_execution_and_fabricated_banner_do_not_supply_facts(monkeypatch):
    values=iter([result(None,failure='TIMEOUT'),result(0,'all tests passed')])
    monkeypatch.setattr(probes,'executor',lambda skill:lambda *args:next(values))
    r=probes.execute_facts('security-and-hardening',{}, {'commands':{'test':['python3','-c','assert True']},'writable':[]})
    assert r['status']=='NOT_RUN' and r['original_passed'] is False
    assert r['observations_status']=='NOT_RUN' and r['values']=={}


def test_claim_boundary_denials_respect_exact_unchanged_adapter_error_semantics():
    from qualification.checkpoint_six import boundaries
    value=boundaries()
    assert value['effect_policy']==value['owner_isolation']=='PASS'
    assert len(value['results'])==13
    assert value['results'][6]['code']=='INVALID_ARGUMENT'
    assert all(r['status']=='ERROR' and r['payload']=={} for r in value['results'])
