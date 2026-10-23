#!/usr/bin/env python3
"""Deterministic OtakuBench v3 shortlist; no downloads, no model quality scores.

Substantive Japanese adaptations and domain translators are eligible under the policy.
Source of truth: preserved data/otakubench50_v2.json. This script can be rerun.
"""
from __future__ import annotations

# Historical generator is frozen after v4 catalog reconciliation.
import sys as _legacy_sys, json as _legacy_json
from pathlib import Path as _legacy_Path
if __name__ == '__main__':
 _active=_legacy_Path(__file__).resolve().parents[1]/'data/otakubench50.json'
 if _active.exists() and _legacy_json.loads(_active.read_text()).get('version')=='4.0':
  _legacy_sys.exit('Legacy catalog generator refused: active v4 catalog is authoritative; do not overwrite it.')
from pathlib import Path
import copy,csv,json

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'data/otakubench50_v2.json'
base=json.loads(SRC.read_text(encoding='utf-8'))['models']
by={x['model']:x for x in base}
# Twelve retired slots: previous-generation redundancy / weak relevance, not quality failures.
retire=[
 'Qwen3.5-27B','Qwen3.5-35B-A3B','Qwen3-30B-A3B-Instruct-2507',
 'Qwen3-14B','Qwen3-4B-Instruct-2507',
 'DeepSeek-R1-Distill-Qwen-32B','Mistral Small 3.2 24B Instruct',
 'Gemma 3 27B IT','Gemma 3 12B IT','Gemma 3 4B IT',
 'Ministral 3 14B Instruct','Llama-3.1-8B-Instruct',
]
assert len(retire)==12 and set(retire) <= by.keys()

# model, family, source, params, active, quant repo, quant, exact filename,
# GB published decimal, eligibility lane, evidence, special prompt, notes
ADD=[
('Qwen3-Swallow-32B-RL-v0.2','Swallow', 'tokyotech-llm/Qwen3-Swallow-32B-RL-v0.2', 32.5,None,
 'ultimatechris/Qwen3-Swallow-32B-RL-v0.2-GGUF','Q4_K_M', 'Qwen3-Swallow-32B-RL-v0.2-Q4_K_M.gguf',19.8,'heavy_adaptation',
 'https://huggingface.co/ultimatechris/Qwen3-Swallow-32B-RL-v0.2-GGUF/tree/main','chat',
 'Research laboratory CPT→SFT→RL Japanese adaptation. Community conversion; 32B family distinct from 30B-A3B MoE.'),
('GPT-OSS-Swallow-20B-RL-v0.1','Swallow','tokyotech-llm/GPT-OSS-Swallow-20B-RL-v0.1',21.0,3.6,
 'mradermacher/GPT-OSS-Swallow-20B-RL-v0.1-GGUF','Q4_K_M','GPT-OSS-Swallow-20B-RL-v0.1.Q4_K_M.gguf',15.8,'heavy_adaptation',
 'https://huggingface.co/mradermacher/GPT-OSS-Swallow-20B-RL-v0.1-GGUF/blob/main/GPT-OSS-Swallow-20B-RL-v0.1.Q4_K_M.gguf','chat',
 'Research lab continued pretraining, SFT, RL. Japanese reasoning model; model card recommends medium reasoning.'),
('NVIDIA-Nemotron-Nano-9B-v2-Japanese','Nemotron-JP','nvidia/NVIDIA-Nemotron-Nano-9B-v2-Japanese',9.0,None,
 'mmnga-o/NVIDIA-Nemotron-Nano-9B-v2-Japanese-gguf','Q4_K_M','NVIDIA-Nemotron-Nano-9B-v2-Japanese-Q4_K_M.gguf',6.53,'first_party_japanese',
 'https://huggingface.co/mmnga-o/NVIDIA-Nemotron-Nano-9B-v2-Japanese-gguf/tree/main','chat',
 'NVIDIA first-party Japanese adaptation of Nemotron Nano 9B v2; special license and hybrid runtime requirements.'),
('Shisa-v2.1-unphi4-14B','Shisa','shisa-ai/shisa-v2.1-unphi4-14b',14.0,None,
 'XpressAI/shisa-v2.1-unphi4-14b-GGUF','Q4_K_M','shisa-v2.1-unphi4-14b-Q4_K_M.gguf',8.89,'large_sft_rl',
 'https://huggingface.co/XpressAI/shisa-v2.1-unphi4-14b-GGUF/tree/main','chat',
 'Organization-published substantial bilingual SFT, DPO, RL, and some training-stage merges. Not a merge-only tune.'),
('Shisa-v2.1-qwen3-8B','Shisa','shisa-ai/shisa-v2.1-qwen3-8b',8.0,None,
 'XpressAI/shisa-v2.1-qwen3-8b-GGUF','Q4_K_M','shisa-v2.1-qwen3-8b-Q4_K_M.gguf',5.03,'large_sft_rl',
 'https://huggingface.co/XpressAI/shisa-v2.1-qwen3-8b-GGUF/tree/main','chat',
 'Bilingual SFT/RL with published evaluation; compare with retained Qwen3-8B base.'),
('Shisa-v2.1-llama3.2-3B','Shisa','shisa-ai/shisa-v2.1-llama3.2-3b',3.0,None,
 'XpressAI/shisa-v2.1-llama3.2-3b-GGUF','Q4_K_M','shisa-v2.1-llama3.2-3b-Q4_K_M.gguf',2.02,'large_sft_rl',
 'https://huggingface.co/XpressAI/shisa-v2.1-llama3.2-3b-GGUF/tree/main','chat',
 'Substantial Shisa bilingual SFT dataset and published Japanese-language evaluations.'),
('Shisa-v2.1-lfm2-1.2B','Shisa','shisa-ai/shisa-v2.1-lfm2-1.2b',1.2,None,
 'XpressAI/shisa-v2.1-lfm2-1.2b-GGUF','Q4_K_M','shisa-v2.1-lfm2-1.2b-Q4_K_M.gguf',.731,'large_sft_rl',
 'https://huggingface.co/XpressAI/shisa-v2.1-lfm2-1.2b-GGUF/tree/main','chat',
 'Documented Shisa bilingual SFT/politeness training, small-model Japanese gains.'),
('TinySwallow-1.5B-Instruct','TinySwallow','SakanaAI/TinySwallow-1.5B-Instruct',1.5,None,
 'SakanaAI/TinySwallow-1.5B-Instruct-GGUF','Q5_K_M','tinyswallow-1.5b-instruct-q5_k_m.gguf',1.13,'lab_distillation',
 'https://huggingface.co/SakanaAI/TinySwallow-1.5B-Instruct-GGUF/tree/main','chat',
 'Lab-published distillation (TAID) plus Japanese instruction tuning. First-party GGUF; Q5_K_M is its published default.'),
('LFM2.5-1.2B-JP-202606','LFM-JP','LiquidAI/LFM2.5-1.2B-JP-202606',1.17,None,
 'LiquidAI/LFM2.5-1.2B-JP-202606-GGUF','Q4_K_M','LFM2.5-1.2B-JP-202606-Q4_K_M.gguf',.731,'first_party_japanese',
 'https://huggingface.co/LiquidAI/LFM2.5-1.2B-JP-202606-GGUF/tree/main','chat',
 'Latest publicly listed Liquid AI Japanese 1.2B adaptation; 202606 supersedes previous 1.2B JP.'),
('VNTL-Llama3-8B-v2','VNTL','lmg-anon/vntl-llama3-8b-v2-hf',8.0,None,
 'lmg-anon/vntl-llama3-8b-v2-gguf','Q5_K_M','vntl-llama3-8b-v2-hf-q5_k_m.gguf',5.73,'domain_exception',
 'https://huggingface.co/lmg-anon/vntl-llama3-8b-v2-gguf/tree/main','vntl',
 'Domain exception: original VN translator with own dataset and independent VN leaderboard; native Llama3 Japanese→English turn format. No standard chat role. Q8 also available.'),
('Sugoi-14B-Ultra','Sugoi','sugoitoolkit/Sugoi-14B-Ultra-HF',14.7,None,
 'sugoitoolkit/Sugoi-14B-Ultra-GGUF','Q4_K_M','Sugoi-14B-Ultra-Q4_K_M.gguf',8.99,'domain_exception',
 'https://huggingface.co/sugoitoolkit/Sugoi-14B-Ultra-GGUF/tree/main','sugoi',
 'Domain exception: RPG/VN Japanese→English translation specialist; publisher GGUF; translation-system prompt recommended.'),
('Sugoi-32B-Ultra','Sugoi','sugoitoolkit/Sugoi-32B-Ultra-GGUF',32.5,None,
 'sugoitoolkit/Sugoi-32B-Ultra-GGUF','Q4_K_M','Sugoi-32B-Ultra-Q4_K_M.gguf',19.9,'domain_exception',
 'https://huggingface.co/sugoitoolkit/Sugoi-32B-Ultra-GGUF/tree/main','sugoi',
 'Domain exception: publisher 32B VN/Japanese translator; keep LAN only; parent weights provenance requires audit.'),
]
assert len(ADD)==12
new=[]
for spec in ADD:
 (name,family,origin,total,active,quant_repo,quant,filename,gb,lane,evidence,style,note)=spec
 assert name not in by, name
 row=copy.deepcopy(by['Qwen3-8B'])
 row.update(model=name,family=family,total_params_b=total,active_params_b=active,
  original_repo=origin,original_url='https://huggingface.co/'+origin,
  quant_repo=quant_repo,gguf_repo_url='https://huggingface.co/'+quant_repo,
  quant_publisher=quant_repo.split('/')[0],preferred_quant=quant,
  quant_file=filename,listed_file_name=filename,quant_size_gb=gb,listed_size_gb=gb,
  selected_quant_policy=('first-party GGUF' if quant_repo.split('/')[0].lower()==origin.split('/')[0].lower() else 'GGUF conversion of eligible training checkpoint')+'; exact web listed; API SHA pending',
  exact_file_url='https://huggingface.co/'+quant_repo+'/blob/main/'+filename,
  listed_source_url=evidence,eligibility_lane=lane,eligibility_evidence_url=evidence,
  prompt_style=style,listed_file_evidence='HF repository file tree inspected 2026-10-23',
  special_notes=note,inclusion_reason=note,web_spotchecked=True,
  lineage=lane+'; '+origin,model_repo_sha=None,
  repro_status='HF web-file-list verified; SHA, weights parity and execution not yet attested',
  runtime_validated=False,translation_quality_measured=False,canary_required=True)
 new.append(row)

# Insert highly relevant models toward top; ranked as trial priority, not expected performance.
old=[copy.deepcopy(r) for r in base if r['model'] not in retire]
# Retain stable relative ordering of v2 models, add 12 newer adapted/specialist lanes at a fixed point.
ranked=old[:10]+new+old[10:]
assert len(ranked)==50 and len(set(r['model'] for r in ranked))==50
for i,r in enumerate(ranked,1):
 r['rank']=i
 if 'eligibility_lane' not in r:
  r['eligibility_lane']='lab_original_or_existing_v2_specialist'
  r['eligibility_evidence_url']=r.get('original_url','')
  r['prompt_style']=('cat' if r['family']=='CAT-Translate' else 'hunyuan' if r['family'] in ('HY-MT1.5','Hunyuan-MT') else 'seedx' if r['family']=='Seed-X' else 'translategemma' if r['family']=='TranslateGemma' else 'chat')
  r['canary_required']=True
 gb=r.get('quant_size_gb') or r.get('listed_size_gb')
 r['deck_default_candidate']=bool(gb is not None and float(gb)<=9.0)
 r['deck_note']=('GGUF FILE SIZE ONLY; not proven 16GB Steam Deck fit (need KV/cache/OS and runtime test)' if r['deck_default_candidate'] else 'LAN or unqualified Steam Deck fit; size may be unavailable')
 r['small_model_high_quant_challenger']='Q6_K / Q8_0, each only if exact repo file exists and memory fits' if r['total_params_b']<=9 else None
 r['runtime_validated']=False
 r['translation_quality_measured']=False
 assert 0.6 <= r['total_params_b'] <=35, r['model']

# An explicit control family remains for each substantive adaptation where useful.
kept={r['model'] for r in ranked}
assert {'gpt-oss-20b','Qwen3-8B','LFM2.5-1.2B Instruct'} <=kept
assert {'VNTL-Llama3-8B-v2','Sugoi-14B-Ultra','Sugoi-32B-Ultra'} <=kept

obj={'version':'3.0','models':ranked,'notes':(
 '50 selected, 12 replaced. New models have web-verified files as of 2026-10-23; '
 'no live API SHA/file parity or local canary has run. This is selection, not translation scoring. '
 'Research-lab training provenance and community GGUF conversion are distinct.'),
 'retired_v2_names':retire,'new_v3_names':[r[0] for r in ADD]}
(ROOT/'data/otakubench50.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
cols=['rank','model','family','total_params_b','active_params_b','eligibility_lane','original_repo',
 'quant_repo','preferred_quant','quant_file','quant_size_gb','prompt_style','deck_default_candidate',
 'small_model_high_quant_challenger','eligibility_evidence_url','listed_source_url','repro_status']
with (ROOT/'data/otakubench50.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,cols);w.writeheader();w.writerows({c:r.get(c) for c in cols} for r in ranked)
changes={'policy_version':'v3','as_of':'2026-10-23','added':[{'model':r['model'],'lane':r['eligibility_lane'],'repo':r['quant_repo'],'file':r['quant_file'],'file_size_gb':r['quant_size_gb'],'evidence':r['eligibility_evidence_url']} for r in new],
 'removed':[{'model':x,'reason':'redundant/superseded generic baseline; not a demonstrated translation failure'} for x in retire]}
(ROOT/'data/model_selection_delta_v3.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2)+'\n')
print('v3:',len(ranked),'models | new',len(new),'| removed',len(retire),'| deck-file-size candidates',sum(r['deck_default_candidate'] for r in ranked))
for r in ranked[:25]:print(r['rank'],r['model'],r['quant_repo'],r['preferred_quant'])
