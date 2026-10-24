"""Regression tests for v4: bug fix, source hashes, lineage and scene protocol."""
import hashlib,json,subprocess,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import judge,paired_stats,run_translations,aggregate
from context_gain import index

def read(path):return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
GOLD=ROOT/'benchmark/otakubench/data/build'

def test_source_counts_and_hook_noise_vs_stammer():
    lines=read(GOLD/'lines_gold.jsonl');scenes={r['id']:r for r in read(GOLD/'scenes_gold.jsonl')}
    assert len(lines)==250 and len(scenes)==31
    assert 'ご存じだったのなら' in next(r for r in lines if r['id']=='JMB-047')['japanese']
    assert len(next(r for r in lines if r['id']=='JMB-093')['alternate_references'])>=3
    assert 'ただいま' not in next(r for r in lines if r['id']=='JMB-199')['japanese']
    assert scenes['OTB-P005']['target_japanese'].endswith('あの日だけは笑って見られない。」')
    for i in ('OTB-P009','OTB-P025'):
        g=scenes[i];assert 'duplicate' in ' '.join(g['hook_artifacts'])
        assert len(g['contextual_japanese_lines'])==4
        assert len(g['full_english_reference'].splitlines())==3
    assert 'まだ\nまだ' in scenes['OTB-P025']['full_japanese']
    assert 'セックス' in scenes['OTB-P019']['target_japanese']
    assert '内臓' in scenes['OTB-P020']['target_japanese']
    assert 'ほざくな' in scenes['OTB-P021']['target_japanese']
    assert '犬が居ぬ' in scenes['OTB-P031']['target_japanese']
    assert 'everyone understands' in scenes['OTB-P029']['english_reference']

def test_native_vntl_prompt_no_bos_and_metadata():
    case={'japanese':'【澪】「私じゃない。」\n【透】「確かか？」'}
    a=SimpleNamespace(prompt_style='vntl',mode='full',dataset='scenes',model='test',max_tokens=2048)
    text=run_translations.make_payload(case,a)['prompt']
    assert text.startswith('<|start_header_id|>Metadata')
    assert '[character] Name: 澪' in text and '[character] Name: 透' in text
    assert '[澪]: ' in text and '[透]: ' in text
    assert '<|begin_of_text|>' not in text
    assert text.endswith('<|start_header_id|>English<|end_header_id|>\n\n')

def test_non_chat_ancestor_control_is_explicitly_diagnostic():
    row=next(r for r in json.loads((ROOT/'data/otakubench50.json').read_text())['models'] if r['model']=='rinna-llama-3-youko-8b')
    assert row['evaluation_role']=='ancestor_diagnostic_only' and row['prompt_style']=='base_completion'
    a=SimpleNamespace(prompt_style='base_completion',mode='bare',dataset='lines',model='test',max_tokens=512)
    p=run_translations.make_payload({'japanese':'どうして？'},a)
    assert 'English: It is raining.' in p['prompt']
    assert p['prompt'].endswith('どうして？\nEnglish:')

def test_current_lineage_control_pairs_and_recency():
    models=json.loads((ROOT/'data/otakubench50.json').read_text())['models']
    by={r['model']:r for r in models}
    assert len(by)==50
    for x in ('Hunyuan-MT-7B','RakutenAI-7B-instruct','Qwen2.5-7B Instruct'):assert x not in by
    for x in ('rinna-llama-3-youko-8b','Phi-4 14B','Qwen3-4B-Instruct-2507','Qwen2.5-14B-Instruct','Llama-3.2-3B-Instruct'):assert x in by
    assert by['VNTL-Llama3-8B-v2']['quant_repo'].startswith('lmg-anon/')
    assert by['Phi-4 14B']['quant_file']=='phi-4-Q4_K_M.gguf'
    assert not any(r['runtime_validated'] for r in models)

def test_paired_bootstrap_detects_consistent_gain_and_no_fake_precision():
    expected=set(range(30));a={i:10 for i in expected};b={i:8 for i in expected}
    d=paired_stats.paired_delta(a,b,expected,reps=500)
    assert d['shared_items']==30 and d['paired_bootstrap_95_ci']==[2.0,2.0]
    assert d['interval_excludes_zero'] and d['mean_delta_a_minus_b']==2
    same=paired_stats.paired_delta(a,a,expected,reps=500)
    assert not same['interval_excludes_zero'] and same['win_rate_a']==0

def test_gold_uncertain_is_per_arm_not_global(tmp_path):
    refs=aggregate.get_gold('lines','eval')
    id_=next(i for i,r in refs.items() if r['difficulty']>=2)
    scores={'adequacy':4,'pragmatics':4,'fluency':2,'flags':[],'gold_uncertain':False,'refusal':False}
    rows=[]
    for arm,flag in [('model-a',True),('model-b',False)]:
        rows.append({'id':id_,'model':'gpt-6.1-sol','candidate_model':arm,'run_id':arm,
          'dataset':'lines','mode':'bare','gold_sha256':judge.sha(refs[id_]),'annotated':False,
          'score':dict(scores,gold_uncertain=flag)})
    path=tmp_path/'judge.jsonl';path.write_text(''.join(json.dumps(r)+'\n' for r in rows))
    cmd=[sys.executable,str(ROOT/'tools/aggregate.py'),'--judgments',str(path),'--dataset','lines','--mode','bare','--split','eval']
    result=json.loads(subprocess.check_output(cmd,text=True))
    assert result['global_gold_uncertain_excluded']==[]
    by={r['run_id']:r for r in result['results']}
    assert by['model-a']['n_scored']==0 and by['model-b']['n_scored']==1
    assert result['min_scored_items_for_publishable_rank']==100

def test_paired_context_gain_requires_same_gold_and_run():
    refs={r['id']:r for r in read(GOLD/'scenes_gold.jsonl')}
    g=refs['OTB-P001']
    score={'adequacy':4,'pragmatics':4,'fluency':2,'gold_uncertain':False}
    base={'id':'OTB-P001','dataset':'scenes','model':'gpt-6.1-sol','run_id':'base','gold_sha256':judge.sha(g),'score':score}
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as folder:
        path=Path(folder)/'samples.jsonl';path.write_text(json.dumps(dict(base,mode='bare'))+'\n'+json.dumps(dict(base,mode='context'))+'\n')
        bare=index([path],'bare','gpt-6.1-sol','dev',refs)
        ctx=index([path],'context','gpt-6.1-sol','dev',refs)
        assert bare==ctx=={'base':{'OTB-P001':10}}

def test_judge_rejects_stale_or_unfingerprinted_output(tmp_path):
    path=tmp_path/'inference.jsonl';path.write_text(json.dumps({'id':'JMB-001','model':'test','translation':'Hello','mode':'bare','dataset':'lines','source_sha256':'old'} )+'\n')
    cmd=[sys.executable,str(ROOT/'tools/judge.py'),'--responses',str(path),'--dataset','lines','--mode','bare','--output',str(tmp_path/'none.jsonl')]
    res=subprocess.run(cmd,text=True,capture_output=True)
    assert res.returncode!=0 and 'source_sha256' in res.stderr
    assert not (tmp_path/'none.jsonl').exists()

def test_scenes_not_published_with_only_25_eval_examples():
    refs=aggregate.get_gold('scenes','eval');assert len(refs)==25
    # Publishing gate is audited, calibrated, coverage AND >=60 scored scene items.
    s=ROOT/'tools/aggregate.py'
    assert "100 if args.dataset=='lines' else 60" in s.read_text()

def test_hearsay_challenge_not_wind_chime():
    g=next(r for r in read(GOLD/'lines_gold.jsonl') if r['id']=='JMB-073')
    assert '風の便り' in g['japanese']
    assert 'wind chime' not in ' '.join([g['english_reference'],*g['alternate_references']]).lower()
    assert any('grapevine' in x or 'indirectly' in x for x in g['alternate_references'])


def test_reconciliation_is_idempotent_and_legacy_docs_preserved():
    p=ROOT/'data/otakubench50.json';before=p.read_bytes()
    q=subprocess.run([sys.executable,str(ROOT/'tools/reconcile_catalog_v4.py')],capture_output=True,text=True)
    assert q.returncode==0,q.stderr
    assert p.read_bytes()==before
    assert (ROOT/'CATALOG_V3.md').exists()


def test_base_completion_api_response_parsed_not_chat(monkeypatch,tmp_path):
    import io
    class MockResp:
        def __init__(self,data):self.data=data
        def __enter__(self):return self
        def __exit__(self,*args):return False
        def read(self,*args):return self.data.read(*args)
    urls=[]
    def fake_urlopen(request,timeout=180):
        urls.append(request.full_url)
        return MockResp(io.BytesIO(json.dumps({'choices':[{'text':'Welcome back.','finish_reason':'stop'}],
            'usage':{'completion_tokens':4}}).encode()))
    monkeypatch.setattr(run_translations,'urlopen',fake_urlopen)
    outfile=tmp_path/'responses.jsonl'
    monkeypatch.setattr(sys,'argv',['run_translations.py','--model','base','--prompt-style','base_completion',
        '--dataset','lines','--mode','bare','--limit','1','--output',str(outfile),'--execute'])
    assert run_translations.main()==0
    records=read(outfile)
    assert len(records)==1 and records[0]['translation']=='Welcome back.' and not records[0]['error']
    assert urls==['http://127.0.0.1:8125/v1/completions']


def test_model_pilot_ranks_are_deck_file_size_proxy_not_runtime_proof():
    rows=json.loads((ROOT/'data/otakubench50.json').read_text())['models']
    for rank in (15,18,19,20,31,46):
        assert rows[rank-1]['deck_default_candidate']
    assert rows[31]['model']=='TranslateGemma 27B IT' and not rows[31]['deck_default_candidate']

def test_provenance_cannot_publish_unattested_or_uncanaried_runs(tmp_path):
    refs=aggregate.get_gold('lines','dev');ids=[i for i,g in refs.items() if g['difficulty']>=2]
    s={'adequacy':4,'pragmatics':4,'fluency':2,'flags':[],'gold_uncertain':False,'refusal':False}
    records=[]
    for arm,attested,canary in [('uncertified',False,False),('sha_only',True,False),('pinned_plus_canary',True,True)]:
        for id_ in ids:
            records.append({'id':id_,'model':'gpt-6.1-sol','run_id':arm,'candidate_model':arm,
                'dataset':'lines','mode':'bare','gold_sha256':judge.sha(refs[id_]),
                'annotated':False,'score':s,'quant_attested':attested,'canary_passed':canary,
                'quant_repo_sha':'a'*40})
    f=tmp_path/'judge.jsonl';f.write_text(''.join(json.dumps(x)+'\n' for x in records))
    cmd=[sys.executable,str(ROOT/'tools/aggregate.py'),'--judgments',str(f),'--dataset','lines',
        '--mode','bare','--split','dev','--bootstrap-reps','100']
    report=json.loads(subprocess.check_output(cmd,text=True))
    arms={r['run_id']:r for r in report['results']}
    assert not arms['uncertified']['attested_canary_provenance']
    assert not arms['sha_only']['attested_canary_provenance']
    assert arms['pinned_plus_canary']['attested_canary_provenance']
    assert all(not r['publishable_rank'] for r in arms.values())  # dev sample size floor
    assert report['compare_pairs_mode']=='adjacent'
    assert len(report['pairwise_comparisons'])==2


def test_gold_auditors_must_come_from_distinct_providers(tmp_path):
    refs=aggregate.get_gold('lines','dev');expected=[i for i,g in refs.items() if g['difficulty']>=2]
    # Two independent model IDs both on OpenAI still do NOT qualify as
    # two independent providers; mixing in Anthropic then does.
    base=[]
    for provider,model in (('openai','modelA'),('openai','modelB')):
        for id_ in expected:
            base.append({'dataset':'lines','id':id_,'provider':provider,'model':model,
                'gold_sha256':judge.sha(refs[id_]),'finding':{'severity':'none'}})
    f=tmp_path/'audits.jsonl';f.write_text(''.join(json.dumps(x)+'\n' for x in base))
    j=tmp_path/'empty_judge.jsonl';j.write_text('')
    cmd=[sys.executable,str(ROOT/'tools/aggregate.py'),'--judgments',str(j),
        '--gold-audits',str(f),'--dataset','lines','--split','dev']
    report=json.loads(subprocess.check_output(cmd,text=True))
    assert not report['gold_audit']['gate']
    assert report['gold_audit']['two_independent_audits_for']==0
    for id_ in expected:
        base.append({'dataset':'lines','id':id_,'provider':'anthropic','model':'modelC',
            'gold_sha256':judge.sha(refs[id_]),'finding':{'severity':'none'}})
    f.write_text(''.join(json.dumps(x)+'\n' for x in base))
    report=json.loads(subprocess.check_output(cmd,text=True))
    assert report['gold_audit']['gate']
    assert report['gold_audit']['two_independent_audits_for']==len(expected)


def test_identical_translations_are_judged_once(monkeypatch,tmp_path):
    calls=[]
    def fake_api(*a,**k):
        calls.append(a[3]['candidate_english'])
        score={'adequacy':4,'pragmatics':3,'fluency':2,'flags':[],'refusal':False,'gold_uncertain':False,
               'confidence':0.9,'evidence':'ok','acceptable_variant':False}
        return json.dumps(score),{},{'input_tokens':500,'output_tokens':50,'estimated_standard_usd_excluding_cache_write':0.0},'stop'
    monkeypatch.setattr(judge,'api_request',fake_api)
    src=hashlib.sha256((GOLD/'lines_bare.jsonl').read_bytes()).hexdigest()
    out=tmp_path/'judge'
    def run(model,text):
        resp=tmp_path/f'{model}.jsonl'
        resp.write_text(json.dumps({'id':'JMB-053','model':model,'translation':text,'source_sha256':src})+'\n')
        monkeypatch.setattr(sys,'argv',['judge.py','--responses',str(resp),'--dataset','lines','--output',str(out/f'{model}.lines_eval.jsonl'),
                                        '--ledger',str(tmp_path/'ledger.jsonl'),'--execute'])
        assert judge.main()==0
        return read(out/f'{model}.lines_eval.jsonl')
    out.mkdir()
    a=run('A','That child keeps secrets.')
    b=run('B','That child keeps secrets.')
    c=run('C','That kid has secrets.')
    assert calls==['That child keeps secrets.','That kid has secrets.']  # B made no call
    assert b[0]['reused_from']==a[0]['key'] and b[0]['score']==a[0]['score'] and b[0]['candidate_model']=='B'
    assert 'reused_from' not in c[0] and len(read(tmp_path/'ledger.jsonl'))==2
    assert run('B','That child keeps secrets.')==b  # idempotent: nothing new on rerun


def test_backfilled_content_key_matches_and_refuses_changed_inputs(monkeypatch,tmp_path):
    import backfill_content_keys as bf
    monkeypatch.setattr(judge,'api_request',lambda *a,**k:(json.dumps({'adequacy':4,'pragmatics':4,'fluency':2,'flags':[],'refusal':False,
        'gold_uncertain':False,'confidence':0.9,'evidence':'ok','acceptable_variant':False}),{},{'input_tokens':1,'output_tokens':1},'stop'))
    src=hashlib.sha256((GOLD/'lines_bare.jsonl').read_bytes()).hexdigest()
    res=tmp_path/'results/screen';out=tmp_path/'judge';out.mkdir()
    for m,text in (('A','That child keeps secrets.'),('B','That kid has secrets.')):
        (res/m).mkdir(parents=True)
        (res/m/'lines_bare.jsonl').write_text(json.dumps({'id':'JMB-053','model':m,'translation':text,'source_sha256':src})+'\n')
        monkeypatch.setattr(sys,'argv',['judge.py','--responses',str(res/m/'lines_bare.jsonl'),'--dataset','lines',
                                        '--output',str(out/f'{m}.lines_eval.jsonl'),'--ledger',str(tmp_path/'ledger.jsonl'),'--execute'])
        assert judge.main()==0
    want={m:read(out/f'{m}.lines_eval.jsonl')[0]['content_key'] for m in 'AB'}
    for m in 'AB':  # simulate judgments made before content_key existed
        f=out/f'{m}.lines_eval.jsonl';rows=read(f)
        for r in rows:r.pop('content_key')
        f.write_text(''.join(json.dumps(r)+'\n' for r in rows))
    (res/'B/lines_bare.jsonl').write_text(json.dumps({'id':'JMB-053','model':'B','translation':'Changed since judging.','source_sha256':src})+'\n')
    monkeypatch.setattr(sys,'argv',['backfill','--dir',str(out),'--results',str(tmp_path/'results'),'--write'])
    bf.main()
    assert read(out/'A.lines_eval.jsonl')[0]['content_key']==want['A']  # same key judge.py would have stored
    assert 'content_key' not in read(out/'B.lines_eval.jsonl')[0]  # response no longer what the judge saw
