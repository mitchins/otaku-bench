#!/usr/bin/env python3
"""Deterministic selection of 50 lab-published candidate models (NO evaluation scores)."""
import csv, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
# rank, display name, family, total parameters B, active B (None=dense/unspecified), GGUF repo, recommended default quant,
# original publisher/model, rationale, priority group, special requirements
ROWS = [
(1,'Qwen3.8-27B','Qwen',27,None,'unsloth/Qwen3.8-27B-GGUF','UD-Q4_K_M','Qwen/Qwen3.8-27B','Newer Qwen frontier; high HF community uptake','A',''),
(2,'Gemma 4 31B IT','Gemma',31,None,'bartowski/google_gemma-4-31B-it-GGUF','Q4_K_M','google/gemma-4-31b-it','Strong multilingual large dense reference','A',''),
(3,'Qwen3.6-35B-A3B','Qwen',35,3,'bartowski/Qwen_Qwen3.6-35B-A3B-GGUF','Q4_K_M','Qwen/Qwen3.6-35B-A3B','Large MoE high capability at relatively low active compute','A',''),
(4,'Qwen3.6-27B','Qwen',27,None,'bartowski/Qwen_Qwen3.6-27B-GGUF','Q4_K_M','Qwen/Qwen3.6-27B','Current strong dense model, between 3.5 and 3.8','A',''),
(5,'Qwen3.5-27B','Qwen',27,None,'bartowski/Qwen_Qwen3.5-27B-GGUF','Q4_K_M','Qwen/Qwen3.5-27B','Popular dense multilingual control','A',''),
(6,'Gemma 4 26B-A4B IT','Gemma',26,4,'unsloth/gemma-4-26B-A4B-it-GGUF','UD-Q4_K_M','google/gemma-4-26B-A4B-it','High quality MoE speed/quality comparison','A',''),
(7,'Qwen3.5-35B-A3B','Qwen',35,3,'bartowski/Qwen_Qwen3.5-35B-A3B-GGUF','Q4_K_M','Qwen/Qwen3.5-35B-A3B','Popular 35B MoE anchor','A',''),
(8,'LLM-jp-4.1-32B-A3B Thinking','LLM-jp',32.139,3.827,'llm-jp/llm-jp-4.1-32b-a3b-thinking-gguf','Q4_K_M','llm-jp/llm-jp-4.1-32b-a3b-thinking','New original Japanese-first large MoE','A','upstream llama.cpp v0.6.0+ with LLM-jp-4.1 Harmony support REQUIRED'),
(9,'LLM-jp-4.1-33B Thinking','LLM-jp',33.22,None,'llm-jp/llm-jp-4.1-33b-thinking-gguf','Q4_K_M','llm-jp/llm-jp-4.1-33b-thinking','Japanese-first 33B dense reference','A','upstream llama.cpp v0.6.0+ with LLM-jp-4.1 Harmony support REQUIRED'),
(10,'Gemma 4 12B IT','Gemma',12,None,'unsloth/gemma-4-12b-it-GGUF','UD-Q4_K_XL','google/gemma-4-12b-it','New 12B unified multilingual middle tier','A',''),
(11,'Qwen3.5-9B','Qwen',9,None,'bartowski/Qwen_Qwen3.5-9B-GGUF','Q4_K_M','Qwen/Qwen3.5-9B','Popular 9B quality sweet spot','A',''),
(12,'Qwen3.5-4B','Qwen',4,None,'bartowski/Qwen_Qwen3.5-4B-GGUF','Q4_K_M','Qwen/Qwen3.5-4B','Popular everyday 4B; matches specified Bartowski default example','A',''),
(13,'TranslateGemma 27B IT','TranslateGemma',27,None,'mradermacher/translategemma-27b-it-GGUF','Q4_K_M','google/translategemma-27b-it','Purpose-built translation baseline; not generic chat','A','translation-specific prompt format; community GGUF backup'),
(14,'TranslateGemma 12B IT','TranslateGemma',12,None,'mradermacher/translategemma-12b-it-GGUF','Q4_K_M','google/translategemma-12b-it','Translation-focused middle tier','A','translation-specific prompt format; community GGUF backup'),
(15,'TranslateGemma 4B IT','TranslateGemma',4,None,'mradermacher/translategemma-4b-it-GGUF','Q4_K_M','google/translategemma-4b-it','Translation-focused edge tier','A','translation-specific prompt format; community GGUF backup'),
(16,'LLM-jp-4.1-8B Thinking','LLM-jp',8.59,None,'llm-jp/llm-jp-4.1-8b-thinking-gguf','Q4_K_M','llm-jp/llm-jp-4.1-8b-thinking','Japanese-first smaller instruct/reasoning model','A','upstream llama.cpp v0.6.0+ with LLM-jp-4.1 Harmony support REQUIRED'),
(17,'LFM2.5-24B-A2B','LiquidAI',24,2,'bartowski/LiquidAI_LFM2.5-24B-A2B-GGUF','Q4_K_M','LiquidAI/LFM2.5-24B-A2B','Very recent lab MoE and strong edge efficiency hypothesis','A','verify new architecture support in llama.cpp'),
(18,'GLM-4.7-Flash','GLM',30,3,'bartowski/zai-org_GLM-4.7-Flash-GGUF','Q4_K_M','zai-org/GLM-4.7-Flash','Efficient strong reasoning alternative','A',''),
(19,'Qwen3-30B-A3B-Instruct-2507','Qwen',30,3,'unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF','UD-Q4_K_XL','Qwen/Qwen3-30B-A3B-Instruct-2507','Popular no-reasoning MoE baseline','B',''),
(20,'Qwen3-32B','Qwen',32,None,'bartowski/Qwen_Qwen3-32B-GGUF','Q4_K_M','Qwen/Qwen3-32B','Earlier large dense multilingual benchmark','B',''),
(21,'Qwen3-14B','Qwen',14,None,'unsloth/Qwen3-14B-GGUF','UD-Q4_K_XL','Qwen/Qwen3-14B','Popular medium model control','B',''),
(22,'Qwen3-8B','Qwen',8,None,'bartowski/Qwen_Qwen3-8B-GGUF','Q4_K_M','Qwen/Qwen3-8B','Extremely popular prior-generation control','B',''),
(23,'gpt-oss-20b','OpenAI',21,3.6,'bartowski/openai_gpt-oss-20b-GGUF','Q4_K_M','openai/gpt-oss-20b','Very popular 21B-total/3.6B-active local reasoning weights; Bartowski recommended Q4_K_M wrapper','B','Harmony template/reasoning-output handling; FFN MoE tensors retain native MXFP4_MOE inside Q4_K_M GGUF'),
(24,'Mistral Small 3.2 24B Instruct','Mistral',24,None,'bartowski/mistralai_Mistral-Small-3.2-24B-Instruct-2506-GGUF','Q4_K_M','mistralai/Mistral-Small-3.2-24B-Instruct-2506','Multilingual 24B dense competitor','B',''),
(25,'Gemma 3 27B IT','Gemma',27,None,'unsloth/gemma-3-27b-it-GGUF','UD-Q4_K_XL','google/gemma-3-27b-it','Prior-generation top open dense competitor','B','Gemma model license, unlike Gemma 4 Apache'),
(26,'Qwen3-4B-Instruct-2507','Qwen',4,None,'unsloth/Qwen3-4B-Instruct-2507-GGUF','UD-Q4_K_XL','Qwen/Qwen3-4B-Instruct-2507','Known practical nonthinking 4B comparison','B',''),
(27,'Phi-4 14B','Phi',14,None,'bartowski/phi-4-GGUF','Q4_K_M','microsoft/phi-4','Compact strong reasoning, lower Japanese priority','B',''),
(28,'Nemotron 3 Nano 30B-A3B','NVIDIA',32,3,'bartowski/nvidia_Nemotron-3-Nano-30B-A3B-GGUF','Q4_K_M','nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16','Popular hybrid MoE, contrasting architecture','B','Quant file larger than ordinary Q4 due hybrid/embedding weights'),
(29,'Qwen2.5-32B Instruct','Qwen',32,None,'bartowski/Qwen2.5-32B-Instruct-GGUF','Q4_K_M','Qwen/Qwen2.5-32B-Instruct','Widely used older benchmark comparator','B',''),
(30,'Gemma 4 E4B IT','Gemma',8.0,None,'unsloth/gemma-4-E4B-it-GGUF','UD-Q4_K_XL','google/gemma-4-E4B-it','Effective 4B / larger total hybrid PLE edge reference','B','E4B 4.5B effective; 8B total including embeddings (Google model card)'),
(31,'Gemma 4 E2B IT','Gemma',5.1,None,'unsloth/gemma-4-E2B-it-GGUF','UD-Q4_K_XL','google/gemma-4-E2B-it','Effective 2B / larger total hybrid PLE edge reference','B','E2B 2.3B effective; 5.1B total including embeddings (Google model card)'),
(32,'Gemma 3 12B IT','Gemma',12,None,'bartowski/google_gemma-3-12b-it-GGUF','Q4_K_M','google/gemma-3-12b-it','Popular earlier high-quality mid-tier','B','Gemma license'),
(33,'Gemma 3 4B IT','Gemma',4,None,'bartowski/google_gemma-3-4b-it-GGUF','Q4_K_M','google/gemma-3-4b-it','Extremely widespread 4B comparison','B','Gemma license'),
(34,'Ministral 3 14B Instruct','Mistral',14,None,'unsloth/Ministral-3-14B-Instruct-2512-GGUF','UD-Q4_K_XL','mistralai/Ministral-3-14B-Instruct-2512','Practical dense smaller Mistral','B',''),
(35,'Ministral 3 8B Instruct','Mistral',8,None,'unsloth/Ministral-3-8B-Instruct-2512-GGUF','UD-Q4_K_XL','mistralai/Ministral-3-8B-Instruct-2512','Popular compact multilingual contender','B',''),
(36,'Ministral 3 3B Instruct','Mistral',3,None,'unsloth/Ministral-3-3B-Instruct-2512-GGUF','UD-Q4_K_XL','mistralai/Ministral-3-3B-Instruct-2512','Small Mistral compact baseline','B',''),
(37,'Qwen3.5-2B','Qwen',2,None,'bartowski/Qwen_Qwen3.5-2B-GGUF','Q4_K_M','Qwen/Qwen3.5-2B','Popular tiny-to-small real-world quant','B',''),
(38,'Qwen3.5-0.8B','Qwen',0.8,None,'bartowski/Qwen_Qwen3.5-0.8B-GGUF','Q4_K_M','Qwen/Qwen3.5-0.8B','Current sub-1B baseline','B',''),
(39,'Qwen3-1.7B','Qwen',1.7,None,'bartowski/Qwen_Qwen3-1.7B-GGUF','Q4_K_M','Qwen/Qwen3-1.7B','Very popular sub-2B control','B',''),
(40,'Qwen3-0.6B','Qwen',0.6,None,'bartowski/Qwen_Qwen3-0.6B-GGUF','Q4_K_M','Qwen/Qwen3-0.6B','Most downloaded extreme lightweight model','B',''),
(41,'Qwen2.5-7B Instruct','Qwen',7,None,'bartowski/Qwen2.5-7B-Instruct-GGUF','Q4_K_M','Qwen/Qwen2.5-7B-Instruct','Older highly adopted translation-capable baseline','B',''),
(42,'Phi-4-mini-instruct','Phi',3.8,None,'bartowski/microsoft_Phi-4-mini-instruct-GGUF','Q4_K_M','microsoft/Phi-4-mini-instruct','Small strong instruction model; language coverage challenger','B',''),
(43,'Aya Expanse 8B','Aya',8,None,'bartowski/aya-expanse-8b-GGUF','Q4_K_M','CohereForAI/aya-expanse-8b','Multilingual-specific baseline with Japanese coverage','B',''),
(44,'LFM2.5-2.6B','LiquidAI',2.6,None,'bartowski/LiquidAI_LFM2.5-2.6B-GGUF','Q4_K_M','LiquidAI/LFM2.5-2.6B','Recent compact lab edge comparison','B',''),
(45,'LFM2.5-1.2B Instruct','LiquidAI',1.2,None,'LiquidAI/LFM2.5-1.2B-Instruct-GGUF','Q4_K_M','LiquidAI/LFM2.5-1.2B-Instruct','Extremely small edge comparison','B',''),
(46,'DeepSeek-R1-Distill-Qwen-32B','DeepSeek',32,None,'bartowski/DeepSeek-R1-Distill-Qwen-32B-GGUF','Q4_K_M','deepseek-ai/DeepSeek-R1-Distill-Qwen-32B','Lab-distilled reasoning checkpoint, substantial new training','B','Exclude informal community fine-tunes; reasoning extraction'),
(47,'SmolLM3-3B','SmolLM',3,None,'bartowski/HuggingFaceTB_SmolLM3-3B-GGUF','Q4_K_M','HuggingFaceTB/SmolLM3-3B','Popular Apache small model reference','B',''),
(48,'Llama-3.1-8B-Instruct','Llama',8,None,'bartowski/Meta-Llama-3.1-8B-Instruct-GGUF','Q4_K_M','meta-llama/Meta-Llama-3.1-8B-Instruct','Ubiquitous local baseline','B','Meta Llama community license'),
(49,'Llama-3.2-3B-Instruct','Llama',3,None,'bartowski/Llama-3.2-3B-Instruct-GGUF','Q4_K_M','meta-llama/Llama-3.2-3B-Instruct','Ubiquitous 3B mobile baseline','B','Meta Llama community license'),
(50,'RakutenAI-7B-instruct','Rakuten',7,None,'mradermacher/RakutenAI-7B-instruct-GGUF','Q4_K_M','Rakuten/RakutenAI-7B-instruct','Original-lab Japanese adaptation with instruction tuning','B','Older model; lab Japanese adaptation from Mistral (not community finetune)'),
]

def main():
    evidence_path=ROOT/'data'/'web_spotchecks.json'
    evidence={r['rank']:r for r in json.loads(evidence_path.read_text())['entries']} if evidence_path.exists() else {}
    assert len(ROWS)==50
    keys=['rank','model','family','total_params_b','active_params_b','quant_repo','preferred_quant','original_repo','inclusion_reason','tier','special_notes']
    models=[]
    for row in ROWS:
        d=dict(zip(keys,row))
        assert 0.6 <= d['total_params_b'] <= 35
        d['lineage'] = 'lab_distilled' if d['family'] in ('DeepSeek','TranslateGemma') else ('lab_adaptation' if d['family']=='Rakuten' else 'original_lab_release')
        d['quant_publisher'] = d['quant_repo'].split('/')[0]
        d['gguf_repo_url']='https://huggingface.co/'+d['quant_repo']
        d['original_url']='https://huggingface.co/'+d['original_repo']
        d['repro_status']='shortlisted; HF API file attestation pending'
        d['quant_file']=None
        d['quant_size_gb']=None
        d['exact_file_url']=None
        check=evidence.get(d['rank'])
        d['listed_file_name']=check['file'] if check else None
        d['listed_size_gb']=check['displayed_gb'] if check else None
        d['listed_source_url']=check['source_url'] if check else None
        d['web_spotchecked']=bool(check)
        d['model_repo_sha']=None
        d['selected_quant_policy']='Bartowski publisher recommended Q4_K_M; Unsloth UD-Q4_K_XL/UD-Q4_K_M; publisher GGUF same 4-bit; gpt-oss Q4_K_M with native MXFP4_MOE experts preserved'
        models.append(d)
    assert len({m['original_repo'] for m in models})==50
    assert len({m['quant_repo'] for m in models})==50
    p=ROOT/'data'/'candidates.json';p.write_text(json.dumps({'schema_version':'1.0','as_of':'2026-10-23','task':'Japanese-to-English translation, 250-item benchmark','policy':{'min_total_params_b':0.6,'max_total_params_b':35,'total_params_rule':'total stored parameter count, not MoE active count','lineage':'original lab releases and major lab distilled checkpoints only','quant':'publisher recommended Bartowski Q4_K_M or Unsloth practical UD Q4 or official GGUF','ranking':'curated acquisition / testing priority, NOT observed JP translation quality','status':'selection curated from HF pages and vendor model cards; exact file paths require live HF API attestation; some repo links may be corrected by preflight'},'models':models},ensure_ascii=False,indent=2)+'\n')
    with (ROOT/'data'/'candidates.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(models[0]));w.writeheader();w.writerows(models)
    print('OK: 50 original-lab-lineage candidates, none outside size interval')
if __name__=='__main__':main()
