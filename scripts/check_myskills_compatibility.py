#!/usr/bin/env python3
"""Read-only source probes. No private source content is copied into public evidence."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

parser = argparse.ArgumentParser()
for name in ('myeve', 'myfactory', 'relay'):
    parser.add_argument('--' + name, type=Path, required=True)
args = parser.parse_args()
shas = {name: subprocess.check_output(['git', '-C', str(getattr(args, name)), 'rev-parse', 'HEAD'], text=True).strip() for name in ('myeve', 'myfactory', 'relay')}
factory = args.myfactory / 'packages/contracts/src/cloud-execution.ts'
eve = (args.myeve / 'apps/eve/lib/engineering/factory-routing.ts').read_text()
relay = (args.relay / 'lib/v2/federation/contracts.ts').read_text()
assert 'No automatic native fallback' in eve or 'no automatic native fallback' in eve
assert 'work.generation' in eve and 'factoryVersion' in eve
assert '.strict()' in relay and 'work.request' in relay and 'skill' not in relay.lower()
# Exercise the actual canonical Factory parser, without a server or provider.
script = '''
const {parseCloudPrepare} = await import(process.argv[2]);
const source={repository:'fixture/project',commit:'a'.repeat(40),tree:'b'.repeat(40)};
const grant={clientId:'fixture',source,commands:['true'],allowedPaths:['fixture.txt'],maxDurationMs:10000,maxSpendUsd:1};
const input={protocol:'MYFACTORY_EXECUTION_V2',requestId:'00000000-0000-4000-8000-000000000001',workId:'00000000-0000-4000-8000-000000000002',workGeneration:1,repository:source.repository,deadline:new Date(10000).toISOString(),maxSpendUsd:1,source,input:{title:'Fixture',description:'Synthetic protocol check',kind:'investigation',acceptanceCriteria:['Fixture only'],checkCommands:['true'],allowedPaths:['fixture.txt']}};
parseCloudPrepare(input,grant,1);
let rejected=false;try{parseCloudPrepare({...input,skill:{id:'fixture'}},grant,1)}catch{rejected=true}
if(!rejected)throw Error('Expected explicit protocol change gate');
console.log('canonical_factory_parser_pass_and_unknown_skill_rejected');
'''
with tempfile.TemporaryDirectory(prefix='myskills-contract-') as directory:
    path = Path(directory) / 'probe.mjs'
    path.write_text(script)
    result = subprocess.run(['node', str(path), str(factory)], check=True, capture_output=True, text=True)
print(json.dumps({'source_shas': shas, 'factory_parser_probe': result.stdout.strip(),
                  'myeve_source_contract': 'NO_AUTOMATIC_FALLBACK', 'relay_source_contract': 'STRICT_NO_SKILL_EXTENSION',
                  'live_integration': 'NOT_RUN', 'source_modified': False}, indent=2))
