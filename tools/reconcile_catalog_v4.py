#!/usr/bin/env python3
"""Reconcile 50 candidate slots, preserving original GGUF quant/revision gates."""
from __future__ import annotations
import copy,csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'data/otakubench50.json'
# Always regenerate from the frozen v3 source, never from the active v4 output.
# That makes this correction reproducible and idempotent.
old=json.loads((ROOT/'data/otakubench50_v3.json').read_text());by={r['model']:r for r in old['models']}
removed=['Hunyuan-MT-7B','Qwen2.5-7B Instruct','Aya Expanse 8B','LFM2.5-2.6B','RakutenAI-7B-instruct']
# Name, family, total params, original, converter, file, reported GB, why
new=[
 ('Qwen3-4B-Instruct-2507','Qwen',4.0,'Qwen/Qwen3-4B-Instruct-2507',
  'bartowski/Qwen_Qwen3-4B-Instruct-2507-GGUF','Qwen3-4B-Instruct-2507-Q4_K_M.gguf',2.50,
  'Strong non-thinking Deck-class original-control challenger.'),
 ('rinna-llama-3-youko-8b','rinna',8.0,'rinna/llama-3-youko-8b',
  'mmnga/rinna-llama-3-youko-8b-gguf','rinna-llama-3-youko-8b-Q4_K_M.gguf',4.92,
  'Actual continued-pretrained Japanese base of VNTL v2; NOT Meta Llama-3-8B raw.'),
 ('Qwen2.5-14B-Instruct','Qwen',14.7,'Qwen/Qwen2.5-14B-Instruct',
  'bartowski/Qwen2.5-14B-Instruct-GGUF','Qwen2.5-14B-Instruct-Q4_K_M.gguf',8.99,
  'Declared original 14B base of Sugoi Ultra 14B.'),
 ('Phi-4 14B','Microsoft',14.7,'microsoft/phi-4',
  'bartowski/phi-4-GGUF','phi-4-Q4_K_M.gguf',9.05,
  'Original phi-4 control for Shisa v2.1 unphi4 14B (Unsloth intermediate is a weight conversion).'),
 ('Llama-3.2-3B-Instruct','Meta',3.0,'meta-llama/Llama-3.2-3B-Instruct',
  'bartowski/Llama-3.2-3B-Instruct-GGUF','Llama-3.2-3B-Instruct-Q4_K_M.gguf',2.02,
  'Original instructed Llama 3.2 base for Shisa 3B, useful Deck-class control.'),
]
# Exact Qwen2.5-14B GGUF file is provisional pending API attestation; no fabricated file-size number.
for x in removed:assert x in by,x
assert all(x[0] not in by for x in new)
rows=[copy.deepcopy(r) for r in old['models'] if r['model'] not in removed]
for model,family,params,original,quant_repo,filename,gb,why in new:
 row=copy.deepcopy(by['Qwen3.5-4B'])
 row.update(model=model,family=family,total_params_b=params,active_params_b=params,original_repo=original,quant_repo=quant_repo,
   original_url=f'https://huggingface.co/{original}',gguf_repo_url=f'https://huggingface.co/{quant_repo}',
   quant_publisher=quant_repo.split('/')[0],preferred_quant='Q4_K_M',quant_file=filename,
   listed_file_name=filename,quant_size_gb=gb,listed_size_gb=gb,exact_file_url=f'https://huggingface.co/{quant_repo}/blob/main/{filename}',
   listed_source_url=f'https://huggingface.co/{quant_repo}/tree/main',selected_quant_policy='recommended default Q4_K_M; live HF SHA and file attestation required',
   eligibility_lane='lab_original_or_existing_v2_specialist',eligibility_evidence_url=f'https://huggingface.co/{original}',
   prompt_style=('base_completion' if model=='rinna-llama-3-youko-8b' else 'chat'),special_notes=why,inclusion_reason=why,lineage='original research lab weight checkpoint',
   model_repo_sha=None,repro_status='web-listed / pending live API attestation and execution',
   web_spotchecked=bool(gb is not None),listed_file_evidence='Repository page and model card; revalidate exact file with resolver',
   runtime_validated=False,translation_quality_measured=False,canary_required=True,
   evaluation_role=('ancestor_diagnostic_only' if model=='rinna-llama-3-youko-8b' else 'full_candidate'))
 rows.append(row)
# Retain original v3 trial priorities; add controls as designated tail-arm candidates.
assert len(rows)==50
for i,row in enumerate(rows,1):
 row['rank']=i
 gb=row.get('quant_size_gb') or row.get('listed_size_gb')
 row['deck_default_candidate']=bool(gb is not None and gb<=9.0)
 row['deck_note']='GGUF size proxy only; not proven Steam Deck RAM fit' if row['deck_default_candidate'] else 'LAN / unknown memory requirements'
 row['small_model_high_quant_challenger']='Q6_K / Q8_0 only after exact variant and bytes attested' if row['total_params_b']<=9 else None
 assert .6<=row['total_params_b']<=35
old.update(version='4.0',models=rows,removed_v4=removed,added_v4=[x[0] for x in new],
 notes='Exactly 50. Original adaptation-base controls restored. Prioritization ≠ proven performance. Pinned GGUF attestation before trusted run.')
p.write_text(json.dumps(old,ensure_ascii=False,indent=2)+'\n')
fields=['rank','model','family','total_params_b','active_params_b','eligibility_lane','original_repo',
 'quant_repo','preferred_quant','quant_file','quant_size_gb','prompt_style','deck_default_candidate','small_model_high_quant_challenger','eligibility_evidence_url','listed_source_url','repro_status']
with (ROOT/'data/otakubench50.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fields);w.writeheader();w.writerows({k:r.get(k) for k in fields} for r in rows)
(ROOT/'data/model_selection_delta_v4.json').write_text(json.dumps({'added_v4':[x[0] for x in new],'removed_v4':removed,
 'required_controls':{'VNTL-Llama3-8B-v2':'rinna-llama-3-youko-8b','Sugoi-14B-Ultra':'Qwen2.5-14B-Instruct',
 'Shisa-v2.1-unphi4-14B':'Phi-4 14B','Shisa-v2.1-llama3.2-3B':'Llama-3.2-3B-Instruct',
 'Shisa-v2.1-qwen3-8B':'Qwen3-8B','GPT-OSS-Swallow-20B-RL-v0.1':'gpt-oss-20b'}},indent=2)+'\n')
print('Retained',len(rows),'candidates. New/controls:',*[x[0] for x in new])
