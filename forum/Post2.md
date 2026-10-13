# The Reference — Live Community Data

Live community data. The full interactive experience (filtering,
comparing, recommendations, guides) is on the site →
[The Local AI Stack](https://madgoathaz.github.io/llm-matrix/)

## A taste of what's in there

- **Kif** — 1× 4090 + 128GB RAM (Strata, IQ3_S) — 125B agentic coding
- **digitalscream** — 2× R9700 32GB (Radiance, FP8) — 200+ tok/s serving
- **SgtAwesomesauce** — 4× v620 96GB (vLLM/ROCm, W4A16) — 840k KV context
- **manoreken2** — 1× 5090 + 1TB RAM (Colibri, Q8_K_XL) — 671B batch runs

Full data (27 entries), updated weekly → [the site](https://madgoathaz.github.io/llm-matrix/)

## What the site does better

- **Filter** by GPU, VRAM, backend, use case
- **Compare** any two setups side-by-side
- **Recommend** a model from your hardware

## 📋 Submit your setup — COPY THIS TEMPLATE:
```
[COMMUNITY-SUBMISSION]
hardware: [e.g., 1x RTX 4090 24GB + 128GB RAM]
vram:     [e.g., 24GB — pick: under 16 / 16-23 / 24-31 / 32-47 / 48-95 / 96+ GB]
model:    [e.g., Llama 3.1 8B, Qwen3.8-27B]
backend:  [e.g., Ollama, llama.cpp, vLLM]
quant:    [e.g., Q4_K_M, Q5_K_S, FP16, FP8]
speed:    [e.g., 45 tok/s, ~30 t/s] (optional)
use_case: [e.g., daily chat, coding, summarization]
notes:    [e.g., launch flags, quirks, anything else] (optional)
[/COMMUNITY-SUBMISSION]
```
