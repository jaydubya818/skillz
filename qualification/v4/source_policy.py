"""Restricted fixture syntax before dispatch. Container policy remains mandatory."""
import ast
from qualification.native_validation import module_allowed,without_main_guard
from qualification.workflow_validation import pure_functions,regression
from qualification.v4.execution import execute


def permitted(skill,files):
    if skill=='tdd':
        return clamp_allowed(files.get('clamp.py','')) and (
            'test_clamp.py' not in files or regression(without_main_guard(files['test_clamp.py']),'clamp','clamp','equal'))
    path='api.py' if skill=='api-and-interface-design' else 'security.py'
    source=files.get(path,'')
    if not module_allowed(source,{'sqlite3'} if skill=='api-and-interface-design' else set()):return False
    attributes={'connect','execute','executemany','fetchone','fetchall','cursor','commit','rollback','close','get','keys','items','values','in_transaction','rowcount'}
    tree=ast.parse(source)
    functions={n.name for n in tree.body if isinstance(n,ast.FunctionDef)}
    calls=functions|{'isinstance','str','dict','bool','len','list','tuple','set','int','float','RuntimeError','ValueError','Exception'}
    for n in ast.walk(tree):
        if isinstance(n,ast.Attribute) and n.attr not in attributes:return False
        if isinstance(n,ast.Call) and (not isinstance(n.func,(ast.Name,ast.Attribute)) or isinstance(n.func,ast.Name) and n.func.id not in calls):return False
    return True


def clamp_allowed(source):
    # A call-name allowlist alone is unsafe: `max = eval; max(...)` rebinds it.
    # This fixture admits only pure expressions over its three data parameters.
    try: tree=ast.parse(source)
    except (SyntaxError,TypeError): return False
    if len(tree.body)!=1 or not isinstance(tree.body[0],ast.FunctionDef):return False
    function=tree.body[0]
    if function.name!='clamp' or function.decorator_list or function.returns:return False
    args=function.args
    if args.posonlyargs or args.kwonlyargs or args.defaults or args.vararg or args.kwarg:return False
    if [a.arg for a in args.args]!=['value','low','high'] or any(a.annotation for a in args.args):return False
    allowed=(ast.Module,ast.FunctionDef,ast.arguments,ast.arg,ast.Return,ast.If,ast.IfExp,
             ast.Expr,ast.Constant,ast.Name,ast.Load,ast.Call,ast.Compare,ast.BoolOp,ast.UnaryOp,
             ast.BinOp,ast.And,ast.Or,ast.Not,ast.USub,ast.UAdd,ast.Add,ast.Sub,ast.Mult,
             ast.Lt,ast.LtE,ast.Gt,ast.GtE,ast.Eq,ast.NotEq)
    for node in ast.walk(tree):
        if not isinstance(node,allowed):return False
        if isinstance(node,ast.FunctionDef) and node is not function:return False
        if isinstance(node,ast.Name) and node.id not in {'value','low','high','min','max'}:return False
        if isinstance(node,ast.Call) and (not isinstance(node.func,ast.Name) or node.func.id not in {'min','max'} or node.keywords):return False
        if isinstance(node,ast.Constant) and type(node.value) not in (int,float,str,bool,type(None)):return False
    return True


def executor(skill):
    def run(files,argv,writable,cancel=None):
        if not permitted(skill,files):
            return {'exit_code':None,'failure':'SOURCE_POLICY','stdout':'','stderr':'Unsupported fixture syntax; no command dispatched.',
                    'cleanup_confirmed':True,'unauthorized_changes':[],'evidence':None}
        return execute(files,argv,writable,cancel)
    return run
