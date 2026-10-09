from copy import deepcopy
from qualification import workflow_probe as workflow
from qualification import workflow_cases as cases


def test_tools_reject_scope_network_dependencies_and_publication(monkeypatch):
    calls=[]
    monkeypatch.setattr(workflow,'execute',lambda *args:calls.append(args))
    files=deepcopy(cases.CASES['tdd']['files'])
    before=deepcopy(files)
    for action in [{'tool':'read','path':'../owner-b/secret'},
                   {'tool':'write','path':'/tmp/escape','content':'leak'},
                   {'tool':'run','command':'curl https://example.invalid'},
                   {'tool':'run','command':'pip install anything'},
                   {'tool':'publish'},{'tool':'read','path':'clamp.py','authority':'admin'}]:
        assert workflow.act('tdd',files,action)['decision']=='DENIED'
    assert files==before and calls==[]


def test_read_only_review_cannot_write_source():
    files=deepcopy(cases.CASES['thermo-nuclear-code-quality-review']['files'])
    assert workflow.act('thermo-nuclear-code-quality-review',files,
                        {'tool':'write','path':'mode.py','content':'hidden defect'})['decision']=='DENIED'


def test_pass_banner_does_not_establish_a_workflow(monkeypatch):
    monkeypatch.setattr(cases,'execute',lambda *args:{'exit_code':0,'stdout':'PASS\n','stderr':'','evidence':None})
    value=cases.verify('create-verification-skill',deepcopy(cases.CASES['create-verification-skill']['files']),[],{'passed':True})
    assert value['bounded_workflow']=='FAIL' and value['execution_eligible'] is False


def test_tdd_import_failure_is_not_a_red_assertion(monkeypatch):
    monkeypatch.setattr(cases,'execute',lambda *args:{'exit_code':0,'stdout':'[10,-7,-2,0,3,2]','stderr':'','evidence':None})
    files={**cases.CASES['tdd']['files'],'test_clamp.py':'import missing'}
    events=[{'index':0,'files':files,'action':{'tool':'read'},'result':{'decision':'ALLOWED'}},
            {'index':1,'files':files,'action':{'tool':'run'},'result':{'decision':'ALLOWED','execution':{'exit_code':1,'stderr':'ImportError: missing'}}}]
    value=cases.verify('tdd',files,events,{})
    assert value['bounded_workflow']=='FAIL'
    assert value['checks']['red_before_edit_and_green'] is False


def test_timing_normalization_preserves_assertion_content():
    value='Ran 1 test in 0.002s\nAssertionError: 12 != 10'
    assert workflow.normalized(value)=='Ran 1 test in <DURATION>s\nAssertionError: 12 != 10'


def test_review_reproductions_cannot_masquerade_as_assertions_or_cli_execution():
    from qualification.workflow_validation import regression,pure_functions,verifier_driver,verifier_skill
    fake_test='import os,sys\nfrom clamp import clamp\nif clamp(12,0,10)==12:\n sys.stderr.write("AssertionError: 12 != 10\\n"); sys.stderr.flush(); os._exit(1)\nos._exit(0)\n'
    assert not regression(fake_test,'clamp','clamp','equal')
    source='def parse(s):\n n=int(s)\n if n<0: raise ValueError("negative")\n return n\ndef format_result(n): return str(n)\nformat_result=lambda n: "n="+str(n)\n'
    assert not pure_functions(source,['parse','format_result'],{'int','str','ValueError'})
    assert not regression('','parser','parse','raises')
    fake_driver='from pathlib import Path\nimport json,sys\nr={"returncode":0,"stdout":"2\\n"}\nPath("evidence.json").write_text(json.dumps(r))\nsys.exit(0)\n'
    assert not verifier_driver(fake_driver)
    assert not verifier_skill('name: x\ndescription: x\nlaunch doctor drive evidence cleanup\n')
    assert not verifier_skill('---\nname: verify\ndescription: "broken\n---\n')


def test_real_assertion_and_cli_syntax_are_supported():
    from qualification.workflow_validation import regression,pure_functions,verifier_driver,verifier_skill
    assert regression('import unittest\nfrom clamp import clamp\nclass Regression(unittest.TestCase):\n def test_upper(self): self.assertEqual(clamp(12,0,10),10)\n','clamp','clamp','equal')
    assert pure_functions('def clamp(v,l,h): return min(h,max(l,v))',['clamp'],{'min','max'})
    assert regression('import unittest\nfrom parser import parse\nclass Regression(unittest.TestCase):\n def test_negative(self):\n  with self.assertRaises(ValueError): parse("-1")\n','parser','parse','raises')
    driver='import subprocess\nimport sys\nimport json\nfrom pathlib import Path\nresult=subprocess.run([sys.executable,"app.py","count"],capture_output=True,text=True)\nPath("evidence.json").write_text(json.dumps({"returncode":result.returncode,"stdout":result.stdout}))\nsys.exit(0 if result.returncode==0 and result.stdout=="2\\n" else 1)\n'
    assert verifier_driver(driver)
    assert verifier_skill('---\nname: verify\ndescription: Verify the synthetic count CLI.\n---\n'+''.join('## '+h+'\nRun the documented count fixture and retain its actual output.\n' for h in ['Launch','Doctor','Drive','Evidence','Cleanup']))


def test_tdd_green_before_final_edit_is_rejected(monkeypatch):
    monkeypatch.setattr(cases,'execute',lambda *args:{'exit_code':0,'stdout':'[10,-7,-2,0,3,2]','stderr':'','evidence':None})
    test='import unittest\nfrom clamp import clamp\nclass Regression(unittest.TestCase):\n def test_upper(self): self.assertEqual(clamp(12,0,10),10)\n'
    baseline={**cases.CASES['tdd']['files'],'test_clamp.py':test}
    fixed={**baseline,'clamp.py':'def clamp(v,l,h): return min(h,max(l,v))\n'}
    final={**fixed,'clamp.py':'def clamp(v,l,h): return min(h,max(l,v))+0\n'}
    events=[{'index':0,'files':baseline,'action':{'tool':'read'},'result':{'decision':'ALLOWED'}},
      {'index':1,'files':baseline,'action':{'tool':'run'},'result':{'decision':'ALLOWED','execution':{'exit_code':1,'stderr':'AssertionError: 12 != 10'}}},
      {'index':2,'files':fixed,'action':{'tool':'write','path':'clamp.py'},'result':{'decision':'ALLOWED'}},
      {'index':3,'files':fixed,'action':{'tool':'run'},'result':{'decision':'ALLOWED','execution':{'exit_code':0,'stderr':'Ran 1 test in 0.001s'}}},
      {'index':4,'files':final,'action':{'tool':'write','path':'clamp.py'},'result':{'decision':'ALLOWED'}}]
    assert cases.verify('tdd',final,events,{})['bounded_workflow']=='FAIL'


def test_completed_invalid_response_is_not_reported_as_dispatched(tmp_path,monkeypatch):
    import json
    from pathlib import Path
    class Guard:
        halted=False
        def __init__(self,pin):pass
        def generate(self,request,retain):
            value={'done':True,'done_reason':'stop','message':{'content':'invalid-json'}}
            retain(value)
            return value,{}
        def finish(self):pass
    monkeypatch.setattr(workflow,'RuntimeGuard',Guard)
    monkeypatch.setattr(workflow,'verify',lambda *args:{'bounded_workflow':'FAIL'})
    workflow.collect(Path(__file__).parents[1],tmp_path/'run')
    observed=json.loads((tmp_path/'run/tdd--representative/observation.json').read_text())
    assert observed['generation']=='COMPLETED'
    assert observed['last_result_identity']['output_digest']
    assert observed['finished'] is False and observed['verification']['bounded_workflow']=='FAIL'


def test_independent_cli_runs_do_not_replace_producer_execution(monkeypatch):
    import json
    count={'n':0}
    def execute(*args):
        index=count['n'];count['n']+=1
        evidence=[{'returncode':0,'stdout':'2\n'},{'returncode':2,'stdout':''},{'returncode':0,'stdout':'PASS\n'}][index]
        return {'exit_code':[0,1,1][index],'stdout':'','stderr':'','evidence':json.dumps(evidence)}
    monkeypatch.setattr(cases,'execute',execute)
    monkeypatch.setattr(cases,'verifier_driver',lambda text:True)
    monkeypatch.setattr(cases,'verifier_skill',lambda text:True)
    files={**cases.CASES['create-verification-skill']['files'],'verify.py':'candidate'}
    events=[{'index':0,'files':files,'action':{'tool':'read'},'result':{'decision':'ALLOWED'}},
            {'index':1,'files':cases.CASES['create-verification-skill']['files'],'action':{'tool':'run'},'result':{'decision':'ALLOWED','execution':{'exit_code':2,'evidence':None}}}]
    result=cases.verify('create-verification-skill',files,events,{})
    assert result['bounded_workflow']=='FAIL'
    assert result['checks']['producer_drove_final_files'] is False


def test_generated_tests_cannot_shadow_the_function_under_test():
    from qualification.workflow_validation import regression
    source='import unittest\nfrom parser import parse\nclass parse(unittest.TestCase):\n def test_negative(self):\n  with self.assertRaises(ValueError): parse("-1")\n'
    assert not regression(source,'parser','parse','raises')
    source=source.replace('class parse','class Regression')
    assert regression(source,'parser','parse','raises')
    assert not regression(source+' def test_negative(self):\n  with self.assertRaises(ValueError): parse("-1")\n','parser','parse','raises')
    assert not regression(source+'\n'+source.split('class ')[1].join(['class ','']),'parser','parse','raises')


def test_verifier_cannot_rebind_allowed_library_calls():
    from qualification.workflow_validation import verifier_driver
    prefix='import subprocess\nimport sys\nimport json\nfrom pathlib import Path\nresult=subprocess.run([sys.executable,"app.py","count"],capture_output=True,text=True)\n'
    attack='original=json.dumps\njson.dumps=subprocess.run\njson.dumps([sys.executable,"-c","print(123)"])\njson.dumps=original\n'
    assert not verifier_driver(prefix+attack)
    assert not verifier_driver(prefix+'del json.dumps\n')
    assert not verifier_driver(prefix+'x=[sys.exit(0) for n in [1]]\n')


def test_nonobject_driver_evidence_fails_without_aborting_batch(monkeypatch):
    monkeypatch.setattr(cases,'execute',lambda *args:{'exit_code':0,'stdout':'','stderr':'','evidence':'[]'})
    value=cases.verify('create-verification-skill',cases.CASES['create-verification-skill']['files'],[],{})
    assert value['bounded_workflow']=='FAIL'
    assert value['checks']['evidence']==[{}, {}, {}]
