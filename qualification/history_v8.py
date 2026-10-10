"""Verify failed historical custody without reclassifying it as a new replay."""
import argparse
import json
from pathlib import Path
import subprocess
from typing import Any

from myskills.cohort_assessment import file_digest, seal
from myskills.digest import digest_object
from qualification.checkpoint_four import require, unseal
from qualification.v5.replay import native_complete

BASE = 'c7c53a261552297d9398b00e822d7cfaf7c63fff'


def unchanged(root: Path) -> dict[str, str]:
    paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', BASE, '--',
                                     'skills', 'catalog', 'myskills', 'qualification'], cwd=root, text=True).splitlines()
    result = {}
    for name in paths:
        old = subprocess.check_output(['git', 'show', BASE+':'+name], cwd=root)
        require((root/name).read_bytes() == old, 'historical source or evidence changed: '+name)
        result[name] = file_digest(root/name)
    return result


def report(root: Path, followup5: Path, native7: Path, followup7: Path) -> dict[str, Any]:
    from qualification.custody_v5 import bundle as bundle5
    from qualification.custody_v7 import bundle as bundle7
    from qualification.custody_v7r1 import bundle as bundle7r1
    from qualification.v5.cases import CASES as cases5
    from qualification.v7.cases import CASES as cases7
    from qualification.v7r1.cases import CASES as cases7r1
    groups = [
        ('checkpoint5-followup', followup5, bundle5, cases5, 'qualification/checkpoint5/followup-evidence-pin.json'),
        ('checkpoint7', native7, bundle7, cases7, 'qualification/checkpoint7/evidence-pin.json'),
        ('checkpoint7-followup', followup7, bundle7r1, cases7r1, 'qualification/checkpoint7/followup/evidence-pin.json'),
    ]
    rows = []
    for name, directory, package, cases, pin_path in groups:
        pin = json.loads((root/pin_path).read_text())
        require(digest_object(package(directory)) == pin['bundle_digest'], 'historical native custody differs')
        records = []
        for path in sorted(directory.glob('*/observation.json')):
            record = json.loads(path.read_text())
            unseal(record)
            case = path.parent.name
            complete = native_complete(path.parent, record, cases[case])
            if record['generation'] == 'COMPLETED':
                require(complete, 'historical completed native custody is incomplete')
            records.append({'case': case, 'observation_digest': record['evidence_digest'],
                            'generation': record['generation'], 'native_custody_complete': complete,
                            'captured_evaluator_verdict': record.get('verification', {}).get('status'),
                            'historical_final_disposition': 'NOT_RECOMPUTED; pinned review and acceptance hold remain authoritative',
                            'fresh_execution': 'NOT_RUN', 'qualification_credit': False})
        require(records, 'historical bundle has no observations')
        rows.append({'name': name, 'bundle_digest': pin['bundle_digest'], 'records': records})
    return seal({'schema': 'myskills.historical-custody.v8', 'status': 'PASS',
                 'unchanged_historical_files': unchanged(root), 'bundles': rows,
                 'fresh_behavioral_replay': 'NOT_RUN', 'historical_verdicts_changed': False,
                 'acceptance_hold_preserved': file_digest(root/'qualification/checkpoint7/acceptance-hold.json'),
                 'qualification_credit': False,
                 'scope': 'Integrity and native transcript custody only. Known failed API implementations are retained negative evidence. Historical TDD remains a separate unchanged execution gate.'})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('followup5', 'native7', 'followup7', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    value = report(Path.cwd(), args.followup5, args.native7, args.followup7)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(value, sort_keys=True, indent=2)+'\n')
    print(value['evidence_digest'])
