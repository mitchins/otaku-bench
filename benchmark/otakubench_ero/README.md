# OtakuBench ero slice — research release 0.3.1

**32 original Japanese→English scenes: 24 main, 8 reserve.** Same direction as the screen translator. Not an English-to-Japanese set.

v0.3.1 is a small patch on v0.3: one jargon reference corrected, two checks relaxed where English means the same thing, and completeness checks that every model passed removed. Across v0.1–v0.3 the four local models refused nothing. That arm is for other families. `review/SELF_TEST.md` is not a model result.

## What it is for

Two scores, reported separately. Do not average them.

1. **Fidelity, given an attempt.** Act, direction, register, formula, consent. History can change the reading.
2. **Refusal or no output.** Counted apart from a bad translation.

## Adult boundary

Unchanged. Every participant is at least 26 in the gold metadata. Ages are not in the Japanese. No school, no kinship sex, no ageplay. The safeword pair and the consent split are kept. See `PROTOCOL.md`.

## Read first

- `PROTOCOL.md` — task, prompt, judging.
- `review/SELF_TEST.md` — literal baseline pass rate by family.
- `data/ero24_turns_blind.jsonl` — primary input. Japanese history and the current line only.

Not wired into `mission/run.sh`. Do not add a sentence that permits sexual content. That would measure a different task.

```bash
python benchmark/otakubench_ero/tools/author.py
python benchmark/otakubench_ero/tools/validate.py
python -m pytest benchmark/otakubench_ero/tests -q
```

Do not pool these items with v0.1, the v4 200 lines, or the hard slice. New source hashes.
