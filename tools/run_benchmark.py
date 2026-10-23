#!/usr/bin/env python3
"""Local OpenAI-compatible JP-Media-250 runner with native TranslateGemma support.

This consumes the bundled 250-item set without changing references. Doesn't rank
models by reference overlap. Output is append-only and resumable by case ID.
"""
from __future__ import annotations
import argparse, json, os, re, sys, time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[1]
BENCHMARK=ROOT/'benchmark'/'jpmedia250'
SYSTEM=('You are a professional Japanese-to-English translator. Translate the Japanese text '
        'into faithful, natural English. Preserve ambiguity, emotional nuance and social context. '
        'Do not explain; output only the translation.')
CANARY_INDICES=(0, 30, 88, 150, 211)


def make_messages(case:dict,style:str,mode:str):
    if style=='translategemma':
        if mode!='bare':
            raise ValueError('Native TranslateGemma cannot accept separate scene context. Use --mode bare.')
        # Official Google model-card structure; no system role.
        return [{'role':'user','content':[{'type':'text','source_lang_code':'ja',
                     'target_lang_code':'en','text':case['japanese']}]}]
    text=case['japanese']
    if mode=='context':
        text='Scene context (not text to translate): '+case['scene_context']+'\n\nJapanese text:\n'+text
    return [{'role':'system','content':SYSTEM},{'role':'user','content':text}]


def extract_text(value):
    if isinstance(value,str): return value
    if isinstance(value,list):
        return '\n'.join(v.get('text','') for v in value if isinstance(v,dict) and v.get('type')=='text')
    return ''


def clean(text):
    # Only strip a closed <think> block; if reasoning is unclosed, mark output empty.
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.S|re.I).strip()
    if text.startswith('<think>') and '</think>' not in text:
        return ''
    if len(text)>1 and text[0]=='"'==text[-1] and text.count('"')==2:
        text=text[1:-1]
    return text.strip()


def request_api(url,key,payload,timeout,retries):
    data=json.dumps(payload,ensure_ascii=False).encode()
    for attempt in range(retries+1):
        req=Request(url,data=data,headers={'Content-Type':'application/json',
                    'Authorization':f'Bearer {key}'},method='POST')
        try:
            with urlopen(req,timeout=timeout) as res:
                return json.load(res)
        except (HTTPError,URLError,TimeoutError):
            if attempt==retries: raise
            time.sleep(min(2**attempt,5))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base-url',default='http://127.0.0.1:8125/v1')
    p.add_argument('--model',default='jpmedia250')
    p.add_argument('--api-key',default=os.environ.get('OPENAI_API_KEY','local'))
    p.add_argument('--mode',choices=['bare','context'],default='bare')
    p.add_argument('--prompt-style',choices=['chat','translategemma'],default='chat')
    p.add_argument('--split',choices=['all','dev','eval'],default='all')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--max-tokens',type=int,default=2048)
    p.add_argument('--temperature',type=float,default=0)
    p.add_argument('--timeout',type=int,default=180)
    p.add_argument('--retries',type=int,default=1)
    p.add_argument('--limit',type=int,default=0)
    p.add_argument('--canary',action='store_true',help='Five stratified cases, spanning categories')
    p.add_argument('--max-consecutive-errors',type=int,default=3)
    p.add_argument('--dry-run',action='store_true')
    args=p.parse_args()
    source='jpmedia250_blind_with_context.jsonl' if args.mode=='context' else 'jpmedia250_blind_japanese_only.jsonl'
    cases=[json.loads(x) for x in (BENCHMARK/'data'/'build'/source).read_text().splitlines()]
    if args.canary:
        cases=[cases[n] for n in CANARY_INDICES]
    elif args.split!='all':
        cases=[x for x in cases if x['split']==args.split]
    if args.limit:
        cases=cases[:args.limit]
    if not cases: p.error('No matching cases')
    if args.prompt_style=='translategemma' and args.mode=='context':
        p.error('Native TranslateGemma only accepts --mode bare; context-mode is not comparable')
    if args.dry_run:
        print(json.dumps({'count':len(cases),'first_case':cases[0],
              'first_messages':make_messages(cases[0],args.prompt_style,args.mode)},ensure_ascii=False,indent=2));return 0
    done=set();args.output.parent.mkdir(parents=True,exist_ok=True)
    if args.output.exists():
        for line in args.output.read_text(encoding='utf-8').splitlines():
            try:
                x=json.loads(line)
                if x.get('id') and x.get('translation') and x.get('model')==args.model and x.get('mode')==args.mode and x.get('prompt_style')==args.prompt_style:
                    done.add(x['id'])
            except ValueError: pass
    errors=0; count=0
    with args.output.open('a',encoding='utf-8') as f:
        for i,r in enumerate(cases,1):
            if r['id'] in done:continue
            payload={'model':args.model,'messages':make_messages(r,args.prompt_style,args.mode),
                     'temperature':args.temperature,'max_tokens':args.max_tokens,'stream':False}
            result={'id':r['id'],'model':args.model,'mode':args.mode,'prompt_style':args.prompt_style,
                   'split':r['split'],'difficulty':r['difficulty'], 'challenge':r['primary_challenge'],
                   'japanese':r['japanese']}
            t0=time.perf_counter()
            try:
                response=request_api(args.base_url.rstrip('/')+'/chat/completions',args.api_key,payload,args.timeout,args.retries)
                choice=response['choices'][0]
                msg=choice['message'];raw=extract_text(msg.get('content'))
                result.update(raw_response=raw,translation=clean(raw),finish_reason=choice.get('finish_reason'),
                    usage=response.get('usage',{}))
                if not result['translation']:
                    result['error']='No visible translation (thinking budget exhausted / incompatible chat template?)'
            except Exception as e:
                result['error']=f'{type(e).__name__}: {str(e)[:400]}'
            result['seconds']=round(time.perf_counter()-t0,4)
            f.write(json.dumps(result,ensure_ascii=False)+'\n');f.flush()
            count+=1
            if 'error' in result: errors+=1
            else: errors=0
            print(f"[{i}/{len(cases)}] {r['id']} {result['seconds']:.2f}s {'ERROR '+result['error'] if 'error' in result else 'OK'}",flush=True)
            if errors>=args.max_consecutive_errors:
                print('Aborting after consecutive failures (do not count as translation-quality failure)',file=sys.stderr)
                return 3
    print(f'Added {count} records, output: {args.output}')
    return 0

if __name__=='__main__':sys.exit(main())
