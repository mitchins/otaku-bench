#!/usr/bin/env python3
"""Sequential llama-server 50-model matrix, canary gated; never downloads by default.

Default Q4 is publisher-recommended where available; Q6/Q8 optional distinct arms.
"""
from __future__ import annotations
import argparse,hashlib,json,os,signal,subprocess,sys,time
from pathlib import Path
from urllib.request import urlopen
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'tools/run_translations.py'

def ranges(s):
 out=set()
 for item in s.split(','):
  if '-' in item:
   a,b=map(int,item.split('-',1));out.update(range(a,b+1))
  else:out.add(int(item))
 return out

def stop(proc):
 if proc.poll() is not None:return
 os.killpg(proc.pid,signal.SIGTERM)
 try:proc.wait(timeout=15)
 except subprocess.TimeoutExpired:
  os.killpg(proc.pid,signal.SIGKILL);proc.wait(timeout=10)

def ready(proc,port,wait):
 t0=time.monotonic()
 while time.monotonic()-t0 < wait:
  if proc.poll() is not None:return False
  try:
   with urlopen(f'http://127.0.0.1:{port}/health',timeout=2) as r:
    if r.status==200:return True
  except Exception:pass
  time.sleep(1)
 return False

def count_ok(path,source_sha256=None,run_id=None):
 if not path.exists():return 0
 return len({x['id'] for x in (json.loads(y) for y in path.read_text().splitlines() if y.strip()) if x.get('translation') and not x.get('error') and (source_sha256 is None or x.get('source_sha256')==source_sha256) and (run_id is None or x.get('run_id')==run_id)})

def check_server_flags(binary):
 try:
  info=subprocess.run([binary,'--help'],capture_output=True,text=True,timeout=20,check=False)
  h=info.stdout+info.stderr
  missing=[x for x in ('--reasoning','--jinja','--alias') if x not in h]
  if missing:raise RuntimeError('llama-server missing required flags '+str(missing)+'; install a recent upstream build')
 except (OSError,subprocess.TimeoutExpired) as e:
  raise RuntimeError('llama-server preflight failed: '+str(e)) from e

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--catalog',type=Path,default=ROOT/'data/otakubench50.json')
 p.add_argument('--ranks',default='12-14')
 p.add_argument('--device',choices=['all','deck','lan'],default='all')
 p.add_argument('--dataset',choices=['lines','scenes'],default='lines')
 p.add_argument('--mode',choices=['bare','context','full'],default='bare')
 p.add_argument('--quant',choices=['default','Q6_K','Q8_0'],default='default')
 p.add_argument('--reasoning',choices=['on','off','auto'],default='off')
 p.add_argument('--llama-server',default='llama-server')
 p.add_argument('--port',type=int,default=8125)
 p.add_argument('--ctx-size',type=int,default=8192)
 p.add_argument('--max-tokens',type=int,default=4096,help='Generous output cap for thinking models; incomplete generations are failures')
 p.add_argument('--startup-timeout',type=int,default=600)
 p.add_argument('--output-dir',type=Path,default=ROOT/'results/v4')
 p.add_argument('--allow-unattested',action='store_true',help='Explicit exploratory mode: unpinned GGUF repo and unreviewed source/quant, never count as qualified')
 p.add_argument('--execute',action='store_true')
 args=p.parse_args()
 if args.dataset=='lines' and args.mode!='bare':p.error('line contexts are editorial hints, not test context')
 ids=ranges(args.ranks)
 if not ids or min(ids)<1 or max(ids)>50:p.error('rank outside 1..50')
 rows=[r for r in json.loads(args.catalog.read_text())['models'] if r['rank'] in ids]
 preflight_done=False
 for r in rows:
  if args.device=='deck' and not r['deck_default_candidate']:continue
  if args.device=='lan' and r['deck_default_candidate']:continue
  status='PLANNED'
  if r['family']=='Swallow' and args.reasoning=='off':
   print(json.dumps({'model':r['model'],'status':'SKIP_SWALLOW_REQUIRES_REASONING_ON'}));continue
  if r['family']=='TranslateGemma':
   print(json.dumps({'model':r['model'],'status':'SKIP_TRANSLATEGEMMA_NATIVE_TEMPLATE_UNVERIFIED'}));continue
  if (r['family']=='Seed-X' and args.mode!='bare') or (r['family']=='VNTL' and args.mode=='context'):
   print(json.dumps({'model':r['model'],'status':'SKIP_SPECIALIST_CONTEXT_UNQUALIFIED'}));continue
  if args.quant!='default' and r['total_params_b']>9:
   print(json.dumps({'model':r['model'],'status':'SKIP_HIGH_QUANT_RESTRICTED_TO_SMALL_MODELS'}));continue
  quant=r['preferred_quant'] if args.quant=='default' else args.quant
  attested=(r.get('repro_status')=='HUB_QUANT_ATTESTED' and bool(r.get('model_repo_sha'))
            and quant==r.get('preferred_quant') and bool(r.get('quant_file')))
  if args.execute and not attested and not args.allow_unattested:
   print(json.dumps({'model':r['model'],'status':'BLOCKED_UNATTESTED',
     'detail':'Resolve the selected quant using resolve_ggufs.py, then pass --catalog data/attested.json; or explicitly --allow-unattested for exploratory, unqualified canary.'}));continue
  style=r.get('prompt_style') or ('hunyuan' if r['family'] in ('Hunyuan-MT','HY-MT1.5') else 'cat' if r['family']=='CAT-Translate' else 'seedx' if r['family']=='Seed-X' else 'chat')
  tag=f"{r['rank']:02}_{r['family'].replace(' ','_')}_{quant}_{args.dataset}_{args.mode}_{args.reasoning}"
  revision=r.get('model_repo_sha') or 'UNPINNED'
  if args.execute and not attested:
   print(json.dumps({'model':r['model'],'status':'EXPLORATORY_UNATTESTED','warning':'Scores from this run cannot enter trusted leaderboard'}))
  if args.execute and not preflight_done:
   try:check_server_flags(args.llama_server)
   except RuntimeError as e:p.error(str(e))
   preflight_done=True
  args.output_dir.mkdir(exist_ok=True,parents=True)
  pinned_files=None
  # In attested execution the model is fetched by immutable repository SHA, then
  # loaded using -m. The old -hf repo:quant would silently follow mutable main.
  if args.execute and attested:
   try:
    from huggingface_hub import hf_hub_download
    filenames=r['quant_file'] if isinstance(r['quant_file'],list) else [r['quant_file']]
    pinned_files=[hf_hub_download(repo_id=r['quant_repo'],filename=fn,revision=r['model_repo_sha']) for fn in filenames]
   except Exception as e:
    print(json.dumps({'model':r['model'],'status':'PINNED_DOWNLOAD_FAILED','error':str(e)[:250]}));continue
  load_args=['-m',pinned_files[0]] if pinned_files else ['-hf',r['quant_repo']+':'+quant]
  server=[args.llama_server,*load_args,'--host','127.0.0.1','--port',str(args.port),
          '--ctx-size',str(args.ctx_size),'--parallel','1','--jinja','--reasoning',args.reasoning,'--alias',r['model']]
  base=[sys.executable,str(RUN),'--model',r['model'],'--dataset',args.dataset,'--mode',args.mode,
        '--prompt-style',style,'--max-tokens',str(args.max_tokens),'--run-id',f"{r['model']}:{quant}:{args.reasoning}:{revision[:12]}",'--quant-revision',revision,*(['--quant-attested'] if attested else []),'--base-url',f'http://127.0.0.1:{args.port}/v1']
  source=ROOT/'benchmark/otakubench/data/build'/('lines_bare.jsonl' if args.dataset=='lines' else f'scenes_{args.mode}.jsonl')
  source_sha256=hashlib.sha256(source.read_bytes()).hexdigest()
  run_id=f"{r['model']}:{quant}:{args.reasoning}:{revision[:12]}"
  target=args.output_dir/(tag+'_all.jsonl')
  canary=args.output_dir/(tag+'_canary.jsonl')
  canarycmd=base+['--limit','5','--output',str(canary),'--execute']
  fullcmd=base+['--canary-passed','--output',str(target),'--execute']
  if not args.execute:
   print(json.dumps({'model':r['model'],'style':style,'quant':quant,'status':status,'server_argv':server,
        'canary_argv':canarycmd,'full_argv':fullcmd,'quant_revision':revision,'attested':attested},indent=2));continue
  log=args.output_dir/(tag+'_server.log');result={'model':r['model'],'quant':quant,'dataset':args.dataset,'mode':args.mode,'reasoning':args.reasoning,'quant_repo_sha':revision,'attested':attested}
  with log.open('a') as f:
   proc=subprocess.Popen(server,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
   try:
    if not ready(proc,args.port,args.startup_timeout):result['status']='STARTUP_FAILED'
    else:
     cr=subprocess.run(canarycmd,check=False)
     if cr.returncode!=0 or count_ok(canary,source_sha256,run_id)!=5:result['status']='CANARY_FAILED'
     else:
      rr=subprocess.run(fullcmd,check=False)
      n=count_ok(target,source_sha256,run_id);required=250 if args.dataset=='lines' else 31
      result.update(status='UNJUDGED_COMPLETE' if rr.returncode==0 and n==required else 'INCOMPLETE',translated=n,expected=required)
   finally:
    stop(proc)
    with (args.output_dir/'run_log.jsonl').open('a') as j:j.write(json.dumps(result)+'\n')
    print(json.dumps(result))
if __name__=='__main__':main()
