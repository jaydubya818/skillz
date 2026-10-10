"""Real-container positive/negative controls. Never Skill behavioral evidence."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import threading

from qualification.native_controls import fixed
from qualification.v4.cases import CASES
from qualification.v4.execution import execute
from qualification.v4.runner import run_program
from qualification.v4.source_policy import executor


def controls():
    evidence = {}
    for skill in ('api-and-interface-design', 'security-and-hardening'):
        fixture = CASES[skill]
        path, source = fixed[skill]
        if skill == 'security-and-hardening':
            source = source.replace('payload.get("trusted_owner") and', 'isinstance(payload.get("trusted_owner"),str) and payload.get("trusted_owner") and')
        good = {**fixture['files'], path: source}
        bad = deepcopy(good)
        if skill == 'security-and-hardening':
            bad[path] = source.replace('"destination" not in payload', 'payload.get("destination") is None')
        else:
            bad[path] = source.replace('  c.execute("BEGIN IMMEDIATE")\n', '')
        results = {name: executor(skill)(files, fixture['commands']['test'], fixture['writable'])
                   for name, files in [('bad', bad), ('good', good)]}
        assert results['good']['exit_code'] == 0, results
        assert results['bad']['exit_code'] != 0, results
        assert all(v['cleanup_confirmed'] and not v['unauthorized_changes'] for v in results.values())
        evidence[skill] = results
    for name, script in {
        'symlink_escape': 'import os; os.symlink("/etc/passwd","escape")',
        'evidence_tamper': 'from pathlib import Path; Path("evidence.json").write_text("PASS")',
        'cache_exemption': 'from pathlib import Path; Path("__pycache__").mkdir(); Path("__pycache__/evidence").write_text("PASS")',
    }.items():
        result = execute({}, ['python3', '-c', script], [])
        assert result['unauthorized_changes'] and result['cleanup_confirmed'], result
        evidence[name] = result
    program = 'import time\ndef solve(x):\n time.sleep(60)\n'
    timeout = run_program(program, [None], timeout=1)
    assert timeout['failure'] == 'TIMEOUT' and timeout['container_removed']
    evidence['timeout'] = timeout
    cancel = threading.Event()
    timer = threading.Timer(1, cancel.set)
    timer.start()
    try: cancelled = run_program(program, [None], timeout=10, cancel=cancel)
    finally: timer.join()
    assert cancelled['failure'] == 'CANCELLED' and cancelled['container_removed']
    evidence['cancellation'] = cancelled
    network = run_program('import socket\ndef solve(x):\n try:\n  socket.create_connection(("1.1.1.1",443),timeout=.2)\n  return "UNEXPECTED_NETWORK"\n except OSError:return "DENIED"\n', [None])
    assert network['value'] == ['DENIED'] and network['container_removed'], network
    evidence['network'] = network
    return {'credit': 'ADAPTER_RUNTIME_CONTROLS_ONLY', 'status': 'PASS', 'results': evidence}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    value = controls()
    args.output.write_text(json.dumps(value, sort_keys=True, indent=2)+'\n')
    print('PASS: 8 real-container controls; no Skill credit')
