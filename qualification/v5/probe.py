"""Unpaid pinned native Codex execution of exact checkpoint-5 fixtures."""
import argparse
import json
from pathlib import Path
import subprocess
from myskills.cohort_assessment import file_digest,seal
from myskills.digest import digest_object
from myskills.manifest import ValidationError
from qualification.behavior_v2 import save
from qualification.native_probe import request_for
from qualification.runtime_identity import MODEL,RuntimeGuard
from qualification.v4.adapter import Session,VERSION,schemas
from qualification.v4.probe import IMAGE,context as previous_context,entries
from qualification.v4.native_transport import run_codex
from qualification.v4.provider import LocalResponses
from qualification.v5.cases import CASES,TDD_CASES,POLICY
from qualification.v5.policy import executor,VERSION as POLICY_VERSION
from qualification.v5.evaluate import evaluate,VERSION as EVALUATOR
from qualification.v5.replay import native_complete

HARNESS='codex-app-server/0.157.0+myskills-native-5.0.0'


def context(root):
    old=previous_context(root)
    paths=[p for p in (root/'qualification/v5').glob('*.py')]
    paths += [root/p for p in ('qualification/checkpoint5/profile-policy.json',
              'qualification/policy_successor_v4.py','qualification/checkpoint_four.py',
              'qualification/custody_v4.py','qualification/native_controls.py')]
    return {**old,'schema':'myskills.native-batch.v5','fixtures':CASES,
            'harness':{**old['harness'],**{str(p.relative_to(root)):file_digest(p) for p in sorted(paths)}},
            'evaluator':EVALUATOR,'policy':POLICY_VERSION}


def binding(ctx,name):
    fixture=CASES[name];skill=fixture['skill']
    return {'skill':ctx['specs'][skill]['binding'],'model':{'name':MODEL,'digest':ctx['model_digest']},
            'harness':{'version':HARNESS,'digest':digest_object(ctx['harness'])},
            'adapter':{'version':VERSION,'digest':digest_object({p:d for p,d in ctx['harness'].items() if p.startswith('qualification/v4/')})},
            'task_class':{'name':name,'fixture_digest':digest_object(fixture),'schema_digest':digest_object(schemas(fixture))},
            'environment':{'runtime_digest':digest_object(ctx['runtime']),'planner_image':IMAGE,'candidate_image':ctx['runtime']['environment']['image'],'network':'none','host_mounts':[]},
            'evaluator':{'version':EVALUATOR,'digest':ctx['harness']['qualification/v5/evaluate.py'],'policy_version':POLICY_VERSION,'policy_digest':ctx['harness']['qualification/v5/policy.py']}}


def prompt(root,ctx,name):
    fixture=CASES[name];spec=ctx['specs'][fixture['skill']]
    value=json.loads(request_for(root,spec,False,[])['messages'][1]['content'])
    value.update(task=fixture['task'],scope=fixture['scope'],files=list(fixture['files']),writable=fixture['writable'],commands=list(fixture['commands']),
                 evaluation_version=EVALUATOR,native_runtime=HARNESS)
    return json.dumps(value,sort_keys=True)


def collect(root,output,names):
    output.mkdir(parents=True,exist_ok=False);ctx=context(root);save(output/'context.json',ctx)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    guard=RuntimeGuard(ctx['runtime']);halt=None
    for name in names:
        identity=binding(ctx,name);fixture=CASES[name];directory=output/name;directory.mkdir()
        record={'binding':identity,'collector_commit':commit,'execution_eligible':False,'generation':'NOT_RUN'}
        session=Session(name,fixture,executor(fixture['skill']),directory/'journal',identity)
        if halt is None:
            try:
                guard.check()
                if context(root)!=ctx:raise ValidationError('collector identity changed')
                text=prompt(root,ctx,name);save(directory/'prompt.json',{'policy':POLICY,'prompt':text})
                record['generation']='DISPATCHED';save(directory/'observation.json',record)
                transport=run_codex(IMAGE,MODEL,POLICY,text,session,LocalResponses(guard),journal=directory/'native.jsonl')
                save(directory/'transport.json',transport)
                turns=[r['value']['params']['turn']['status'] for r in transport['records'] if r['channel']=='event' and r['value'].get('method')=='turn/completed']
                if transport['failure'] or transport['exit_code']!=0 or turns!=['completed']:raise ValidationError('native workflow interrupted; no credit')
                record['entries']=entries(directory/'journal')
                if not native_complete(directory,record,fixture):raise ValidationError('native provider, tool custody or cleanup incomplete; no credit')
                guard.check();record['trial_identity']='PRE_POST_CHECKED';record['generation']='COMPLETED'
                record['verification']=evaluate(fixture,session.files,entries(directory/'journal'),session.artifact,session.finished)
            except Exception as error:
                halt=type(error).__name__+': '+str(error);record['error']=halt
                if record['generation']=='DISPATCHED':record['generation']='UNKNOWN'
        else:record['error']='batch halted: '+halt
        record.update(files=session.files,artifact=session.artifact,finished=session.finished,entries=entries(directory/'journal'))
        save(directory/'observation.json',seal(record))
        print(json.dumps({'case':name,'generation':record['generation'],'events':len(session.events),'verification':record.get('verification',{}).get('status'),'error':record.get('error')}),flush=True)
    completion={'runtime_identity':'UNSTABLE','halt':halt,'all_results_admissible':False,'cases':names}
    try:
        guard.finish()
        if context(root)!=ctx:raise ValidationError('collector identity changed')
        completion.update(runtime_identity='STABLE',all_results_admissible=halt is None)
    except Exception as error:completion['error']=str(error)
    save(output/'completion.json',seal(completion))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--case',choices=list(CASES),action='append')
    args=parser.parse_args();collect(Path.cwd(),args.output,args.case or list(TDD_CASES))
