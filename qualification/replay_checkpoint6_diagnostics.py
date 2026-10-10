"""Observe checkpoint 6 without changing its frozen evaluator or failure gates."""
import argparse
import json
from pathlib import Path
import subprocess

from myskills.cohort_assessment import file_digest, seal
from myskills.digest import digest_object
from qualification import checkpoint_six as checkpoint
from qualification import checkpoint_five_followup as legacy
from qualification.checkpoint_four import require
from qualification.v5.cases import CASES
from qualification.workflow_probe import normalized

VERSION = 'myskills.checkpoint6-replay-diagnostics/1.0.0'


def differences(expected, actual, path=''):
    if isinstance(expected, dict) and isinstance(actual, dict):
        result = []
        for key in sorted(expected.keys() | actual.keys()):
            child = path+'/'+key.replace('~', '~0').replace('/', '~1')
            result.extend([child] if key not in expected or key not in actual else differences(expected[key], actual[key], child))
        return result
    return [] if expected == actual else [path or '/']


def enforce(value):
    require(all(check['status'] == 'PASS' for ledger in value['ledgers'].values()
                for check in ledger['retained_failure_regressions']),
            'retained claim regression not reproduced; report preserved')
    require(all(row['functional_tests'] == 'PASS' for row in value['matrix']),
            'bounded behavioral checks failed or did not complete; report preserved')


def replay(root, retained, output):
    output.mkdir(parents=True, exist_ok=False)
    original = legacy.evaluate
    records = {'schema': VERSION,
               'source_sha': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
               'sources': {name: file_digest(root/name) for name in (
                   'qualification/replay_checkpoint6_diagnostics.py', 'qualification/checkpoint_six.py',
                   'qualification/checkpoint_five_followup.py', 'qualification/v5/evaluate.py')},
               'qualification_credit': False, 'evaluations': []}

    def persist():
        (output/'diagnostics.json').write_text(json.dumps(seal(records), sort_keys=True, indent=2)+'\n')

    def capture(*args, **kwargs):
        fixture = args[0]
        names = [name for name in legacy.NAMES if CASES[name] == fixture]
        require(len(names) == 1, 'ambiguous historical evaluation case')
        name = names[0]
        path = retained/name/'observation.json'
        old = json.loads(path.read_text()) if path.exists() else {}
        row = {'case': name, 'fixture_digest': digest_object(fixture),
               'input_digest': digest_object({'args': args, 'kwargs': kwargs}),
               'source_files': args[1], 'observation_digest': old.get('evidence_digest'),
               'expected': normalized(old.get('verification')), 'state': 'DISPATCHED'}
        records['evaluations'].append(row)
        persist()
        try:
            result = original(*args, **kwargs)
        except Exception as error:
            row.update(state='RAISED', error=type(error).__name__+': '+str(error))
            persist()
            raise
        actual = normalized(result)
        row.update(state='RETURNED', actual=actual, matches_frozen=actual == row['expected'],
                   differing_paths=differences(row['expected'], actual))
        persist()  # Retain the result before the legacy comparison can raise.
        return result

    persist()
    legacy.evaluate = capture
    try:
        value = checkpoint.report(root, retained)
        exports = {'checkpoint': value, 'claims': value['ledgers'], 'matrix': value['matrix'],
                   'composition': value['composition'], **value['consumers']}
        for name, data in exports.items():
            (output/(name+'.json')).write_text(json.dumps(data, sort_keys=True, indent=2)+'\n')
        enforce(value)
    except Exception as error:
        records.update(outcome='FAIL', error=type(error).__name__+': '+str(error))
        persist()
        raise
    finally:
        legacy.evaluate = original
    records['outcome'] = 'PASS'
    persist()
    return value


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--retained', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = replay(Path.cwd(), args.retained, args.output)
    print(json.dumps({'evidence_digest': result['evidence_digest']}))
