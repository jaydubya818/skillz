"""Versioned local artifact experiment; full Skill workflow eligibility stays closed."""
import argparse
from copy import deepcopy
import json
from pathlib import Path

from myskills.catalog import build_catalog
from myskills.cohort_assessment import _plan, file_digest, seal
from myskills.digest import digest_object
from myskills.manifest import ValidationError
from qualification import local_probe as legacy
from qualification.runtime_identity import MODEL, PIN, RuntimeGuard, bind_result

KINDS=('representative','adversarial','repeat')


def request_for(root, plan, spec, kind):
    request=legacy.make_request(root,plan,spec,kind=='adversarial')
    request['model']=MODEL
    user=json.loads(request['messages'][1]['content'])
    skill=spec['binding']['skill_id']
    # A new, explicit fixture version repairs ambiguous encoding, not prior verdicts.
    if skill=='figure-it-out':
        user['adapter_contract']+=' Encode counterexample.expected as the exact JSON string "reject".'
    if skill=='principle-sequence-verifiable-units':
        user['adapter_contract']+=' When all units are complete return {"next_unit":null,"stop":true}.'
    if skill=='api-and-interface-design':
        user['fixture']['requests']=[{'trusted_owner':r['owner'],'key':r['key'],'text':r['text']}
                                     for r in user['fixture']['requests']]
    user['evaluation_version']='artifact-v2; earlier responses and verdicts are immutable'
    request['messages'][1]['content']=json.dumps(user,sort_keys=True)
    # The generic v1 object shape allowed misspelled program keys. Make the
    # documented artifact shape machine-readable without changing the oracles.
    shape=deepcopy(legacy.SHAPE)
    artifact={'type':'object'}
    if 'cases' in legacy.PROBES[skill]:
        artifact.update(properties={'program':{'type':'string'}},required=['program'])
        if skill=='tdd':
            artifact['properties']['regression']={'type':'object'}
            artifact['required'].append('regression')
    shape['properties']['artifact']=artifact
    request['format']=shape
    return request


def source_identity(root):
    paths=[root/'qualification'/name for name in
           ('runtime_identity.py','behavior_v2.py','local_probe.py','probe_cases.py')]
    paths+=sorted((root/'myskills').glob('*.py'))
    return {str(path.relative_to(root)):file_digest(path) for path in paths}


def context(root, plan, runtime):
    return {'schema':'myskills.artifact-experiment.v2','runtime':runtime,
        'harness':source_identity(root),'plan_digest':digest_object(plan),
        'evaluation':{'version':'artifact-v2','oracle_digest':file_digest(root/'qualification/local_probe.py'),
                      'corpus_digest':digest_object(legacy.PROBES)},
        'scope':'Artifact generation and offline verification; tool workflows and dependency execution NOT_RUN',
        'catalog_trust':'UNTRUSTED','catalog_qualification':'NOT_EVALUATED','execution_eligible':False}


def save(path, value):
    path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')


def collect(root, output):
    plan=_plan(root,{m['skill_id']:m for m in build_catalog(root)['skills']})
    runtime=json.loads((root/PIN).read_text())
    output.mkdir(parents=True,exist_ok=False)
    ctx=context(root,plan,runtime)
    save(output/'context.json',ctx)
    guard=RuntimeGuard(runtime)
    halt=None
    for spec in plan['skills']:
        for kind in KINDS:
            name=spec['binding']['skill_id']+'--'+kind
            destination=output/name
            destination.mkdir()
            request=request_for(root,plan,spec,kind)
            save(destination/'request.json',request)
            record={'binding':spec['binding'],'kind':kind,'generation':'NOT_RUN','verification':'NOT_RUN',
                    'identity':'NOT_VERIFIED','execution_eligible':False}
            save(destination/'observation.json',record)
            if halt:
                record['error']='run halted: '+halt
            else:
                try:
                    record['generation']='DISPATCHED'
                    save(destination/'observation.json',record)
                    response,loaded=guard.generate(request,lambda r:save(destination/'response.json',r))
                    record['generation']='COMPLETED'
                    record['loaded_model']=loaded
                    record['identity']='PRE_POST_CHECKED_BATCH_HASH_PENDING'
                    record['result_identity']=bind_result(runtime=runtime,harness=ctx['harness'],
                        skill=spec['binding'],fixture=request,evaluation=ctx['evaluation'],output=response)
                    candidate=legacy.parse_candidate(response)
                    record['observations']=legacy.observe(spec['binding']['skill_id'],candidate)
                    record['verification']='COMPLETED'
                    record['result_identity']=bind_result(runtime=runtime,harness=ctx['harness'],
                        skill=spec['binding'],fixture=request,evaluation=ctx['evaluation'],output=response)
                except legacy.ContainmentError as error:
                    halt=str(error);record['error']=halt
                except (OSError,ValueError,KeyError,TypeError) as error:
                    record['error']=str(error)
                    if record['generation']=='DISPATCHED':
                        record['generation']='UNKNOWN';halt='request identity or completion unconfirmed: '+str(error)
                    else:
                        record['verification']='FAIL'
            save(destination/'observation.json',seal(record))
            print(json.dumps({'attempt':name,'generation':record['generation'],
                'oracle':record.get('observations',{}).get('artifact_oracle','NOT_RUN')}),flush=True)
    completion={'runtime_identity':'UNSTABLE','all_results_admissible':False,'error':halt}
    if not halt:
        try:
            guard.finish()
            require_context=context(root,plan,runtime)
            if require_context!=ctx:
                raise ValidationError('harness or fixture changed during experiment')
            completion={'runtime_identity':'STABLE','all_results_admissible':True,
                        'runtime_digest':digest_object(runtime),'full_blob_hashes_before_after':'PASS'}
        except (OSError,ValueError,KeyError,TypeError) as error:
            completion['error']=str(error)
    save(output/'completion.json',seal(completion))


def replay(root, directory, collector_commit=None):
    """Caller must authenticate the whole bundle against the committed custody pin."""
    plan=_plan(root,{m['skill_id']:m for m in build_catalog(root)['skills']})
    runtime=json.loads((root/PIN).read_text())
    ctx=json.loads((directory/'context.json').read_text())
    expected_context=context(root,plan,runtime)
    if collector_commit is not None:
        import re
        import subprocess
        from hashlib import sha256
        if not re.fullmatch(r'[0-9a-f]{40}',collector_commit):raise ValidationError('collector must be an exact commit')
        for path in expected_context['harness']:
            source=subprocess.run(['git','show',collector_commit+':'+path],cwd=root,capture_output=True,check=True,timeout=15)
            expected_context['harness'][path]='sha256:'+sha256(source.stdout).hexdigest()
    if expected_context!=ctx:
        raise ValidationError('runtime, harness or evaluator differs from retained experiment')
    completion=json.loads((directory/'completion.json').read_text())
    if completion.get('all_results_admissible') is not True or completion.get('runtime_identity')!='STABLE':
        raise ValidationError('unstable experiment cannot establish behavioral evidence')
    results=[]
    for spec in plan['skills']:
        attempts=[]
        for kind in KINDS:
            name=spec['binding']['skill_id']+'--'+kind
            d=directory/name
            request=json.loads((d/'request.json').read_text())
            if request!=request_for(root,plan,spec,kind):
                raise ValidationError('request fixture or Skill identity changed')
            record=json.loads((d/'observation.json').read_text())
            if seal({k:v for k,v in record.items() if k!='evidence_digest'})!=record:
                raise ValidationError('observation seal changed')
            if record['binding']!=spec['binding'] or record['execution_eligible'] is not False:
                raise ValidationError('observation binding or authority changed')
            response=json.loads((d/'response.json').read_text())
            expected=bind_result(runtime=runtime,harness=ctx['harness'],skill=spec['binding'],
                fixture=request,evaluation=ctx['evaluation'],output=response)
            if record['verification']=='COMPLETED':
                if record['result_identity']!=expected:
                    raise ValidationError('result identity changed')
                observed=legacy.observe(spec['binding']['skill_id'],legacy.parse_candidate(response))
                if observed!=record['observations']:
                    raise ValidationError('independent artifact replay changed')
            else:
                # Invalid producer format is a retained failure, not an omitted run.
                try:
                    legacy.parse_candidate(response)
                except (ValueError,KeyError,TypeError):
                    pass
                else:
                    raise ValidationError('unexplained artifact verification failure')
            attempts.append({'kind':kind,'output_digest':digest_object(response['message']['content']),
                'artifact_oracle':record.get('observations',{}).get('artifact_oracle','FAIL'),
                'effect_request_check':record.get('observations',{}).get('effect_request_check','NOT_RUN'),
                'evidence_digest':record['evidence_digest']})
        same=attempts[0]['output_digest']==attempts[2]['output_digest']
        results.append({'binding':spec['binding'],'attempts':attempts,'repeat_output_equal':same,
            'behavioral_status':'PARTIAL','trust':'UNTRUSTED','execution_eligible':False,
            'full_workflow':'NOT_RUN','scope':legacy.PROBES[spec['binding']['skill_id']]['scope']})
    return results


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--collect',required=True,type=Path)
    args=parser.parse_args()
    collect(Path(__file__).resolve().parents[1],args.collect)
