"""Strict tool replay with durable evidence written before comparisons."""
import json
from pathlib import Path
from typing import Any

from myskills.digest import digest_object
from qualification.checkpoint_four import require, unseal
from qualification.v4.adapter import Session, validate_output
from qualification.v5.policy import executor
from qualification.workflow_probe import normalized


def replay_entries(fixture: dict[str, Any], record: dict[str, Any], directory: Path, output: Path) -> Session:
    identity = record['binding']
    name = identity['task_class']['name']
    session = Session(name, fixture, executor(fixture['skill']), output/name, identity)
    previous = 'GENESIS'
    for index, entry in enumerate(record['entries']):
        request, result = entry['request'], entry['result']
        validate_output(result, name, request['call_id'], digest_object(request))
        require(result['previous'] == previous, 'tool chain reordered')
        previous = result['evidence_digest']
        completed = json.loads((directory/'journal'/f'{index}-completed.json').read_text())
        unseal(completed)
        require(completed['binding'] == identity and completed['request'] == request
                and completed['result'] == result and completed['files'] == entry['files'], 'journal changed')
        dispatched = directory/'journal'/f'{index}-dispatched.json'
        if result['status'] == 'OK':
            require(dispatched.exists(), 'missing pre-effect record')
        if dispatched.exists():
            before = json.loads(dispatched.read_text())
            unseal(before)
            require(before['binding'] == identity and before['request'] == request
                    and before['files'] == session.files, 'pre-effect state changed')
        actual = session.call(request['call_id'], request['tool'], request['arguments'])
        def stable(value: dict[str, Any]) -> dict[str, Any]:
            return normalized({key: item for key, item in value.items() if key not in ('previous', 'evidence_digest')})
        require(stable(actual) == stable(result) and session.files == entry['files'], 'independent tool replay differs; actual journal retained')
    require(session.files == record['files'] and session.finished == record['finished']
            and session.artifact == record['artifact'], 'final state differs')
    return session
