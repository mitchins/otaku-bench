"""Offline v3 model-admission, provenance, quant, and native-prompt checks."""
import copy
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from resolve_ggufs import attestation_for_row, group_quant_files, quant_matches
from run_translations import make_payload

MODEL = json.loads((ROOT / 'data/otakubench50.json').read_text(encoding='utf-8'))
V2 = json.loads((ROOT / 'data/otakubench50_v2.json').read_text(encoding='utf-8'))
V3 = json.loads((ROOT / 'data/otakubench50_v3.json').read_text(encoding='utf-8'))
V4_DELTA = json.loads((ROOT / 'data/model_selection_delta_v4.json').read_text(encoding='utf-8'))
BY = {r['model']: r for r in MODEL['models']}
DELTA = json.loads((ROOT / 'data/model_selection_delta_v3.json').read_text(encoding='utf-8'))


def test_count_and_selection_delta():
    current = set(BY)
    before = {r['model'] for r in V3['models']}
    assert len(MODEL['models']) == 50 == len(current)
    assert [r['rank'] for r in MODEL['models']] == list(range(1, 51))
    assert len(DELTA['added']) == len(DELTA['removed']) == 12
    assert current - before == set(V4_DELTA['added_v4'])
    assert before - current == set(V4_DELTA['removed_v4'])
    assert len({r['original_repo'] for r in MODEL['models']}) == 50


def test_eligibility_and_documented_domain_exception():
    allowed = {'lab_original_or_existing_v2_specialist','first_party_japanese',
               'heavy_adaptation','large_sft_rl','lab_distillation','domain_exception'}
    assert all(.6 <= r['total_params_b'] <= 35 for r in MODEL['models'])
    assert all(r['eligibility_lane'] in allowed for r in MODEL['models'])
    assert {r['model'] for r in MODEL['models'] if r['eligibility_lane'] == 'domain_exception'} == {
        'VNTL-Llama3-8B-v2', 'Sugoi-14B-Ultra', 'Sugoi-32B-Ultra'}
    assert all(r['eligibility_evidence_url'].startswith('https://huggingface.co/') for r in MODEL['models'])
    for name in ('Qwen3-8B','gpt-oss-20b','LFM2.5-1.2B Instruct'):
        assert name in BY  # base controls to test gains from adaptations
    assert all(not r['runtime_validated'] and not r['translation_quality_measured'] for r in MODEL['models'])


def test_exact_added_quant_files_and_publisher_separation():
    added = [BY[x['model']] for x in DELTA['added']]
    assert len({(x['quant_repo'], x['quant_file']) for x in added}) == 12
    for row in added:
        assert row['quant_file'].endswith('.gguf')
        assert quant_matches(row['quant_file'], row['preferred_quant'])
        assert row['quant_repo'] in row['exact_file_url']
        assert row['quant_file'] in row['exact_file_url']
        assert row['original_repo'] in row['original_url']
        assert row['model_repo_sha'] is None
        assert not row['repro_status'].startswith('HUB_QUANT_ATTESTED')
        assert row['quant_size_gb'] > 0
    assert BY['TinySwallow-1.5B-Instruct']['preferred_quant'] == 'Q5_K_M'
    assert BY['VNTL-Llama3-8B-v2']['preferred_quant'] == 'Q5_K_M'
    assert BY['LFM2.5-1.2B-JP-202606']['quant_publisher'] == 'LiquidAI'
    assert BY['Sugoi-14B-Ultra']['quant_publisher'] == 'sugoitoolkit'
    assert BY['Qwen3-Swallow-32B-RL-v0.2']['quant_publisher'] == 'ultimatechris'


def test_deck_flag_is_file_size_proxy_only():
    assert all(r['deck_default_candidate'] == ((r.get('quant_size_gb') or r.get('listed_size_gb')) is not None
                  and (r.get('quant_size_gb') or r.get('listed_size_gb')) <= 9.0) for r in MODEL['models'])
    assert all('not proven' in r['deck_note'].lower() for r in MODEL['models']
               if r['deck_default_candidate'])
    assert not BY['Sugoi-32B-Ultra']['deck_default_candidate']
    assert BY['Sugoi-14B-Ultra']['deck_default_candidate']


def test_native_vntl_prompt_and_sugoi_including_bare_multiline():
    args = SimpleNamespace(prompt_style='vntl',dataset='lines',mode='bare',max_tokens=512,model='unit-model')
    case = {'japanese': '……お兄ちゃん。\n今日は帰らないの？'}
    p = make_payload(case,args)
    assert 'messages' not in p
    assert p['prompt'].startswith('<|start_header_id|>Japanese')
    assert '<|begin_of_text|>' not in p['prompt']
    assert '……お兄ちゃん。\n今日は帰らないの？' in p['prompt']
    assert p['prompt'].endswith('<|start_header_id|>English<|end_header_id|>\n\n')
    assert p['stop'] == ['<|eot_id|>']
    args.dataset = 'scenes'  # v2 VNTL card explicitly documents multi-line support
    assert make_payload(case,args)['prompt'] == p['prompt']
    args.mode = 'full'
    assert 'Japanese' in make_payload(case,args)['prompt']
    args.mode = 'context'
    with pytest.raises(ValueError): make_payload(case,args)
    args.prompt_style = 'sugoi'
    args.mode = 'bare'
    p = make_payload(case,args)
    assert p['messages'][0]['role']=='system'
    assert 'localizer' in p['messages'][0]['content']
    assert p['messages'][1]['role']=='user'
    assert p['temperature']==.1 and p['repeat_penalty']==1.1


def test_fake_hf_parent_mismatch_is_not_trusted():
    fake = SimpleNamespace(sha='c'*40, downloads=12,
        card_data={'base_model':'rinna/llama-3-youko-8b'},
        siblings=[SimpleNamespace(rfilename=BY['VNTL-Llama3-8B-v2']['quant_file'], size=5730000000)])
    class FakeApi:
        def model_info(self, name, files_metadata):
            assert files_metadata
            return fake
    out = attestation_for_row(BY['VNTL-Llama3-8B-v2'], FakeApi())
    assert out['repro_status'] == 'HUB_QUANT_ATTESTED_PARENT_REVIEW_PENDING'
    assert out['model_repo_sha'] == 'c'*40
    assert out['lineage_attestation'] == 'upstream_ancestry_or_mismatch_requires_review'


def test_matching_parent_hf_metadata_does_not_claim_runtime_pass():
    model=BY['Sugoi-14B-Ultra']
    fake=SimpleNamespace(sha='a'*40, downloads=100,
       card_data={'base_model':model['original_repo']},
       siblings=[SimpleNamespace(rfilename=model['quant_file'], size=8990000000)])
    class Api:
        def model_info(self, *_args, **_kwargs):
            return fake
    out=attestation_for_row(model, Api())
    assert out['repro_status']=='HUB_QUANT_ATTESTED'
    assert out['lineage_attestation']=='publisher_declared'
    assert not out['runtime_validated']


def test_runner_default_catalog_and_strict_execution_block(tmp_path):
    cmd = [sys.executable,str(ROOT/'tools/run_matrix_v2.py'), '--ranks','18-21',
           '--device','deck','--dataset','lines','--mode','bare','--reasoning','off',
           '--output-dir',str(tmp_path)]
    p=subprocess.run(cmd,text=True,capture_output=True,check=True)
    assert 'TinySwallow-1.5B-Instruct' in p.stdout
    assert 'VNTL-Llama3-8B-v2' in p.stdout
    assert '"style": "vntl"' in p.stdout
    assert '"quant": "Q5_K_M"' in p.stdout
    assert not list(tmp_path.iterdir())  # no downloads or outputs on preview
    p=subprocess.run(cmd+['--execute'],text=True,capture_output=True,check=True)
    assert p.stdout.count('BLOCKED_UNATTESTED')==4
    assert not list(tmp_path.iterdir())


def test_v3_generator_does_not_overwrite_active_v4(tmp_path):
    p=ROOT/'tools/curate_50_v3.py'
    existing=(ROOT/'data/otakubench50.json').read_bytes()
    a=subprocess.run([sys.executable,str(p)],text=True,capture_output=True)
    assert a.returncode != 0
    assert 'legacy' in (a.stderr+a.stdout).lower()
    assert existing==(ROOT/'data/otakubench50.json').read_bytes()
