"""Retain legacy evaluator results before its strict replay comparison can fail."""
import argparse
import json
from pathlib import Path
import subprocess

from myskills.cohort_assessment import file_digest, seal
from myskills.digest import digest_object
from qualification import checkpoint_five_followup as legacy


def replay(root, retained, output):
    output.mkdir(parents=True, exist_ok=False)
    original = legacy.evaluate
    observations = []
    context = {
        'schema': 'myskills.legacy-replay-diagnostics.v1',
        'source_sha': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
        'sources': {path: file_digest(root / path) for path in (
            'qualification/replay_followup_diagnostics.py',
            'qualification/checkpoint_five_followup.py',
            'qualification/v5/evaluate.py')},
        'qualification_credit': False,
        'observations': observations,
    }

    def persist():
        (output / 'diagnostics.json').write_text(json.dumps(seal(context), sort_keys=True, indent=2) + '\n')

    def capture(*args, **kwargs):
        observation = {'input_digest': digest_object({'args': args, 'kwargs': kwargs}),
                       'fixture_digest': digest_object(args[0]), 'source_files': args[1], 'state': 'DISPATCHED'}
        observations.append(observation)
        persist()
        try:
            result = original(*args, **kwargs)
        except Exception as error:
            observation.update(state='RAISED', error=type(error).__name__ + ': ' + str(error))
            persist()
            raise
        observation.update(state='RETURNED', result=result)
        persist()  # Must precede legacy.report's comparison and potential exception.
        return result

    persist()
    legacy.evaluate = capture
    try:
        value = legacy.report(root, retained)
    except Exception as error:
        context.update(outcome='FAIL', error=type(error).__name__ + ': ' + str(error))
        persist()
        raise  # Diagnostic capture never converts a failed replay into success.
    finally:
        legacy.evaluate = original
    context['outcome'] = 'PASS'
    persist()
    (output / 'followup.json').write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')
    return value


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--retained', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = replay(Path.cwd(), args.retained, args.output)
    print(json.dumps({'evidence_digest': result['evidence_digest'], 'cases': [row['status'] for row in result['matrix']]}))
