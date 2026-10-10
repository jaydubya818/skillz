"""Assisted correction tasks bind failed predecessor source and explicit plans."""
from copy import deepcopy
import json
from pathlib import Path

from myskills.digest import digest_object
from qualification.v7.cases import CASES as ORIGINAL, POLICY, SPECS
from qualification.v8.checks import API, SECURITY

INPUTS = json.loads((Path(__file__).parents[1]/'checkpoint8/input-snapshots.json').read_text())
FEEDBACK = '''This is a review-assisted checkpoint-8 correction, not unassisted development.
Read every initial file. Your FIRST write must copy the complete protected contract-plan.json
into contract.md (API) or threat-model.md (security). This records requirements BEFORE implementation.
Do not edit any code before that complete plan is recorded. A placeholder document is insufficient.
API: the retained PRAGMA journal_mode=WAL races with another request and raises SQLITE_BUSY.
Remove that per-request statement. Preserve the existing database journal configuration.
Change sqlite3.connect timeout from 30.0 to 1.0 seconds. Keep insert-first transaction semantics,
legacy nullable schema, responses, owner scoping, and try/finally connection cleanup.
Do not add retry loops, change tests, swallow errors, or claim unbounded concurrency guarantees.
Security: inspect retained code, preserve present null data versus missing data, and verify all
negative cases. Do not change correct source merely to create an edit.
Run test and legacy. Use ONLY actual successful calls from THIS trial as evidence.
Then replace the plan document with the required final claim JSON using exact source digests.
A call_id is the actual call_... identifier, not an evidence_digest. Retained old calls are invalid.
After final JSON is written, run test again. The document may cite the earlier successful test
for the same executable source; finish must cite the final test and exact final document digest.
Call finish exactly once. After COMPLETED, make no further tool calls.
Finish notes exactly: See the bound document and tool records. Offline fixture scope only.
Final plain text exactly: Recorded. Offline fixture scope only.
Never claim independent qualification. Report real failures; no fabricated evidence.
'''
CASES = {}
for name, old in ORIGINAL.items():
    fixture = deepcopy(old); skill = fixture['skill']; api = skill == 'api-and-interface-design'
    source = 'api.py' if api else 'security.py'; doc = 'contract.md' if api else 'threat-model.md'
    for path in [source, doc]: fixture['files'][path] = INPUTS['skills'][skill]['files'][path]
    plan = {'phase': 'CONTRACT_PLAN', 'skill': skill, 'requirements': SPECS[skill],
            'initial_source_digest': digest_object(fixture['files'][source]), 'implementation_scope': [source],
            'required_tests': ['test', 'legacy'], 'publication_authorized': False}
    fixture['files']['contract-plan.json'] = json.dumps(plan, sort_keys=True, indent=2)+'\n'
    fixture['files']['review-feedback.md'] = FEEDBACK
    fixture['commands']['test'] = ['python3', '-c', API if api else SECURITY]
    fixture['task'] += ' This successor starts from the sealed checkpoint-7 representative output. '+FEEDBACK
    fixture['scope'] += ' Exact reviewer-assisted plan-first correction with evaluator 8.0.0; no general capability claim.'
    CASES[name] = fixture
