"""Persist independent replay effects before unchanged qualification comparisons."""
import argparse
import json
from pathlib import Path
import subprocess

from myskills.cohort_assessment import file_digest, seal
from qualification import checkpoint_seven as checkpoint
from qualification.v5 import replay as tools_replay
from qualification.v7 import evaluate as evaluator


def replay(root, retained, previous, output, initial=None):
    output.mkdir(parents=True, exist_ok=False)
    original_session = tools_replay.Session
    original_evaluator = evaluator.executor
    original_controls = checkpoint.executor
    records = {'schema': 'myskills.checkpoint7-replay-diagnostics.v1',
               'source_sha': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
               'observer_digest': file_digest(root/'qualification/replay_checkpoint7_diagnostics.py'),
               'qualification_credit': False, 'executions': []}

    def persist():
        (output/'diagnostics.json').write_text(json.dumps(seal(records), sort_keys=True, indent=2)+'\n')

    def session(name, fixture, execute):
        # Adapter behavior is unchanged; enable its existing durable journal.
        record = json.loads((retained/name/'observation.json').read_text())
        return original_session(name, fixture, execute, output/'replay-journal'/name, record['binding'])

    def observe_executor(factory, phase):
        def executor(skill):
            execute = factory(skill)
            def run(*args, **kwargs):
                observation = {'phase': phase, 'skill': skill, 'args': args, 'kwargs': kwargs, 'state': 'DISPATCHED'}
                records['executions'].append(observation)
                persist()
                try:
                    result = execute(*args, **kwargs)
                except Exception as error:
                    observation.update(state='RAISED', error=type(error).__name__+': '+str(error))
                    persist()
                    raise
                observation.update(state='RETURNED', result=result)
                persist()
                return result
            return run
        return executor

    persist()
    tools_replay.Session = session
    evaluator.executor = observe_executor(original_evaluator, 'profile-evaluator')
    checkpoint.executor = observe_executor(original_controls, 'evaluator-controls')
    try:
        value = checkpoint.report(root, retained, previous, initial)
    except Exception as error:
        records.update(outcome='FAIL', error=type(error).__name__+': '+str(error))
        persist()
        raise
    finally:
        tools_replay.Session = original_session
        evaluator.executor = original_evaluator
        checkpoint.executor = original_controls
    records['outcome'] = 'PASS'
    persist()
    exports = {'checkpoint': value, 'matrix': value['matrix'], 'profiles': value['profiles'],
               'composition': value['composition'], **value['consumers']}
    for name, data in exports.items():
        (output/(name+'.json')).write_text(json.dumps(data, sort_keys=True, indent=2)+'\n')
    return value


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--retained', type=Path, required=True)
    parser.add_argument('--previous', type=Path, required=True)
    parser.add_argument('--initial', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    value = replay(Path.cwd(), args.retained, args.previous, args.output, args.initial)
    print(json.dumps({'evidence_digest': value['evidence_digest'], 'profiles': {k:v['status'] for k,v in value['profiles'].items()}}))
