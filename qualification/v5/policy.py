"""Narrow syntax policy; immutable adapter and offline runtime enforce effects."""
import ast
import math
from qualification.native_validation import without_main_guard
from qualification.policy_successor_v4 import api_source_allowed
from qualification.v4.source_policy import clamp_allowed, permitted

VERSION='fixture-policy/5.0.0'


def assertions(source):
    """Parse inert unittest syntax into data, never execute candidate bytes here."""
    try:tree=ast.parse(without_main_guard(source))
    except (SyntaxError,TypeError):return None
    def body(node):
        nodes=list(node.body)
        if nodes and isinstance(nodes[0],ast.Expr) and isinstance(nodes[0].value,ast.Constant) and isinstance(nodes[0].value.value,str):nodes.pop(0)
        return nodes
    nodes=body(tree);imports=[n for n in nodes if isinstance(n,(ast.Import,ast.ImportFrom))]
    classes=[n for n in nodes if isinstance(n,ast.ClassDef)]
    if len(nodes)!=len(imports)+len(classes) or len(imports)!=2 or not classes:return None
    if {ast.unparse(n) for n in imports}!={'import unittest','from clamp import clamp'}:return None
    result=[];names=set()
    for cls in classes:
        if cls.name in names or cls.name in {'clamp','unittest'} or cls.decorator_list or cls.keywords or [ast.unparse(b) for b in cls.bases]!=['unittest.TestCase']:return None
        names.add(cls.name);methods=set()
        for method in body(cls):
            if not isinstance(method,ast.FunctionDef) or not method.name.startswith('test') or method.name in methods or method.decorator_list or method.returns or ast.unparse(method.args)!='self':return None
            methods.add(method.name)
            for statement in body(method):
                if not isinstance(statement,ast.Expr) or not isinstance(statement.value,ast.Call):return None
                call=statement.value
                if ast.unparse(call.func)!='self.assertEqual' or call.keywords or len(call.args)!=2:return None
                actual,expected=call.args
                if not isinstance(actual,ast.Call) or ast.unparse(actual.func)!='clamp' or actual.keywords:return None
                try:values=[ast.literal_eval(a) for a in [*actual.args,expected]]
                except (ValueError,TypeError):return None
                if not values or any(type(v) not in (int,float) or not math.isfinite(v) or abs(v)>1000000 for v in values):return None
                result.append((values[:-1],values[-1]))
    return result if result else None


def allowed(skill,files):
    if skill=='tdd':
        return clamp_allowed(files.get('clamp.py','')) and ('test_clamp.py' not in files or assertions(files['test_clamp.py']) is not None)
    if skill=='api-and-interface-design':return api_source_allowed(files)
    return permitted(skill,files)


def executor(skill):
    from qualification.v5.execution import execute
    def run(files,argv,writable,cancel=None):
        if not allowed(skill,files):
            return {'exit_code':None,'failure':'SOURCE_POLICY','stdout':'','stderr':'Unsupported fixture syntax; no command dispatched.',
                    'cleanup_confirmed':True,'unauthorized_changes':[],'evidence':None}
        return execute(files,argv,writable,cancel)
    return run
