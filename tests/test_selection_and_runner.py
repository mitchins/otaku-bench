import json, subprocess, sys
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from resolve_ggufs import quant_matches,select_quant_files,group_quant_files,attestation_for_row
from run_benchmark import make_messages,CANARY_INDICES,clean
from run_matrix import cmd_for

CATALOG=json.loads((ROOT/'data'/'candidates.json').read_text())['models']
GOLD=ROOT/'benchmark'/'jpmedia250'/'data'/'build'/'jpmedia250_gold.jsonl'


def test_exact_50_lab_lineage_and_ceiling():
    assert len(CATALOG)==50
    assert len({x['original_repo'] for x in CATALOG})==50
    assert {x['lineage'] for x in CATALOG}<={'original_lab_release','lab_distilled','lab_adaptation'}
    assert min(x['total_params_b'] for x in CATALOG)>=0.6
    assert max(x['total_params_b'] for x in CATALOG)<=35
    assert next(x for x in CATALOG if x['rank']==30)['total_params_b']==8
    assert next(x for x in CATALOG if x['rank']==31)['total_params_b']==5.1


def test_full_dataset_and_no_duplicate_japanese():
    gold=[json.loads(x) for x in GOLD.read_text().splitlines()]
    assert len(gold)==250
    assert len({x['id'] for x in gold})==250
    assert len({x['japanese'] for x in gold})==250
    assert len(CANARY_INDICES)==5
    assert all(0<=i<250 for i in CANARY_INDICES)


def test_quant_match_strict_and_multipart():
    assert quant_matches('Qwen_Qwen3.5-4B-Q4_K_M.gguf','Q4_K_M')
    assert not quant_matches('Qwen-UD-Q4_K_M.gguf','Q4_K_M')
    assert quant_matches('Qwen-UD-Q4_K_M.gguf','UD-Q4_K_M')
    assert quant_matches('mradermacher.27b.Q4_K_M.gguf','Q4_K_M')
    assert not quant_matches('mmproj-Q4_K_M.gguf','Q4_K_M')
    assert not quant_matches('mtp-Q4_K_M.gguf','Q4_K_M')
    data=[{'path':f'Qwen-UD-Q4_K_XL-{n:05d}-of-00002.gguf','size':40} for n in (1,2)]
    assert len(group_quant_files(data,'UD-Q4_K_XL'))==2
    assert group_quant_files(data[:1],'UD-Q4_K_XL') is None


def test_no_implicit_fallback():
    fs=[{'path':'Qwen-UD-Q4_K_XL.gguf','size':500}]
    assert select_quant_files(fs,'UD-Q4_K_M')==(None,None,False)
    chosen,q,fallback=select_quant_files(fs,'UD-Q4_K_M',allow_fallback=True)
    assert q=='UD-Q4_K_XL' and fallback is True and chosen==fs


def test_fake_hf_attestation_records_real_filename_and_commit():
    fake=SimpleNamespace(sha='a'*40,downloads=1234,siblings=[
        SimpleNamespace(rfilename='Qwen_Qwen3.5-4B-Q4_K_M.gguf',size=3_010_000_000),
        SimpleNamespace(rfilename='mmproj-Q4_K_M.gguf',size=450_000_000)])
    class API:
        def model_info(self,repo,files_metadata):
            assert files_metadata
            return fake
    row=CATALOG[11]
    out=attestation_for_row(row,API())
    assert out['repro_status']=='HUB_QUANT_ATTESTED'
    assert out['quant_size_gb']==3.01
    assert out['quant_file']=='Qwen_Qwen3.5-4B-Q4_K_M.gguf'
    assert 'blob/'+'a'*40+'/' in out['exact_file_url']
    assert out['model_repo_sha']=='a'*40


def test_native_translation_prompt_and_context_refusal():
    case={'japanese':'風の便り','scene_context':'Overheard through a friend'}
    msgs=make_messages(case,'translategemma','bare')
    assert len(msgs)==1 and len(msgs[0]['content'])==1
    assert msgs[0]['content'][0]['source_lang_code']=='ja'
    assert msgs[0]['content'][0]['target_lang_code']=='en'
    import pytest
    with pytest.raises(ValueError):make_messages(case,'translategemma','context')
    assert make_messages(case,'chat','context')[1]['content'].find('Overheard')>0


def test_clean_removes_reasoning_and_refuses_unclosed():
    assert clean('<think>secret</think>Correct translation')=='Correct translation'
    assert clean('<think>incomplete')==''


def test_matrix_argv_uses_publisher_quant_not_forced_q4():
    args=SimpleNamespace(llama_server=Path('llama-server'),port=8125,ctx_size=4096,gpu_layers=99)
    cmd=cmd_for(CATALOG[0],args)
    assert 'unsloth/Qwen3.8-27B-GGUF:UD-Q4_K_M' in cmd
    assert 'bartowski/openai_gpt-oss-20b-GGUF:Q4_K_M' in cmd_for(CATALOG[22],args)[2]


def test_cli_dry_run_and_matrix():
    subprocess.run([sys.executable,str(ROOT/'tools'/'run_benchmark.py'),'--canary',
        '--prompt-style','translategemma','--output','/tmp/dont_write.jsonl','--dry-run'],check=True,
        stdout=subprocess.DEVNULL)
    subprocess.run([sys.executable,str(ROOT/'tools'/'run_matrix.py'),'--ranks','1,12'],
        check=True,stdout=subprocess.DEVNULL)


def test_translategemma_text_renders_ja_to_en():
    from types import SimpleNamespace
    import run_translations
    p=run_translations.make_payload({'japanese':'先に行ってて。'},SimpleNamespace(prompt_style='translategemma_text',dataset='lines',mode='bare',max_tokens=64,model='x'))
    assert 'Japanese (ja) to English (en)' in p['prompt'] and 'en-GB' not in p['prompt']
    assert p['prompt'].endswith('先に行ってて。<end_of_turn>\n<start_of_turn>model\n')


def test_reasoning_markup_is_stripped_across_families():
    import run_translations as rt
    cases = {'draft</think>final': 'final', '<think>x</think>ok': 'ok', '<thinking>a</thinking>B': 'B',
             '[THINK]plan[/THINK]Done.': 'Done.', '<seed:think>x</seed:think>Y': 'Y',
             '<|channel|>analysis<|message|>plan<|end|><|start|>assistant<|channel|>final<|message|>Hello.<|return|>': 'Hello.'}
    for raw, want in cases.items():
        assert rt.strip_answer(raw, None) == (want, None)
    assert rt.strip_answer('<think>still going', None)[1] == 'unclosed thinking'


def test_mechanical_zeros_and_compliance_flags():
    import mechanical as mech
    src = '【澪】「鍵を預かったのは、昨日の夕方よ。」'
    assert mech.zero_reason(src, '【Mio】「鍵を預かったのは、昨日の夕方よ。」', None) == 'exact_echo'  # tag translated, body not
    assert mech.zero_reason(src, '【Mio】"I took the key yesterday evening."', None) is None
    assert mech.zero_reason(src, '', None) == 'inference_failure'
    assert mech.zero_reason(src, 'x', 'hit 256-token cap') == 'inference_failure'
    assert mech.flags('もういい。', 'Forget it.\n\n*(Note: dismissive tone)*') == ['commentary', 'format']
    assert mech.flags('雨だ。', 'It is raining.\n\nOr, more naturally: It’s raining.') == ['commentary']
    # a translation that itself begins with "Or" is not commentary (JMB-234: 気のせいだろうか)
    assert mech.flags('好感度が上がった音がした。気のせいだろうか。', 'A warm chime.\n(Or maybe just my imagination.)') == []
    assert mech.flags('【健】「もう帰るん？」', 'Ken: "Going home already?"') == ['format']
