# Evaluation rubric / annotation policy

## Inputs

**Japanese-only** and **Japanese+scene** are separate benchmarks. For contextual
translation, the evaluator may see `scene_context` but not `english_reference`,
`alternate_references` or `translation_note`. The reference/scoring staff may
see all fields, but should blind-rate candidate responses before using gold.

## Rating /10

| Dimension | Range | Full credit | Typical deductions |
|---|---:|---|---|
| Meaning/adequacy | 0–4 | Correct content, actors, negation, time/aspect, modality and focus | Wrong referent, omitted critical assertion, inverted negation, invented fact |
| Pragmatics, register & subtext | 0–4 | Correct speech act, indirectness, social status, sarcasm, character voice, cultural meaning | Literalized idiom, lost refusal, made hedging definitive, changed politeness hierarchy |
| Natural English | 0–2 | Fluent, idiomatic English suitable for the speaker/context | Awkward literal phrasing, stilted or incorrect English |

For meaning and pragmatics, use integer anchors: **4** fully adequate, **3** a
minor nuance error, **2** partial, **1** substantially wrong, **0** opposite or
unusable. Fluency: **2** natural, **1** awkward but clear, **0** difficult to follow.

**Error flag vocabulary**: `NEG` negation; `AGENT` role assignment; `ASPECT`
time/aspect; `MOD` modality/uncertainty; `IDIOM` literalized idiom; `VOICE`
character register; `KEIGO` politeness/hierarchy; `IMPL` speech act or implicature;
`CULT` culture; `HUMOUR` pun missed; `ADD` hallucination; `OMIT` dropped clause.

## Variant policy

A reference is one good English realization, not a unique exact output. Grade
meaning and discourse function, not word order or literal phrase choice.
Accept natural localization of proverbs if the force survives. For homophonic puns
that cannot be carried literally, a clever English substitute OR an in-dialogue
acknowledgment of the pun can both score well, depending on scene constraints.

In deliberately ambiguous lines, **do not reward hallucinated specificity**.
If the scene has not identified the subject, pronoun gender or unseen agent,
accurate neutral English may outperform a confident, guessed agent. When scene
context specifies the speech act, use that evidence rather than generic readings.

## Examples of expected discrimination

- `JMB-076` — `今日はちょっと……。` in invitation context is a polite refusal;
  'Today is a little...' is not an adequate final translation.
- `JMB-063` — `足を洗ったはずの男が、また賭場にいた。` is quitting gambling,
  not washing someone's feet.
- `JMB-084` — `別に嫌いとは言ってない。` denies dislike but does **not**
  directly assert love. *(Check row ID and context in gold; IDs are mechanically assigned.)*
- `JMB-141` — `「できない」じゃない。「やらない」だろ。` tests inability
  vs unwillingness.
- `JMB-248` — not lying need not entail full disclosure.

## Suggested protocol

1. Run each model at fixed decoding settings in Japanese-only and contextual modes.
2. Randomize model identities and case order for blind human adjudication.
3. Compare semantic adequacy and pragmatic sensitivity per primary challenge and
   difficulty, not just an aggregate score.
4. Track disagreement and uncertain reference quality; do not adjudicate every
   alternative by literal gold match.
5. Quarantine evaluation items from fine-tuning, prompt examples and retry loops.

**Not yet independently adjudicated:** Japanese-naturalness, regional-stylization
fidelity, and metric/model calibration. The provenance field is intentionally
`independently_authored_original` for every row.
