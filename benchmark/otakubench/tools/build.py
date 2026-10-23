#!/usr/bin/env python3
"""OtakuBench v2: stable-ID dataset build; 250 original line probes + 31 scenes.

The authoritative editable inputs are data/items/lines.jsonl and
 data/scenes/scenes.jsonl. Never attach alternates by positional row number.
"""
from __future__ import annotations
import csv, hashlib, json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'data/items/lines.jsonl'
SCENES=ROOT/'data/scenes/scenes.jsonl'
OUT=ROOT/'data/build'

def load(path):
 return [json.loads(x) for x in path.read_text(encoding='utf8').splitlines() if x.strip()]

def dump(path,rows):
 path.write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in rows),encoding='utf8')

def check(lines,scenes):
 assert len(lines)==250 and len(scenes)==31
 assert len({r['id'] for r in lines})==250
 assert len({r['japanese'] for r in lines})==250
 assert {r['id'] for r in lines}=={f'JMB-{i:03d}' for i in range(1,251)}
 assert len({r['id'] for r in scenes})==31
 assert {r['id'] for r in scenes}=={f'OTB-P{i:03d}' for i in range(1,32)}
 assert all(isinstance(r['alternate_references'],list) and isinstance(r['english_reference'],str) and r['english_reference'] for r in lines)
 assert all(len(r['contextual_japanese_lines'])>=3 and r['full_japanese']=='\n'.join(r['contextual_japanese_lines']) and r['target_japanese']==r['contextual_japanese_lines'][-1] for r in scenes)
 assert all(r['english_reference'].strip() and r['full_english_reference'].strip() for r in scenes)
 assert all(r['scene_context'] and r['context_type']=='editorial_annotation_not_model_input' for r in lines)
 assert Counter(x['split'] for x in lines)=={'dev':50,'eval':200}
 assert Counter(x['split'] for x in scenes)=={'dev':6,'eval':25}

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 lines,scenes=load(SRC),load(SCENES);check(lines,scenes)
 dump(OUT/'lines_gold.jsonl',lines)
 # Context label is explicitly excluded from blind line probes; v1 scene-context exposed answers.
 dump(OUT/'lines_bare.jsonl',[{'id':r['id'],'japanese':r['japanese'],'split':r['split'],'challenge':r['primary_challenge'],'difficulty':r['difficulty']} for r in lines])
 dump(OUT/'scenes_gold.jsonl',scenes)
 for mode in ('bare','context','full'):
  blind=[]
  for r in scenes:
   d={'id':r['id'],'split':r['split'],'challenge':r['phenomenon'],'medium_style':r['medium_style']}
   if r.get('hook_artifacts'):d['hook_artifacts']=r['hook_artifacts']
   if mode=='bare':d['japanese']=r['target_japanese']
   elif mode=='context':d.update(japanese=r['target_japanese'],preceding_lines=r['context_lines'])
   else:d['japanese']=r['full_japanese']
   blind.append(d)
  dump(OUT/f'scenes_{mode}.jsonl',blind)
 # Flat CSV for nonprogrammatic auditing, with stable-ID alternates
 for stem,rs,cols in [('lines',lines,['id','split','scenario_style_unvalidated','genre_style_unvalidated','difficulty','primary_challenge','japanese','english_reference','alternate_references','scene_context','translation_note','tags']),
                       ('scenes',scenes,['id','split','medium_style','phenomenon','full_japanese','full_english_reference','translation_note','tags'])]:
  with (OUT/f'{stem}_gold.csv').open('w',encoding='utf-8-sig',newline='') as f:
   w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
   for r in rs:
    w.writerow({c:(' || '.join(r[c]) if isinstance(r.get(c),list) else r.get(c,'')) for c in cols})
 manifest={'name':'OtakuBench','version':'4.0.0-editorial-draft','line_items':len(lines),'scene_items':len(scenes),
           'source_sha256':{x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in (SRC,SCENES)},
           'gold_sha256':{x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in (OUT/'lines_gold.jsonl',OUT/'scenes_gold.jsonl')},
           'split':{'lines':dict(Counter(r['split'] for r in lines)),'scenes':dict(Counter(r['split'] for r in scenes))},
           'media_metadata_policy':'line scenario_style_unvalidated is legacy round-robin bookkeeping only; exclude from medium performance claims',
           'contexts':'line scene_context is judge-only original annotation and must never reach translator; passage context contains only actual preceding Japanese',
           'truth':'editorial-draft translations, no human or external judge gold validation performed'}
 (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'lines':len(lines),'scenes':len(scenes),'manifest':str(OUT/'manifest.json')},indent=2))
if __name__=='__main__':main()
