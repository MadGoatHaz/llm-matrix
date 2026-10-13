# The Reference — Live Community Data

Live data from the community. For filtering, comparisons, recommendations,
and guides → [the interactive site](https://madgoathaz.github.io/llm-matrix/).

## The table

| Contributor | Hardware | Model | Backend | Quant | Use Case |
|---|---|---|---|---|---|
| Kif | 1x 4090 + 128GB RAM | Qwen3.8-Flash-Next 125B | Strata | IQ3_S | Agentic coding on one 24GB card |
| digitalscream | 2x R9700 32GB | Swift 1.5 Flash-Next | Radiance | FP8 | 200+ tok/s agent serving |
| SgtAwesomesauce | 4x v620 96GB | Qwen3.8-Flash-Next | vLLM/ROCm | W4A16 | Agentic coding, 840k KV |
| manoreken2 | 1x 5090 + 1TB RAM | DeepSeek-V4-Pro 671B | Colibri | Q8_K_XL | Niche translation, batch |
| lhl | 96GB+ multi-system | DS 4.1 Flash (3-way eval) | vLLM | FP8 | High-volume evals |

## How to read it

- **Hardware** = what's in the box (VRAM + RAM). **Model / Quant** = what's running.
- **Backend** = the runtime — Strata is hybrid offload, Radiance is AMD-tuned.
- Speed, context, and power numbers live on the site, not in the table.

## The site does more

A table can't filter, compare, or teach. The site can:

- **Interactive filtering** — by GPU, VRAM, backend, and use case
- **Side-by-side comparison** — any two setups
- **"Find my model"** — recommendations from your hardware
- **Guides + launch commands** — step-by-step, copy-paste, per backend

## Submit your setup

Copy, fill, paste:

****
gpu:      [e.g. 2x RTX 4090 24GB]
model:    [name + quant]
backend:  [vLLM / llama.cpp / Strata / ...]
use_case: [what you run it for]
verdict:  [one line — does it work?]
****

**Updated weekly** via automated pull from this thread.
