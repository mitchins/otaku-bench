# Data policy

A benchmark whose answers are public ends up in training data, and then it measures memory instead of translation. So:

| | Public | Encrypted (git-crypt) |
|---|---|---|
| Japanese source text (all splits) | ✓ | |
| Dev split gold: 50 lines, 6 scenes | ✓ `benchmark/otakubench/data/public/` | |
| Eval split gold: 200 lines, 25 scenes | | ✓ |
| Translator's trap notes | | ✓ |
| Raw model outputs and per-item judgments | | ✓ (they quote or paraphrase the references) |
| Aggregate reports (ranking, latency) | ✓ | |

The Japanese text is original, written in the style of the genres. It isn't taken from any published title. Some scenes deliberately include intense but legal fiction (explicit adult content between adults, graphic violence, heavy profanity) to detect over-refusal and censoring.

`benchmark/otakubench_ero/` is a separate, unreleased adult-register slice (currently v0.3.1). It is git-crypted except the README, and it is not part of the 200-line ranking.

To work with the encrypted files you need the repository key: `git-crypt unlock /path/to/otakubench-git-crypt.key`.
