"""Versioned assistance for the two-edit API task, retaining runtime 8.2.0."""
import argparse
from contextlib import contextmanager
from copy import deepcopy
import json
from pathlib import Path

from myskills.cohort_assessment import file_digest
from myskills.digest import digest_object
from qualification import runtime_successor_v8 as previous
from qualification import successor_probe_v8 as collector
from qualification.v4.adapter import schemas
from qualification.v8.cases import CASES as ORIGINAL

HARNESS = 'codex-app-server/0.157.0+myskills-native-8.2.1-assisted-edit'
FEEDBACK = ('The previous representative candidate also changed whitespace inside the CREATE TABLE SQL literal. '
            'That failed the exact structural edit policy. Preserve every string literal and all other source bytes. '
            'Starting from the source returned by read_file, make only these two literal edits: '
            'remove the entire indented conn.execute("PRAGMA journal_mode=WAL") line and replace timeout=30.0 with timeout=1.0. '
            'Do not retype, reformat, or reconstruct the CREATE TABLE statement. '
            'All original plan-first, test, source-claim, final-output, and effect rules still apply.')
CASES = deepcopy(ORIGINAL)
for fixture in CASES.values():
    if fixture['skill'] == 'api-and-interface-design':
        fixture['task'] += ' Additional reviewed workflow correction: '+FEEDBACK
        fixture['files']['review-feedback.md'] += '\n'+FEEDBACK+'\n'
        fixture['scope'] += ' Versioned literal-edit assistance; the frozen structural evaluator is unchanged.'


def context(root):
    old = previous.context(root)
    correction = {'version': HARNESS, 'parent_context_digest': digest_object(old),
                  'parent_api_failure': 'sha256:e01ea1fedd209f66141e23904653afa00038e8fa49402706b9c4ffa8438d9160',
                  'corpus_digest': digest_object(CASES),
                  'tool_contracts': {name: digest_object(schemas(case)) for name, case in CASES.items()},
                  'runtime_changed': False, 'evaluator_changed': False, 'skill_instructions_changed': False}
    return {**old, 'schema': 'myskills.native-batch.v8.2.1-assisted-edit', 'fixtures': CASES,
            'workflow_correction': correction,
            'harness': {**old['harness'], 'qualification/workflow_correction_v8.py': file_digest(root/'qualification/workflow_correction_v8.py')}}


def binding(ctx, name):
    value = previous.binding(ctx, name)
    fixture = CASES[name]
    value['harness']['version'] = HARNESS
    value['task_class'].update(fixture_digest=digest_object(fixture), schema_digest=digest_object(schemas(fixture)),
                              workflow_correction_digest=digest_object(ctx['workflow_correction']))
    return value


def prompt(root, ctx, name):
    value = json.loads(previous.prompt(root, ctx, name))
    value.update(task=CASES[name]['task'], scope=CASES[name]['scope'], native_runtime=HARNESS)
    return json.dumps(value, sort_keys=True)


@contextmanager
def corrected_collector():
    replacements = {'CASES': CASES, 'context': context, 'binding': binding, 'prompt': prompt}
    original = {key: getattr(collector, key) for key in replacements}
    try:
        for key, value in replacements.items():
            setattr(collector, key, value)
        yield
    finally:
        for key, value in original.items():
            setattr(collector, key, value)


def collect(root, evidence, output):
    with corrected_collector():
        collector.collect(root, evidence, output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    collect(Path.cwd(), args.evidence, args.output)
