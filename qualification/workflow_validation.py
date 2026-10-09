"""Restricted syntax checks for fixed fixtures, not a general Python sandbox.

These reject unsupported forms before they can masquerade as trusted observations.
Candidate code still runs only in the existing offline container.
"""
import ast
import re
from myskills.catalog import frontmatter


def pure_functions(source, names, calls):
    try:tree=ast.parse(source)
    except (SyntaxError,TypeError):return False
    if len(tree.body)!=len(names) or {getattr(n,'name',None) for n in tree.body}!=set(names):return False
    for node in tree.body:
        if not isinstance(node,ast.FunctionDef) or node.decorator_list or node.returns or node.args.defaults or node.args.kw_defaults:return False
        if any(a.annotation for a in [*node.args.args,*node.args.posonlyargs,*node.args.kwonlyargs]):return False
    for node in ast.walk(tree):
        if isinstance(node,(ast.Import,ast.ImportFrom,ast.Attribute,ast.Global,ast.Nonlocal,ast.Lambda,ast.With,ast.AsyncFunctionDef,ast.ClassDef,ast.Delete,ast.Yield,ast.YieldFrom,ast.Await)):
            return False
        if isinstance(node,ast.Call) and (not isinstance(node.func,ast.Name) or node.func.id not in calls):return False
        if isinstance(node,ast.Name) and node.id.startswith('__'):return False
    return True


def literal(node):
    try:return ast.literal_eval(node)
    except (ValueError,TypeError):return None


def regression(source, module, function, mode):
    """Require real unittest assertions with literals and no reporting side effects."""
    try:tree=ast.parse(source)
    except (SyntaxError,TypeError):return False
    imports=[];classes=[]
    for node in tree.body:
        if isinstance(node,(ast.Import,ast.ImportFrom)):imports.append(node)
        elif isinstance(node,ast.ClassDef):classes.append(node)
        else:return False
    expected_imports={f'import unittest',f'from {module} import {function}'}
    if {ast.unparse(n) for n in imports}!=expected_imports or len(imports)!=2 or not classes:return False
    found=False
    class_names=set()
    for cls in classes:
        if cls.name in class_names or cls.name in (module,function,'unittest','ValueError'):return False
        class_names.add(cls.name)
        if cls.decorator_list or cls.keywords or len(cls.bases)!=1 or ast.unparse(cls.bases[0])!='unittest.TestCase':return False
        method_names=set()
        for method in cls.body:
            if not isinstance(method,ast.FunctionDef) or not method.name.startswith('test') or method.decorator_list or method.returns:return False
            if method.name in method_names:return False
            method_names.add(method.name)
            if ast.unparse(method.args)!='self':return False
            for statement in method.body:
                if mode=='equal':
                    if not isinstance(statement,ast.Expr) or not isinstance(statement.value,ast.Call):return False
                    call=statement.value
                    if ast.unparse(call.func)!='self.assertEqual' or call.keywords or len(call.args)!=2:return False
                    left,right=call.args
                    if not isinstance(left,ast.Call) or ast.unparse(left.func)!=function or left.keywords:return False
                    args=[literal(a) for a in left.args];expected=literal(right)
                    if any(type(v) not in (int,float) for v in [*args,expected]):return False
                    found=found or (args==[12,0,10] and expected==10)
                else:
                    if not isinstance(statement,ast.With) or len(statement.items)!=1 or len(statement.body)!=1:return False
                    item=statement.items[0]
                    if item.optional_vars is not None or not isinstance(item.context_expr,ast.Call):return False
                    call=item.context_expr
                    if ast.unparse(call.func)!='self.assertRaises' or call.keywords or len(call.args)!=1 or ast.unparse(call.args[0])!='ValueError':return False
                    expr=statement.body[0]
                    if not isinstance(expr,ast.Expr) or not isinstance(expr.value,ast.Call):return False
                    call=expr.value
                    if ast.unparse(call.func)!=function or call.keywords or len(call.args)!=1 or literal(call.args[0])!='-1':return False
                    found=True
    return found


def verifier_driver(source):
    """The first non-import statement must invoke the real fixture CLI.

Only the known subprocess call is trusted as invocation evidence. Subsequent data
claims must still match independent good/broken/false-banner executions.
"""
    try:tree=ast.parse(source)
    except (SyntaxError,TypeError):return False
    imports=[];body=list(tree.body)
    while body and isinstance(body[0],(ast.Import,ast.ImportFrom)):imports.append(body.pop(0))
    permitted={'import subprocess','import sys','import json','from pathlib import Path'}
    if set(ast.unparse(n) for n in imports)!=permitted or len(imports)!=4 or not body:return False
    first=body[0]
    if not isinstance(first,ast.Assign) or len(first.targets)!=1 or not isinstance(first.targets[0],ast.Name):return False
    if first.targets[0].id in ('subprocess','sys','json','Path'):return False
    call=first.value
    if not isinstance(call,ast.Call) or ast.unparse(call.func)!='subprocess.run' or len(call.args)!=1:return False
    if ast.unparse(call.args[0])!="[sys.executable, 'app.py', 'count']":return False
    options={k.arg:literal(k.value) for k in call.keywords}
    if options!={'capture_output':True,'text':True}:return False
    # CLI invocation has already occurred before any remaining producer statement.
    # Reject extra imports/rebindings that could affect independent driver checks.
    allowed=(ast.Module,ast.Assign,ast.Expr,ast.If,ast.IfExp,ast.Name,ast.Load,ast.Store,
             ast.Constant,ast.Dict,ast.List,ast.Tuple,ast.Attribute,ast.Call,ast.keyword,
             ast.Compare,ast.Eq,ast.NotEq,ast.BoolOp,ast.And,ast.Or,ast.UnaryOp,ast.Not)
    for node in ast.walk(ast.Module(body=body[1:],type_ignores=[])):
        if not isinstance(node,allowed):return False
        if isinstance(node,ast.Assign) and (len(node.targets)!=1 or not isinstance(node.targets[0],ast.Name)):return False
        if isinstance(node,ast.Name) and (node.id.startswith('__') or isinstance(node.ctx,ast.Store) and node.id in ('subprocess','sys','json','Path')):return False
        if isinstance(node,ast.Call) and ast.unparse(node.func) not in ('json.dumps','Path','sys.exit','Path(\'evidence.json\').write_text'):
            return False
    return True


def verifier_skill(source):
    try:fields=frontmatter(source)
    except (ValueError,TypeError):return False
    if fields.get('name')!='verify':return False
    parts=source.split('---\n',2)
    if len(parts)!=3:return False
    front,body=parts[1:]
    headings=re.findall(r'^## (Launch|Doctor|Drive|Evidence|Cleanup)\s*\n(.+?)(?=^## |\Z)',body,re.M|re.S)
    return {h for h,b in headings if len(b.strip())>=20}=={'Launch','Doctor','Drive','Evidence','Cleanup'}
