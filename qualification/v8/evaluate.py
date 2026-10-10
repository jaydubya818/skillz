"""Successor evaluation adds verified plan order; historical evaluators stay fixed."""
import ast
import json
from typing import Any

from myskills.cohort_assessment import seal
from myskills.digest import digest_object
from qualification.v8.controls import resource_controls
from qualification.v7.evaluate import assess as historical_assess

VERSION = 'myskills-profile-evaluator/8.0.0'


def plan_before_implementation(fixture: dict[str, Any], entries: list[dict[str, Any]]) -> bool:
    doc = 'contract.md' if fixture['skill'] == 'api-and-interface-design' else 'threat-model.md'
    writes = [e for e in entries if e['request']['tool'] == 'write_file' and e['result']['status'] == 'OK']
    if not writes or writes[0]['request']['arguments']['path'] != doc:
        return False
    try:
        actual = json.loads(writes[0]['request']['arguments']['content'])
    except (TypeError, ValueError, KeyError):
        return False
    return digest_object(actual) == digest_object(json.loads(fixture['files']['contract-plan.json']))


def bounded_api_policy(source: str) -> bool:
    """Admit only the reviewed two-edit correction, modulo comments/formatting.

    A connection keyword alone cannot bound later PRAGMA changes, recursive
    retries or rebinding. This finite assisted profile makes no general API
    implementation claim. Runtime checks remain mandatory for matching source.
    """
    from qualification.v8.cases import INPUTS
    baseline = INPUTS['skills']['api-and-interface-design']['files']['api.py']
    expected = baseline.replace('    conn.execute("PRAGMA journal_mode=WAL")\n', '').replace('timeout=30.0', 'timeout=1.0')
    try:
        return ast.dump(ast.parse(source)) == ast.dump(ast.parse(expected))
    except (SyntaxError, TypeError):
        return False


def assess(fixture: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
    value = historical_assess(fixture, record)
    value.pop('evidence_digest')
    value['version'] = VERSION
    value['checks']['specific_contract_plan_before_implementation'] = plan_before_implementation(fixture, record['entries'])
    if fixture['skill'] == 'api-and-interface-design':
        value['checks']['bounded_connection_without_retry_loop'] = bounded_api_policy(record['files']['api.py'])
    else:
        value['specific_resource_controls'] = resource_controls(record['files'], fixture['writable'])
        value['checks']['specific_resource_denials'] = value['specific_resource_controls']['status'] == 'PASS'
    value['status'] = 'PASS' if all(value['checks'].values()) else 'FAIL'
    return seal(value)
