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


# Judged for qualification but kept off the published board until the user decides (e.g. other engine/hardware).
OFF_BOARD = {'02_Gemma_4_31B_IT+NVFP4-vllm'}


def main() -> int:
    summ = summaries()
    rows = []
    names = sorted({p.name[:-len('.jsonl')].rsplit('.', 1)[0] for p in JUDGE.glob('*.jsonl')} - OFF_BOARD)  # model names contain dots
    for name in names:
        row = {'name': name}
        flags = Counter()
        for arm, (gf, split) in ARMS.items():
            want = arm_ids(gf, split)
            cur = gold_shas(gf)
            scored = {j['id']: j['score'] for j in load(JUDGE / f'{name}.{arm}.jsonl')
                      if 'score' in j and j.get('gold_sha256') == cur.get(j['id'])}
            if not scored:
                row[arm] = None
                continue
            # mechanical zeros (failed, echoed, not run) override any judgment and count toward completion
            zeros, fl = mechanical(name, arm, want)
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
        row['label'] = (s.get('model') or name.split('_', 1)[-1].replace('_', ' ')) + (f' ({variant})' if variant else '')
        rows.append(row)

    def key(r):  # complete lines arm first, then lines mean
        la = r.get('lines_eval')
        return (-(la[1] == la[2]) if la else 1, -(la[0] if la else 0))

    rows.sort(key=key)
    done = [r for r in rows if all(r.get(a) and r[a][1] == r[a][2] for a in ARMS)]
    queued = [r for r in rows if r not in done]
    gb = lambda r: f"{r['vram'] / 1024:.1f}" if r['vram'] else '—'
    out = ['# Ranking', '',
           '| # | Model | Hard lines /10 | Full scenes /10 | Bad lines (≤5) | Seconds per line | VRAM GB | Most common slips |',
           '|---:|---|---:|---:|---:|---:|---:|---|']
    for n, r in enumerate(done, 1):
        out.append(f"| {n} | **{r['label']}** | {r['lines_eval'][0]:.2f} | {r['scenes_full'][0]:.2f} | {r['lines_eval_low']} "
                   f"| {f'{r["lat"]:.2f}' if r['lat'] else '—'} | {gb(r)} | {r['slips']} |")
    if queued:
        out += ['', 'Being judged: ' + ', '.join(
            f"{r['label']} ({(r.get('lines_eval') or (0, 0, 200))[1]}/200 lines)" for r in queued) + '.']
    if done:
        out += ['', '## By category', '', 'Share of the 20 eval lines in each category translated well (9 or 10 out of 10). '
                'With 20 lines per cell, differences under about 20 points are noise.', '',
                '| Model | ' + ' | '.join(label for _, label in CATS) + ' |', '|---|' + '---:|' * len(CATS)]
        for r in done:
            out.append(f"| {r['label']} | " + ' | '.join(f"{100 * g / n:.0f}%" for c, _ in CATS for g, n in [r['cats'][c]]) + ' |')
    if done:
        out += ['', '## Output compliance', '',
                'Decided mechanically, identically for every model. **Automatic zeros** are already in the scores above: no usable '
                'output, or the source returned untranslated. **Flags** are recorded only and do not change the score yet: '
                '*commentary* = an alternative, note or literal gloss appended to the translation; *format* = speaker labels '
                'rewritten as `Name:` or markdown emphasis.', '',
                '| Model | Zero: no output | Zero: untranslated | Commentary | Format |', '|---|---:|---:|---:|---:|']
        for r in done:
            z = r['lines_eval_zero'] + r['scenes_full_zero']
            f = r['lines_eval_flags'] + r['scenes_full_flags']
            out.append(f"| {r['label']} | {z['inference_failure'] + z['not_run']} | {z['exact_echo']} | {f['commentary']} | {f['format']} |")
    out += ['', 'Scores are out of 10: adequacy 0–4, pragmatics and voice 0–4, fluency 0–2, judged by GPT-6.1 Sol. '
            'A line the model failed to produce scores 0. Speed is the median time to finish a line with 6 lines of history on an RTX 3090.']
    (RES / 'judge/RANKING.md').write_text('\n'.join(out) + '\n', encoding='utf8')

    # one-paragraph answer for the landing page
    if done:
        b = done[0]
        head = (f"**Best so far: {b['label']}.** It scores {b['lines_eval'][0]:.2f}/10 on the hard lines and "
                f"{b['scenes_full'][0]:.2f}/10 on full scenes, finishing a line in {b['lat']} s using {gb(b)} GB of VRAM. "
                f"{len(done)} model{'s' if len(done) != 1 else ''} fully judged so far.")
    else:
        head = 'No model is fully judged yet.'
    (RES / 'judge/HEADLINE.md').write_text(head + '\n', encoding='utf8')
    (RES / 'judge/BOARD.html').write_text(board(done, queued), encoding='utf8')
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


def board(done: list[dict], queued: list[dict]) -> str:
    """Landing-page leaderboard: one bar per model on a 0-10 axis; each row expands to its details.

    Kept free of blank lines so Markdown passes it through as one raw HTML block.
    """
    e = lambda s: html.escape(str(s))
    rows = []
    for n, r in enumerate(done, 1):
        score, scenes = r['lines_eval'][0], r['scenes_full'][0]
        qual = ' · '.join(x for x in (f"{r['lat']:.2f} s/line" if r['lat'] else '', fits(r['vram'])) if x)
        tip = f"{r['label']}: {score:.2f}/10 on hard lines, {scenes:.2f}/10 on full scenes"
        vram = f"{r['vram'] / 1024:.1f} GB VRAM loaded" if r['vram'] else ''
        rows.append(
            f'<details class="ob-row"><summary title="{e(tip)}">'
            f'<span class="ob-rank">{n}</span><span class="ob-name">{e(r["label"])}</span>'
            f'<span class="ob-track"><span class="ob-bar" style="width:{score * 10:.1f}%"></span></span>'
            f'<span class="ob-score">{score:.2f}</span><span class="ob-qual">{e(qual)}</span></summary>'
            f'<div class="ob-more"><span><b>{scenes:.2f}</b>/10 on 31 full scenes</span>'
            f'<span><b>{r["lines_eval_low"]}</b> of 200 lines scored 5 or less</span>'
            f'<span>Most common slips: {e(r["slips"] or "none")}</span>'
            f'<span>{e(vram)}</span>{cat_bars(r.get("cats"))}</div></details>')
    for r in queued:
        got = (r.get('lines_eval') or (0, 0, 200))[1]
        rows.append(f'<div class="ob-row ob-queued"><span class="ob-rank">·</span><span class="ob-name">{e(r["label"])}</span>'
                    f'<span class="ob-pending">being judged: {got}/200 lines</span></div>')
    axis = ('<div class="ob-axis" aria-hidden="true"><span></span><span></span>'
            '<span class="ob-ticks"><span>0</span><span>5</span><span>10</span></span><span></span><span></span></div>')
    return ('<div class="ob-board" role="list" aria-label="Ranking by score on 200 hard lines, out of 10">'
            + ''.join(rows) + axis + '</div>\n')


if __name__ == '__main__':
    raise SystemExit(main())
