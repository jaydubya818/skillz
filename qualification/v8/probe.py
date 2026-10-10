"""Bounded unpaid native Codex collection with frozen adapter and local model."""
import argparse
import json
from pathlib import Path
from typing import Any
import subprocess
from myskills.cohort_assessment import file_digest,seal
from myskills.digest import digest_object
from myskills.manifest import ValidationError
from qualification.behavior_v2 import save
from qualification.native_probe import request_for
from qualification.runtime_identity import MODEL,RuntimeGuard
from qualification.v4.adapter import Session,VERSION,schemas
from qualification.v4.probe import IMAGE,entries
from qualification.v4.native_transport import run_codex
from qualification.v4.provider import LocalResponses
from qualification.v7r1.probe import context as historical_context
from qualification.v5.policy import executor
from qualification.v5.replay import native_complete
from qualification.v8.cases import CASES,POLICY
from qualification.v8.evaluate import assess,VERSION as EVALUATOR

HARNESS='codex-app-server/0.157.0+myskills-native-8.0.0'


def context(root: Path) -> dict[str, Any]:
    old=historical_context(root)
    paths=sorted((root/'qualification/v8').glob('*.py'))+[root/'qualification/checkpoint8/input-snapshots.json', root/'qualification/checkpoint7/evaluator-counterexamples.json', root/'qualification/checkpoint7/acceptance-hold.json', root/'qualification/checkpoint7/hosted-counterexample.json']
    return {**old,'schema':'myskills.native-batch.v8','fixtures':CASES,
            'harness':{**old['harness'],**{str(p.relative_to(root)):file_digest(p) for p in paths}},
            'evaluator':EVALUATOR,'historical_evaluator':'myskills-evaluator/5.0.1',
            'historical_evaluator_digest':file_digest(root/'qualification/evaluator_successor_v5.py'),
            'claim_verifier':{str(p.relative_to(root)):file_digest(p) for p in sorted((root/'qualification/v6').glob('*.py'))}}


def binding(ctx: dict[str, Any], name: str) -> dict[str, Any]:
    fixture=CASES[name];skill=fixture['skill']
    return {'skill':ctx['specs'][skill]['binding'],'model':{'name':MODEL,'digest':ctx['model_digest']},
            'harness':{'version':HARNESS,'digest':digest_object(ctx['harness'])},
            'adapter':{'version':VERSION,'digest':digest_object({p:d for p,d in ctx['harness'].items() if p.startswith('qualification/v4/')})},
            'task_class':{'name':name,'fixture_digest':digest_object(fixture),'schema_digest':digest_object(schemas(fixture))},
            'environment':{'runtime_digest':digest_object(ctx['runtime']),'planner_image':IMAGE,'candidate_image':ctx['runtime']['environment']['image'],'network':'none','host_mounts':[]},
            'evaluator':{'version':EVALUATOR,'digest':ctx['harness']['qualification/v8/evaluate.py'],
                         'checks_digest':ctx['harness']['qualification/v8/checks.py'],'source_claims_digest':digest_object(ctx['claim_verifier']),
                         'inherited_terminal_policy_version':ctx['historical_evaluator'],'inherited_terminal_policy_digest':ctx['historical_evaluator_digest']}}


def prompt(root: Path, ctx: dict[str, Any], name: str) -> str:
    fixture=CASES[name];spec=ctx['specs'][fixture['skill']]
    value=json.loads(request_for(root,spec,False,[])['messages'][1]['content'])
    value.update(task=fixture['task'],scope=fixture['scope'],files=list(fixture['files']),writable=fixture['writable'],commands=list(fixture['commands']),
                 evaluation_version=EVALUATOR,native_runtime=HARNESS)
    return json.dumps(value,sort_keys=True)


def retain_assessment(directory: Path, record: dict[str, Any], fixture: dict[str, Any], assessor: Any = assess) -> str | None:
    # Preserve completed native effects before calling any fallible verifier.
    save(directory/'observation.json',seal(record))
    halt=None
    if record['generation']=='COMPLETED':
        try:record['verification']=assessor(fixture,record)
        except Exception as error:
            halt=type(error).__name__+': '+str(error)
            record['verification']={'status':'NOT_RUN','error':halt,'qualification_credit':False}
    save(directory/'observation.json',seal(record))
    return halt


def collect(root: Path, output: Path, names: list[str]) -> None:
    output.mkdir(parents=True,exist_ok=False);ctx=context(root);save(output/'context.json',ctx)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    if subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True).strip():raise ValidationError('commit and review collector before execution')
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
                record['entries']=entries(directory/'journal')
                if transport['failure'] or not native_complete(directory,record,fixture):raise ValidationError('native execution/custody/cleanup incomplete; batch halted')
                guard.check();record['trial_identity']='PRE_POST_CHECKED';record['generation']='COMPLETED'
            except Exception as error:
                halt=type(error).__name__+': '+str(error);record['error']=halt
                if record['generation']=='DISPATCHED':record['generation']='UNKNOWN'
        else:record['error']='batch halted: '+halt
        record.update(files=session.files,artifact=session.artifact,finished=session.finished,entries=entries(directory/'journal'))
        evaluation_error=retain_assessment(directory,record,fixture)
        if evaluation_error is not None:halt=evaluation_error
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
    args=parser.parse_args();collect(Path.cwd(),args.output,args.case or list(CASES))
