"""Read-only catalog and package commands; no skills are executed."""
import argparse
import json
from pathlib import Path
from .catalog import build_catalog
from .manifest import SCHEMA

def main():
    parser = argparse.ArgumentParser(prog='python -m myskills')
    parser.add_argument('command', choices=('catalog', 'validate', 'inspect', 'digest', 'schema', 'overlaps', 'provenance'))
    parser.add_argument('skill_id', nargs='?')
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    if args.command == 'schema':
        print(json.dumps(SCHEMA, indent=2, sort_keys=True))
        return
    catalog = build_catalog(args.root)
    if args.command == 'validate':
        print(json.dumps({'skills': len(catalog['skills']), 'failures': catalog['failures'], 'qualification': 'NOT_EVALUATED'}))
    elif args.command == 'catalog':
        print(json.dumps(catalog, indent=2, sort_keys=True))
    elif args.command == 'overlaps':
        print(json.dumps(catalog['overlap_candidates'], indent=2))
    else:
        skill = next((s for s in catalog['skills'] if s['skill_id'] == args.skill_id), None)
        if skill is None:
            parser.error('skill unavailable')
        result = skill['digest'] if args.command == 'digest' else skill['provenance'] if args.command == 'provenance' else skill
        print(json.dumps(result, indent=2, sort_keys=True))
    if catalog['failures']:
        raise SystemExit(1)

if __name__ == '__main__':
    main()
