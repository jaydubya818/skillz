"""Add sealed tool journals to historical C5/C6 diagnostic replay, without retries."""
import argparse
import json
from pathlib import Path

from myskills.cohort_assessment import file_digest, seal
from qualification import replay_followup_diagnostics as followup
from qualification import replay_checkpoint6_diagnostics as claims
from qualification.checkpoint_four import require
from qualification.v5 import replay as tools_replay

VERSION = 'myskills.historical-tool-replay-diagnostics/2.0.0'


def replay(root, retained, output, checkpoint):
    require(checkpoint in ('5-followup', '6'), 'unsupported diagnostic checkpoint')
    require(not output.exists(), 'diagnostic output already exists')
    original = tools_replay.Session

    def observed(name, fixture, execute):
        record = json.loads((retained/name/'observation.json').read_text())
        return original(name, fixture, execute, output/'replay-journal'/name, record['binding'])

    tools_replay.Session = observed
    try:
        runner = followup if checkpoint == '5-followup' else claims
        return runner.replay(root, retained, output)
    finally:
        tools_replay.Session = original
        if output.exists():
            receipt = seal({'schema': VERSION, 'checkpoint': checkpoint, 'qualification_credit': False,
                            'observer_digest': file_digest(root/'qualification/replay_tool_diagnostics_v2.py'),
                            'legacy_tools_digest': file_digest(root/'qualification/v5/replay.py'),
                            'semantics': 'Existing adapter journal enabled; all original comparisons and exceptions preserved.'})
            with (output/'tool-observer.json').open('x') as stream:
                json.dump(receipt, stream, sort_keys=True, indent=2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint', required=True, choices=['5-followup', '6'])
    parser.add_argument('--retained', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = replay(Path.cwd(), args.retained, args.output, args.checkpoint)
    print(json.dumps({'evidence_digest': result['evidence_digest']}))
