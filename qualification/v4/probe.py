"""Bounded native Codex trials with a pinned, unpaid local model."""
import argparse
import json
from pathlib import Path
import subprocess

from myskills.cohort_assessment import file_digest, seal
from myskills.digest import digest_object
from myskills.manifest import ValidationError
from qualification.behavior_v2 import save
from qualification.local_probe import ContainmentError
from qualification.native_probe import plan, request_for, harness as legacy_harness
from qualification.runtime_identity import MODEL, MODEL_DIGEST, PIN, RuntimeGuard
from qualification.v4.adapter import Session, VERSION, schemas
from qualification.v4.cases import CASES, COHORT, POLICY
from qualification.v4.evaluate import evaluate
from qualification.v4.native_transport import run_codex
from qualification.v4.provider import LocalResponses
from qualification.v4.source_policy import executor

IMAGE='sha256:4e19d0e9d9331129700d348fe06cc8aff0d254872aba4096c265007619c1bc60'
HARNESS='codex-app-server/0.157.0+myskills-native-4.0.0'


def harness(root):
    paths=[p for p in (root/'qualification/v4').rglob('*') if p.is_file()
           and p.suffix in ('.py','.json','.mjs') and not {'node_modules','__pycache__'}.intersection(p.parts)]
    return {**legacy_harness(root), **{str(p.relative_to(root)):file_digest(p) for p in sorted(paths)}}


def context(root):
    specs={s['binding']['skill_id']:s for s in plan(root)['skills']}
    return {'schema':'myskills.native-batch.v4','runtime':json.loads((root/PIN).read_text()),
            'harness':harness(root),'native_image':IMAGE,'model':MODEL,'model_digest':'sha256:'+MODEL_DIGEST,
            'specs':{k:specs[k] for k in COHORT},'fixtures':CASES,'adapter':VERSION,
            'catalog_trust':'UNTRUSTED','catalog_qualification':'NOT_EVALUATED','paid_operations':0}


def binding(ctx, skill, adversarial):
    return {'skill':ctx['specs'][skill]['binding'],'model':{'name':MODEL,'digest':ctx['model_digest']},
            'harness':{'version':HARNESS,'digest':digest_object(ctx['harness'])},
            'adapter':{'version':VERSION,'digest':digest_object({p:d for p,d in ctx['harness'].items() if p.startswith('qualification/v4/')})},
            'task_class':{'name':skill+('--adversarial' if adversarial else '--representative'),
                          'fixture_digest':digest_object(CASES[skill]),'schema_digest':digest_object(schemas(CASES[skill]))},
            'environment':{'runtime_digest':digest_object(ctx['runtime']),'planner_image':IMAGE,
                           'candidate_image':ctx['runtime']['environment']['image'],'network':'none','host_mounts':[]}}


def prompt(root, spec, adversarial):
    old=request_for(root,spec,adversarial,[])
    value=json.loads(old['messages'][1]['content']);skill=spec['binding']['skill_id']
    value.update(task=CASES[skill]['task'],scope=CASES[skill].get('scope',''),evaluation_version='native-adapter-v4',
                 native_runtime='Native Codex app-server uses the four myskills dynamic tools. Commands execute in the pinned offline image.')
    return json.dumps(value,sort_keys=True)


def entries(directory):
    result=[]
    for path in sorted(directory.glob('*-completed.json'),key=lambda p:int(p.name.split('-')[0])):
        value=json.loads(path.read_text())
        result.append({'request':value['request'],'result':value['result'],'files':value['files']})
    return result


def collect(root, output):
    output.mkdir(parents=True,exist_ok=False)
    ctx=context(root);save(output/'context.json',ctx)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    guard=RuntimeGuard(ctx['runtime']);halt=None
    for skill in COHORT:
        for adversarial in (False,True):
            identity=binding(ctx,skill,adversarial);name=identity['task_class']['name']
            directory=output/name;directory.mkdir()
            record={'binding':identity,'collector_commit':commit,'execution_eligible':False,'generation':'NOT_RUN'}
            session=Session(name,CASES[skill],executor(skill),directory/'journal',identity)
            if halt is None:
                try:
                    guard.check()
                    if context(root)!=ctx:raise ValidationError('collector identity changed')
                    text=prompt(root,ctx['specs'][skill],adversarial)
                    save(directory/'prompt.json',{'policy':POLICY,'prompt':text})
                    record['generation']='DISPATCHED';save(directory/'observation.json',record)
                    transport=run_codex(IMAGE,MODEL,POLICY,text,session,LocalResponses(guard),journal=directory/'native.jsonl')
                    save(directory/'transport.json',transport)
                    record['native_turns']=[r['value']['params']['turn']['status'] for r in transport['records']
                                            if r['channel']=='event' and r['value'].get('method')=='turn/completed']
                    if transport['failure'] or transport['exit_code']!=0 or record['native_turns']!=['completed']:
                        raise ValidationError('native workflow interrupted or rejected; outcome INCONCLUSIVE')
                    record['generation']='COMPLETED'
                    record['verification']=evaluate(skill,session.files,entries(directory/'journal'),session.artifact,session.finished)
                    provider_status=[r['value']['status'] for r in transport['records']
                                     if r['channel']=='host_response' and 'status' in r['value']]
                    if any(s!=200 for s in provider_status):
                        halt='Native provider protocol rejected; repeating this configuration is not justified'
                    guard.check();record['trial_identity']='PRE_POST_CHECKED'
                except Exception as error:
                    halt=type(error).__name__+': '+str(error)
                    record['error']=halt
                    if record['generation']=='DISPATCHED':record['generation']='UNKNOWN'
                    record['verification']={'bounded_workflow':'NOT_RUN','interruption':'INCONCLUSIVE'}
            else:record['error']='batch halted: '+halt
            record.update(files=session.files,artifact=session.artifact,finished=session.finished,entries=entries(directory/'journal'))
            save(directory/'observation.json',seal(record))
            print(json.dumps({'case':name,'events':len(session.events),'generation':record['generation'],
                              'workflow':record.get('verification',{}).get('bounded_workflow','NOT_RUN'),'error':record.get('error')}),flush=True)
    completion={'runtime_identity':'UNSTABLE','halt':halt,'all_results_admissible':False}
    try:
        guard.finish()
        if context(root)!=ctx:raise ValidationError('collector identity changed')
        completion.update(runtime_identity='STABLE',all_results_admissible=halt is None)
    except Exception as error:completion['error']=str(error)
    save(output/'completion.json',seal(completion))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    collect(Path.cwd(),args.output)
