These empty-think runs (LFM2.5-24B-A2B, Flint 40B-A2.5B) used a prefill of '<think>\n</think>\n\n'. llama-server
already renders an assistant prefill as '<think></think>' + content, so the model saw two think blocks. Flint then
reasoned in its visible reply on 11/93 scene items. Re-run on 2026-10-24 with a single block (prefill '\n'); see
results/studies/flint_adapter/ and mission/studies/flint_adapter.py.
