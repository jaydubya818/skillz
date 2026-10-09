"""Independent, deliberately narrow oracles. Full workflow gates remain NOT_RUN."""

PROBES = {
    'figure-it-out': {
        'contract': 'Return artifact with change_paths (list), phases (ordered read, baseline, regression, fix, verify), and counterexample {path,input,expected}. Plan the parser correction; do not claim execution.',
        'scope': 'Planning artifact and concrete counterexample only; repository work and native tool workflow NOT_RUN.',
    },
    'principle-sequence-verifiable-units': {
        'contract': 'Return artifact.program: Python def solve(x), choosing the next unit from x.units, x.completed and x.last_exit. Return {next_unit: string or null, stop: bool}. A failed last verification must stop. No verification has occurred if last_exit is null. Completed units are a prefix. This probes the scheduling decision only.',
        'scope': 'Generated scheduling predicate only; real per-unit edits, commits and check ordering NOT_RUN.',
        'cases': [
            ({'units': ['a', 'b'], 'completed': ['a'], 'last_exit': 1}, {'next_unit': None, 'stop': True}),
            ({'units': ['a', 'b'], 'completed': ['a'], 'last_exit': 0}, {'next_unit': 'b', 'stop': False}),
            ({'units': ['a', 'b'], 'completed': [], 'last_exit': None}, {'next_unit': 'a', 'stop': False}),
            ({'units': ['a', 'b'], 'completed': ['a','b'], 'last_exit': 0}, {'next_unit': None, 'stop': True}),
        ],
    },
    'tdd': {
        'contract': 'Return artifact.program: Python def solve(x) taking {value,low,high} and returning the corrected clamp result. Also artifact.regression: {input:{value,low,high}, expected:number}. Supply a counterexample to the immutable broken baseline max(low,value). Do not claim that a test ran before the fix; the controller checks both after your output.',
        'scope': 'Generated regression red/green and held-out clamp boundaries; model red-before-edit ordering NOT_RUN.',
        'cases': [({'value':v,'low':lo,'high':hi}, min(hi,max(lo,v))) for v,lo,hi in [(12,0,10),(-1,0,10),(4,0,10),(13,-7,-2),(-9,-7,-2),(0,0,0)]],
    },
    'thermo-nuclear-code-quality-review': {
        'contract': 'Return artifact.findings, a list of {path,line,input,observed,expected}. Review the supplied mode.py. Use a concrete string input, actual output string and expected="reject". Do not edit or invent test runs.',
        'scope': 'Seeded review finding and independently executed counterexample only; broad quality review NOT_RUN.',
    },
    'api-and-interface-design': {
        'contract': 'Return artifact.program: Python def solve(x) implementing an in-memory contract kernel over x.requests. Each request has trusted_owner, key, text and may have untrusted body_owner. Ignore body_owner. Deduplicate by trusted_owner plus key and exact text. Return {responses:[{status:201|200|409,text:string|null}], effects:{owner:count}}. First create=201; identical replay=200; changed payload=409 and null text. Effects count actual distinct creations per owner. This is a kernel, not a real endpoint or concurrency proof.',
        'scope': 'Owner-scoped replay/conflict kernel only; durable endpoint, concurrency and lost-response recovery NOT_RUN.',
        'cases': [({'requests':[
            {'trusted_owner':'a','key':'k','text':'one'},
            {'trusted_owner':'a','key':'k','text':'one'},
            {'trusted_owner':'a','key':'k','text':'changed'},
            {'trusted_owner':'b','key':'k','text':'two','body_owner':'a'}]},
            {'responses':[{'status':201,'text':'one'},{'status':200,'text':'one'},{'status':409,'text':None},{'status':201,'text':'two'}],'effects':{'a':1,'b':1}}),
            ({'requests':[]}, {'responses':[],'effects':{}})],
    },
    'deprecation-and-migration': {
        'contract': 'Return artifact.program: Python def solve(x) for a compare-and-set backfill step. x.row has old,new,version. x.snapshot_version and x.snapshot_old are captured earlier. Return a copied row: fill new from snapshot_old only if current version equals snapshot_version and new is null. Otherwise preserve the whole row. Keep old readable. This is a data transformation predicate, not database or recovery proof.',
        'scope': 'Stale-version and idempotent transformation predicate only; disposable database, interruption and recovery NOT_RUN.',
        'cases': [({'row':{'old':'latest','new':None,'version':2},'snapshot_version':1,'snapshot_old':'before'}, {'old':'latest','new':None,'version':2}),
            ({'row':{'old':'latest','new':None,'version':2},'snapshot_version':2,'snapshot_old':'latest'}, {'old':'latest','new':'latest','version':2}),
            ({'row':{'old':'latest','new':'newer','version':2},'snapshot_version':2,'snapshot_old':'latest'}, {'old':'latest','new':'newer','version':2})],
    },
    'frontend-ui-engineering': {
        'contract': 'Return artifact.program: Python def solve(x) as a pure state transition for note editing. State={owner,request,text,status}, event={type,owner,request,text?}. submit on a non-pending state sets pending and request; duplicate submit while pending does nothing. success/failure only applies when owner and request match and state.status=pending. success sets status=success and replaces text; failure sets status=request-failure and preserves text. Every unmatched event leaves state unchanged. This probes the reducer, not a browser or accessibility.',
        'scope': 'Pending, failure and stale-response reducer only; UI, keyboard, layout and accessibility NOT_RUN.',
        'cases': [({'state':{'owner':'a','request':2,'text':'draft','status':'pending'},'event':{'type':'success','owner':'b','request':2,'text':'foreign'}}, {'owner':'a','request':2,'text':'draft','status':'pending'}),
            ({'state':{'owner':'a','request':2,'text':'draft','status':'pending'},'event':{'type':'success','owner':'a','request':1,'text':'stale'}}, {'owner':'a','request':2,'text':'draft','status':'pending'}),
            ({'state':{'owner':'a','request':2,'text':'draft','status':'pending'},'event':{'type':'failure','owner':'a','request':2}}, {'owner':'a','request':2,'text':'draft','status':'request-failure'}),
            ({'state':{'owner':'a','request':2,'text':'draft','status':'pending'},'event':{'type':'submit','owner':'a','request':3}}, {'owner':'a','request':2,'text':'draft','status':'pending'}),
            ({'state':{'owner':'a','request':2,'text':'draft','status':'pending'},'event':{'type':'success','owner':'a','request':2,'text':'saved'}}, {'owner':'a','request':2,'text':'saved','status':'success'})],
    },
    'security-and-hardening': {
        'contract': 'Return artifact.program: Python def solve(x) for an owner-scoped resource read. x.trusted_owner is authenticated; x.body_owner is untrusted. x.resource={owner,data}. Return {status:200,data:resource.data} only for matching trusted owner; otherwise {status:403,data:null}. Any x.destination request is disallowed and must return {status:403,data:null} without fetching. Use no network, files or credentials.',
        'scope': 'Owner authorization and destination-denial function only; application-wide security and OS syscall tracing NOT_RUN.',
        'cases': [({'trusted_owner':'a','body_owner':'b','resource':{'owner':'b','data':'PRIVATE_B'}}, {'status':403,'data':None}),
            ({'trusted_owner':'a','resource':{'owner':'a','data':'own'}}, {'status':200,'data':'own'}),
            ({'trusted_owner':'a','resource':{'owner':'a','data':'own'},'destination':'http://127.0.0.1/private'}, {'status':403,'data':None})],
    },
    'ci-cd-and-automation': {
        'contract': 'Return artifact.pipeline with event="pull_request", permissions={contents:"read"}, commands=["python -m pytest tests -q"], continue_on_error=false, publish=false, credentials=[], shell_interpolation=[] for the supplied Python fixture. This is an abstract validation job, not an installed GitHub workflow.',
        'scope': 'Validation configuration contract only; generated hosted workflow and actual CI failure propagation NOT_RUN.',
    },
    'create-verification-skill': {
        'contract': 'Return artifact.program: Python def solve(x) evaluating a count CLI observation {exit_code,stdout}. Return {passed:bool} only when exit_code is 0 and stdout is exactly "2\\n". A PASS banner, malformed value or a nonzero exit must fail. This probes the generated assertion, not a generated driver executing the CLI.',
        'scope': 'Generated verification predicate only; tailored Skill creation, CLI driving and evidence cleanup NOT_RUN.',
        'cases': [({'exit_code':0,'stdout':'2\n'}, {'passed':True}), ({'exit_code':0,'stdout':'PASS\n'}, {'passed':False}), ({'exit_code':2,'stdout':'2\n'}, {'passed':False}), ({'exit_code':1,'stdout':'not-an-integer\n'}, {'passed':False})],
    },
}
