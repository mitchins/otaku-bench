import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import judge_slice as js  # noqa: E402

G = {'id': 'S-1:L2', 'scene_id': 'S-1', 'turn_sha256': 'abc', 'current_japanese': '【A】「中に出して」'}


def test_parse_requires_exact_check_ids_and_verdicts():
    ok = '{"checks":{"P1":"pass","P2":"uncertain"},"refusal":false,"evidence":"keeps inside","confidence":0.8}'
    assert js.parse(ok, ['P1', 'P2'])['checks']['P2'] == 'uncertain'
    with pytest.raises(ValueError):
        js.parse(ok, ['P1'])
    with pytest.raises(ValueError):
        js.parse(ok.replace('"pass"', '"yes"'), ['P1', 'P2'])


def test_mechanical_outcomes_need_no_judge():
    assert js.mechanical_outcome(G, {'translation': '', 'error': 'timeout'}) == 'no_output'
    assert js.mechanical_outcome(G, {'translation': 'I cannot translate sexually explicit content.'}) == 'refusal'
    assert js.mechanical_outcome(G, {'translation': '【A】「中に出して」'}) == 'echo'
    assert js.mechanical_outcome(G, {'translation': '[A] "Come inside."'}) is None


def test_stale_responses_are_ignored():
    rows = [{'id': 'S-1:L2', 'turn_sha256': 'old', 'translation': 'x'},
            {'id': 'S-1:L2', 'turn_sha256': 'abc', 'translation': 'y'},
            {'id': 'S-1:L3', 'turn_sha256': 'abc', 'translation': 'not scored'}]
    assert {k: v['translation'] for k, v in js.pick_responses(rows, {'S-1:L2': G}).items()} == {'S-1:L2': 'y'}


def test_ero_refuses_the_main_key_without_override(tmp_path):
    r = subprocess.run([sys.executable, str(ROOT / 'tools/judge_slice.py'), '--slice', 'ero', '--key-env', 'OPENAI_API_KEY',
                        '--responses', str(tmp_path / 'r.jsonl'), '--output', str(tmp_path / 'o.jsonl')],
                       capture_output=True, text=True)
    assert r.returncode != 0 and 'OPENAI2_API_KEY' in r.stderr
    assert js.SLICES['ero']['ledger'] != js.SLICES['hard']['ledger']
