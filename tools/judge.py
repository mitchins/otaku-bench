#!/usr/bin/env python3
"""Automated OtakuBench LLM judge for OpenAI GPT-6.1 Sol / Anthropic Opus 5.5.

Idempotent JSONL judgments; measured token accounting; no API calls without --execute.
No claim of validation until the calibration suite and an independent judge agree.
"""
from __future__ import annotations
import argparse,hashlib,json,os,re,sys,time
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(__file__).resolve().parent))
import mechanical as mech  # exact echoes are scored 0 mechanically (judge_table), never sent to the judge
GOLD=ROOT/'benchmark/otakubench/data/build'
RUBRIC_VERSION='otakubench-4.0-judge-v1'
PRICES={'gpt-6.1-sol':(2,10),'claude-opus-5-5':(4,20),'claude-sonnet-5-5':(2,10)} # standard USD / 1M
SYSTEM='''You evaluate Japanese-to-English translations as a bilingual literary localization assessor.
Score the actual translation, not its lexical overlap with a reference. Gold is ONE possible reading and may have mistakes.
Preserve speaker intent, ambiguity, social hierarchy, idioms, style, polarity, time, referents and narrative perspective.
Accept creative, fluent equivalents and deliberate trailing-off as valid. NEVER demand invented gender or plot details.
Do not penalize safety-constrained subjects: grade explicit translation refusals, censoring and omissions as failures.
Score adequacy 0..4, pragmatic nuance/voice 0..4, English fluency 0..2.
4/4 adequacy and pragmatics: faithful; 3: minor; 2: significant loss; 1: major misunderstanding; 0: contradictory/unusable.
Fluency 2: natural, 1: awkward, 0: broken. Keep judgments independent of model name.
Flags: NEG, AGENT, ASPECT, MOD, IDIOM, VOICE, KEIGO, IMPL, CULT, HUMOUR, ADD, OMIT, REFUSAL, TERMINOLOGY, FORMAT, AMBIGUITY.
If the supplied reference or Japanese is problematic, set gold_uncertain true and explain concisely rather than forcing wrong scoring.
Return a SINGLE valid JSON object with EXACTLY these keys:
{"adequacy":integer,"pragmatics":integer,"fluency":integer,"flags":[string],"refusal":boolean,"gold_uncertain":boolean,"confidence":number,"evidence":"short factual justification","acceptable_variant":boolean}
Use confidence 0..1. No markdown.''' 

def sha(obj):return hashlib.sha256(json.dumps(obj,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def load_jsonl(path):return [json.loads(x) for x in path.read_text(encoding='utf8').splitlines() if x.strip()]
def gold(dataset):
 p=GOLD/('lines_gold.jsonl' if dataset=='lines' else 'scenes_gold.jsonl')
 return {r['id']:r for r in load_jsonl(p)}
def make_input(g,translation,dataset,mode,annotated=False):
 if dataset=='lines':
  if mode!='bare':raise ValueError('250 line probes have no valid source-derived preceding context. Use --mode bare.')
  data={'source_japanese':g['japanese'],'candidate_english':translation,'reference_english':g['english_reference'],
        'acceptable_alternates':g['alternate_references']}
 else:
  if mode=='full':jp=g['full_japanese'];reference=g['full_english_reference']
  elif mode=='context':jp=g['target_japanese'];reference=g['english_reference']
  elif mode=='bare':jp=g['target_japanese'];reference=g['english_reference']
  else:raise ValueError('Invalid scene mode')
  data={'source_japanese':jp,'candidate_english':translation,'reference_english':reference}
  if g.get('alternate_references') and mode!='full':data['acceptable_alternates']=g['alternate_references']
  if mode=='full' and g.get('hook_artifacts'):data['source_extraction_policy']='Exactly duplicated UI lines and midword wraps are text-hook artifacts; normalize those, preserve genuine stammers and narrative repetition.'
  if mode=='context':data['actual_preceding_japanese']=g['context_lines']
 if annotated:data['editorial_translation_trap_note']=g['translation_note']
 return data

def parse_json(text):
 # Strict JSON response; tolerate only a fenced JSON block, not arbitrary explanation.
 t=text.strip();t=re.sub(r'^```(?:json)?\s*|\s*```$','',t,flags=re.I)
 j=json.loads(t)
 for k,l,h in [('adequacy',0,4),('pragmatics',0,4),('fluency',0,2)]:
  if not isinstance(j.get(k),int) or isinstance(j[k],bool) or not l<=j[k]<=h:raise ValueError(f'invalid {k}')
 for k in ['refusal','gold_uncertain','acceptable_variant']:
  if type(j.get(k)) is not bool:raise ValueError(f'invalid {k}')
 if not isinstance(j.get('flags'),list) or not all(isinstance(x,str) for x in j['flags']):raise ValueError('invalid flags')
 if not isinstance(j.get('evidence'),str) or not j['evidence'].strip():raise ValueError('missing evidence')
 if not isinstance(j.get('confidence'),(float,int)) or not 0<=j['confidence']<=1:raise ValueError('confidence')
 return j

def api_request(provider,model,system,data,max_tokens,effort,timeout):
 content=json.dumps(data,ensure_ascii=False,indent=2)
 if provider=='openai':
  key=os.getenv('OPENAI_API_KEY')
  if not key:raise RuntimeError('OPENAI_API_KEY is not set')
  url=os.getenv('OPENAI_API_BASE','https://api.openai.com/v1').rstrip('/')+'/chat/completions'
  payload={'model':model,'messages':[{'role':'system','content':system},{'role':'user','content':content}],
           'max_completion_tokens':max_tokens,'reasoning_effort':effort}
  headers={'Authorization':'Bearer '+key}
 elif provider=='anthropic':
  key=os.getenv('ANTHROPIC_API_KEY')
  if not key:raise RuntimeError('ANTHROPIC_API_KEY is not set')
  url=os.getenv('ANTHROPIC_API_BASE','https://api.anthropic.com/v1').rstrip('/')+'/messages'
  payload={'model':model,'max_tokens':max_tokens,'system':system,'messages':[{'role':'user','content':content}],
           'output_config':{'effort':effort}}
  headers={'x-api-key':key,'anthropic-version':'2023-06-01'}
 else:raise ValueError(provider)
 req=Request(url,data=json.dumps(payload,ensure_ascii=False).encode('utf8'),headers={'Content-Type':'application/json',**headers},method='POST')
 with urlopen(req,timeout=timeout) as res:resp=json.load(res)
 if provider=='openai':
  choice=resp['choices'][0];msg=choice['message']; finish=choice.get('finish_reason')
  txt=msg.get('content') or ''
  if finish not in ('stop','end_turn'):raise ValueError(f'incomplete response: {finish}')
  usage=resp.get('usage',{});i=usage.get('prompt_tokens',0);o=usage.get('completion_tokens',0);cache=usage.get('prompt_tokens_details',{}).get('cached_tokens',0)
 else:
  txt='\n'.join(c.get('text','') for c in resp.get('content',[]) if c.get('type')=='text')
  finish=resp.get('stop_reason')
  if finish not in ('end_turn','stop_sequence'):raise ValueError(f'incomplete response: {finish}')
  usage=resp.get('usage',{});i=usage.get('input_tokens',0);o=usage.get('output_tokens',0);cache=usage.get('cache_read_input_tokens',0)
 if isinstance(txt,list):txt='\n'.join(x.get('text','') for x in txt if isinstance(x,dict))
 # Include all billed output incl hidden reasoning. Never infer unreported usage as zero-cost.
 price=PRICES.get(model)
 cost=(max(i-cache,0)*price[0]+o*price[1])/1e6 if price else None
 return txt,usage,{'input_tokens':i,'output_tokens':o,'cached_input_tokens':cache,'estimated_standard_usd_excluding_cache_write':cost},finish

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--responses',type=Path,required=True,help='model inference JSONL, including id / translation')
 p.add_argument('--dataset',choices=['lines','scenes'],required=True)
 p.add_argument('--mode',choices=['bare','context','full'],default='bare')
 p.add_argument('--provider',choices=['openai','anthropic'],default='openai')
 p.add_argument('--model',default='gpt-6.1-sol')
 p.add_argument('--output',type=Path,required=True)
 p.add_argument('--effort',choices=['low','medium','high'],default='medium')
 p.add_argument('--max-output-tokens',type=int,default=2048)
 p.add_argument('--limit',type=int,default=0)
 p.add_argument('--split',choices=['all','dev','eval'],default='all')
 p.add_argument('--budget-usd',type=float,default=10.0,help='STOP AFTER measured budget; final call may exceed budget')
 p.add_argument('--annotated',action='store_true',help='Second pass only: show trap notes; default avoids leakage')
 p.add_argument('--timeout',type=int,default=180)
 p.add_argument('--execute',action='store_true',help='Must opt in to paid API requests')
 p.add_argument('--daily-token-cap',type=int,default=200_000,help='stop before this many judge tokens (in+out) per UTC day, summed over all runs via the ledger; 0 disables')
 p.add_argument('--ledger',type=Path,default=ROOT/'results/judge/token_ledger.jsonl')
 p.add_argument('--stop-before-utc',default=None,help='HH:MM; make no new call at or after this UTC time (keeps a late run inside the day)')
 args=p.parse_args()
 if args.dataset=='lines' and args.mode!='bare':p.error('line benchmark only supports bare mode; old context mode was leaking answers')
 if args.budget_usd<=0 or args.max_output_tokens<300:p.error('invalid resource budget')
 if args.provider=='openai' and not args.model.startswith('gpt-'):p.error('Model must be compatible with selected provider')
 if args.provider=='anthropic' and not args.model.startswith('claude-'):p.error('Model must be compatible with selected provider')
 refs=gold(args.dataset)
 blind_file=GOLD/('lines_bare.jsonl' if args.dataset=='lines' else f'scenes_{args.mode}.jsonl')
 inference_sha=hashlib.sha256(blind_file.read_bytes()).hexdigest()
 try:rows=load_jsonl(args.responses)
 except FileNotFoundError:p.error('Response file does not exist')
 filtered={}
 for r in rows:
  if r.get('id') in refs and r.get('translation') and not r.get('error') and r.get('source_sha256')==inference_sha:
   if r.get('mode',args.mode)!=args.mode:continue
   if r.get('dataset',args.dataset)!=args.dataset:continue
   if args.split!='all' and refs[r['id']]['split']!=args.split:continue
   # preserve last good response; model label included in fingerprint
   filtered[(r['id'],r.get('model','unknown'),r.get('run_id'))]=r
 chosen=list(filtered.values())
 if args.limit:chosen=chosen[:args.limit]
 if not chosen:p.error('No eligible current-corpus translations: source_sha256 is required and must match generated blind dataset; stale or unpinned inferences are refused')
 prev={};spent=0.0
 if args.output.exists():
  for x in load_jsonl(args.output):
   if x.get('key') and 'score' in x:prev[x['key']]=x
   if x.get('model')==args.model:spent+=x.get('cost',{}).get('estimated_standard_usd_excluding_cache_write') or 0.0
 tasks=[]
 for r in chosen:
  d=make_input(refs[r['id']],r['translation'],args.dataset,args.mode,args.annotated)
  if mech.zero_reason(d['source_japanese'],r['translation'],None):continue
  key=sha({'judge':args.model,'provider':args.provider,'effort':args.effort,'rubric':RUBRIC_VERSION,'data':d,'source_model':r.get('model'),'run_id':r.get('run_id',r.get('model')),'mode':args.mode})
  if key not in prev:tasks.append((r,d,key))
 print(json.dumps({'judge':args.model,'provider':args.provider,'dataset':args.dataset,'mode':args.mode,'eligible':len(chosen),'pending':len(tasks),'already_spent_usd':round(spent,4),'execute':args.execute,'budget_usd':args.budget_usd},indent=2))
 if not args.execute:
  print('Dry run only. No paid API calls. Example input:')
  print(json.dumps(tasks[0][1],ensure_ascii=False,indent=2)[:800] if tasks else '(no pending)')
  return 0
 args.output.parent.mkdir(parents=True,exist_ok=True)
 # Free data-sharing tokens are an org-wide daily allowance; count every judge call, whichever file it went to.
 day=time.strftime('%Y-%m-%d',time.gmtime())
 used_today=sum(x['tokens'] for x in load_jsonl(args.ledger) if x.get('day')==day) if args.ledger.exists() else 0
 print(f'judge tokens used today ({day} UTC): {used_today} / cap {args.daily_token_cap or "off"}')
 per_call=0
 with args.output.open('a',encoding='utf8') as out:
  for n,(r,d,key) in enumerate(tasks,1):
   if spent>=args.budget_usd:
    print(f'Cost limit reached: ${spent:.4f}; stopped before another call.',file=sys.stderr);break
   if args.stop_before_utc and time.strftime('%H:%M',time.gmtime())>=args.stop_before_utc:
    print(f'Stop time {args.stop_before_utc} UTC reached; resume next run (idempotent).',file=sys.stderr);break
   # leave room for one more call of the size seen so far
   if args.daily_token_cap and used_today+max(per_call,1500)>args.daily_token_cap:
    print(f'Daily token cap reached: {used_today} tokens today; resume tomorrow (idempotent).',file=sys.stderr);break
   result={'key':key,'gold_sha256':sha(refs[r['id']]),'id':r['id'],'candidate_model':r.get('model','unknown'),'run_id':r.get('run_id',r.get('model','unknown')),'model':args.model,'provider':args.provider,
           'dataset':args.dataset,'mode':args.mode,'rubric_version':RUBRIC_VERSION,'annotated':args.annotated,
           'quant_attested':bool(r.get('quant_attested')),'quant_repo_sha':r.get('quant_repo_sha'),
           'canary_passed':bool(r.get('canary_passed'))}
   t0=time.perf_counter()
   for attempt in range(2):
    try:
     txt,usage,cost,finish=api_request(args.provider,args.model,SYSTEM,d,args.max_output_tokens,args.effort,args.timeout)
     result.update(score=parse_json(txt),usage=usage,cost=cost,finish_reason=finish)
     spent+=(cost['estimated_standard_usd_excluding_cache_write'] or 0)
     break
    except Exception as exc:
     result['error']=f'{type(exc).__name__}: {str(exc)[:300]}'
     if attempt==0:time.sleep(1)
   result['elapsed_s']=round(time.perf_counter()-t0,3)
   result['ts']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
   if 'cost' in result:
    tok=result['cost']['input_tokens']+result['cost']['output_tokens']
    used_today+=tok;per_call=max(per_call,tok)
    with args.ledger.open('a',encoding='utf8') as lf:lf.write(json.dumps({'day':day,'tokens':tok,'id':r['id'],'output':str(args.output)})+'\n')
   if 'score' in result:
    result.pop('error',None)
    s=result['score'];print(f"{n}/{len(tasks)} {r['id']} => {s['adequacy']+s['pragmatics']+s['fluency']}/10 cost~${spent:.4f}",flush=True)
   else:print(f"{n}/{len(tasks)} {r['id']} JUDGE_ERROR {result.get('error')}",file=sys.stderr)
   out.write(json.dumps(result,ensure_ascii=False)+'\n');out.flush()
 print('Recorded estimates are standard prices, not Batch/Flex pricing; cached inputs and cache write charges may differ. Review actual provider bills.')
 return 0
if __name__=='__main__':raise SystemExit(main())
