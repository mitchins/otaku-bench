"""Tests for the read-only scoring sensitivity report."""
import importlib.util
import json
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'mission' / 'score_sensitivity.py'
spec = importlib.util.spec_from_file_location('score_sensitivity', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def score(a, p, f):
    return {'adequacy': a, 'pragmatics': p, 'fluency': f,
            'flags': [], 'refusal': False}


def test_gated_score_guarantees():
    assert mod.gated_nuance(score(4, 4, 2)) == 10
    assert mod.gated_nuance(score(4, 3, 2)) == 8
    assert mod.gated_nuance(score(3, 4, 2)) == 7.5
    assert mod.gated_nuance(score(2, 4, 2)) == 5
    assert mod.gated_nuance(score(4, 4, 1)) == 9
    assert mod.gated_nuance(score(0, 4, 2)) == 0


def test_stale_gold_and_partial_are_explicit(tmp_path):
    refs = {'JMB-001': {'id': 'JMB-001', 'split': 'eval'},
            'JMB-002': {'id': 'JMB-002', 'split': 'eval'}}
    correct = {'id': 'JMB-001', 'dataset': 'lines', 'mode': 'bare',
               'score': score(4, 3, 2),
               'gold_sha256': mod.gold_digest(refs['JMB-001'])}
    stale = {'id': 'JMB-002', 'dataset': 'lines', 'mode': 'bare',
             'score': score(4, 4, 2), 'gold_sha256': 'outdated'}
    f = tmp_path / 'model.lines_eval.jsonl'
    f.write_text('\n'.join(map(json.dumps, [correct, stale])) + '\n',
                 encoding='utf-8')
    result = mod.summarize(f, refs)
    assert result['status'] == 'PARTIAL'
    assert result['scored'] == 1 and result['expected'] == 2
    assert result['raw'] == 9 and result['gated'] == 8
    assert result['stale_rejected'] == 1
