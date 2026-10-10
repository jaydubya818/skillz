import base64
import json

import pytest

from myskills.manifest import ValidationError
from qualification.disclosure_v8 import native_view, scan
from qualification.runtime_identity import MODEL


def fixture():
    output = [{'type': 'reasoning', 'encrypted_content': 'PRIVATE_OPAQUE_CANARY'},
              {'type': 'function_call', 'namespace': 'myskills', 'name': 'read_file',
               'call_id': 'call_fixture', 'arguments': '{"path":"api.py"}'}]
    body = 'data: '+json.dumps({'type': 'response.completed', 'response':
                             {'model': MODEL, 'status': 'completed', 'output': output}})+'\n'
    records = [
        {'channel': 'provider', 'id': 0, 'value': {'model': MODEL, 'instructions': 'PRIVATE_INSTRUCTION_CANARY',
                                                 'input': 'PRIVATE_HISTORY_CANARY', 'client_metadata': {'owner': 'PRIVATE_OWNER_CANARY'}}},
        {'channel': 'host_response', 'id': 0, 'value': {'status': 200, 'body': base64.b64encode(body.encode()).decode()}},
        {'channel': 'event', 'value': {'method': 'turn/completed', 'params':
                                      {'threadId': 'PRIVATE_THREAD_CANARY', 'turn': {'status': 'completed', 'items': output}}}},
        {'channel': 'stderr', 'value': 'PRIVATE_STDERR_CANARY'}]
    text = ''.join(json.dumps(row)+'\n' for row in records)
    transport = {'records': records, 'image': 'sha256:'+'a'*64, 'cleanup_confirmed': True,
                 'exit_code': 0, 'failure': None, 'network': 'none', 'host_mounts': []}
    return text, transport


def test_projection_excludes_all_private_channels_and_keeps_tool_identity():
    text, transport = fixture()
    witness, summary = native_view(text, json.dumps(transport))
    public = json.dumps([witness, summary])
    assert 'PRIVATE_' not in public
    assert 'reasoning' not in public and 'encrypted_content' not in public
    assert witness['provider_calls'][0]['function_calls'] == [
        {'call_id': 'call_fixture', 'tool': 'read_file', 'arguments': {'path': 'api.py'}}]
    assert witness['raw_transcript_replay'] is False
    assert summary['raw_transcript_replay'] is False


@pytest.mark.parametrize('key,value', [('cleanup_confirmed', False), ('network', 'host'), ('host_mounts', ['/private']), ('exit_code', 1)])
def test_failed_or_broadened_transport_is_not_published_as_clean(key, value):
    text, transport = fixture(); transport[key] = value
    with pytest.raises(ValidationError, match='transport boundary'):
        native_view(text, json.dumps(transport))


def test_mismatching_transport_is_rejected():
    text, transport = fixture(); transport['records'] = []
    with pytest.raises(ValidationError, match='transcript differ'):
        native_view(text, json.dumps(transport))


@pytest.mark.parametrize('content', ['-----BEGIN PRIVATE KEY-----', '/Users/example/secret',
                                    '/private/tmp/private', '{"encrypted_content":"opaque"}',
                                    'github_pat_'+'x'*30])
def test_public_scan_blocks_known_private_patterns(content):
    assert scan(content)
