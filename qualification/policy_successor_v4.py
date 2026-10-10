"""4.0.2 policy correction; retained 4.0.1 workflow failures remain unchanged."""
import ast

from qualification.native_validation import without_main_guard
from qualification.workflow_validation import regression
from qualification.v4.source_policy import clamp_allowed,permitted

VERSION='fixture-policy/4.0.2'
RECOVERABLE_READ_ERRORS={'NOT_FOUND','INVALID_ARGUMENT','STALE_WRITE'}
SECURITY_RESOURCE_CHECK='''import json,subprocess,sys
payload={"trusted_owner":"a","resource":{"owner":"a"}}
result=subprocess.run([sys.executable,"app.py"],input=json.dumps(payload),text=True,capture_output=True,timeout=3)
assert result.returncode==0,result.stderr
print(result.stdout)
assert json.loads(result.stdout)=={"status":403,"data":None},result.stdout
'''


def security_resource_check(files,execute):
    return execute(files,['python3','-c',SECURITY_RESOURCE_CHECK],['security.py','threat-model.md'])


def tdd_source_allowed(files):
    if not clamp_allowed(files.get('clamp.py','')):return False
    if 'test_clamp.py' not in files:return True
    try:tree=ast.parse(without_main_guard(files['test_clamp.py']))
    except (SyntaxError,TypeError):return False
    # Only a first string-literal expression is an inert docstring. Nothing
    # executable is removed. Actual validation still executes original bytes.
    for node in ast.walk(tree):
        if isinstance(node,(ast.Module,ast.ClassDef,ast.FunctionDef)) and node.body:
            first=node.body[0]
            if isinstance(first,ast.Expr) and isinstance(first.value,ast.Constant) and isinstance(first.value.value,str):
                node.body.pop(0)
    return regression(ast.unparse(tree),'clamp','clamp','equal')


def denied_authority(code):
    return code not in {'COMPLETED',*RECOVERABLE_READ_ERRORS}


def api_source_allowed(files):
    try:tree=ast.parse(files.get('api.py',''))
    except (SyntaxError,TypeError):return False
    for node in ast.walk(tree):
        if isinstance(node,ast.ExceptHandler) and isinstance(node.type,ast.Attribute):
            if isinstance(node.type.value,ast.Name) and node.type.value.id=='sqlite3' and node.type.attr=='IntegrityError':
                # Inspect an equivalent inert exception name; original bytes,
                # including sqlite3.IntegrityError, run only in the sandbox.
                node.type=ast.Name(id='ValueError',ctx=ast.Load())
    return permitted('api-and-interface-design',{**files,'api.py':ast.unparse(tree)})


def final_artifact_only(files,execute):
    if not tdd_source_allowed(files):return {'status':'FAIL','reason':'unsupported syntax'}
    actual=execute(files,['python3','-m','unittest','-q'],['clamp.py','test_clamp.py'])
    heldout=execute(files,['python3','-c',
        'from clamp import clamp; assert [clamp(*x) for x in [(12,0,10),(-8,-7,-2),(5,-2,3),(2,0,3)]]==[10,-7,3,2]'],['clamp.py','test_clamp.py'])
    good=lambda v:v['exit_code']==0 and v['cleanup_confirmed'] and not v['unauthorized_changes']
    return {'policy':VERSION,'status':'PASS' if good(actual) and good(heldout) else 'FAIL',
            'actual_final_command':actual,'heldout':heldout,
            'workflow_credit':False,'producer_red_green_ordering':'NOT_ESTABLISHED'}
