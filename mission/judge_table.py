#!/usr/bin/env python3
"""Comparison table of judged models -> results/judge/RANKING.md.

Means are over the whole arm: items the model failed to produce (cap hit, errors) score 0, so a model
can't rank higher by dropping hard lines. Latency/VRAM come from the mission summaries.
"""
from __future__ import annotations

import hashlib
import html
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import mechanical as mech  # noqa: E402
import judge_slice as js  # noqa: E402  (slice gold, input hashing; importing makes no API calls)
sys.path.insert(0, str(ROOT / 'mission'))
import metric_preview as mp  # noqa: E402  (screen-ready Pass %, rule A)
RES = ROOT / 'results'
JUDGE = RES / 'judge/sol'
GOLD = ROOT / 'benchmark/otakubench/data/build'
ARMS = {'scenes_full': ('scenes_gold.jsonl', None), 'lines_eval': ('lines_gold.jsonl', 'eval')}
RESPONSES = {'scenes_full': 'scenes_full', 'lines_eval': 'lines_bare'}  # response file behind each judged arm
# judge flags in reader terms
SLIPS = {'IDIOM': 'idioms', 'VOICE': 'voice', 'OMIT': 'omissions', 'ADD': 'additions', 'AGENT': 'who did what',
         'NEG': 'negation', 'ASPECT': 'tense/aspect', 'MOD': 'modality', 'KEIGO': 'politeness', 'IMPL': 'implication',
         'CULT': 'cultural terms', 'HUMOUR': 'wordplay', 'REFUSAL': 'refusals', 'TERMINOLOGY': 'terms',
         'FORMAT': 'formatting', 'AMBIGUITY': 'ambiguity'}
# the 10 line categories (20 eval lines each), in one fixed order so models compare side by side
CATS = [('idiom_proverb', 'Idioms & proverbs'), ('wordplay_irony', 'Wordplay & irony'),
        ('dialect_character_voice', 'Dialect & voice'), ('keigo_politeness', 'Politeness (keigo)'),
        ('indirectness_pragmatics', 'Indirect speech'), ('emotion_subtext', 'Emotional subtext'),
        ('ellipsis_coreference', 'Omitted subjects'), ('culture_institutions', 'Culture & institutions'),
        ('genre_literary_structure', 'Literary style'), ('mimetics_onomatopoeia', 'Onomatopoeia')]
GOOD = 9  # "translated well": at most a minor slip


def load(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding='utf8').splitlines() if x.strip()] if p.exists() else []


def gold_shas(gold_file: str) -> dict[str, str]:
    # same fingerprint judge.py stores; a judgment of older gold is stale and reads as pending
    return {g['id']: hashlib.sha256(json.dumps(g, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
            for g in load(GOLD / gold_file)}


def arm_ids(gold_file: str, split: str | None) -> set[str]:
    return {g['id'] for g in load(GOLD / gold_file) if split is None or g['split'] == split}


def line_cats() -> dict[str, list[str]]:
    out = {c: [] for c, _ in CATS}
    for g in load(GOLD / 'lines_gold.jsonl'):
        if g['split'] == 'eval':
            out[g['primary_challenge']].append(g['id'])
    return out


def response_dir(name: str) -> Path | None:
    """Judge-file name -> its response dir: 03_X, 36_X+empty-think (screen_variants), 01_X+UD-Q6_K_L (screen_quants)."""
    base, _, tag = name.partition('+')
    for d in ([RES / 'screen' / base] if not tag else [RES / 'screen_variants' / tag / base, RES / 'screen_quants' / tag / base]):
        if d.is_dir():
            return d
    return None


# --- Pass % per slice: the board's common scale. Overview = mean(Standard, Hard), equal weight per slice. ---
OVERVIEW_SLICES = ('standard', 'hard')  # Adult is shown and sortable, never blended (ero PROTOCOL.md)


def standard_pass(name: str) -> dict | None:
    """Screen-ready Pass % on the 200 eval lines (mission/metric_preview.py rule A); None until all 200 are decided."""
    gold = {g['id']: g for g in load(GOLD / 'lines_gold.jsonl') if g.get('split') == 'eval'}
    blind_path = GOLD / 'lines_bare.jsonl'
    blind = {r['id']: r for r in load(blind_path)}
    d = response_dir(name)
    s = mp.summarize(name, load(JUDGE / f'{name}.lines_eval.jsonl'), load(d / 'lines_bare.jsonl') if d else [],
                     gold, blind, hashlib.sha256(blind_path.read_bytes()).hexdigest())
    if s['status'] != 'COMPLETE':
        return None
    return {'pct': s['screen_ready_pct'], 'ci': s['screen_ready_95_ci'], 'n': s['total']}


def slice_result(slice_: str, name: str) -> dict | None:
    """Pass % on the hard or ero slice, from the judgment of the response currently on disk for every scored turn.

    pass = every check on the line passes; uncertain is not a pass. A judge refusal is neither pass nor fail
    (left out of the denominator, counted). Ero: refusals are reported as their own rate and the pass rate is
    among non-refused lines (ero PROTOCOL.md); hard: a refusal is a failed line. None until every turn is decided.
    """
    base, _, tag = name.partition('+')
    resp = RES / 'screen_slices' / (f'{tag}/' if tag else '') / base / f'{slice_}_turns.jsonl'
    cfg = js.SLICES[slice_]
    gold = {g['id']: g for g in load(cfg['gold']) if g['is_scored_target']}
    chosen = js.pick_responses(load(resp), gold) if resp.is_file() else {}
    judged = {}
    for x in load(RES / 'judge/slices' / slice_ / f'{name}.jsonl'):
        g, r = gold.get(x['id']), chosen.get(x['id'])
        if (g and r and x.get('outcome') not in (None, 'judge_error') and x.get('run_id') == r.get('run_id')
                and x.get('turn_sha256') == g['turn_sha256'] and x.get('gold_sha256') == js.sha(js.make_input(slice_, g))):
            judged[x['id']] = x
    if not judged:
        return None
    out = {'done': len(judged), 'total': len(gold), 'pct': None}
    if len(judged) < len(gold):
        return out
    passes, refused, judge_refused, over_sex = [], 0, 0, 0
    for i, x in judged.items():
        if x['outcome'] == 'judge_refusal':
            judge_refused += 1
            continue
        is_refusal = x['outcome'] == 'refusal' or bool(x.get('judge_flagged_refusal'))
        ok = x['outcome'] == 'judged' and not is_refusal and all(v == 'pass' for v in (x.get('checks') or {}).values())
        if slice_ == 'ero':
            exp = gold[i]['refusal_expectation']
            refused += is_refusal and exp == 'must_translate'
            over_sex += exp == 'must_not_sexualize' and not ok and not is_refusal
            if is_refusal:
                continue
        passes.append(float(ok))
    out.update(pct=round(100 * sum(passes) / len(passes), 1) if passes else None, ci=mp.percentile_ci(passes),
               n=len(passes), judge_refused=judge_refused)
    if slice_ == 'ero':
        must = sum(g['refusal_expectation'] == 'must_translate' for g in gold.values())
        out.update(refused=refused, refused_of=must, refused_pct=round(100 * refused / must, 1),
                   over_sex=over_sex, over_sex_of=len(gold) - must)
    return out


def mechanical(name: str, arm: str, want: set[str]) -> tuple[dict[str, str], Counter]:
    """Items decided without the judge (id -> reason; scored 0), and compliance flags on the rest.
    Written to results/judge/mechanical/ so every automatic zero is auditable."""
    d = response_dir(name)
    src = {g['id']: g['japanese'] for g in load(GOLD / f'{RESPONSES[arm]}.jsonl')}
    resp = {r['id']: r for r in load(d / f'{RESPONSES[arm]}.jsonl')} if d else {}
    zeros, fl, recs = {}, Counter(), []
    for i in sorted(want):
        r = resp.get(i)
        why = 'not_run' if r is None else mech.zero_reason(src[i], r.get('translation'), r.get('error'))
        if why:
            zeros[i] = why
        else:
            fl.update(mech.flags(src[i], r['translation']))
        recs.append({'id': i, 'zero': why, 'flags': [] if why else mech.flags(src[i], r['translation'])})
    out = RES / 'judge/mechanical' / f'{name}.{arm}.jsonl'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(''.join(json.dumps(x) + '\n' for x in recs), encoding='utf8')
    return zeros, fl


def summaries() -> dict[str, dict]:
    out = {}
    for p in [RES / 'screen/summary.jsonl', *RES.glob('screen_variants/*/summary.jsonl'), *RES.glob('screen_quants/*/summary.jsonl')]:
        variant = p.parent.name if p.parent.parent.name in ('screen_variants', 'screen_quants') else ''
        for r in load(p):
            out[f"{r['rank']:02d}" + (f'+{variant}' if variant else '')] = r
    return out


# Judged for qualification or as a cloud reference, but kept off the published board until the user decides (e.g. other engine/hardware).
OFF_BOARD = {'02_Gemma_4_31B_IT+NVFP4-vllm', 'C01_Gemini-3.5-Flash-Lite', 'C01_Gemini-3.5-Flash-Lite+explicit-target', 'C01_Gemini-3.5-Flash-Lite+short-system'}
# One board entry assembled from per-arm runs (entry -> judged name per arm), shown with an asterisk and FOOTNOTES.
COMPOSITE = {'C01_Gemini-3.5-Flash-Lite*': {'lines_eval': 'C01_Gemini-3.5-Flash-Lite', 'scenes_full': 'C01_Gemini-3.5-Flash-Lite+short-system',
                                            # slices: the vendor-recommended short system prompt, as for scenes (user, 2026-11-03)
                                            'hard': 'C01_Gemini-3.5-Flash-Lite+short-system', 'ero': 'C01_Gemini-3.5-Flash-Lite+short-system'}}
LABELS = {'C01_Gemini-3.5-Flash-Lite*': 'Gemini 3.5 Flash-Lite (cloud)*',
          'C02_Claude-Haiku-5.5': 'Claude Haiku 5.5 (cloud)', 'C03_Claude-Sonnet-5.5': 'Claude Sonnet 5.5 (cloud)',
          'C04_Gemini-3.8-Flash': 'Gemini 3.8 Flash (cloud)',
          # expert-count prunes of one model: the base entry is the 120e file, the smaller prunes are screen_quants tags
          '68_Gemma_4_26B-A4B_heretic_JP-pruned_120e+72e': 'Gemma 4 26B-A4B heretic JP-pruned 72e',
          '68_Gemma_4_26B-A4B_heretic_JP-pruned_120e+96e': 'Gemma 4 26B-A4B heretic JP-pruned 96e'}
FOOTNOTES = {'C01_Gemini-3.5-Flash-Lite*': 'Gemini: full scenes use only the first sentence of the system prompt; '
             'with the full prompt it returns some scenes untranslated.'}


def main() -> int:
    summ = summaries()
    rows = []
    names = sorted({p.name[:-len('.jsonl')].rsplit('.', 1)[0] for p in JUDGE.glob('*.jsonl')} - OFF_BOARD) + list(COMPOSITE)  # model names contain dots
    for name in names:
        row = {'name': name}
        flags = Counter()
        for arm, (gf, split) in ARMS.items():
            src_name = COMPOSITE.get(name, {}).get(arm, name)
            want = arm_ids(gf, split)
            cur = gold_shas(gf)
            scored = {j['id']: j['score'] for j in load(JUDGE / f'{src_name}.{arm}.jsonl')
                      if 'score' in j and j.get('gold_sha256') == cur.get(j['id'])}
            if not scored:
                row[arm] = None
                continue
            # mechanical zeros (failed, echoed, not run) override any judgment and count toward completion
            zeros, fl = mechanical(src_name, arm, want)
            scored = {i: sc for i, sc in scored.items() if i in want and i not in zeros}
            total = sum(s['adequacy'] + s['pragmatics'] + s['fluency'] for s in scored.values())
            row[arm] = (total / len(want), len(scored) + len(zeros), len(want))
            row[arm + '_low'] = len(zeros) + sum(1 for s in scored.values() if s['adequacy'] + s['pragmatics'] + s['fluency'] <= 5)
            row[arm + '_zero'] = Counter(zeros.values())
            row[arm + '_flags'] = fl
            flags.update(f for s in scored.values() for f in s['flags'])
            if arm == 'lines_eval':
                total_of = lambda i: sum(scored[i][k] for k in ('adequacy', 'pragmatics', 'fluency')) if i in scored else 0
                row['cats'] = {c: (sum(total_of(i) >= GOOD for i in ids), len(ids)) for c, ids in line_cats().items()}
        variant = name.partition('+')[2]
        s = summ.get(name.partition('_')[0] + (f'+{variant}' if variant else ''), {})
        row['lat'] = ((s.get('latency') or {}).get(str(s.get('gate_depth', 6))) or {}).get('median_s')
        row['vram'] = s.get('vram_used_mib_loaded')
        row['slips'] = ', '.join(SLIPS.get(f, f.lower()) for f, _ in flags.most_common(3))
        # Always name the quant, so a bare "Gemma 4 31B IT" is never mistaken for its Q5_K_M row; prompt variants follow it.
        tags = [t for t in (s.get('quant'), variant if name not in LABELS else '') if t]
        tags = list(dict.fromkeys(tags))  # a screen_quants tag usually is the quant
        base = LABELS.get(name) or s.get('model') or name.split('_', 1)[-1].replace('_', ' ')
        row['label'] = base + (f" ({', '.join(tags)})" if tags else '')
        row['note'] = FOOTNOTES.get(name)
        row['standard'] = standard_pass(COMPOSITE.get(name, {}).get('lines_eval', name))
        row['hard'] = slice_result('hard', COMPOSITE.get(name, {}).get('hard', name))
        row['adult'] = slice_result('ero', COMPOSITE.get(name, {}).get('ero', name))
        parts = [(row[k] or {}).get('pct') for k in OVERVIEW_SLICES]
        row['overview'] = round(sum(parts) / len(parts), 1) if all(p is not None for p in parts) else None
        rows.append(row)

    done = [r for r in rows if all(r.get(a) and r[a][1] == r[a][2] for a in ARMS) and r['standard']]
    queued = [r for r in rows if r not in done]
    # Overview once any model has every overview slice; until then (Hard not judged yet) Standard
    sort_key = 'overview' if any(r['overview'] is not None for r in done) else 'standard'
    done.sort(key=lambda r: (sort_value(r, sort_key) is None, -(sort_value(r, sort_key) or 0), -r['standard']['pct'], r['label']))
    queued.sort(key=lambda r: -(r.get('lines_eval') or (0, 0))[1])
    md = lambda s: s.replace('*', '\\*')
    gb = lambda r: f"{r['vram'] / 1024:.1f}" if r['vram'] else '—'
    pct = lambda x: f"{x:.1f}" if x is not None else '—'
    out = [f'# Ranking ({VERSION})', '',
           f'Sorted by **{SORT_NAMES[sort_key]}**. Pass % is the share of lines translated in full: meaning and intent intact, '
           'readable English, nothing added. Overview is the plain mean of Standard and Hard. Adult is reported separately: '
           'pass % among the lines the model did not refuse, with the refusal rate beside it. A dash means not judged yet.', '',
           '| # | Model | Overview % | Standard % | Hard % | Adult % (not refused) | Adult refused % '
           '| Standard /10 | Full scenes /10 | Bad lines (≤5) | Seconds per line | VRAM GB | Most common slips |',
           '|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|']
    n = 0
    for r in done:
        n += sort_value(r, sort_key) is not None
        a = r['adult'] or {}
        out.append(f"| {n if sort_value(r, sort_key) is not None else '·'} | **{md(r['label'])}** | {pct(r['overview'])} "
                   f"| {pct(r['standard']['pct'])} | {pct((r['hard'] or {}).get('pct'))} | {pct(a.get('pct'))} "
                   f"| {pct(a.get('refused_pct'))} | {r['lines_eval'][0]:.2f} | {r['scenes_full'][0]:.2f} | {r['lines_eval_low']} "
                   f"| {f'{r["lat"]:.2f}' if r['lat'] else '—'} | {gb(r)} | {r['slips']} |")
    out += [''] + [f"\\* {r['note']}" for r in done if r['note']] if any(r['note'] for r in done) else []
    if queued:
        out += ['', 'Being judged: ' + ', '.join(
            f"{r['label']} ({(r.get('lines_eval') or (0, 0, 200))[1]}/200 lines)" for r in queued) + '.']
    if done:
        out += ['', '## By category', '', 'Share of the 20 eval lines in each category translated well (9 or 10 out of 10). '
                'With 20 lines per cell, differences under about 20 points are noise.', '',
                '| Model | ' + ' | '.join(label for _, label in CATS) + ' |', '|---|' + '---:|' * len(CATS)]
        for r in done:
            out.append(f"| {md(r['label'])} | " + ' | '.join(f"{100 * g / n:.0f}%" for c, _ in CATS for g, n in [r['cats'][c]]) + ' |')
    if done:
        out += ['', '## Output compliance', '',
                'Decided mechanically, identically for every model. **Automatic zeros** are already in the scores above: no usable '
                'output, or the source returned untranslated. **Flags** do not change the /10 scores; *commentary* fails a line for Pass %: '
                '*commentary* = an alternative, note or literal gloss appended to the translation; *format* = speaker labels '
                'rewritten as `Name:` or markdown emphasis.', '',
                '| Model | Zero: no output | Zero: untranslated | Commentary | Format |', '|---|---:|---:|---:|---:|']
        for r in done:
            z = r['lines_eval_zero'] + r['scenes_full_zero']
            f = r['lines_eval_flags'] + r['scenes_full_flags']
            out.append(f"| {md(r['label'])} | {z['inference_failure'] + z['not_run']} | {z['exact_echo']} | {f['commentary']} | {f['format']} |")
    out += ['', 'Standard: 200 eval lines judged by GPT-6.1 Sol on adequacy 0–4, pragmatics and voice 0–4, fluency 0–2; a line passes '
            'at 4, 4 and at least 1 with no commentary appended. Hard and Adult: each line has named checks, and it passes when '
            'every check passes (uncertain is not a pass). A line the model failed to produce fails (scores 0 out of 10). '
            'Speed is the median time to finish a line with 6 lines of history on an RTX 3090.']
    (RES / 'judge/RANKING.md').write_text('\n'.join(out) + '\n', encoding='utf8')

    # one-paragraph answer for the landing page
    if done:
        b = done[0]
        hard = (b['hard'] or {}).get('pct')
        head = (f"**Best so far: {b['label']}.** It passes {b['standard']['pct']:.0f}% of the 200 standard lines"
                + (f" and {hard:.0f}% of the hard slice" if hard is not None else '')
                + (f", finishing a line in {b['lat']:.2f} s using {gb(b)} GB of VRAM. " if b['lat'] is not None
                   else ". It is a cloud model, so it has no local speed or VRAM figure. ")
                + f"{len(done)} model{'s' if len(done) != 1 else ''} fully judged so far.")
    else:
        head = 'No model is fully judged yet.'
    (RES / 'judge/HEADLINE.md').write_text(head + '\n', encoding='utf8')
    (RES / 'judge/BOARD.html').write_text(board(done, queued, sort_key), encoding='utf8')
    print('\n'.join(out) + '\n\n' + head)
    return 0


def fits(mib: int | None) -> str:
    """Smallest common GPU memory size the loaded model fits in, with ~1 GB left for the desktop."""
    if not mib:
        return ''
    for gb in (8, 12, 16, 24):
        if mib <= (gb - 1) * 1024:
            return f'fits {gb} GB'
    return 'needs > 24 GB'


def cat_bars(cats: dict | None) -> str:
    if not cats:
        return ''
    cells = ''.join(
        f'<span class="ob-cat"><span class="ob-cat-name">{html.escape(label)}</span>'
        f'<span class="ob-track"><span class="ob-bar" style="width:{100 * good / n:.0f}%"></span></span>'
        f'<span class="ob-cat-val">{100 * good / n:.0f}%</span></span>'
        for c, label in CATS for good, n in [cats[c]])
    return ('<span class="ob-cats-head">Lines translated well (9 or 10 out of 10), by category. '
            '20 lines each, so treat differences under about 20 points as noise.</span>'
            f'<span class="ob-cats">{cells}</span>')


VERSION = 'Preview'  # becomes '1.0' when the method and slices freeze; 1.x for follow-ups
SORT_NAMES = {'overview': 'Overview', 'standard': 'Standard', 'hard': 'Hard', 'adult': 'Adult'}


def sort_value(r: dict, key: str) -> float | None:
    if key == 'overview':
        return r['overview']
    return (r.get(key) or {}).get('pct')


def cell(res: dict | None, slice_name: str, label: str) -> str:
    """One slice's mini bar: 0-100 % with a faint 95% interval behind it; a dash until judged."""
    e = lambda x: html.escape(str(x))
    if not res or res.get('pct') is None:
        why = f"{res['done']}/{res['total']} lines judged" if res else 'not judged yet'
        return f'<span class="ob-cell ob-na" title="{e(label)}: {why}"><span class="ob-cell-name">{e(label)}</span>—</span>'
    lo, hi = res.get('ci') or (res['pct'], res['pct'])
    tip = f"{label}: {res['pct']:.1f}% of {res['n']} lines pass (95% interval {lo:.0f}–{hi:.0f}%)"
    extra = ''
    if 'refused_pct' in res:
        tip += f"; refused {res['refused']} of {res['refused_of']} lines that should be translated"
        extra = f'<span class="ob-ref">{res["refused_pct"]:.0f}% refused</span>'
    return (f'<span class="ob-cell" title="{e(tip)}"><span class="ob-cell-name">{e(label)}</span>'
            f'<span class="ob-track"><span class="ob-ci" style="left:{lo:.1f}%;width:{max(hi - lo, 0):.1f}%"></span>'
            f'<span class="ob-bar" style="width:{res["pct"]:.1f}%"></span></span>'
            f'<span class="ob-val">{res["pct"]:.0f}%</span>{extra}</span>')


def board(done: list[dict], queued: list[dict], sort_key: str) -> str:
    """Landing-page leaderboard: Overview number plus one 0-100 % bar per slice; headers re-sort (docs/javascripts/board.js).

    Kept free of blank lines so Markdown passes it through as one raw HTML block.
    """
    e = lambda s: html.escape(str(s))
    data = lambda x: '' if x is None else f'{x:.1f}'
    rows, n = [], 0
    for r in done:
        v = sort_value(r, sort_key)
        n += v is not None
        qual = ' · '.join(x for x in (f"{r['lat']:.2f} s/line" if r['lat'] else '', fits(r['vram'])) if x)
        vram = f"{r['vram'] / 1024:.1f} GB VRAM loaded" if r['vram'] else ''
        note = f'<span>* {e(r["note"])}</span>' if r['note'] else ''
        a, h = r['adult'] or {}, r['hard'] or {}
        adult_more = (f'<span>Adult: refused <b>{a["refused"]}</b> of {a["refused_of"]} lines that should be translated; '
                      f'sexualised <b>{a["over_sex"]}</b> of {a["over_sex_of"]} that should not be</span>') if a.get('pct') is not None else ''
        ov = f'{r["overview"]:.0f}%' if r['overview'] is not None else '—'
        rows.append(
            f'<details class="ob-row" data-overview="{data(r["overview"])}" data-standard="{data(r["standard"]["pct"])}" '
            f'data-hard="{data(h.get("pct"))}" data-adult="{data(a.get("pct"))}">'
            f'<summary><span class="ob-rank">{n if v is not None else "·"}</span><span class="ob-name">{e(r["label"])}</span>'
            f'<span class="ob-overview" title="Overview: mean of Standard and Hard">{ov}</span>'
            + cell(r['standard'], 'standard', 'Standard') + cell(r['hard'], 'hard', 'Hard') + cell(r['adult'], 'adult', 'Adult')
            + f'<span class="ob-qual">{e(qual)}</span></summary>'
            f'<div class="ob-more"><span><b>{r["lines_eval"][0]:.2f}</b>/10 on the 200 standard lines, '
            f'<b>{r["scenes_full"][0]:.2f}</b>/10 on 31 full scenes</span>'
            f'<span><b>{r["lines_eval_low"]}</b> of 200 standard lines scored 5 or less</span>'
            f'<span>Most common slips: {e(r["slips"] or "none")}</span>'
            f'{adult_more}<span>{e(vram)}</span>{note}{cat_bars(r.get("cats"))}</div></details>')
    for r in queued:
        got = (r.get('lines_eval') or (0, 0, 200))[1]
        rows.append(f'<div class="ob-row ob-queued"><span class="ob-rank">·</span><span class="ob-name">{e(r["label"])}</span>'
                    f'<span class="ob-pending">being judged: {got}/200 standard lines</span></div>')
    btn = lambda k, tip: (f'<button type="button" class="ob-sort" data-key="{k}" aria-pressed="{str(k == sort_key).lower()}" '
                          f'title="{e(tip)}">{SORT_NAMES[k]}</button>')
    head = ('<div class="ob-head"><span class="ob-rank">#</span><span class="ob-name">Model</span>'
            + btn('overview', 'Sort by Overview: the plain mean of Standard and Hard Pass %')
            + btn('standard', 'Sort by Standard: Pass % on the 200 public-method lines')
            + btn('hard', 'Sort by Hard: Pass % on the unreleased hard slice')
            + btn('adult', 'Sort by Adult: Pass % among lines not refused; refusal rate shown beside it')
            + '<span class="ob-qual">Speed · fits</span></div>')
    return (f'<div class="ob-board" data-sort="{sort_key}" role="list" aria-label="Ranking by {SORT_NAMES[sort_key]} Pass %">'
            + head + ''.join(rows) + '</div>\n')


if __name__ == '__main__':
    raise SystemExit(main())
