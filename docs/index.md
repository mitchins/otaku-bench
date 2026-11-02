---
hide:
  - navigation
  - toc
---

# OtakuBench <small>Preview</small>

!!! note "Preview"
    The method and test sets are still changing, so scores and ranks may move. Version 1.0 will freeze them; later changes ship as 1.1, 1.2 and so on, with old results kept for comparison.

Which local model should translate the visual-novel line on your screen? Ranked by **Pass %**, the share of lines translated in full: meaning and intent intact, readable English, nothing added. Only models fast enough to read along with are included: under 2 s per line on an RTX 3090.

- **Standard**: 200 Japanese lines built around idioms, keigo, negation, dialect and ellipsis.
- **Hard**: an unreleased slice of 167 lines from 57 scenes, each line with named checks a careless translation fails.
- **Adult**: an unreleased slice of 72 lines from adult scenes. Shown as the pass rate among lines the model didn't refuse, with the refusal rate beside it. It isn't part of the Overview.
- **Overview**: the plain mean of Standard and Hard.

--8<-- "results/judge/BOARD.html"

<small>Judged by GPT-6.1 Sol. Click a column name to sort by it, or a model for its full-scene score and typical mistakes. Faint lines behind the bars are 95% intervals: bars whose lines overlap are not clearly different. A dash means not judged yet; until the Hard slice is judged, the board is sorted by Standard. New models are added as the daily judging run finishes them.</small>

??? question "What's being tested?"
    Each model runs the way a screen translator would: a short instruction, a few lines of dialogue history, and the line on screen. That means a 2k context window, a 256-token output cap, and thinking switched off. Nobody waits 40 seconds for a line.

    The 200 lines are written to catch the mistakes that ruin a scene: 油を売る read literally as "selling oil", 猫をかぶる as "pretends to be a cat", or a negation or a who-did-what reversed. Separately, the 31 full scenes test whether names, speakers and tone hold up across a conversation.

??? question "How is it scored?"
    On the Standard lines the judge gives each translation 0–4 for meaning, 0–4 for intent and voice, and 0–2 for natural English. A line passes at 4, 4 and at least 1, with no note or alternative appended. On the Hard and Adult slices each line has named checks (who did it, what was negated, what was left unsaid), and it passes when all of them pass. The judge treats the reference as one valid reading, not the only one, so creative equivalents aren't penalised. It doesn't know which model it's judging. A line the model failed to produce fails.

    One judge and one run per model: differences of a few tenths between neighbours are within noise. More in **[Method](method.md)**.

??? question "Why speed first?"
    A translation that arrives after you've clicked to the next line is useless. Before any quality testing, every model must finish a line in under 2 s (median) and 3 s (slowest 10%), measured with 6 lines of history. On a 3090 almost everything passes, even dense 27–31B models at about 1.2 s. On smaller hardware the trade-off matters more. **[Latency](latency.md)** has every model's speed and memory use.

??? question "Which models didn't make the cut?"
    Of the 50 candidates, 44 produced translations. Out for screen use:

    - **Thinking models that won't stop thinking.** The three LLM-jp-4.1 Thinking models, and Qwen3-Swallow-8B-RL, which reasons in its visible reply.
    - **GPT-OSS-Swallow-20B**: 2.9 s per line even at low reasoning effort.
    - **Nemotron 3 Nano 30B-A3B**: too big for 24 GB at Q4, so it's deferred to a larger GPU.

    Some others needed a workaround to run at all: gpt-oss-20b at low effort, LFM2.5-24B with an empty think block. These are labelled wherever they appear.

??? question "Can I see the test data?"
    The 50 development lines and 6 scenes are public. The 200 evaluation lines and their reference translations are encrypted in the repository, so the test doesn't leak into future models' training data. See **[Data policy](data.md)**.
