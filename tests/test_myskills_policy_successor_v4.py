from qualification.policy_successor_v4 import tdd_source_allowed,denied_authority
from qualification.v4.source_policy import permitted


def test_inert_docstrings_do_not_grant_executable_test_setup():
    test='import unittest\nfrom clamp import clamp\nclass TestClamp(unittest.TestCase):\n def test_boundary(self):\n  """Boundary regression."""\n  self.assertEqual(clamp(12,0,10),10)\n'
    files={'clamp.py':'def clamp(value,low,high): return min(max(low,value),high)','test_clamp.py':test}
    assert not permitted('tdd',files)  # Frozen failure stays reproducible.
    assert tdd_source_allowed(files)
    assert not tdd_source_allowed({**files,'test_clamp.py':test.replace('"""Boundary regression."""','print("forged")')})
    assert not tdd_source_allowed({**files,'test_clamp.py':test+'print("forged")\n'})
    assert not denied_authority('NOT_FOUND')
    assert denied_authority('EFFECT_DENIED') and denied_authority('CONTAINMENT_FAILURE')


def test_sqlite_integrity_error_handler_is_data_not_extension_authority():
    from qualification.policy_successor_v4 import api_source_allowed
    source='import sqlite3\ndef handle(a,b,c):\n try: return sqlite3.connect(c)\n except sqlite3.IntegrityError: return None\n'
    assert not permitted('api-and-interface-design',{'api.py':source})
    assert api_source_allowed({'api.py':source})
    assert not api_source_allowed({'api.py':source.replace('IntegrityError','enable_load_extension')})
    assert not api_source_allowed({'api.py':source+'\ndef bad(): return sqlite3.enable_load_extension(True)\n'})
