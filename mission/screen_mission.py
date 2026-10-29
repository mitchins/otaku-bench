#!/usr/bin/env python3
"""OtakuBench screen-translator mission.

Answers one question: which local GGUF translates the line on screen well enough,
fast enough? Runs ONE model at a time on ONE pinned GPU with a realistic
"VN screen" profile:

  * 2048-token context, 256-token output cap, thinking off, temperature 0
  * latency gate first (time-to-first-token and full-line time with dialogue history)
  * dialogue-history depth sweep (0/3/6/12/24 preceding lines) for the latency curve
  * quality arms only for models that pass the gate:
      lines/bare (250), scenes/bare, scenes/context, scenes/full (31 each)

Outputs are judge.py-compatible JSONL (same dataset/mode/source_sha256 fields).
Models that cannot fit the selected GPU are recorded as DEFER_5090, not failures.
Resumable: completed models and completed case IDs are skipped on rerun.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import signal
import socket
import statistics
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from urllib.error import URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import run_translations as rt  # noqa: E402  (native prompt formats live there)

DATA = ROOT / 'benchmark/otakubench/data/build'
PROFILE = 'screen-v1'
CTX = 2048
MAX_TOKENS = 256
DEPTHS = (0, 3, 6, 12, 24)
GATE_DEPTH = 6
CANARY_INDICES = (0, 30, 88, 150, 211)
LATENCY_SCENES = 12

# Which arms each native prompt style can legitimately run.
STYLE_ARMS = {
    'chat': {('lines', 'bare'), ('scenes', 'bare'), ('scenes', 'context'), ('scenes', 'full')},
    'hunyuan': {('lines', 'bare'), ('scenes', 'bare'), ('scenes', 'context'), ('scenes', 'full')},
    'hymt2': {('lines', 'bare'), ('scenes', 'bare'), ('scenes', 'context'), ('scenes', 'full')},
    'cat': {('lines', 'bare'), ('scenes', 'bare'), ('scenes', 'context'), ('scenes', 'full')},
    'sugoi': {('lines', 'bare'), ('scenes', 'bare'), ('scenes', 'context'), ('scenes', 'full')},
    'vntl': {('lines', 'bare'), ('scenes', 'bare'), ('scenes', 'full')},
    'seedx': {('lines', 'bare'), ('scenes', 'bare')},
    'translategemma_text': {('lines', 'bare'), ('scenes', 'bare'), ('scenes', 'full')},  # no context channel
    'base_completion': {('lines', 'bare'), ('scenes', 'bare')},
    'base_primed': {('lines', 'bare'), ('scenes', 'bare'), ('scenes', 'full')},
}
# Follow-up arms for models the baseline profile can't run. Each gets its own run_id and output dir.
VARIANTS = {
    'effort-low': {'max_tokens': 1024, 'kwargs': {'reasoning_effort': 'low'}},  # gpt-oss: no true off switch
    # Template always thinks; prefill an empty think block (unofficial). llama-server already renders an assistant
    # prefill as '<think></think>' + content, so the content must NOT repeat the tags: '<think>\n</think>' here gave
    # two blocks and made Flint reason in its visible reply on 11/93 scene items (studies/flint_adapter.py).
    'empty-think': {'prefill': '\n'},
    'primed': {'style': {'base_completion': 'base_primed'}},  # base models: closed answer frame + stop
    # Omni models pick the output modality from the system prompt; without this LFM3-Omni answers in interleaved
    # text+speech, and the hidden audio tokens run to the cap mid-sentence. Suffix documented on the model card.
    'respond-in-text': {'system_suffix': ' Respond in text.'},
    # The chat user messages never name the target language (only the system prompt does). Gemini 3.5 Flash-Lite echoes
    # the Japanese on some scenes even with the system prompt in place, and translates once the user turn says it.
    # Candidate fix for the next prompt version for every model; until then it's a variant arm.
    'explicit-target': {'user_rewrite': (('Translate only this Japanese line:', 'Translate only this Japanese line into English:'),
                                         ('Translate ONLY this new line:', 'Translate ONLY this new line from Japanese to English:'),
                                         ('Translate this WHOLE scene,', 'Translate this WHOLE scene from Japanese to English,'))},
}
VARIANT: dict = {}
HISTORY_STYLES = {'chat', 'hunyuan', 'hymt2', 'sugoi'}  # cat has no context channel
COMPLETION_STYLES = {'seedx', 'vntl', 'base_completion', 'base_primed', 'translategemma_text'}
ARM_ORDER = (('lines', 'bare'), ('scenes', 'bare'), ('scenes', 'context'), ('scenes', 'full'))
OOM_PATTERNS = re.compile(r'out of memory|cudaMalloc failed|failed to allocate|CUDA error|unable to load model|ggml_backend_cuda_buffer_type_alloc_buffer', re.I)


# ---------------------------------------------------------------- utilities
def log(msg: str) -> None:
    print(f"{time.strftime('%H:%M:%S')} {msg}", flush=True)


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text(encoding='utf8').splitlines() if x.strip()]


def append_jsonl(path: Path, rec: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf8') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def slug(s: str) -> str:
    return re.sub(r'[^A-Za-z0-9._-]+', '_', s).strip('_')


def pct(values: list[float], q: float) -> float | None:
    if not values:
        return None
    v = sorted(values)
    k = max(0, min(len(v) - 1, int(round(q * (len(v) - 1)))))
    return round(v[k], 3)


def med(values: list[float]) -> float | None:
    return round(statistics.median(values), 3) if values else None


def style_for(row: dict) -> str:
    fam = row.get('family', '')
    remap = VARIANT.get('style', {})
    if row.get('prompt_style') in remap:
        return remap[row['prompt_style']]
    if row.get('prompt_style') == 'translategemma':
        return 'translategemma_text'  # llama-server drops the lang-code content parts; see run_translations
    return row.get('prompt_style') or ('hunyuan' if fam in ('Hunyuan-MT', 'HY-MT1.5') else
                                       'cat' if fam == 'CAT-Translate' else
                                       'seedx' if fam == 'Seed-X' else 'chat')


def size_gb(row: dict) -> tuple[float, bool]:
    s = row.get('quant_size_gb') or row.get('listed_size_gb')
    if s:
        return float(s), False
    return round(float(row.get('total_params_b') or 8) * 0.62, 2), True  # ~Q4_K_M bytes/param


# ---------------------------------------------------------------- GPU / disk
def gpu_info(nvsmi: str, index: int) -> dict | None:
    try:
        out = subprocess.run([nvsmi, '--query-gpu=index,pci.bus_id,name,memory.free,memory.used,memory.total',
                              '--format=csv,noheader,nounits', '-i', str(index)],
                             capture_output=True, text=True, timeout=20, check=True).stdout.strip()
        idx, bus, name, free, used, total = [x.strip() for x in out.split(',')]
        return {'index': int(idx), 'bus_id': bus, 'name': name, 'free_mib': int(free),
                'used_mib': int(used), 'total_mib': int(total)}
    except Exception as e:  # noqa: BLE001
        log(f'⚠️  nvidia-smi query failed: {e}')
        return None


def hf_cache_dir() -> Path:
    if os.environ.get('HF_HUB_CACHE'):
        return Path(os.environ['HF_HUB_CACHE'])
    return Path(os.environ.get('HF_HOME', Path.home() / '.cache/huggingface')) / 'hub'


# ---------------------------------------------------------------- llama-server
def server_caps(binary: str) -> dict:
    try:
        h = subprocess.run([binary, '--help'], capture_output=True, text=True, timeout=30).stdout
        h += subprocess.run([binary, '--help'], capture_output=True, text=True, timeout=30).stderr
    except (OSError, subprocess.TimeoutExpired) as e:
        raise SystemExit(f'❌ cannot run {binary} --help: {e}')
    return {
        'jinja': bool(re.search(r'--jinja(?![-\w])', h)),
        # exact flag, NOT a prefix match on --reasoning-budget / --reasoning-format
        'reasoning': bool(re.search(r'--reasoning(?![-\w])', h)),
        'reasoning_budget': bool(re.search(r'--reasoning-budget(?![-\w])', h)),
        'alias': bool(re.search(r'--alias(?![-\w])', h)),
    }


def port_free(port: int) -> bool:
    with socket.socket() as s:
        return s.connect_ex(('127.0.0.1', port)) != 0


def wait_ready(proc: subprocess.Popen, port: int, seconds: int) -> bool:
    t0 = time.monotonic()
    while time.monotonic() - t0 < seconds:
        if proc.poll() is not None:
            return False
        try:
            with urlopen(f'http://127.0.0.1:{port}/health', timeout=3) as r:
                if r.status == 200:
                    return True
        except Exception:  # noqa: BLE001
            pass
        time.sleep(1)
    return False


def stop(proc: subprocess.Popen | None) -> None:
    if not proc or proc.poll() is not None:
        return
    try:
        os.killpg(proc.pid, signal.SIGTERM)
        proc.wait(timeout=20)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.wait(timeout=10)
    except ProcessLookupError:
        pass


def tail(path: Path, n: int = 40) -> str:
    try:
        return '\n'.join(path.read_text(errors='replace').splitlines()[-n:])
    except OSError:
        return ''


# ---------------------------------------------------------------- requests
def build_payload(case: dict, style: str, dataset: str, mode: str) -> tuple[dict, bool]:
    ns = SimpleNamespace(prompt_style=style, model='otb', dataset=dataset, mode=mode, max_tokens=MAX_TOKENS)
    payload = rt.make_payload(case, ns)
    payload['max_tokens'] = MAX_TOKENS
    payload['stream'] = True
    payload['cache_prompt'] = True
    if 'messages' in payload:
        # Belt and braces with the server flag: templates that support it switch thinking off.
        payload['chat_template_kwargs'] = {'enable_thinking': False, **VARIANT.get('kwargs', {})}
        if VARIANT.get('system_suffix') and payload['messages'][0]['role'] == 'system':
            payload['messages'][0]['content'] += VARIANT['system_suffix']
        user = payload['messages'][-1]
        for old, new in VARIANT.get('user_rewrite', ()):
            if user['role'] == 'user' and isinstance(user['content'], str) and old in user['content']:
                user['content'] = user['content'].replace(old, new, 1)
        if VARIANT.get('prefill'):
            payload['messages'].append({'role': 'assistant', 'content': VARIANT['prefill']})
    return payload, style in COMPLETION_STYLES


def stream_once(base: str, payload: dict, completions: bool, timeout: float) -> dict:
    url = base + ('/completions' if completions else '/chat/completions')
    req = Request(url, data=json.dumps(payload, ensure_ascii=False).encode(),
                  headers={'Content-Type': 'application/json', 'Authorization': 'Bearer local'}, method='POST')
    t0 = time.perf_counter()
    ttft = None
    text, reasoning = [], []
    finish = timings = usage = None
    with urlopen(req, timeout=timeout) as resp:
        for raw in resp:
            if time.perf_counter() - t0 > timeout:
                raise TimeoutError(f'stream exceeded {timeout}s')
            line = raw.decode('utf-8', 'replace').strip()
            if not line.startswith('data:'):
                continue
            data = line[5:].strip()
            if data == '[DONE]':
                break
            try:
                obj = json.loads(data)
            except json.JSONDecodeError:
                continue
            timings = obj.get('timings') or timings
            usage = obj.get('usage') or usage
            for ch in obj.get('choices') or []:
                if completions:
                    piece, rpiece = ch.get('text'), None
                else:
                    delta = ch.get('delta') or {}
                    piece, rpiece = delta.get('content'), delta.get('reasoning_content')
                if piece:
                    if ttft is None:
                        ttft = time.perf_counter() - t0
                    text.append(piece)
                if rpiece:
                    reasoning.append(rpiece)
                if ch.get('finish_reason'):
                    finish = ch['finish_reason']
    return {'raw': ''.join(text), 'reasoning': ''.join(reasoning), 'finish': finish,
            'ttft_s': round(ttft, 4) if ttft is not None else None,
            'seconds': round(time.perf_counter() - t0, 4), 'timings': timings, 'usage': usage}


def translate(base: str, case: dict, style: str, dataset: str, mode: str, timeout: float) -> dict:
    rec = {'translation': '', 'error': None}
    try:
        payload, completions = build_payload(case, style, dataset, mode)
        res = stream_once(base, payload, completions, timeout)
        text, err = rt.strip_answer(res['raw'], None)
        if res['finish'] == 'length':
            err = f'hit {MAX_TOKENS}-token cap (thinking or runaway output)'
        elif res['reasoning'] and not text:
            err = 'thinking output only; no visible translation'
        rec.update(translation=text if not err else '', raw_response=res['raw'], error=err,
                   finish_reason=res['finish'], seconds=res['seconds'], ttft_s=res['ttft_s'],
                   reasoning_chars=len(res['reasoning']), timings=res['timings'], usage=res['usage'])
    except Exception as e:  # noqa: BLE001
        rec.update(error=f'{type(e).__name__}: {str(e)[:200]}')
    return rec


# ---------------------------------------------------------------- latency cases
def latency_cases() -> list[dict]:
    ctx = load_jsonl(DATA / 'scenes_context.jsonl')
    full = load_jsonl(DATA / 'scenes_full.jsonl')
    pool = [ln for s in full for ln in s['japanese'].split('\n') if ln.strip()]
    targets = [c for c in ctx if c['split'] == 'eval'][:LATENCY_SCENES]
    cases = []
    for c in targets:
        own = list(c.get('preceding_lines') or [])
        filler = [ln for ln in pool if ln not in own and ln != c['japanese']]
        for d in DEPTHS:
            hist = (filler + own)[-d:] if d else []
            cases.append({'id': f"{c['id']}@d{d}", 'scene_id': c['id'], 'depth': d,
                          'japanese': c['japanese'], 'preceding_lines': hist})
    return cases


# ---------------------------------------------------------------- per-model run
def run_model(row: dict, args, caps: dict, out_dir: Path, summary_path: Path) -> dict:
    style = style_for(row)
    gb, est = size_gb(row)
    quant = row.get('selected_quant') or row.get('preferred_quant')
    revision = row.get('model_repo_sha') or 'UNPINNED'
    pinned = bool(row.get('quant_file') and row.get('model_repo_sha'))
    attested = row.get('repro_status') == 'HUB_QUANT_ATTESTED'
    run_id = f"{row['model']}:{quant}:off:{revision[:12]}:{PROFILE}"
    mdir = out_dir / f"{row['rank']:02d}_{slug(row['model'])}"
    result = {'rank': row['rank'], 'model': row['model'], 'family': row.get('family'), 'style': style,
              'quant': quant, 'size_gb': gb, 'size_estimated': est, 'run_id': run_id,
              'quant_repo_sha': revision, 'quant_attested': attested, 'pinned': pinned,
              'profile': PROFILE, 'gpu_index': args.gpu, 'started': time.strftime('%Y-%m-%dT%H:%M:%S%z')}

    def finish(status: str, **extra) -> dict:
        result.update(status=status, finished=time.strftime('%Y-%m-%dT%H:%M:%S%z'), **extra)
        append_jsonl(summary_path, result)
        log(f"{'✅' if status == 'COMPLETE' else '⏭️ '} {row['rank']:02d} {row['model']} → {status}")
        return result

    if style not in STYLE_ARMS:
        return finish('SKIP_UNKNOWN_PROMPT_STYLE')
    if not pinned and args.strict:
        return finish('SKIP_UNATTESTED_STRICT')

    # --- fit checks (before any download)
    gpu = gpu_info(args.nvidia_smi, args.gpu)
    if gpu:
        result['gpu_bus_id'] = gpu['bus_id']
        need = int(gb * 1e9 / 1048576) + args.headroom_mib
        result['vram_need_mib'] = need
        result['vram_free_mib_before'] = gpu['free_mib']
        if need > gpu['free_mib']:
            return finish('DEFER_5090', reason=f"needs ~{need} MiB, GPU {args.gpu} has {gpu['free_mib']} MiB free")
    disk_free_gb = shutil.disk_usage(hf_cache_dir() if hf_cache_dir().exists() else Path.home()).free / 1e9
    if disk_free_gb < gb + args.disk_reserve_gb:
        return finish('SKIP_DISK', reason=f'{disk_free_gb:.1f} GB free, need {gb + args.disk_reserve_gb:.1f}')

    # --- weights
    downloaded: list[str] = []
    if pinned:
        try:
            from huggingface_hub import hf_hub_download, try_to_load_from_cache
            files = row['quant_file'] if isinstance(row['quant_file'], list) else [row['quant_file']]
            # files already cached before this run belong to someone else; --prune must leave them alone
            cached_before = {f for f in files
                             if isinstance(try_to_load_from_cache(row['quant_repo'], f, revision=revision), str)}
            log(f"⬇️  {row['model']} ({gb:.1f} GB) {row['quant_repo']}@{revision[:12]}")
            paths = [hf_hub_download(repo_id=row['quant_repo'], filename=f, revision=revision) for f in files]
            downloaded = [p for f, p in zip(files, paths) if f not in cached_before]
        except Exception as e:  # noqa: BLE001
            return finish('DOWNLOAD_FAILED', reason=f'{type(e).__name__}: {str(e)[:300]}')
        load_args = ['-m', paths[0]]
    else:
        load_args = ['-hf', f"{row['quant_repo']}:{quant}"]

    mdir.mkdir(parents=True, exist_ok=True)
    server_log = mdir / 'server.log'
    cmd = [args.llama_server, *load_args, '--host', '127.0.0.1', '--port', str(args.port),
           '-ngl', '99', '-c', str(CTX), '--parallel', '1']
    if caps['jinja'] and style not in COMPLETION_STYLES:
        cmd.append('--jinja')
    if caps['reasoning']:
        cmd += ['--reasoning', 'off']
    elif caps['reasoning_budget']:
        cmd += ['--reasoning-budget', '0']
    if caps['alias']:
        cmd += ['--alias', 'otb']
    cmd += args.extra_server_args
    result['server_argv'] = cmd
    env = dict(os.environ, CUDA_DEVICE_ORDER='PCI_BUS_ID', CUDA_VISIBLE_DEVICES=str(args.gpu))

    if not port_free(args.port):
        return finish('PORT_BUSY', reason=f'port {args.port} already in use')
    log(f"🚀 {row['rank']:02d} {row['model']} [{style}] on GPU {args.gpu}")
    with server_log.open('a') as lf:
        proc = subprocess.Popen(cmd, stdout=lf, stderr=subprocess.STDOUT, env=env, start_new_session=True)
    base = f'http://127.0.0.1:{args.port}/v1'
    try:
        if not wait_ready(proc, args.port, args.startup_timeout if pinned else args.startup_timeout * 3):
            t = tail(server_log)
            if OOM_PATTERNS.search(t):
                return finish('DEFER_5090', reason='out of memory at load', log_tail=t[-1500:])
            return finish('STARTUP_FAILED', log_tail=t[-1500:])
        g = gpu_info(args.nvidia_smi, args.gpu)
        if g:
            result['vram_used_mib_loaded'] = g['used_mib']

        common = {'model': row['model'], 'run_id': run_id, 'quant_repo_sha': revision,
                  'quant_attested': attested, 'prompt_style': style, 'profile': PROFILE}

        # --- canary: 5 fixed lines must all produce a translation
        lines = load_jsonl(DATA / 'lines_bare.jsonl')
        lines_sha = sha_file(DATA / 'lines_bare.jsonl')
        canary_ok, first_err = 0, None
        for i in CANARY_INDICES:
            rec = translate(base, lines[i], style, 'lines', 'bare', args.timeout)
            rec.update(id=lines[i]['id'], dataset='lines', mode='bare', source_sha256=lines_sha, **common)
            append_jsonl(mdir / 'canary.jsonl', rec)
            canary_ok += bool(rec['translation'] and not rec['error'])
            first_err = first_err or rec['error']
        if canary_ok < len(CANARY_INDICES):
            return finish('CANARY_FAILED', canary_ok=canary_ok, reason=first_err)
        common['canary_passed'] = True

        # --- latency gate + history-depth sweep
        lat_path = mdir / 'latency.jsonl'
        done = {r['id'] for r in load_jsonl(lat_path) if not r.get('error')}
        depths = DEPTHS if style in HISTORY_STYLES else (0,)
        for c in latency_cases():
            if c['depth'] not in depths or c['id'] in done:
                continue
            mode = 'context' if c['depth'] else 'bare'
            rec = translate(base, c, style, 'scenes', mode, args.timeout)
            rec.update(id=c['id'], scene_id=c['scene_id'], depth=c['depth'], **common)
            append_jsonl(lat_path, rec)
        lat = [r for r in load_jsonl(lat_path) if r.get('run_id') == run_id]
        by_depth = {}
        for d in depths:
            ok = [r for r in lat if r.get('depth') == d and not r.get('error')]
            tps = [r['timings']['predicted_per_second'] for r in ok
                   if isinstance(r.get('timings'), dict) and r['timings'].get('predicted_per_second')]
            by_depth[str(d)] = {'n_ok': len(ok), 'n_err': sum(1 for r in lat if r.get('depth') == d and r.get('error')),
                                'median_s': med([r['seconds'] for r in ok]), 'p90_s': pct([r['seconds'] for r in ok], .9),
                                'median_ttft_s': med([r['ttft_s'] for r in ok if r.get('ttft_s') is not None]),
                                'median_tok_s': med(tps)}
        gate_d = str(GATE_DEPTH if GATE_DEPTH in depths else 0)
        gate = by_depth[gate_d]
        result['latency'] = by_depth
        result['gate_depth'] = int(gate_d)
        passed = (gate['median_s'] is not None and gate['median_s'] <= args.budget_s
                  and (gate['p90_s'] or 1e9) <= args.budget_p90_s and gate['n_err'] <= 2)
        result['latency_gate'] = 'PASS' if passed else 'FAIL'
        log(f"⏱️  depth {gate_d}: median {gate['median_s']}s p90 {gate['p90_s']}s ttft {gate['median_ttft_s']}s → {result['latency_gate']}")
        if not passed and not args.quality_even_if_slow:
            return finish('LATENCY_FAIL')

        # --- quality arms (judge.py-compatible)
        arms = {}
        for dataset, mode in ARM_ORDER:
            if (dataset, mode) not in STYLE_ARMS[style]:
                arms[f'{dataset}_{mode}'] = 'n/a'
                continue
            src = DATA / ('lines_bare.jsonl' if dataset == 'lines' else f'scenes_{mode}.jsonl')
            src_sha = sha_file(src)
            path = mdir / f'{dataset}_{mode}.jsonl'
            done = {r['id'] for r in load_jsonl(path)
                    if r.get('translation') and not r.get('error') and r.get('run_id') == run_id and r.get('source_sha256') == src_sha}
            cases = load_jsonl(src)
            consecutive = 0
            for c in cases:
                if c['id'] in done:
                    continue
                rec = translate(base, c, style, dataset, mode, args.timeout)
                rec.update(id=c['id'], dataset=dataset, mode=mode, source_sha256=src_sha, split=c.get('split'), **common)
                append_jsonl(path, rec)
                consecutive = consecutive + 1 if rec['error'] else 0
                if consecutive >= 3:
                    log(f'⚠️  {dataset}/{mode}: 3 consecutive errors, abandoning arm')
                    break
            ok = {r['id'] for r in load_jsonl(path)
                  if r.get('translation') and not r.get('error') and r.get('run_id') == run_id and r.get('source_sha256') == src_sha}
            arms[f'{dataset}_{mode}'] = f'{len(ok)}/{len(cases)}'
            log(f'📝 {dataset}/{mode}: {len(ok)}/{len(cases)}')
        g = gpu_info(args.nvidia_smi, args.gpu)
        if g:
            result['vram_used_mib_end'] = g['used_mib']
        complete = all(v == 'n/a' or v.split('/')[0] == v.split('/')[1] for v in arms.values())
        return finish('COMPLETE' if complete else 'PARTIAL', arms=arms)
    finally:
        stop(proc)
        if args.prune and downloaded:
            for p in downloaded:
                try:
                    blob = Path(p).resolve()
                    Path(p).unlink(missing_ok=True)
                    blob.unlink(missing_ok=True)
                except OSError as e:
                    log(f'⚠️  prune failed for {p}: {e}')


# ---------------------------------------------------------------- main
def parse_ranks(s: str | None) -> set[int] | None:
    if not s:
        return None
    out = set()
    for part in s.split(','):
        a, _, b = part.partition('-')
        out.update(range(int(a), int(b or a) + 1))
    return out


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--catalog', type=Path, default=None, help='default: data/attested.json if present, else data/otakubench50.json')
    p.add_argument('--ranks', default=None, help='e.g. 15,18-20 (default: all)')
    p.add_argument('--gpu', type=int, default=0, help='nvidia-smi index (PCI bus order) to pin; default 0')
    p.add_argument('--port', type=int, default=8125)
    p.add_argument('--llama-server', default=os.environ.get('LLAMA_SERVER', 'llama-server'))
    p.add_argument('--nvidia-smi', default=os.environ.get('NVIDIA_SMI', 'nvidia-smi'))
    p.add_argument('--budget-s', type=float, default=2.0, help='latency gate: median full-line seconds at depth 6')
    p.add_argument('--budget-p90-s', type=float, default=3.0)
    p.add_argument('--timeout', type=float, default=60, help='per-request seconds')
    p.add_argument('--startup-timeout', type=int, default=300)
    p.add_argument('--headroom-mib', type=int, default=1800, help='VRAM beyond weights for 2k KV + compute buffers')
    p.add_argument('--disk-reserve-gb', type=float, default=10)
    p.add_argument('--quality-even-if-slow', action='store_true', help='run quality arms even after a latency FAIL')
    p.add_argument('--strict', action='store_true', help='skip models without a pinned, resolved GGUF')
    p.add_argument('--prune', action='store_true', help='delete each GGUF from the HF cache after its run')
    p.add_argument('--redo', action='store_true', help='rerun models already marked COMPLETE/terminal')
    p.add_argument('--output-dir', type=Path, default=ROOT / 'results/screen')
    p.add_argument('--dry-run', action='store_true', help='print the plan; no downloads, no server')
    p.add_argument('--variant', choices=sorted(VARIANTS), help='follow-up arm; writes to results/screen_variants/<variant>')
    p.add_argument('extra_server_args', nargs='*', help='after --, extra llama-server flags (e.g. -- -fa on)')
    args = p.parse_args()
    global PROFILE, MAX_TOKENS
    if args.variant:
        VARIANT.update(VARIANTS[args.variant])
        PROFILE = f'{PROFILE}+{args.variant}'
        MAX_TOKENS = VARIANT.get('max_tokens', MAX_TOKENS)
        if args.output_dir == ROOT / 'results/screen':
            args.output_dir = ROOT / 'results/screen_variants' / args.variant

    catalog = args.catalog or (ROOT / 'data/attested.json' if (ROOT / 'data/attested.json').exists() else ROOT / 'data/otakubench50.json')
    rows = json.loads(catalog.read_text())['models']
    want = parse_ranks(args.ranks)
    rows = [r for r in rows if want is None or r['rank'] in want]
    rows.sort(key=lambda r: (size_gb(r)[0], r['rank']))  # small first; big edge cases last
    out_dir = args.output_dir
    summary_path = out_dir / 'summary.jsonl'
    terminal = {'COMPLETE', 'LATENCY_FAIL', 'CANARY_FAILED', 'SKIP_TEMPLATE_UNVERIFIED', 'SKIP_UNKNOWN_PROMPT_STYLE'}
    prior = {}
    for r in load_jsonl(summary_path):
        prior[r['run_id']] = r['status']

    gpu = gpu_info(args.nvidia_smi, args.gpu)
    log(f"📋 catalog {catalog.name}: {len(rows)} models · GPU {args.gpu}: "
        + (f"{gpu['name']} {gpu['bus_id']} {gpu['free_mib']}/{gpu['total_mib']} MiB free" if gpu else 'unknown'))
    if gpu and gpu['used_mib'] > 1024:
        log(f"⚠️  GPU {args.gpu} already has {gpu['used_mib']} MiB in use — is something else running on it?")

    if args.dry_run:
        print(f"{'rank':>4} {'size':>6} {'style':<16} {'weights':<9} {'fit':<10} model")
        for r in rows:
            gb, est = size_gb(r)
            style = style_for(r)
            need = int(gb * 1e9 / 1048576) + args.headroom_mib
            fit = ('?' if not gpu else ('ok' if need <= gpu['free_mib'] else 'DEFER_5090'))
            w = 'pinned' if (r.get('quant_file') and r.get('model_repo_sha')) else '-hf'
            print(f"{r['rank']:>4} {gb:>5.1f}{'~' if est else ' '} {style:<16} {w:<9} {fit:<10} {r['model']}")
        return 0

    caps = server_caps(args.llama_server)
    log(f'🔧 llama-server caps: {caps}')
    if not (caps['reasoning'] or caps['reasoning_budget']):
        log('⚠️  no --reasoning / --reasoning-budget flag: relying on chat_template_kwargs to disable thinking')

    for r in rows:
        style = style_for(r)
        quant = r.get('selected_quant') or r.get('preferred_quant')
        rid = f"{r['model']}:{quant}:off:{(r.get('model_repo_sha') or 'UNPINNED')[:12]}:{PROFILE}"
        if prior.get(rid) in terminal and not args.redo:
            log(f"↩️  {r['rank']:02d} {r['model']} already {prior[rid]}")
            continue
        try:
            run_model(r, args, caps, out_dir, summary_path)
        except KeyboardInterrupt:
            log('🛑 interrupted')
            return 130
    log('🏁 mission pass finished — run: python3 mission/report.py')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
