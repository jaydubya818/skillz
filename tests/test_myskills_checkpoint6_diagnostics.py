import json
from pathlib import Path

import pytest

from myskills.manifest import ValidationError
from qualification.checkpoint_four import unseal
from qualification.v5.cases import CASES


def test_divergent_evaluation_is_retained_before_legacy_failure(tmp_path, monkeypatch):
    from qualification import replay_checkpoint6_diagnostics as observer
    name = 'api-and-interface-design--follow-up'
    expected = {'status': 'PASS', 'evidence': {'final': {'exit_code': 0}}}
    actual = {'status': 'FAIL', 'evidence': {'final': {'exit_code': 1, 'stderr': 'database is locked'}}}
    folder = tmp_path/name
    folder.mkdir()
    (folder/'observation.json').write_text(json.dumps({'verification': expected, 'evidence_digest': 'retained-observation'}))
    evaluate = lambda *args, **kwargs: actual
    monkeypatch.setattr(observer.legacy, 'evaluate', evaluate)
    def fail(*args):
        assert observer.legacy.evaluate(CASES[name], {'api.py': 'source'}, [], {}, True) is actual
        raise ValidationError('follow-up frozen evaluation differs')
    monkeypatch.setattr(observer.checkpoint, 'report', fail)
    with pytest.raises(ValidationError, match='frozen evaluation differs'):
        observer.replay(Path.cwd(), tmp_path, tmp_path/'result')
    report = json.loads((tmp_path/'result/diagnostics.json').read_text())
    unseal(report)
    row = report['evaluations'][0]
    assert row['case'] == name
    assert row['expected'] == expected
    assert row['actual'] == actual
    assert row['matches_frozen'] is False
    assert '/evidence/final/exit_code' in row['differing_paths']
    assert report['outcome'] == 'FAIL' and report['qualification_credit'] is False
    assert observer.legacy.evaluate is evaluate


def test_execution_error_is_not_classified_as_a_model_verdict(tmp_path, monkeypatch):
    from qualification import replay_checkpoint6_diagnostics as observer
    def broken(*args, **kwargs):
        raise OSError('fixture infrastructure failed')
    monkeypatch.setattr(observer.legacy, 'evaluate', broken)
    monkeypatch.setattr(observer.checkpoint, 'report', lambda *args: observer.legacy.evaluate(CASES['api-and-interface-design--follow-up'], {}, [], {}, False))
    with pytest.raises(OSError, match='infrastructure'):
        observer.replay(Path.cwd(), tmp_path, tmp_path/'result')
    row = json.loads((tmp_path/'result/diagnostics.json').read_text())['evaluations'][0]
    assert row['state'] == 'RAISED'
    assert 'actual' not in row
    assert observer.legacy.evaluate is broken


def test_final_checkpoint_gates_remain_fail_closed(tmp_path):
    from qualification import replay_checkpoint6_diagnostics as observer
    with pytest.raises(ValidationError, match='retained claim regression'):
        observer.enforce({'ledgers': {'api': {'retained_failure_regressions': [{'status': 'FAIL'}]}}, 'matrix': []})
    with pytest.raises(ValidationError, match='bounded behavioral'):
        observer.enforce({'ledgers': {}, 'matrix': [{'functional_tests': 'FAIL'}]})
