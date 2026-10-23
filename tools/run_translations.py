#!/usr/bin/env python3
"""Run OtakuBench line/scene translations against an OpenAI-compatible endpoint.

Model setup belongs to the caller. Never feed gold editorial context into generation.
"""
from __future__ import annotations
import argparse,hashlib,json,os,re,sys,time
from pathlib import Path
from urllib.request import Request,urlopen
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'benchmark/otakubench/data/build'
SYSTEM='Translate the supplied Japanese into faithful, natural English. Preserve nuance, speaker tags, line breaks, intent, ambiguity and characterization. Output only the translation with no commentary.'

TG_PROMPT=('<start_of_turn>user\nYou are a professional Japanese (ja) to English (en) translator. Your goal is to accurately convey the meaning and '
 'nuances of the original Japanese text while adhering to English grammar, vocabulary, and cultural sensitivities.\n'
 'Produce only the English translation, without any additional explanations or commentary. Please translate the following Japanese text into English:\n\n\n')

def load(path):return [json.loads(x) for x in path.read_text(encoding='utf8').splitlines() if x.strip()]

def prompt(case,dataset,mode):
 if dataset=='lines' and mode!='bare':raise ValueError('Legacy line contexts leak editorial answers. Use bare.')
 ja=case['japanese']
 if dataset=='scenes' and mode=='context':
  return 'Previous dialogue (for context ONLY; do not translate it):\n'+ '\n'.join(case['preceding_lines'])+'\n\nTranslate ONLY this new line:\n'+ja
 if dataset=='scenes' and mode=='full':
  instruction='Translate this WHOLE scene, preserving each meaningful line and speaker label'
  if case.get('hook_artifacts'):instruction+='; repair extraction artifacts (duplicated UI lines and mid-word hook linebreaks), but retain intentional stutters'
  return instruction+':\n'+ja
 return 'Translate only this Japanese line:\n'+ja

def choice_file(dataset,mode):
 if dataset=='lines':return DATA/'lines_bare.jsonl'
 return DATA/f'scenes_{mode}.jsonl'

def strip_answer(text,reasoning):
 # If an incomplete thought is returned as content, never treat it as translation.
 if '<think>' in text and '</think>' not in text:return '', 'unclosed thinking'
 text=re.sub(r'<think>.*?</think>','',text,flags=re.S|re.I).strip()
 # Some third-party GGUFs don't mark EOS as a control token, so it is rendered as text (e.g. CAT's '</s>').
 text=re.sub(r'(\s*(</s>|<\|endoftext\|>|<\|im_end\|>|<eos>|<\|eot_id\|>))+\s*$','',text)
 if not text:return '', 'empty answer'
 if re.search(r'(?i)^\s*(i cannot translate|sorry, i can\W*t translate|i\W*m unable to translate)',text):
  return text,'visible refusal'
 return text,None

def make_payload(r,args):
 ja=r['japanese']
 if args.prompt_style=='vntl':
  if args.mode=='context':
   raise ValueError('VNTL contextual-turn history has not yet passed its native prompt canary')
  # v2 card: Metadata (optional), Japanese, English Llama-3 headers.
  # llama-server /completion injects the BOS from model metadata. NEVER emit
  # a literal <|begin_of_text|> as well, or the input may contain two BOS tokens.
  native=re.sub(r'【([^】]+)】\s*',r'[\1]: ',ja)
  names=list(dict.fromkeys(re.findall(r'【([^】]+)】',ja)))
  meta=('<|start_header_id|>Metadata<|end_header_id|>\n\n'
        + '\n'.join('[character] Name: '+x for x in names)
        +'<|eot_id|>') if names else ''
  return {'prompt':meta+'<|start_header_id|>Japanese<|end_header_id|>\n\n'
              +native+'<|eot_id|><|start_header_id|>English<|end_header_id|>\n\n',
          'max_tokens':args.max_tokens,'temperature':0,'stream':False,'stop':['<|eot_id|>']}

 if args.prompt_style=='base_primed':
  # Primed frame for base models: every answer closes with <sep>, so the stop fires instead of the model rambling on.
  return {'prompt':'Japanese: 雨が降っています。\nThe English translation is: It is raining.<sep>\n\n'
                   'Japanese: 【母】「早く寝なさい。」\n【健】「はーい。」\nThe English translation is: 【Mom】 "Go to bed already."\n【Ken】 "Okaaay."<sep>\n\n'
                   'Japanese: 昨日は何も言えなかった。\nThe English translation is: I couldn’t say anything yesterday.<sep>\n\n'
                   'Japanese: '+ja+'\nThe English translation is:',
          'max_tokens':args.max_tokens,'temperature':0,'stream':False,'stop':['<sep>','\nJapanese:']}
 if args.prompt_style=='base_completion':
  # Non-instruction-tuned ancestor control; two independent original exemplars.
  # This arm is diagnostic and must not be ranked alongside instruction-tuned models.
  return {'prompt':'Japanese: 雨が降っています。\nEnglish: It is raining.\n\nJapanese: 昨日は何も言えなかった。\nEnglish: I couldn’t say anything yesterday.\n\nJapanese: '+ja+'\nEnglish:',
          'max_tokens':args.max_tokens,'temperature':0,'stream':False,'stop':['\nJapanese:','<|eot_id|>']}
 if args.prompt_style=='translategemma_text':
  # llama-server drops source/target_lang_code from content parts, so the GGUF's own template renders an
  # en-GB -> en-GB prompt. Render that template's text branch by hand for ja -> en and use raw completion.
  return {'prompt':TG_PROMPT+ja.strip()+'<end_of_turn>\n<start_of_turn>model\n',
          'max_tokens':args.max_tokens,'temperature':0,'stream':False}
 if args.prompt_style=='seedx':
  # Official lab instructions: no chat template; language tag <en> is required.
  # Use raw /completion rather than Chat Completions. Model card discourages unofficial GGUF.
  return {'prompt':f'Translate the following Japanese sentence into English:\n{ja} <en>',
          'max_tokens':args.max_tokens,'temperature':0,'stream':False}
 if args.prompt_style=='hunyuan':
  # Official XX-to-XX instruction and explicitly no system role.
  # Segment translators translate everything they're given, so never wrap our English chat instructions in the source.
  if args.mode=='context' and r.get('preceding_lines'):
   # Model card's contextual template is Chinese-only; with 英语 the 1.8B answers in Chinese on ~40% of scenes.
   # English rendering of the same instruction: 0/31 non-English on the 1.8B.
   content='\n'.join(r['preceding_lines'])+'\nRefer to the information above and translate the following segment into English, without translating the context or adding any explanation:\n'+ja
  else:
   content='Translate the following segment into English, without additional explanation.\n\n'+ja
  messages=[{'role':'user','content':content}]
 elif args.prompt_style=='cat':
  # CyberAgent first-party prompt. llama-server applies the model-specific GGUF chat template.
  # The card documents no context channel, so context mode sends the target line alone (history is unusable).
  messages=[{'role':'user','content':'Translate the following Japanese text into English.\n\n'+ja}]
 elif args.prompt_style=='sugoi':
  messages=[{'role':'system','content':('You are a professional localizer whose primary goal is to translate Japanese to English. '
           'You should use colloquial or slang or nsfw vocabulary if it makes the translation more accurate. '
           'Always respond in English.')},
           {'role':'user','content':prompt(r,args.dataset,args.mode)}]
 elif args.prompt_style=='translategemma':
  messages=[{'role':'user','content':[{'type':'text','source_lang_code':'ja','target_lang_code':'en','text':ja}]}]
 else:
  messages=[{'role':'system','content':SYSTEM},{'role':'user','content':prompt(r,args.dataset,args.mode)}]
 payload={'model':args.model,'messages':messages,'max_tokens':args.max_tokens,'temperature':0,'stream':False}
 if args.prompt_style=='sugoi':
  payload.update(temperature=0.1,top_p=0.95,min_p=0.05,repeat_penalty=1.1)
 return payload

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--dataset',choices=['lines','scenes'],default='lines')
 p.add_argument('--mode',choices=['bare','context','full'],default='bare')
 p.add_argument('--base-url',default='http://127.0.0.1:8125/v1')
 p.add_argument('--prompt-style',choices=['chat','hunyuan','cat','seedx','translategemma','translategemma_text','vntl','sugoi','base_completion','base_primed'],default='chat')
 p.add_argument('--experimental-native-template',action='store_true',help='Native TranslateGemma schema is NOT proven compatible with llama-server; canary first')
 p.add_argument('--model',required=True,help='Actual model identity; not shared alias')
 p.add_argument('--run-id',default=None,help='Reproducible unique inference arm, including quant and reasoning; defaults to model/style')
 p.add_argument('--quant-revision',default=None,help='Actual immutable GGUF repository SHA from resolver')
 p.add_argument('--quant-attested',action='store_true',help='Matrix-runner verified Hugging Face GGUF pin and file metadata')
 p.add_argument('--canary-passed',action='store_true',help='This full batch follows a successful five-case canary in matrix runner')
 p.add_argument('--api-key',default=os.getenv('LOCAL_LLM_API_KEY','local'))
 p.add_argument('--max-tokens',type=int,default=2048)
 p.add_argument('--limit',type=int,default=0)
 p.add_argument('--split',choices=['all','dev','eval'],default='all')
 p.add_argument('--output',type=Path,required=True)
 p.add_argument('--timeout',type=int,default=180)
 p.add_argument('--execute',action='store_true')
 args=p.parse_args()
 if args.dataset=='lines' and args.mode!='bare':p.error('No valid contextual 250-line arm')
 if args.dataset=='lines' and args.mode=='full':p.error('No full line arm')
 if args.prompt_style in ('seedx','translategemma','base_completion') and args.mode!='bare':p.error('Seed-X/TranslateGemma formatting not qualified for contextual/full mode')
 if args.prompt_style=='vntl' and args.mode=='context':p.error('VNTL context mode not qualified; bare lines and full scenes are supported')
 if args.prompt_style=='translategemma' and not args.experimental_native_template:p.error('TranslateGemma native schema requires explicit --experimental-native-template; zero completed verified runs')
 cases=load(choice_file(args.dataset,args.mode))
 if args.split!='all':cases=[x for x in cases if x['split']==args.split]
 if args.limit:cases=cases[:args.limit]
 if not cases:p.error('No matching cases')
 digest=hashlib.sha256(choice_file(args.dataset,args.mode).read_bytes()).hexdigest()
 run_id=args.run_id or (args.model+':'+args.prompt_style)
 print(json.dumps({'dataset':args.dataset,'mode':args.mode,'cases':len(cases),'model':args.model,'run_id':run_id,'style':args.prompt_style,'benchmark_sha256':digest,'execute':args.execute},indent=2))
 if not args.execute:
  print(json.dumps({'first_messages':make_payload(cases[0],args)['messages'] if 'messages' in make_payload(cases[0],args) else make_payload(cases[0],args)['prompt']},ensure_ascii=False,indent=2));return 0
 args.output.parent.mkdir(exist_ok=True,parents=True)
 done=set()
 if args.output.exists():
  for r in load(args.output):
   if r.get('translation') and r.get('model')==args.model and r.get('run_id')==run_id and r.get('mode')==args.mode and r.get('dataset')==args.dataset and r.get('source_sha256')==digest and r.get('prompt_style')==args.prompt_style:done.add(r['id'])
 failures=0
 with args.output.open('a',encoding='utf8') as f:
  for i,r in enumerate(cases,1):
   if r['id'] in done:continue
   payload=make_payload(r,args)
   t=time.perf_counter();rec={'id':r['id'],'dataset':args.dataset,'mode':args.mode,'model':args.model,'run_id':run_id,'source_sha256':digest,'prompt_style':args.prompt_style,'quant_repo_sha':args.quant_revision,'quant_attested':args.quant_attested,'canary_passed':args.canary_passed}
   try:
    req=Request(args.base_url.rstrip('/')+('/completions' if args.prompt_style in ('seedx','vntl','base_completion') else '/chat/completions'),data=json.dumps(payload,ensure_ascii=False).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+args.api_key},method='POST')
    with urlopen(req,timeout=args.timeout) as resp:data=json.load(resp)
    if args.prompt_style in ('seedx','vntl','base_completion'):
     c=data['choices'][0];reason=c.get('finish_reason');msg={};raw=c.get('text','')
    else:
     c=data['choices'][0];reason=c.get('finish_reason');msg=c['message'];raw=msg.get('content') or ''
    if isinstance(raw,list):raw='\n'.join(p.get('text','') for p in raw if isinstance(p,dict))
    translation,error=strip_answer(raw,msg.get('reasoning_content'))
    if reason not in ('stop','end_turn'):error=f'incomplete finish reason {reason}'
    rec.update(translation=translation,raw_response=raw,finish_reason=reason,usage=data.get('usage',{}),error=error)
   except Exception as e:rec.update(translation='',error=f'{type(e).__name__}: {str(e)[:200]}')
   rec['seconds']=round(time.perf_counter()-t,3)
   if rec.get('error'):failures+=1
   else:failures=0
   f.write(json.dumps(rec,ensure_ascii=False)+'\n');f.flush()
   print(f"{i}/{len(cases)} {r['id']} {rec['seconds']}s: {'OK' if not rec.get('error') else rec['error']}",flush=True)
   if failures>=3:print('Three consecutive errors; aborting. Check model/template before proceeding.',file=sys.stderr);return 3
 return 0
if __name__=='__main__':raise SystemExit(main())
