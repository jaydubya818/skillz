"""One bounded correction batch with explicit independent review feedback."""
from copy import deepcopy
import json
from pathlib import Path
from qualification.v7.cases import CASES as INITIAL,POLICY

INPUTS=json.loads((Path(__file__).parents[1]/'checkpoint7/followup/input-snapshots.json').read_text())
FEEDBACK='''This is an explicitly review-assisted successor, not an unassisted task.
The initial API outputs retained a false source comment claiming BEGIN IMMEDIATE;
the source actually uses insertion plus sqlite3.IntegrityError replay handling.
Remove that inaccurate comment. Do not change the tested SQL behavior or schema.
The initial security output confused evidence_digest with call_id. A call_id is
the actual call_... string at the top level of the tool response, not sha256:...
The document must cite a real successful test for its final executable sources.
After writing the document, another final test runs. The document retains its
earlier valid test call citation; the finish artifact cites the final test call.
Do not say both cite the same call. Source/document digests DO use sha256:...
and must be copied from actual read_file/write_file payload.digest values.
Previous input document call IDs belong to the failed predecessor trial and
cannot establish this new workflow. Replace them using this trial's own calls.
The initial outputs also attempted tools after finish. Call finish EXACTLY ONCE.
After its COMPLETED response, issue no further tools, reads or finish retries.
Use finish notes exactly: See the bound document and tool records. Offline fixture scope only.
Use the final plain text response exactly: Recorded. Offline fixture scope only.
These neutral statements add no unsupported technical or qualification claims.
All original checks and limits remain mandatory. Any failure must remain a failure.
'''
CASES={}
for name,old in INITIAL.items():
    fixture=deepcopy(old);skill=fixture['skill']
    source='api.py' if skill=='api-and-interface-design' else 'security.py'
    doc='contract.md' if skill=='api-and-interface-design' else 'threat-model.md'
    previous=INPUTS['initial_cases'][skill]
    for path in [source,doc]:fixture['files'][path]=previous['files'][path]
    fixture['files']['review-feedback.md']=FEEDBACK
    fixture['task']+=' This successor begins with the sealed failed representative output. Read and apply protected review-feedback.md. '+FEEDBACK
    fixture['scope']+=' Explicit independent-review-assisted correction; no unassisted or general-purpose qualification.'
    CASES[name]=fixture
