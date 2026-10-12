# Community Submission Data Analysis

**Source:** 29 posts, 2026-09-18 → 2026-10-12
**Formal [COMMUNITY-SUBMISSION] blocks:** 23 (incl. 3 OP exemplars)
**Distinct model configurations:** 25
**[QUICK-SUBMIT] blocks actually used:** 0

## Summary

| Metric | Value |
|---|---|
| Unique data contributors | 11 |
| Rigs by vendor | AMD 6, NVIDIA 4, Apple 0 |
| VRAM spread | 16 GB → 256 GB + 1TB RAM hybrids |
| Decode range | 1 → 200+ tok/s |
| Prefill range | 79 → 6,200 tok/s |
| Power range | 75W → 900W |
| Context tested | 8k → 262k tokens |
| Dominant backend | llama.cpp/llama-swap (~40%) |
| Dominant model family | Qwen incl. Swift (~55%) |
| Dominant quant | GGUF ~70%, FP8 ~20% |

## Hardware Distribution
- AMD: Radeon VII 16GB, 2x R9700, 2x W7900, 4x v620, 4x R9700, 4x MI210
- NVIDIA: RTX 4000 Ada 20GB, RTX 4090 24GB (hybrid), RTX 5090 32GB + 1TB RAM, 2x 96GB systems
- Apple: NONE

## Backend Distribution
- llama.cpp/llama-swap (ROCm): ~9 payloads
- vLLM (incl. radiance fork): 2
- Radiance 1.3.0: 1
- Strata 0.1.42: 1
- Ollama: 1
- Colibri (CPU-only): 1
- TensorRT-LLM, LM Studio: 0

## Model Families
- Qwen (incl. Swift, Carnice): ~55%
- DeepSeek: ~28%
- Gemma 4: ~8%
- GLM, KAT-Coder, Other: ~9%
- Ornith: 0% (matrix-only, no community submission)

## Quant Formats
- GGUF Q4_K_M: ~24%
- GGUF Q8_0/UD: ~20%
- GGUF misc (Q5, IQ3, I-Nano, etc): ~24%
- FP8 native: ~12%
- W4A16 AutoRound/AWQ: ~4%
- NVFP4: 0 structured (prose only)

## Performance Highlights
- Fastest decode: 200+ tok/s (Radiance, 2x R9700, MTP)
- Fastest prefill: 6,200 tok/s (Radiance)
- Largest KV: ~840k tokens (4x v620)
- Most impressive: 125B on single 4090 via Strata (108 tok/s)
- Slowest: 1 tok/s (671B on 1TB RAM, unattended batch)

## Use Cases
- Agentic coding: ~50%
- Niche translation: ~30% (one person, 10 payloads)
- General research: ~15%
- Security, embeddings, multi-agent: singletons
- Creative writing, roleplay, vision: ZERO

## Data Quality
- **Gold standard:** Kif #26 (driver versions, RAM specs, VRAM MiB, median stats)
- **Complete:** s1ugh34d #8, SgtAwesomesauce #22, digitalscream #28
- **Sparse:** manoreken2 #12 (3-4 fields each)
- **Malformed:** manoreken2 #18 (no wrapper tags)
- **Most missing fields:** ttft_cold, prefill_tps, power_draw, os_driver

## Parser Notes
- Handle unwrapped key:value fragments (post #18)
- One block can carry 2+ configs (post #21, separated by `------`)
- Dedupe OP exemplars in post #2 against real posts
- Values contain inline units and ranges
- manoreken2 uses non-standard tier labels
- Post #15 deleted (numbering gap)
