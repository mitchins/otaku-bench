"""Offline contract tests for OtakuBench v2. No inference or paid judge calls."""
import json, sys, subprocess
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
sys.path.insert(0,str(ROOT/'benchmark/otakubench/tools'))
import judge,run_translations,calibrate_judge,aggregate
import importlib.util
spec=importlib.util.spec_from_file_location('otakubench_builder_under_test',ROOT/'benchmark/otakubench/tools/build.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
check,load=builder.check,builder.load

SRC=ROOT/'benchmark/otakubench/data'

def test_gold_cardinality_and_stable_ids():
    lines=load(SRC/'items/lines.jsonl');scenes=load(SRC/'scenes/scenes.jsonl')
    check(lines,scenes)
    assert len(lines)==250 and len(scenes)==31
    assert len(set(x['japanese'] for x in lines))==250
    assert Counter(x['difficulty'] for x in lines)=={1:50,2:50,3:50,4:50,5:50}
    assert {x['id'] for x in scenes}=={f'OTB-P{i:03d}' for i in range(1,32)}

def test_editorial_context_does_not_leak_into_translator():
    lines=load(SRC/'items/lines.jsonl')
    blind=load(SRC/'build/lines_bare.jsonl')
    assert all('scene_context' not in row and 'english_reference' not in row and 'translation_note' not in row for row in blind)
    a=SimpleNamespace(prompt_style='chat',dataset='lines',mode='bare',model='local',max_tokens=2048)
    text=json.dumps(run_translations.make_payload(blind[75],a),ensure_ascii=False)
    assert lines[75]['scene_context'] not in text
    assert lines[75]['english_reference'] not in text
    try:run_translations.prompt({'japanese':'こんにちは','scene_context':'declines'},'lines','context')
    except ValueError:pass
    else:raise AssertionError('context leakage accepted')

def test_stable_id_references_and_known_corrections():
    rows={r['id']:r for r in load(SRC/'build/lines_gold.jsonl')}
    assert '戻っております' in rows['JMB-036']['japanese']
    assert '黙っていらっしゃった' in rows['JMB-047']['japanese']
    assert 'even' not in rows['JMB-114']['english_reference'].lower()
    assert 'her ' not in rows['JMB-053']['english_reference'].lower()
    assert 'her ' not in rows['JMB-210']['english_reference'].lower()
    assert any('little' in x for x in rows['JMB-076']['alternate_references'])
    assert any('swordsman' in x for x in [rows['JMB-111']['english_reference']]+rows['JMB-111']['alternate_references'])
    assert all(x['reference_alternates_id_stable'] for x in rows.values())

def test_real_context_not_answer_hints():
    scenes=load(SRC/'scenes/scenes.jsonl')
    assert all(len(x['context_lines'])>=2 for x in scenes)
    cases=load(SRC/'build/scenes_context.jsonl')
    g={x['id']:x for x in scenes}
    for c in cases:
        assert c['preceding_lines']==g[c['id']]['context_lines']
        assert c['japanese']==g[c['id']]['target_japanese']
        assert 'translation_note' not in c and 'english_reference' not in c
    prompt=run_translations.prompt(cases[0],'scenes','context')
    assert cases[0]['preceding_lines'][0] in prompt
    assert cases[0]['japanese'] in prompt
    assert g[cases[0]['id']]['translation_note'] not in prompt

def test_json_judge_strict_parse_and_no_gender_required():
    a={'adequacy':4,'pragmatics':4,'fluency':2,'flags':[],'refusal':False,'gold_uncertain':False,
       'confidence':.8,'evidence':'all entities preserved','acceptable_variant':True}
    assert judge.parse_json(json.dumps(a))['adequacy']==4
    for bad in [dict(a,adequacy=5),dict(a,fluency=True),dict(a,confidence=-.1),dict(a,evidence='')]:
        try:judge.parse_json(json.dumps(bad))
        except ValueError:pass
        else:raise AssertionError('invalid judged output accepted')
    line=judge.gold('lines')['JMB-053']
    data=judge.make_input(line,'That child keeps secrets.','lines','bare')
    assert data['candidate_english'].startswith('That child')
    assert 'scene_context' not in data and 'editorial_translation_trap_note' not in data

def test_reasoning_output_must_not_be_translation():
    assert run_translations.strip_answer('<think>unfinished',None)[0]==''
    assert run_translations.strip_answer('<think>reason</think>Hello.',None)[0]=='Hello.'
    assert run_translations.strip_answer("I cannot translate this violent scene.",None)[1]=='visible refusal'

def test_native_prompts_and_templates_are_not_equivalent():
    r={'japanese':'風の便り'}
    args=SimpleNamespace(prompt_style='seedx',model='a',dataset='lines',mode='bare',max_tokens=2048)
    p=run_translations.make_payload(r,args)
    assert p['prompt'].endswith('風の便り <en>') and 'messages' not in p
    args.prompt_style='cat';p=run_translations.make_payload(r,args)
    assert len(p['messages'])==1 and p['messages'][0]['content'].startswith('Translate the following Japanese text')
    args.prompt_style='hunyuan';p=run_translations.make_payload(r,args)
    assert len(p['messages'])==1 and p['messages'][0]['role']=='user'
    args.prompt_style='chat';p=run_translations.make_payload(r,args)
    assert p['messages'][0]['role']=='system'
    args.prompt_style='translategemma';p=run_translations.make_payload(r,args)
    assert p['messages'][0]['content'][0]['source_lang_code']=='ja'

def test_pairwise_calibration_swaps_and_gates():
    fs=calibrate_judge.fixtures()
    assert len(fs)==24
    for f in fs:
        a,x=calibrate_judge.make_case(f,0)
        b,y=calibrate_judge.make_case(f,1)
        assert x=='A' and y=='B'
        assert a['translation_A']==b['translation_B']
    complete=[{'id':f['id'],'order':order,'expected':expect,'response':{'winner':expect}} for f in fs
              for order,expect in [(0,'A'),(1,'B')]]
    assert calibrate_judge.summarize(complete)['gate']
    fail=complete.copy();fail[0]=dict(fail[0],response={'winner':'B'})
    assert not (calibrate_judge.summarize(fail)['accuracy']==1)
    assert not calibrate_judge.summarize(complete[:10])['gate']

def test_curated50_meets_param_and_lineage_rule():
    models=json.loads((ROOT/'data/otakubench50.json').read_text())['models']
    assert len(models)==len({r['model'] for r in models})==50
    assert [r['rank'] for r in models]==list(range(1,51))
    assert all(.6<=r['total_params_b']<=35 for r in models)
    specialist={'Seed-X-PPO-7B','Qwen3-Swallow-8B-RL-v0.2','Qwen3-Swallow-30B-A3B-RL-v0.2',
                'CAT-Translate-7B','CAT-Translate-3.3B-beta','CAT-Translate-1.4B','CAT-Translate-0.8B','HY-MT1.5-7B','HY-MT1.5-1.8B'}
    assert specialist <= {r['model'] for r in models}
    assert all(not r['runtime_validated'] and not r['translation_quality_measured'] for r in models)
    assert 'PLaMo' in (ROOT/'data/out_of_matrix_specialists.json').read_text()

def test_aggregate_excludes_easy_lines_and_is_calibration_gated():
    refs={r['id']:r for r in load(SRC/'build/lines_gold.jsonl')}
    eval_ids={id_ for id_,r in refs.items() if r['split']=='eval'}
    normal={id_ for id_ in eval_ids if refs[id_]['difficulty']>=2}
    assert len(normal)==160 and len(eval_ids)==200
    good={'id':next(iter(normal)),'score':{'adequacy':4,'pragmatics':4,'fluency':2,'gold_uncertain':False,'flags':[],'refusal':False}}
    stat=aggregate.summarize_one([good],normal,refs,set(),{},.95)
    assert stat['n_expected']==160 and stat['n_scored']==1
    assert not stat['rankable_coverage']
    assert aggregate.ci([10.,10.])==[10.0,10.0]

def test_v2_dry_run_avoid_paid_and_downloads(tmp_path):
    for argv in [
        ['run_translations.py','--model','local-test','--dataset','scenes','--mode','context','--limit','2','--output',str(tmp_path/'r.jsonl')],
        ['judge.py','--responses',str(tmp_path/'mock.jsonl'),'--dataset','lines','--output',str(tmp_path/'j.jsonl')],
        ['calibrate_judge.py','--output',str(tmp_path/'c.jsonl')],
        ['run_matrix_v2.py','--ranks','12-14','--dataset','scenes','--mode','context','--reasoning','on']]:
        if argv[0]=='judge.py':(tmp_path/'mock.jsonl').write_text(json.dumps({'id':'JMB-001','translation':'Go ahead without me','model':'mock','source_sha256':__import__('hashlib').sha256((SRC/'build/lines_bare.jsonl').read_bytes()).hexdigest()})+'\n')
        r=subprocess.run([sys.executable,str(ROOT/'tools'/argv[0])]+argv[1:],capture_output=True,text=True)
        assert r.returncode==0,(r.stdout,r.stderr)
    assert not (tmp_path/'r.jsonl').exists()
    assert not (tmp_path/'j.jsonl').exists()
    assert not (tmp_path/'c.jsonl').exists()
