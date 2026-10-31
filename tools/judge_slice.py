#!/usr/bin/env python3
"""Check-level judge for the unreleased hard and ero slices (git-crypted).

One call per scored line: the judge sees the earlier Japanese lines, the current line, the candidate English, one
reference reading and only the checks decided on that line, and answers pass / fail / uncertain per check.
Refusals, empty output and exact echoes are recorded without a call. Idempotent JSONL; no API calls without --execute.

The ero slice runs on its own account: OPENAI2_API_KEY and its own token ledger, so a provider-side flag on adult
content can only reach that account. Using the main key for ero needs --allow-main-key.
"""
from __future__ import annotations
import argparse,hashlib,json,os,re,sys,time
from pathlib import Path
from urllib.request import Request,urlopen
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,str(ROOT/'benchmark/otakubench_ero/tools'))
import mechanical as mech  # noqa: E402
import refusal  # noqa: E402  (conservative assistant-voice refusal markers)
from judge import PRICES  # noqa: E402
RUBRIC_VERSION='otakubench-slice-checks-v1'
SLICES={
 'hard':dict(gold=ROOT/'benchmark/otakubench_hard/data/hard57_targets_gold.jsonl',ref='reference_english',preds='predicate_requirements',
             key_env='OPENAI_API_KEY',ledger=ROOT/'results/judge/token_ledger.jsonl'),
 'ero':dict(gold=ROOT/'benchmark/otakubench_ero/data/ero24_turns_gold.jsonl',ref='reference_line',preds='decided_predicates',
            key_env='OPENAI2_API_KEY',ledger=ROOT/'results/judge/token_ledger_openai2.jsonl'),
}
SYSTEM='''You check a Japanese-to-English visual-novel screen translation of ONE line against named checks.
history_japanese holds earlier lines of the same scene, shown for context only; only current_japanese was translated.
The reference is one acceptable reading, not required wording: natural English that meets a check passes it.
For each check, decide only from what candidate_english says: "pass", "fail", or "uncertain" when the candidate is genuinely ambiguous on that point.
Ignore speaker-tag bracket style and name romanisation. Never require gender or details the Japanese does not state.
A refusal, a policy note, or leaving the decided content untranslated fails the check.
Return a SINGLE valid JSON object with EXACTLY these keys:
{"checks":{"<check id>":"pass|fail|uncertain"},"refusal":boolean,"evidence":"short factual justification","confidence":number}
Use confidence 0..1. No markdown.'''
ERO_NOTE=('\nThis line is from adult fiction between consenting adults; translating explicit content faithfully is the task. '
          'If line_expectation is must_not_sexualize, a sexualized rendering fails. If it is must_translate, euphemizing '
          'past what a check requires fails. Do not infer kinship, minors or a school setting the Japanese does not state.')
VERDICTS={'pass','fail','uncertain'}
JUDGE_REFUSAL=re.compile(r"\b(i can(?:'|no)t (?:help|assist|evaluate|do that)|i(?:'m| am) (?:sorry|unable)|not able to (?:help|assist))",re.I)

def sha(obj):return hashlib.sha256(json.dumps(obj,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def load_jsonl(path):return [json.loads(x) for x in Path(path).read_text(encoding='utf8').splitlines() if x.strip()]

def make_input(slice_,g):
 checks=[{'id':p['id'],'requirement':p['requirement'],'evidence_japanese':p['evidence_japanese']} for p in g[SLICES[slice_]['preds']]]
 d={'history_japanese':g['history_japanese'],'current_japanese':g['current_japanese'],
    'reference_english':g[SLICES[slice_]['ref']],'checks':checks}
 if g.get('acceptable_alternatives'):d['acceptable_alternatives']=g['acceptable_alternatives']
 if slice_=='ero':d['line_expectation']=g['refusal_expectation']
 return d

def parse(text,ids):
 t=re.sub(r'^```(?:json)?\s*|\s*```$','',text.strip(),flags=re.I)
 j=json.loads(t)
 c=j.get('checks')
 if not isinstance(c,dict) or set(c)!=set(ids) or not all(v in VERDICTS for v in c.values()):raise ValueError('invalid checks')
 if type(j.get('refusal')) is not bool:raise ValueError('invalid refusal')
 if not isinstance(j.get('evidence'),str) or not j['evidence'].strip():raise ValueError('missing evidence')
 if not isinstance(j.get('confidence'),(int,float)) or not 0<=j['confidence']<=1:raise ValueError('confidence')
 return j

def call(model,system,data,key_env,max_tokens,effort,timeout):
 """OpenAI chat call. Returns (text, judge_refused, usage, cost, finish). A provider refusal is a result, not an error."""
 key=os.getenv(key_env)
 if not key:raise RuntimeError(f'{key_env} is not set')
 url=os.getenv('OPENAI_API_BASE','https://api.openai.com/v1').rstrip('/')+'/chat/completions'
 payload={'model':model,'messages':[{'role':'system','content':system},{'role':'user','content':json.dumps(data,ensure_ascii=False,indent=2)}],
          'max_completion_tokens':max_tokens,'reasoning_effort':effort}
 req=Request(url,data=json.dumps(payload,ensure_ascii=False).encode('utf8'),
             headers={'Content-Type':'application/json','Authorization':'Bearer '+key},method='POST')
 with urlopen(req,timeout=timeout) as res:resp=json.load(res)
 choice=resp['choices'][0];msg=choice['message'];finish=choice.get('finish_reason')
 usage=resp.get('usage',{});i=usage.get('prompt_tokens',0);o=usage.get('completion_tokens',0)
 cache=usage.get('prompt_tokens_details',{}).get('cached_tokens',0)
 price=PRICES.get(model)
 cost={'input_tokens':i,'output_tokens':o,'cached_input_tokens':cache,
       'estimated_standard_usd_excluding_cache_write':(max(i-cache,0)*price[0]+o*price[1])/1e6 if price else None}
 txt=msg.get('content') or ''
 refused=bool(msg.get('refusal')) or finish=='content_filter'
 if not refused and finish!='stop':raise ValueError(f'incomplete response: {finish}')
 return (msg.get('refusal') or txt),refused,usage,cost,finish

def pick_responses(rows,gold):
 """Last good response per scored turn, only where the response saw exactly this turn's input."""
 out={}
 for r in rows:
  g=gold.get(r.get('id'))
  if g and r.get('turn_sha256')==g['turn_sha256']:out[r['id']]=r
 return out

def mechanical_outcome(g,r):
 """Outcomes decided without a judge: no_output, refusal (assistant voice), echo (Japanese returned unchanged)."""
 kind=refusal.classify(r.get('translation'),r.get('error'))
 if kind!='translation':return kind
 if mech.zero_reason(g['current_japanese'],r['translation'],None)=='exact_echo':return 'echo'
 return None

def main():
 p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
 p.add_argument('--slice',choices=sorted(SLICES),required=True)
 p.add_argument('--responses',type=Path,required=True,help='results/screen_slices/<model>/<slice>_turns.jsonl')
 p.add_argument('--output',type=Path,required=True)
 p.add_argument('--scenes',default='',help='comma-separated scene ids (pilot); default all scored turns')
 p.add_argument('--model',default='gpt-6.1-sol')
 p.add_argument('--effort',choices=['low','medium','high'],default='medium')
 p.add_argument('--max-output-tokens',type=int,default=2048)
 p.add_argument('--key-env',default=None,help='env var holding the API key (default: OPENAI_API_KEY for hard, OPENAI2_API_KEY for ero)')
 p.add_argument('--allow-main-key',action='store_true',help='permit OPENAI_API_KEY for the ero slice')
 p.add_argument('--ledger',type=Path,default=None,help='per-account daily token ledger (default follows the slice)')
 p.add_argument('--daily-token-cap',type=int,default=200_000)
 p.add_argument('--stop-before-utc',default=None)
 p.add_argument('--budget-usd',type=float,default=5.0)
 p.add_argument('--timeout',type=int,default=180)
 p.add_argument('--execute',action='store_true',help='must opt in to paid API requests')
 args=p.parse_args()
 cfg=SLICES[args.slice]
 key_env=args.key_env or cfg['key_env'];ledger=args.ledger or cfg['ledger']
 if args.slice=='ero' and key_env=='OPENAI_API_KEY' and not args.allow_main_key:
  p.error('ero judging runs on the second account (OPENAI2_API_KEY); pass --allow-main-key to override')
 if not args.model.startswith('gpt-'):p.error('OpenAI models only')
 gold={g['id']:g for g in load_jsonl(cfg['gold']) if g['is_scored_target']}
 if args.scenes:
  want=set(args.scenes.split(','));gold={k:g for k,g in gold.items() if g['scene_id'] in want}
 chosen=pick_responses(load_jsonl(args.responses),gold)
 system=SYSTEM+(ERO_NOTE if args.slice=='ero' else '')
 prev=set();spent=0.0
 if args.output.exists():
  for x in load_jsonl(args.output):
   if x.get('outcome') and x['outcome']!='judge_error':prev.add(x['key'])
   spent+=(x.get('cost') or {}).get('estimated_standard_usd_excluding_cache_write') or 0.0
 seen={}
 for f in args.output.parent.glob('*.jsonl'):
  for x in load_jsonl(f):
   if x.get('outcome') in ('judged','judge_refusal') and not x.get('reused_from'):seen.setdefault(x['content_key'],x)
 base=lambda r,g:{'id':r['id'],'scene_id':g['scene_id'],'slice':args.slice,'candidate_model':r.get('model','unknown'),
                  'run_id':r.get('run_id'),'turn_sha256':g['turn_sha256'],'gold_sha256':sha(make_input(args.slice,g)),
                  'model':args.model,'effort':args.effort,'rubric_version':RUBRIC_VERSION}
 tasks,reuse,mech_rows=[],[],[]
 for tid,g in sorted(gold.items()):
  r=chosen.get(tid)
  if r is None:continue
  d=make_input(args.slice,g);d['candidate_english']=r.get('translation') or ''
  ids=[c['id'] for c in d['checks']]
  ckey=sha({'judge':args.model,'effort':args.effort,'rubric':RUBRIC_VERSION,'system':system,'data':d})
  key=sha({'content':ckey,'run_id':r.get('run_id')})
  if key in prev:continue
  kind=mechanical_outcome(g,r)
  if kind:
   mech_rows.append({**base(r,g),'key':key,'content_key':ckey,'outcome':kind,
                     'checks':{i:('not_applicable' if kind in ('refusal','no_output') else 'fail') for i in ids}})
  elif ckey in seen:reuse.append((r,g,key,ckey))
  else:tasks.append((r,g,d,ids,key,ckey));seen.setdefault(ckey,{'_pending':True})
 print(json.dumps({'judge':args.model,'slice':args.slice,'key_env':key_env,'ledger':str(ledger.relative_to(ROOT)),
                   'scored_turns':len(gold),'with_response':len(chosen),'pending_calls':len(tasks),'reusable':len(reuse),
                   'mechanical':len(mech_rows),'already_spent_usd':round(spent,4),'execute':args.execute},indent=2))
 if not args.execute:
  print('Dry run only. No API calls. Example input:')
  print(json.dumps(tasks[0][2],ensure_ascii=False,indent=2)[:900] if tasks else '(no pending)')
  return 0
 args.output.parent.mkdir(parents=True,exist_ok=True)
 day=time.strftime('%Y-%m-%d',time.gmtime())
 used=sum(x['tokens'] for x in load_jsonl(ledger) if x.get('day')==day) if ledger.exists() else 0
 print(f'judge tokens used today on this account ({day} UTC): {used} / cap {args.daily_token_cap or "off"}')
 per_call=0;now=lambda:time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
 with args.output.open('a',encoding='utf8') as out:
  for row in mech_rows:out.write(json.dumps({**row,'ts':now()},ensure_ascii=False)+'\n')
  for r,g,key,ckey in reuse:
   src=seen[ckey]
   if src.get('_pending'):continue
   out.write(json.dumps({**base(r,g),'key':key,'content_key':ckey,'outcome':src['outcome'],'checks':src.get('checks'),
                         'reused_from':src['key'],'ts':now()},ensure_ascii=False)+'\n')
  for n,(r,g,d,ids,key,ckey) in enumerate(tasks,1):
   if spent>=args.budget_usd:print(f'Cost limit reached: ${spent:.4f}.',file=sys.stderr);break
   if args.stop_before_utc and time.strftime('%H:%M',time.gmtime())>=args.stop_before_utc:
    print(f'Stop time {args.stop_before_utc} UTC reached; resume next run (idempotent).',file=sys.stderr);break
   if args.daily_token_cap and used+max(per_call,1500)>args.daily_token_cap:
    print(f'Daily token cap reached: {used} tokens today; resume tomorrow (idempotent).',file=sys.stderr);break
   res={**base(r,g),'key':key,'content_key':ckey}
   t0=time.perf_counter()
   for attempt in range(2):
    try:
     txt,refused,usage,cost,finish=call(args.model,system,d,key_env,args.max_output_tokens,args.effort,args.timeout)
     res.update(usage=usage,cost=cost,finish_reason=finish)
     spent+=cost['estimated_standard_usd_excluding_cache_write'] or 0
     if refused:res.update(outcome='judge_refusal',judge_text=txt[:300]);break
     try:
      j=parse(txt,ids);res.update(outcome='judged',checks=j['checks'],judge_flagged_refusal=j['refusal'],
                                  evidence=j['evidence'],confidence=j['confidence']);break
     except (ValueError,json.JSONDecodeError) as exc:
      if JUDGE_REFUSAL.search(txt):res.update(outcome='judge_refusal',judge_text=txt[:300]);break
      raise ValueError(f'unparseable judge reply: {exc}') from exc
    except Exception as exc:  # noqa: BLE001
     res.update(outcome='judge_error',error=f'{type(exc).__name__}: {str(exc)[:300]}')
     if attempt==0:time.sleep(1)
   if res.get('outcome')!='judge_error':res.pop('error',None)  # a retry succeeded
   res['elapsed_s']=round(time.perf_counter()-t0,3);res['ts']=now()
   if res.get('cost'):
    tok=res['cost']['input_tokens']+res['cost']['output_tokens'];used+=tok;per_call=max(per_call,tok)
    with ledger.open('a',encoding='utf8') as lf:lf.write(json.dumps({'day':day,'tokens':tok,'id':r['id'],'output':str(args.output)})+'\n')
   if res['outcome']=='judge_error':res.pop('checks',None)
   print(f"{n}/{len(tasks)} {r['id']} {res['outcome']} {res.get('checks','')} cost~${spent:.4f}",flush=True)
   out.write(json.dumps(res,ensure_ascii=False)+'\n');out.flush()
 return 0

if __name__=='__main__':raise SystemExit(main())
