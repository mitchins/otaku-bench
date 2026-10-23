# JP-Media-250

A **real 250-record Japanese→English translation benchmark dataset**, designed to test
small and large LLMs on nuance common to visual novels, light novels, games and anime.

**Status:** v1.0.0 editorial draft. The records exist in `data/build/jpmedia250_gold.*`.
This is not a proposed research plan or a 20-row illustrative sample.

## Important provenance distinction

- The **250 Japanese lines are original, genre-inspired test sentences** assembled
  for this dataset; some incorporate conventional Japanese idioms, proverbs and stock
  greetings. **They are not verified quotations from identifiable works.**
- The media field is a **counterbalanced format/style scenario label**, not an
  assertion that a sentence was copied from an anime, novel, VN or game. No fictional
  episode, game, creator, URL or chapter is attributed.
- The English references and metadata were drafted as part of this project.
  **They have not undergone independent native-speaker adjudication.** The difficulty
  levels are editorial heuristics, not externally calibrated JLPT equivalents.
- The data are useful for exploratory model comparisons and error discovery now,
  but should not be marketed as independently validated translation gold.

## What ships

| File | Contents |
|---|---|
| `data/build/jpmedia250_gold.csv` | All 250 full annotated examples; UTF-8 with BOM for Excel compatibility |
| `data/build/jpmedia250_gold.jsonl` | All 250 machine-readable records; arrays for tags and alternate translations |
| `data/build/jpmedia250_blind_japanese_only.jsonl` | Japanese-only tasks without gold/context |
| `data/build/jpmedia250_blind_with_context.jsonl` | Japanese plus short scene relationship/context, without gold |
| `data/build/jpmedia250_review.xlsx` | Filterable editorial review workbook; corpus, coverage, overview, rubric |
| `data/build/manifest.json` | Exact counts, provenance, difficulty, challenge distribution, SHA256 |
| `data/sections/*.tsv` | Editable, human-authored master entries (10×25) |
| `tools/build.py` | Deterministic generator and integrity validation |
| `tools/run_api.py` | OpenAI-compatible local inference client; resumable JSONL outputs |
| `tools/score.py` | Weak chrF-lite diagnostic + editable human review CSV |
| `tests/test_dataset.py` | Structural, split-leakage and scoring tests |
| `RUBRIC.md` | Human adjudication and error-tag policy |

## Distribution

- **250 unique Japanese source lines.** 10 primary challenges × 25 examples.
- **Difficulty:** 50 each at D1 / D2 / D3 / D4 / D5. Progresses from easier
  cases to more compositional/pragmatically hard ones *within each challenge*.
- **Media-style scenarios:** 63 visual novel, 63 light novel, 62 game, 62 anime.
  These labels are distributed round-robin and are not source verification.
- **Split:** 50 development items, 200 evaluation items (one development and four
  evaluation cases in each category×difficulty stratum).
- **Tags:** 2+ secondary linguistic/social markers per example.
- **Genres:** romance, school, fantasy, mystery, science fiction, drama, historical,
  political, sports, noir, horror, family, and others.

### Primary categories (25 each)

1. `ellipsis_coreference` — omitted agents, deixis, anaphora, scope
2. `keigo_politeness` — honorifics, humility, hierarchy, formal dissent
3. `idiom_proverb` — common fixed expressions, metaphorical meanings
4. `indirectness_pragmatics` — refusals, requests, hedging and backhanded compliments
5. `dialect_character_voice` — Kansai, stylized regional varieties, archaized voices
6. `wordplay_irony` — homophones, polysemy, comic timing and metalinguistic jokes
7. `mimetics_onomatopoeia` — Japanese sound-symbolic speech, tactile/emotional effects
8. `culture_institutions` — festivals, customs, workplace and social conventions
9. `emotion_subtext` — denial, love, grief, jealousy, constrained agency
10. `genre_literary_structure` — RPG mechanics, narration, logical scope and embedding

## Model evaluation

First compare **Japanese alone** versus **Japanese plus minimal scene context**.
The latter tests appropriate pragmatic inference; the former tests whether a model
hallucinates one possible disambiguation as certain.

### Example: test a local OpenAI-compatible endpoint

```bash
# Regenerate the dataset from section files and validate the counts
python3 tools/build.py
python3 -m unittest discover -s tests -v

# Replace base URL and model name with your running server/model
python3 tools/run_api.py \
  --base-url http://127.0.0.1:1234/v1 \
  --model my-local-model \
  --mode context --split dev \
  --output results/my-model-context-dev.jsonl

python3 tools/run_api.py \
  --base-url http://127.0.0.1:1234/v1 \
  --model my-local-model \
  --mode bare --split eval \
  --output results/my-model-bare-eval.jsonl

# Generates weak surface-overlap diagnostics + a human rating worksheet
python3 tools/score.py results/my-model-context-dev.jsonl \
  --out results/my-model-review.csv
```

The client uses Python's standard library, POSTs to `/chat/completions`, stores
latency and any returned usage, and skips previously successful `(id, model, mode)`
items when resumed. If a local server rejects `max_tokens`, `temperature`, or a
model-specific option, adjust `tools/run_api.py` accordingly. No model inference
has been run against the 250 examples in this build.

### Scoring principle

Use the reference translation and `translation_note` as **guides to meaning**, not
one exact required English wording. A semantically valid paraphrase may differ
in every surface word. Judge **accuracy (0–4)**, **pragmatics/voice (0–4)** and
**English fluency (0–2)**. Record critical mistakes separately.

`tools/score.py` uses a homegrown character n-gram F2 overlap (`chrF-lite`), not
canonical sacreBLEU chrF and not a measure of cultural competence. It is included
for spotting outliers and quickly exporting a review queue, not for trustworthy
model rankings. Do not use it to declare success on idioms, puns or indirectness.

## Reproducibility, QA, and future qualification

`tools/build.py` fails on wrong section sizes, missing fields, duplicate Japanese
source text, incorrect media/difficulty/split counts and insufficient tags.
The native-speaker review, alternative translations, error adjudication, natural
register checks and benchmark contamination check remain **open qualification
work**, not claimed to be done.

For a defensible release: two independent Japanese-proficient annotators should
blind-review all references and contexts (especially stylized regional speech),
resolve disagreements, and separately calibrate D1–D5 using several reference
models. Re-test a held-out independently written set before claiming ranking
validity. Use the 50 dev cases for prompt tuning, never the 200 eval cases.

## Dataset editing

Each `data/sections/*.tsv` line is six pipe-delimited fields:

```text
japanese|english_reference|scene_context|translation_note|comma,separated,tags|genre
```

Each category has 25 lines in 5 groups of 5 (D1–D5). IDs and format-style labels
are assigned by `tools/build.py` in that stable order. Change the source TSVs,
not the generated files, then run `build.py` and the tests. IDs are stable only
if rows are not inserted, deleted or re-ordered.
