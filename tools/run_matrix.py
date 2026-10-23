#!/usr/bin/env python3
"""Serial, bounded local llama-server matrix: canary -> full benchmark -> metrics.

Opt-in execution: default prints commands only. Downloads persist in user's HF
cache; the program never deletes models or blindly downloads the whole matrix.
"""
from __future__ import annotations
import argparse,json,os,signal,subprocess,sys,time
from pathlib import Path
from urllib.request import urlopen

ROOT=Path(__file__).resolve().parents[1]
RUNNER=ROOT/'tools'/'run_benchmark.py'

def rows_from_catalog(path:Path,ranks:set[int]):
    data=json.loads(path.read_text())['models']
    return [x for x in data if x['rank'] in ranks]

def cmd_for(row,args):
    quant=row.get('selected_quant') or row['preferred_quant']
    # The -hf selector is resolved by llama.cpp against publisher manifest.
    return [str(args.llama_server),'-hf',row['quant_repo']+':'+quant,
            '--host','127.0.0.1','--port',str(args.port),'--ctx-size',str(args.ctx_size),
            '--n-gpu-layers',str(args.gpu_layers),'--parallel','1','--alias','jpmedia250']

def wait_ready(proc,port,seconds):
    start=time.monotonic()
    while time.monotonic()-start<seconds:
        if proc.poll() is not None: return False
        for url in (f'http://127.0.0.1:{port}/health',f'http://127.0.0.1:{port}/v1/models'):
            try:
                with urlopen(url,timeout=2) as r:
                    if r.status==200: return True
            except Exception: pass
        time.sleep(1)
    return False

def stop(proc):
    if proc.poll() is not None:return
    try:
        os.killpg(proc.pid,signal.SIGTERM)
    except ProcessLookupError:return
    try:proc.wait(timeout=15)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid,signal.SIGKILL)
        proc.wait(timeout=5)

def nonempty_count(path):
    if not path.exists():return 0
    return sum(bool(json.loads(s).get('translation')) for s in path.read_text().splitlines() if s.strip())

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--catalog',type=Path,default=ROOT/'data'/'candidates.json')
    p.add_argument('--ranks',default='1,12,15',help='Comma separated; use 1-50 to run the full set')
    p.add_argument('--llama-server',type=Path,default=Path('llama-server'))
    p.add_argument('--port',type=int,default=8125)
    p.add_argument('--ctx-size',type=int,default=4096)
    p.add_argument('--gpu-layers',type=int,default=99)
    p.add_argument('--startup-timeout',type=int,default=900)
    p.add_argument('--timeout',type=int,default=240)
    p.add_argument('--max-tokens',type=int,default=2048)
    p.add_argument('--mode',choices=['bare','context'],default='bare')
    p.add_argument('--limit-cases',type=int,default=0,help='Limit full run for debugging; 0=all')
    p.add_argument('--output-dir',type=Path,default=ROOT/'results')
    p.add_argument('--execute',action='store_true',help='Actually run llama-server and download model GGUFs')
    p.add_argument('--skip-canary',action='store_true',help='Only when model already canary qualified')
    args=p.parse_args()
    def ranges(s):
        result=set()
        for part in s.split(','):
            if '-' in part:
                a,b=map(int,part.split('-',1));result.update(range(a,b+1))
            else:result.add(int(part))
        return result
    ranks=ranges(args.ranks)
    if not ranks or min(ranks)<1 or max(ranks)>50:p.error('rank must lie in [1,50]')
    selected=rows_from_catalog(args.catalog,ranks)
    if len(selected)!=len(ranks):p.error('some ranks missing in manifest')
    args.output_dir.mkdir(exist_ok=True,parents=True)
    summary=[]
    for row in selected:
        rank=row['rank']
        if row['family']=='TranslateGemma' and args.mode=='context':
            summary.append({'rank':rank,'status':'SKIPPED_NATIVE_CONTEXT_UNSUPPORTED'})
            print(f"{rank:02} SKIP native TranslateGemma doesn't accept context mode");continue
        stem=f"{rank:02d}_{row['model'].replace('/','_').replace(' ','_')}_{args.mode}"
        style='translategemma' if row['family']=='TranslateGemma' else 'chat'
        server=cmd_for(row,args)
        base=[sys.executable,str(RUNNER),'--base-url',f'http://127.0.0.1:{args.port}/v1',
              '--model','jpmedia250','--mode',args.mode,'--prompt-style',style,
              '--timeout',str(args.timeout),'--max-tokens',str(args.max_tokens)]
        canary=base+['--canary','--output',str(args.output_dir/(stem+'_canary.jsonl'))]
        full=base+['--output',str(args.output_dir/(stem+'_all.jsonl'))]
        if args.limit_cases:full+=['--limit',str(args.limit_cases)]
        if not args.execute:
            print(json.dumps({'rank':rank,'model':row['model'],'repo':row['quant_repo'],
               'selected_quant':row.get('selected_quant') or row['preferred_quant'],
               'server_argv':server,'canary_argv':canary,'full_argv':full},indent=2))
            continue
        logpath=args.output_dir/(stem+'_server.log')
        entry={'rank':rank,'model':row['model'],'quant_repo':row['quant_repo'],
               'quant':row.get('selected_quant') or row['preferred_quant'],
               'manifest_sha':row.get('model_repo_sha'),'mode':args.mode,
               'prompt_style':style}
        with logpath.open('a') as logfile:
            proc=subprocess.Popen(server,stdout=logfile,stderr=subprocess.STDOUT,start_new_session=True)
            try:
                if not wait_ready(proc,args.port,args.startup_timeout):
                    entry.update(status='FAILED_TO_START',server_log=str(logpath));continue
                if not args.skip_canary:
                    ret=subprocess.run(canary,check=False).returncode
                    n=nonempty_count(args.output_dir/(stem+'_canary.jsonl'))
                    if ret or n!=5:
                        entry.update(status='CANARY_FAILED',canary_outputs=n,server_log=str(logpath));continue
                ret=subprocess.run(full,check=False).returncode
                n=nonempty_count(args.output_dir/(stem+'_all.jsonl'))
                entry.update(status='INFERENCE_COMPLETED_UNREVIEWED' if ret==0 else 'INFERENCE_INCOMPLETE',
                             translations=n,full_exit=ret,review_required=True)
            finally:
                stop(proc)
                with (args.output_dir/'matrix_run_log.jsonl').open('a') as f:
                    f.write(json.dumps(entry)+'\n')
                print(json.dumps(entry))
                summary.append(entry)
    if args.execute:
        print(json.dumps({'attempted':len(summary),'completed':sum(x.get('status')=='INFERENCE_COMPLETED_UNREVIEWED' for x in summary)},indent=2))
    return 0

if __name__=='__main__':sys.exit(main())
