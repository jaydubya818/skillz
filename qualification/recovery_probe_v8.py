"""Recovery successor: unchanged model/tools, restarted service, durable custody."""
import argparse
import json
from pathlib import Path
import re
import subprocess
from typing import Any

from myskills.cohort_assessment import file_digest, seal
from myskills.digest import digest_object
from qualification.checkpoint_four import require
from qualification.custody_guard import Vault, protect, release_sources
from qualification.runtime_identity import MODEL, RuntimeGuard
from qualification.v4.adapter import Session
from qualification.v4.native_transport import run_codex
from qualification.v4.probe import IMAGE, entries
from qualification.v4.provider import LocalResponses
from qualification.v5.policy import executor
from qualification.v5.replay import native_complete
from qualification.v8.cases import CASES, POLICY
from qualification.v8.evaluate import assess
from qualification.v8.probe import context as original_context, binding as original_binding, prompt as original_prompt

HARNESS = 'codex-app-server/0.157.0+myskills-native-8.1.0-recovery'
RUNTIME_PIN = 'qualification/checkpoint8/recovery-runtime-pin.json'
OWNER = '01a11f25-f14d-7a13-8036-afac830fd22b'


def stable_runtime(value: dict[str, Any]) -> dict[str, Any]:
    process = re.fullmatch(r'[A-Za-z]{3} [A-Za-z]{3} +[0-9]{1,2} [0-9]{2}:[0-9]{2}:[0-9]{2} [0-9]{4}\s+(.+)', value['service']['process'])
    require(process is not None, 'unrecognized daemon process identity')
    service = {key: item for key, item in value['service'].items() if key not in ('pid', 'process')}
    return {**value, 'service': {**service, 'command': process.group(1)}}


def context(root: Path) -> dict[str, Any]:
    value = original_context(root)
    runtime = json.loads((root/RUNTIME_PIN).read_text())
    require(stable_runtime(runtime) == stable_runtime(value['runtime']), 'recovery changed more than the observed daemon process; successor authorization required')
    paths = ['qualification/recovery_probe_v8.py', 'qualification/custody_guard.py', RUNTIME_PIN]
    return {**value, 'schema': 'myskills.native-batch.v8-recovery', 'runtime': runtime,
            'historical_runtime_digest': digest_object(value['runtime']),
            'runtime_change': 'Exact bytes/environment preserved; daemon PID and start time changed after restart.',
            'harness': {**value['harness'], **{name: file_digest(root/name) for name in paths}}}


def binding(ctx: dict[str, Any], name: str) -> dict[str, Any]:
    value = original_binding(ctx, name)
    value['harness']['version'] = HARNESS
    return value


def prompt(root: Path, ctx: dict[str, Any], name: str) -> str:
    value = json.loads(original_prompt(root, ctx, name))
    value['native_runtime'] = HARNESS
    return json.dumps(value, sort_keys=True)


def collect(root: Path, evidence: Path, output: Path) -> None:
    require(output.resolve().is_relative_to(evidence.resolve()), 'native evidence must use the durable vault')
    require(not subprocess.check_output(['git', 'status', '--porcelain'], cwd=root, text=True).strip(), 'commit and review collector before execution')
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    ctx = context(root)
    vault = Vault(root, evidence, OWNER)
    output.mkdir(parents=True, exist_ok=False)

    def save(path: Path, value: dict[str, Any]) -> None:
        raw = (json.dumps(value, sort_keys=True, indent=2)+'\n').encode()
        vault.retain(str(path.relative_to(evidence)), raw)
        path.write_bytes(raw)
        if path.name != 'observation.json':
            protect(path)

    class GuardedSession(Session):
        def _persist(self, phase: str, value: dict[str, Any]) -> None:
            super()._persist(phase, value)
            path = self.journal/(str(len(self.events))+'-'+phase+'.json')
            vault.retain(str(path.relative_to(evidence)), path.read_bytes())
            protect(path)

    source_paths = subprocess.check_output(['git', 'ls-files'], cwd=root, text=True).splitlines()
    protected = vault.freeze_sources(root, source_paths)
    halt = None
    guard = None
    try:
        save(output/'context.json', ctx)
        try:
            guard = RuntimeGuard(ctx['runtime'])
        except Exception as error:
            halt = type(error).__name__+': '+str(error)
        for name, fixture in CASES.items():
            directory = output/name
            directory.mkdir()
            identity = binding(ctx, name)
            record = {'binding': identity, 'collector_commit': commit, 'execution_eligible': False, 'generation': 'NOT_RUN'}
            session = GuardedSession(name, fixture, executor(fixture['skill']), directory/'journal', identity)
            if halt is None:
                try:
                    guard.check()
                    require(context(root) == ctx, 'collector identity changed')
                    text = prompt(root, ctx, name)
                    save(directory/'prompt.json', {'policy': POLICY, 'prompt': text})
                    record['generation'] = 'DISPATCHED'
                    save(directory/'observation.json', record)
                    journal = directory/'native.jsonl'
                    journal.touch(exist_ok=False)
                    protect(journal, append_only=True)
                    transport = run_codex(IMAGE, MODEL, POLICY, text, session, LocalResponses(guard), journal=journal)
                    vault.retain(str(journal.relative_to(evidence)), journal.read_bytes())
                    save(directory/'transport.json', transport)
                    record['entries'] = entries(directory/'journal')
                    require(not transport['failure'] and native_complete(directory, record, fixture), 'native execution/custody/cleanup incomplete; batch halted')
                    guard.check()
                    record.update(trial_identity='PRE_POST_CHECKED', generation='COMPLETED')
                except Exception as error:
                    halt = type(error).__name__+': '+str(error)
                    record['error'] = halt
                    if record['generation'] == 'DISPATCHED':
                        record['generation'] = 'UNKNOWN'
            else:
                record['error'] = 'batch halted: '+halt
            record.update(files=session.files, artifact=session.artifact, finished=session.finished, entries=entries(directory/'journal'))
            save(directory/'observation.json', seal(record))
            if record['generation'] == 'COMPLETED':
                try:
                    record['verification'] = assess(fixture, record)
                except Exception as error:
                    halt = type(error).__name__+': '+str(error)
                    record['verification'] = {'status': 'NOT_RUN', 'error': halt, 'qualification_credit': False}
                save(directory/'observation.json', seal(record))
            protect(directory/'observation.json')
            print(json.dumps({'case': name, 'generation': record['generation'], 'events': len(session.events),
                              'verification': record.get('verification', {}).get('status'), 'error': record.get('error')}), flush=True)
        completion = {'runtime_identity': 'UNSTABLE', 'halt': halt, 'all_results_admissible': False, 'cases': list(CASES)}
        if guard is not None:
            try:
                guard.finish()
                require(context(root) == ctx, 'collector identity changed')
                completion.update(runtime_identity='STABLE', all_results_admissible=halt is None)
            except Exception as error:
                completion['error'] = type(error).__name__+': '+str(error)
        save(output/'completion.json', seal(completion))
    finally:
        # Evidence remains protected. Only this task's unchanged source flags
        # return to their captured values so final reporting edits can proceed.
        release_sources(root, OWNER, protected)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    collect(Path.cwd(), args.evidence, args.output)
