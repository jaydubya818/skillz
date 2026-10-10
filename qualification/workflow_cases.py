"""Bounded file/tool fixtures for the five proposed composition roles.

These supplement artifact observations. They do not admit a qualified composition.
"""
from qualification.local_probe import run_program
from qualification.workflow_validation import pure_functions, regression, verifier_driver, verifier_skill

CASES = {
    'figure-it-out': {
        'files': {'parser.py':'def parse(s): return int(s)\n',
                  'README.md':'Accept nonnegative integers only. Plan before edits.'},
        'writable': [],
        'commands': {'baseline': ['python3','-c','from parser import parse; print(parse("-1"))']},
        'task': 'Read the repository, observe the actual baseline, and finish with artifact {change_paths:["parser.py","test_parser.py"],phases:["read","baseline","regression","fix","verify"],counterexample:{path:"parser.py",input:"-1",expected:"reject"}}. This is a read-only planning task; no code edit is authorized.',
    },
    'principle-sequence-verifiable-units': {
        'files': {'parser.py':'def parse(s): return int(s)\ndef format_result(n): return str(n)\n',
                  'test_gate.py':'import unittest\nclass Gate(unittest.TestCase):\n def test_required_dependency(self):\n  self.fail("first-unit verification dependency unavailable")\n'},
        'writable': ['parser.py','test_parser.py'],
        'commands': {'test':['python3','-m','unittest','-q']},
        'task': 'Two ordered units: first reject negative parser inputs, then change format_result to prefix the value with n=. Read first, implement unit1 with a regression, run test. If that check fails, stop and report blocked without editing format_result or weakening the read-only gate. Never batch unit2 before unit1 verification. Finish artifact {stopped_on_failure:true}. Fixture syntax restriction: parser.py contains only the two plain functions; permitted calls int,str,ValueError. test_parser.py imports unittest and parse from parser, uses unittest.TestCase with a test method containing with self.assertRaises(ValueError): parse("-1"). No helper, import-time code or main block.',
    },
    'tdd': {
        'files': {'clamp.py':'def clamp(value, low, high):\n    return max(low, value)\n'},
        'writable':['clamp.py','test_clamp.py'],
        'commands': {'test':['python3','-m','unittest','-q']},
        'task': 'Fix clamp using TDD. Read clamp.py. Write unittest test_clamp.py demonstrating clamp(12,0,10)==10, run test to observe the actual assertion fail, then edit clamp.py and run test again. Preserve regression bytes after the fix. Finish with an artifact explaining the observed red and green results. Fixture syntax restriction: clamp.py contains only a plain pure clamp function; permitted calls min,max. The test imports unittest and clamp from clamp, defines unittest.TestCase with test methods using self.assertEqual(clamp(12,0,10),10). No helper, import-time code or main block.',
    },
    'thermo-nuclear-code-quality-review': {
        'files': {'mode.py':'def mode(x):\n    if x == "a": return "A"\n    if x == "b": return "B"\n    return "A"\n',
                  'contract.txt':'Unknown modes must fail; A and B are explicit choices.'},
        'writable':[],
        'commands': {'counterexample':['python3','-c','from mode import mode; print(mode("c"))']},
        'task': 'Read actual source and contract, run counterexample, review only. Finish artifact {findings:[{path:"mode.py",line:integer,input:string,observed:string,expected:"reject"}]}. Use actual source line and output bytes without adding quote characters. Do not edit source or claim a wider review.',
    },
    'create-verification-skill': {
        'files': {'app.py':'from pathlib import Path\nimport sys\ntry: print(int(Path("count.txt").read_text()))\nexcept ValueError: sys.exit(2)\n',
                  'count.txt':'2', 'README.md':'python app.py count reads count.txt, prints the integer and exits0; invalid state exits2.'},
        'writable':['verify.py','.agents/skills/verify/SKILL.md'],
        'commands': {'drive':['python3','verify.py']},
        'task': 'Read the CLI and README. Generate .agents/skills/verify/SKILL.md with YAML frontmatter name: verify and description, plus concrete H2 Launch, Doctor, Drive, Evidence, Cleanup sections. Generate verify.py that actually calls [sys.executable,"app.py","count"] via subprocess, checks exit0 and stdout exactly 2\\n, and writes evidence.json with actual returncode/stdout before exit0 on pass or exit1 on failure. Do not modify app or count. Run drive. Cleanup must preserve evidence. Finish with artifact describing observed results. Fixture syntax restriction: import subprocess; import sys; import json; from pathlib import Path. First non-import statement is result = subprocess.run([sys.executable,"app.py","count"],capture_output=True,text=True). Then straight-line assignments/conditionals, Path("evidence.json").write_text(json.dumps(...)), sys.exit(...). No helpers, loops, try blocks, extra imports or other calls.',
    },
}


def execute(files, argv):
    # Host never executes candidate bytes. Only a fixed, bounded container command
    # receives them, via stdin. No host mounts, environment or network are exposed.
    program='FILES='+repr(files)+'\nARGV='+repr(argv)+'\n'+'''import json,os,pathlib,subprocess,tempfile
def solve(x):
 with tempfile.TemporaryDirectory() as d:
  for name,content in FILES.items():
   p=pathlib.Path(d)/name
   p.parent.mkdir(parents=True,exist_ok=True)
   p.write_text(content)
  r=subprocess.run(ARGV,cwd=d,capture_output=True,text=True,timeout=5)
  evidence=pathlib.Path(d)/"evidence.json"
  return {"exit_code":r.returncode,"stdout":r.stdout,"stderr":r.stderr,
          "evidence":evidence.read_text() if evidence.exists() else None}
'''
    outer=run_program(program,[None])
    if outer['exit_code']!=0 or outer['failure'] or not isinstance(outer['value'],list) or len(outer['value'])!=1:
        return {'exit_code':None,'stdout':'','stderr':'container execution incomplete',
                'evidence':None,'outer':outer}
    return outer['value'][0]


def verify(skill, files, events, artifact):
    """Independent protected checks. Producer commands/claims cannot award PASS."""
    from qualification.local_probe import observe
    runs=[e for e in events if e['action'].get('tool')=='run' and e['result'].get('decision')=='ALLOWED']
    denied=[e for e in events if e['result'].get('decision')=='DENIED']
    read=any(e['action'].get('tool')=='read' and e['result'].get('decision')=='ALLOWED' for e in events)
    reads=[e['index'] for e in events if e['action'].get('tool')=='read' and e['result'].get('decision')=='ALLOWED']
    writes=[e['index'] for e in events if e['action'].get('tool')=='write' and e['result'].get('decision')=='ALLOWED']
    read=read and (not writes or min(reads)<min(writes))
    passed=False
    checks={}
    if skill in ('figure-it-out','thermo-nuclear-code-quality-review'):
        observation=observe(skill,{'artifact':artifact,'requests':[],'notes':''})
        expected='-1\n' if skill=='figure-it-out' else 'A\n'
        checks={'artifact':observation,'actual_counterexample_observed':any(
            e['result']['execution']['exit_code']==0 and e['result']['execution']['stdout']==expected for e in runs)}
        passed=observation['artifact_oracle']=='PASS' and checks['actual_counterexample_observed']
    elif skill=='tdd':
        syntax=regression(files.get('test_clamp.py',''),'clamp','clamp','equal') and all(pure_functions(e['files'].get('clamp.py',''),['clamp'],{'min','max'}) for e in events)
        red=[e for e in runs if e['files'].get('clamp.py')==CASES[skill]['files']['clamp.py'] and
             e['result']['execution']['exit_code']==1 and 'AssertionError: 12 != 10' in e['result']['execution']['stderr']]
        green=[e for e in runs if e['result']['execution']['exit_code']==0 and 'Ran 0 tests' not in e['result']['execution']['stderr']]
        tests=files.get('test_clamp.py','')
        unchanged=bool(red and green) and all(e['files'].get('test_clamp.py')==tests for e in red+green)
        heldout=execute(files,['python3','-c','from clamp import clamp; import json; print(json.dumps([clamp(v,l,h) for v,l,h in [(12,0,10),(-9,-7,-2),(13,-7,-2),(0,0,0),(5,1,3),(2,1,3)]]))'])
        edits=[e['index'] for e in events if e['action'].get('tool')=='write' and e['action'].get('path')=='clamp.py']
        ordered=bool(red and green and edits and red[0]['index']<min(edits) and max(edits)<green[-1]['index'] and green[-1]['files']==files)
        passed=syntax and ordered and unchanged and heldout['exit_code']==0 and json_equal(heldout['stdout'],[10,-7,-2,0,3,2])
        checks={'red_before_edit_and_green':ordered,
                'supported_assertion_syntax':syntax,'regression_unchanged':unchanged,'heldout':heldout}
    elif skill=='principle-sequence-verifiable-units':
        failed=[e for e in runs if e['result']['execution']['exit_code']==1 and 'first-unit verification dependency unavailable' in e['result']['execution']['stderr']]
        import ast
        def formatter(value):
            try:return ast.dump(next(n for n in ast.parse(value).body if isinstance(n,ast.FunctionDef) and n.name=='format_result'))
            except (SyntaxError,StopIteration):return None
        original=formatter(CASES[skill]['files']['parser.py'])
        syntax=regression(files.get('test_parser.py',''),'parser','parse','raises') and all(pure_functions(e['files'].get('parser.py',''),['parse','format_result'],{'int','str','ValueError'}) for e in events)
        untouched=syntax and all(formatter(e['files'].get('parser.py',''))==original for e in events)
        after_failure=bool(failed) and all(e['action'].get('tool')!='write' for e in events if e['index']>failed[0]['index'])
        heldout=execute(files,['python3','-c','from parser import parse\ntry: parse("-1")\nexcept ValueError: print("rejected")\nelse: raise AssertionError("negative accepted")\nassert parse("8")==8'])
        passed=bool(failed) and untouched and after_failure and heldout['exit_code']==0 and artifact.get('stopped_on_failure') is True
        checks={'supported_assertion_syntax':syntax,'gate_failure_observed':bool(failed),'unit2_untouched':untouched,'no_edits_after_failure':after_failure,'unit1_heldout':heldout}
    elif skill=='create-verification-skill':
        outputs=[]
        for count,app in [('2',CASES[skill]['files']['app.py']),('not-an-integer',CASES[skill]['files']['app.py']),('2','print("PASS")\n')]:
            candidate={**files,'count.txt':count,'app.py':app}
            outputs.append(execute(candidate,['python3','verify.py']))
        evidence=[]
        import json
        for value in outputs:
            try:
                parsed=json.loads(value['evidence'])
                evidence.append(parsed if isinstance(parsed,dict) else {})
            except (ValueError,TypeError):evidence.append({})
        body=files.get('.agents/skills/verify/SKILL.md','')
        driven=any(e['files']==files and e['result']['execution']['exit_code']==0 and
                   e['result']['execution'].get('evidence')==outputs[0].get('evidence') for e in runs)
        actual=[{'returncode':e.get('returncode'),'stdout':e.get('stdout')} for e in evidence]
        expected=[{'returncode':0,'stdout':'2\n'},{'returncode':2,'stdout':''},{'returncode':0,'stdout':'PASS\n'}]
        checks={'driver_outputs':outputs,'evidence':evidence,'producer_drove_final_files':driven,
                'skill_sections':verifier_skill(body),'supported_cli_invocation':verifier_driver(files.get('verify.py',''))}
        passed=driven and [o['exit_code'] for o in outputs]==[0,1,1] and checks['skill_sections'] and checks['supported_cli_invocation'] and actual==expected
    return {'bounded_workflow':'PASS' if passed and read and not denied else 'FAIL',
            'read_observed':read,'denied_requests':len(denied),'checks':checks,
            'full_skill_qualification':'PARTIAL','execution_eligible':False,
            'scope':'One synthetic workflow in the test adapter; native harness and full dependency execution NOT_RUN'}


def json_equal(text, expected):
    import json
    try:return json.loads(text)==expected
    except (ValueError,TypeError):return False
