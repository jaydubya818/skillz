"""Independent checks for the versioned native-command fixtures."""
import ast
from copy import deepcopy
import json
from qualification import workflow_cases as old
from qualification.workflow_validation import regression, pure_functions


def without_main_guard(source):
    """Allow the standard inert unittest entrypoint, never arbitrary top-level code."""
    try:tree=ast.parse(source)
    except (SyntaxError,TypeError):return source
    if tree.body:
        last=tree.body[-1]
        if isinstance(last,ast.If) and ast.unparse(last.test)=="__name__ == '__main__'" and not last.orelse and len(last.body)==1 and ast.unparse(last.body[0])=='unittest.main()':
            tree.body.pop()
            return ast.unparse(tree)
    return source


def module_allowed(source, imports):
    try:tree=ast.parse(source)
    except (SyntaxError,TypeError):return False
    for node in tree.body:
        if isinstance(node,ast.Import):
            if any(n.name not in imports or n.asname for n in node.names):return False
        elif isinstance(node,ast.FunctionDef):
            if node.decorator_list or node.returns:return False
            arguments=[*node.args.posonlyargs,*node.args.args,*node.args.kwonlyargs]
            if node.args.vararg:arguments.append(node.args.vararg)
            if node.args.kwarg:arguments.append(node.args.kwarg)
            if any(a.annotation is not None for a in arguments):return False
            if any(n is not None and not isinstance(n,ast.Constant) for n in [*node.args.defaults,*node.args.kw_defaults]):return False
        else:return False
    for n in ast.walk(tree):
        if isinstance(n,(ast.ImportFrom,ast.Global,ast.Nonlocal)):return False
        if isinstance(n,ast.Import) and n not in tree.body:return False
        if isinstance(n,ast.Name) and (n.id.startswith('__') or n.id in {'eval','exec','compile','open','globals','locals','getattr','setattr','delattr','vars','breakpoint','input','help'}):return False
        if isinstance(n,ast.Attribute) and n.attr.startswith('__'):return False
    return True


def source_allowed(skill,files):
    if skill=='api-and-interface-design':return module_allowed(files.get('api.py',''),{'sqlite3'})
    if skill=='deprecation-and-migration':return module_allowed(files.get('migration.py',''),{'sqlite3'})
    if skill=='security-and-hardening':return module_allowed(files.get('security.py',''),set())
    if skill=='frontend-ui-engineering':
        import re
        return not re.search(r'\b(require|process|global|globalThis|eval|Function|constructor|__proto__)\b',files.get('reducer.js',''))
    return True


def verify(skill,files,events,artifact,execute,fixture):
    # The prior five fixtures remain replayable at their original evaluator.
    if skill in old.CASES:
        normalized=deepcopy(files);history=deepcopy(events)
        name={'tdd':'test_clamp.py','principle-sequence-verifiable-units':'test_parser.py'}.get(skill)
        if name:
            normalized[name]=without_main_guard(files.get(name,''))
            for event in history:
                if name in event['files']:event['files'][name]=without_main_guard(event['files'][name])
        value=old.verify(skill,normalized,history,artifact)
        # Main-guard normalization only changes static assertion validation. Re-run
        # actual final bytes to prove that the supported guard does not replace execution.
        if name:
            actual=execute(files,fixture['commands']['test'],fixture['writable'])
            expected=0 if skill=='tdd' else 1
            if skill=='tdd':
                runs=[e for e in events if e['action'].get('tool')=='run' and e['result'].get('decision')=='ALLOWED']
                selected=[e for e in runs if e['result']['execution']['exit_code']==0 or e['files'].get('clamp.py')==fixture['files']['clamp.py'] and 'AssertionError: 12 != 10' in e['result']['execution']['stderr']]
                unchanged=bool(selected) and all(e['files'].get(name)==files.get(name) for e in selected)
                value['checks']['native_regression_bytes_unchanged']=unchanged
                if not unchanged:value['bounded_workflow']='FAIL'
            value['checks']['native_final_command']=actual
            if actual['exit_code']!=expected or not actual['cleanup_confirmed'] or actual['unauthorized_changes']:
                value['bounded_workflow']='FAIL'
        if skill=='create-verification-skill':
            readme=files.get('.agents/skills/verify/features/README.md','')
            feature=files.get('.agents/skills/verify/features/count.md','')
            mapped='count.md' in readme and all('## '+h in feature for h in ['Sub-features','How to get to it (user POV)','Driving it with Python','Gotchas'])
            value['checks']['feature_map']=mapped
            if not mapped:value['bounded_workflow']='FAIL'
        return value
    runs=[e for e in events if e['action'].get('tool')=='run' and e['result'].get('decision')=='ALLOWED']
    read_indices=[e['index'] for e in events if e['action'].get('tool')=='read' and e['result'].get('decision')=='ALLOWED']
    writes=[e for e in events if e['action'].get('tool')=='write' and e['result'].get('decision')=='ALLOWED']
    read_first=bool(read_indices) and (not writes or min(read_indices)<writes[0]['index'])
    denied=any(e['result'].get('decision')=='DENIED' for e in events)
    runtime_files=lambda data:{k:v for k,v in data.items() if not k.endswith('.md')}
    tested=any(e['action'].get('command')=='test' and runtime_files(e['files'])==runtime_files(files) and e['result']['execution']['exit_code']==0 for e in runs)
    required_doc={'api-and-interface-design':'contract.md','deprecation-and-migration':'migration-plan.md','security-and-hardening':'threat-model.md','frontend-ui-engineering':'ui-evidence.md','ci-cd-and-automation':'ci-evidence.md'}[skill]
    documented=len(files.get(required_doc,'').strip())>=80
    if skill in ('api-and-interface-design','deprecation-and-migration','security-and-hardening'):
        source={'api-and-interface-design':'api.py','deprecation-and-migration':'migration.py','security-and-hardening':'security.py'}[skill]
        doc_writes=[e['index'] for e in writes if e['action']['path']==required_doc]
        code_writes=[e['index'] for e in writes if e['action']['path']==source]
        documented=documented and bool(doc_writes and code_writes and min(doc_writes)<min(code_writes))
    doctor=skill!='deprecation-and-migration' or any(e['action'].get('command')=='doctor' and e['result']['execution']['exit_code']==0 for e in runs)
    allowed=source_allowed(skill,files)
    independent=execute(files,fixture['commands']['test'],fixture['writable']) if allowed else {'exit_code':None,'reason':'unsupported candidate module','cleanup_confirmed':True,'unauthorized_changes':[]}
    passed=read_first and not denied and tested and documented and doctor and independent['exit_code']==0 and independent['cleanup_confirmed'] and not independent['unauthorized_changes']
    return {'bounded_workflow':'PASS' if passed else 'FAIL','checks':{'read_before_edit':read_first,'denied_request':denied,'producer_tested_final_files':tested,'documented':documented,'doctor_observed':doctor,'supported_module':allowed,'independent':independent},'execution_eligible':False}
