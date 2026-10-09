from copy import deepcopy
import json
from pathlib import Path
import pytest

from myskills.manifest import ValidationError
from qualification.runtime_identity import MODEL
from qualification.v4.adapter import schemas
from qualification.v4.cases import CASES
from qualification.v4.provider import validate_native_request, wire_schema


def native_request():
    specs=schemas(CASES['tdd'])
    builtin=json.loads(Path('qualification/v4/native-builtin.json').read_text())
    functions=[{'type':'function','name':s['name'],'description':s['description'],
                'strict':False,'parameters':wire_schema(s['inputSchema'])}
               for s in sorted(specs,key=lambda s:s['name'])]
    return {'model':MODEL,'stream':True,'store':False,'tools':[builtin,
            {'type':'namespace','name':'myskills','description':'Tools in the myskills namespace.','tools':functions}]},specs


def test_native_wire_contract_is_bound_separately_and_cannot_gain_tools():
    original,specs=native_request()
    validate_native_request(original,specs)
    for edit in ('model','network','builtin','schema','store'):
        value=deepcopy(original)
        if edit=='model':value['model']='moving-alias'
        elif edit=='network':value['tools'].append({'type':'web_search'})
        elif edit=='builtin':value['tools'][0]['name']='shell'
        elif edit=='schema':value['tools'][1]['tools'][1]['parameters']['properties']['path']['enum'].append('/etc/passwd')
        else:value['store']=True
        with pytest.raises(ValidationError):validate_native_request(value,specs)


def test_native_provider_wall_deadline_interrupts_slow_response(monkeypatch):
    import threading,time
    from qualification.v4 import provider
    class Slow:
        sock=None
        def __init__(self,*a,**kw):pass
        def request(self,*a,**kw):pass
        def getresponse(self):time.sleep(.3);raise TimeoutError('slow')
        def close(self):pass
    monkeypatch.setattr(provider.http.client,'HTTPConnection',Slow)
    request,specs=native_request()
    guard=type('Guard',(),{'check':lambda self:None})()
    start=time.monotonic()
    with pytest.raises(TimeoutError,match='UNKNOWN'):
        provider.LocalResponses(guard)(request,specs,deadline=start+.05,cancel=threading.Event())
    assert time.monotonic()-start<.25
