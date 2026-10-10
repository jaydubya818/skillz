import json
from pathlib import Path
import subprocess
from qualification.native_controls import fixed
from qualification.native_validation import source_allowed

ROOT=Path(__file__).parents[1]


def check(source):
    p=subprocess.run(['node',str(ROOT/'qualification/v4/js-policy/check.mjs')],input=json.dumps(source),capture_output=True,text=True,timeout=5)
    assert p.returncode==0,p.stderr
    return json.loads(p.stdout)


def test_comments_and_strings_are_data_while_effectful_syntax_stays_denied():
    good=fixed['frontend-ui-engineering'][1]
    commented='// process require globalThis are words in a comment\n'+good
    assert not source_allowed('frontend-ui-engineering',{'reducer.js':commented})
    assert check(commented)['allowed'] and not check(commented)['execution_authority']
    assert check("module.exports=(s,e)=>({...s,text:'process require'});")['allowed']
    for attack in [
        'module.exports=(s,e)=>process.env;',
        'module.exports=(s,e)=>globalThis;',
        'module.exports=(s,e)=>s["constructor"];',
        'module.exports=(s,e)=>s.constr\\u0075ctor;',
        'module.exports=(s,e)=>({get x(){return s;}});',
        'module.exports=(s,e)=>({...s,x:import("node:fs")});',
        'module.exports=(s,e)=>{while(true){};};',
        'module.exports=(s,e)=>({__proto__:s});',
        'module.exports=(s,e)=>((()=>{}).constructor("return process")());',
        'module.exports=(s,e)=>({...s}); require("fs");']:
        assert not check(attack)['allowed'],attack
