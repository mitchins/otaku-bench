#!/usr/bin/env python3
"""50-model OtakuBench shortlist: eliminate four low-value clones, add lab translation/Japanese specialists.

Do not claim trained lineage == quantization converter. The model labs supply weights.
Community GGUF repositories are conversions, not novel fine-tunes.
"""
import copy,csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
src=ROOT/'data/candidates.json'
orig=json.loads(src.read_text())['models']
drop={'Qwen3.5-0.8B','Qwen3-0.6B','SmolLM3-3B','Llama-3.2-3B-Instruct',
      'Qwen3-32B','Qwen3-1.7B','Phi-4 14B','Phi-4-mini-instruct','Ministral 3 3B Instruct','Qwen2.5-32B Instruct'}
by={r['model']:r for r in orig}
assert drop<=set(by)
base=[copy.deepcopy(x) for x in orig if x['model'] not in drop]
def clone(key,model,lab,params,origrepo,repo,file,size,notes):
 r=copy.deepcopy(by[key])
 r.update(model=model,family=lab,total_params_b=params,active_params_b=params,
  quant_repo=repo,preferred_quant='Q4_K_M',original_repo=origrepo,quant_publisher=repo.split('/')[0],
  quant_file=file,quant_size_gb=size,listed_file_name=file,listed_size_gb=size,
  exact_file_url='https://huggingface.co/'+repo+'/blob/main/'+file,
  gguf_repo_url='https://huggingface.co/'+repo,original_url='https://huggingface.co/'+origrepo,
  inclusion_reason='Specialist Japanese/translation coverage: '+notes,
  special_notes=notes+'; small models should also be compared at Q6_K/Q8_0 where GGUF exists.',
  lineage='Research-lab trained/continued-pretrained model; third-party converter only, no community fine-tune',
  web_spotchecked=True,listed_source_url='https://huggingface.co/'+repo+'/tree/main',
  model_repo_sha=None,selected_quant_policy='independent converter Q4_K_M; exact file web listed; repo SHA pending live attestation',
  repro_status='web-listed exact file; must validate API path/SHA and model execution')
 return r
special=[
 clone('Qwen3-8B','Hunyuan-MT-7B','Hunyuan-MT',8.0,'tencent/Hunyuan-MT-7B','mradermacher/Hunyuan-MT-7B-GGUF','Hunyuan-MT-7B.Q4_K_M.gguf',4.62,'lab translation specialist, Japanese-English in 33-language support; use model-specific translation prompt'),
 clone('Qwen3-8B','Seed-X-PPO-7B','Seed-X',8.0,'ByteDance-Seed/Seed-X-PPO-7B','mradermacher/Seed-X-PPO-7B-GGUF','Seed-X-PPO-7B.Q4_K_M.gguf',4.56,'ByteDance laboratory PPO-trained translation specialist (Mistral-based); model card requires raw prompt with target language tag <en>; GGUF is unofficial; canary required'),
 clone('Qwen3-8B','Qwen3-Swallow-8B-RL-v0.2','Swallow',8.0,'tokyotech-llm/Qwen3-Swallow-8B-RL-v0.2','mmnga-o/Qwen3-Swallow-8B-RL-v0.2-gguf','Qwen3-Swallow-8B-RL-v0.2-Q4_K_M.gguf',5.03,'significant laboratory Japanese continued pretraining/SFT/RL (not community fine-tune); thinking on per model card'),
 clone('Qwen3-30B-A3B-Instruct-2507','Qwen3-Swallow-30B-A3B-RL-v0.2','Swallow',31.0,'tokyotech-llm/Qwen3-Swallow-30B-A3B-RL-v0.2','yuseiito/Qwen3-Swallow-30B-A3B-RL-v0.2-GGUF','Qwen3-Swallow-30B-A3B-RL-v0.2-Q4_K_M.gguf',18.6,'laboratory Japanese continued-pretraining/SFT/RL MoE; conversion unchanged weights; thinking on'),
]
special[-1]['active_params_b']=3.0
# High relevance, first-party translation development with public GGUFs.
# CAT 3.3 final currently has no independently attested GGUF, so benchmark the
# correctly named laboratory BETA rather than falsely pointing a beta quant at final weights.
special += [
 clone('Qwen3-8B','CAT-Translate-7B','CAT-Translate',7,'cyberagent/CAT-Translate-7b',
       'mradermacher/CAT-Translate-7b-GGUF','CAT-Translate-7b.Q4_K_M.gguf',4.54,
       'CyberAgent laboratory Japanese-English dedicated translation model; MIT; preserve 7B native chat template'),
 clone('Qwen3-8B','CAT-Translate-3.3B-beta','CAT-Translate',3.3,'cyberagent/CAT-Translate-3.3b-beta',
       'mradermacher/CAT-Translate-3.3b-beta-GGUF','CAT-Translate-3.3b-beta.Q4_K_M.gguf',2.07,
       'CyberAgent Japanese-English specialist BETA weights only; current final 3.3b needs fresh GGUF conversion'),
 clone('Qwen3-8B','CAT-Translate-1.4B','CAT-Translate',1.4,'cyberagent/CAT-Translate-1.4b',
       'mradermacher/CAT-Translate-1.4b-GGUF','CAT-Translate-1.4b.Q4_K_M.gguf',0.931,
       'CyberAgent lab Japanese-English specialist; MIT'),
 clone('Qwen3-8B','CAT-Translate-0.8B','CAT-Translate',0.8,'cyberagent/CAT-Translate-0.8b',
       'mradermacher/CAT-Translate-0.8b-GGUF','CAT-Translate-0.8b.Q4_K_M.gguf',0.528,
       'CyberAgent lab Japanese-English specialist; MIT'),
 clone('Qwen3-8B','HY-MT1.5-7B','HY-MT1.5',8,'tencent/HY-MT1.5-7B',
       'tencent/HY-MT1.5-7B-GGUF','HY-MT1.5-7B-Q4_K_M.gguf',4.62,
       'Tencent original official Q4_K_M GGUF; supports context and terminology; check territory restrictions in license'),
 clone('Qwen3-8B','HY-MT1.5-1.8B','HY-MT1.5',1.8,'tencent/HY-MT1.5-1.8B',
       'tencent/HY-MT1.5-1.8B-GGUF','HY-MT1.5-1.8B-Q4_K_M.gguf',1.13,
       'Tencent original official Q4_K_M GGUF; fast small Japanese-English specialist; check license'),
]

# Re-rank selection hypothesis: major specialists after first 10, not a measured leaderboard.
new=base[:10]+[special[i] for i in (3,4,8,0,1,5,2,6,9,7)]+base[10:]
assert len(new)==50 and len({r['model'] for r in new})==50
for i,r in enumerate(new,1):
 r['rank']=i
 r['deck_default_candidate']=bool((r.get('quant_size_gb') or r.get('listed_size_gb') or 999)<=9.0)
 r['deck_note']='Plausible file size only; need measured available RAM, KV and GGUF loading check' if r['deck_default_candidate'] else 'Not eligible for constrained 16GB Steam Deck target without independent fitting proof'
 r['small_model_high_quant_challenger']='Q6_K or Q8_0 separately, if GGUF repo offers exact file' if r['total_params_b']<=9 else None
 r['runtime_validated']=False
 r['translation_quality_measured']=False
(ROOT/'data/otakubench50.json').write_text(json.dumps({'models':new,'notes':'Ranking is hypothesis only; live GGUF API attestation / runtime / judge scoring not run. PLaMo separately tracked due custom runtime.'},indent=2,ensure_ascii=False)+'\n')
with (ROOT/'data/otakubench50.csv').open('w',encoding='utf-8-sig',newline='') as f:
 cols=['rank','model','family','total_params_b','active_params_b','quant_repo','preferred_quant','quant_file','quant_size_gb','deck_default_candidate','deck_note','small_model_high_quant_challenger','original_repo','repro_status']
 w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows({c:r.get(c) for c in cols} for r in new)
(ROOT/'data/out_of_matrix_specialists.json').write_text(json.dumps([{'model':'PLaMo-2-translate','original_repo':'pfnet/plamo-2-translate','parameters_total_b':10,
  'runtime':'vLLM or Transformers trust_remote_code=True using <|plamo:op|> translation prompt; do not present as GGUF drop-in',
  'status':'specialist lane / no attested mainstream recommended GGUF','license':'PLaMo community license with commercial restrictions; read before downloading',
  'why':'Japanese-to-English direct specialism plus pairwise-eval sibling'},
 {'model':'CAT-Translate-3.3B-final','original_repo':'cyberagent/CAT-Translate-3.3b',
  'status':'current lab final has no reliable recommended GGUF yet; 3.3B-beta is in the 50-model GGUF lane',
  'why':'do not misrepresent beta GGUF as the current final lab weights'}],indent=2)+'\n')
print('50 original-lab candidates, 10 substitutions:', [(r['rank'],r['model']) for r in new if r['family'] in {'Hunyuan-MT','HY-MT1.5','Seed-X','Swallow','CAT-Translate'}])
