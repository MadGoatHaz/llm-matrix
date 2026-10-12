---
title: Model Architectures
description: Dense vs Mixture-of-Experts, what "A3B" means, why a 125B model can decode at 3B speed, and how MTP + speculative decoding make big models feel fast — with real Matrix examples.
date: 2026-10-12
author: The Local AI Stack
tags: dense, moe, mixture-of-experts, a3b, mtp, speculative-decoding
difficulty: intermediate
icon: 🏛️
related: kv-cache, backends
---

# Model Architectures: Dense, MoE, and Why 125B Runs at 3B Speed

<div class="callout"><p><b>The 30-second version:</b> A model's *architecture* decides how much of it the GPU touches for each token. **Dense** models use every parameter every step — straightforward, but expensive. **Mixture-of-Experts (MoE)** models are huge in total (125B) but light per token (only a few B active), which is why a 125B model can decode at the speed of a 3B one. The <b>"A3B"</b> in a name means *3B active* out of the total. The catch: MoE needs <i>more</i> memory (all experts must be loaded) but <i>less</i> compute — exactly why hybrid offload engines like Strata shine on it. And <b>MTP + speculative decoding</b> is how some of these get even faster without losing quality.</p></div>

## Dense: every parameter, every token

A **dense** model is the classic design: one continuous stack of layers, and *all* of its parameters participate in computing every single token. A 27B dense model reads all 27B of its weights to produce each character. There is nothing to route around, nothing to skip — the compute cost is simply proportional to the total parameter count.

The Matrix is full of dense models, and they are the "predictable" end of the spectrum:

- **Qwen3.8-27B** — a 27B dense model. Run as FP8 on 2× R9700 it hits **120 t/s** (MadGoat); squeezed to `UD-Q2_K_XL` on a single 16GB Radeon VII it drops to **13.9 t/s** (s1ugh34d). Same architecture, same 27B of work per token — the only thing that changed was the hardware and the precision.
- **Qwen3.5-4B** — a small dense model at **96.4 t/s**, the "leave it always loaded" generalist in the data.
- **DeepSeek-R1-0528-Qwen3-8B** — an 8B dense reasoning distill at **84.4 t/s**.

The rule for dense is easy to remember and hard to beat on small cards: **speed scales with total size**. A 27B dense model will always be slower than a 4B dense model on the same hardware, because it does 6.75× the work per token. That is the cost of dense intelligence — and the reason the next section exists.

## MoE: a model that only uses what it needs

A **Mixture-of-Experts** model replaces most of those dense feed-forward layers with a bank of smaller sub-networks called **experts**, plus a lightweight **router**. For each token, the router picks a small subset of experts (often 2 out of dozens or thousands) and only those run. The rest sit idle for that token — and a *different* subset runs for the next one.

<div class="diagram diagram--flow">
  <div class="diagram-cell">Token<br><b>"the cat"</b></div>
  <div class="diagram-arrow">→</div>
  <div class="diagram-cell">Router<br><b>picks 2 of 6,892</b></div>
  <div class="diagram-arrow">→</div>
  <div class="diagram-cell">Expert 1<br><b>active</b></div>
  <div class="diagram-cell">Expert 2<br><b>active</b></div>
  <div class="diagram-cell">Experts 3–N<br><b>idle</b></div>
  <div class="diagram-arrow">→</div>
  <div class="diagram-cell">Combine<br><b>one output</b></div>
</div>

*Per token, the router lights up a handful of experts and leaves the rest dark. The model is enormous in total, but each character costs the compute of a small model.*

The genius is in the asymmetry. Because experts are specialized, a model can have **far more total parameters** than a dense model of the same "active" size — storing much more knowledge — while paying the per-token compute of the small active set. You get the *recall* of a big model at the *speed* of a small one.

## "A3B" decoded

You will see names like `Qwen3.6-MoE-35B-A3B` or `gemma4:26b-a4b` in the Matrix. The convention is **[Total]B-A[Active]B**:

- **35B-A3B** = 35 billion parameters total, **3 billion active** per token.
- **26B-A4B** = 26 billion total, **4 billion active** per token.

The **total** number is what must be loaded into memory (every expert has to exist somewhere, even the idle ones). The **active** number is what your GPU actually computes for each token — and it is the number that determines your decode speed. A 35B-A3B model feels like a 3B model at the keyboard, while drawing on 35B of stored knowledge.

One honesty note: active-parameter counts in community submissions are *estimates* that sometimes differ from the name. The Matrix's 35B-A3B submission is named "A3B" but its notes describe the compute as "≈ 9B" (a rougher figure that likely bundles the shared expert in with the routed ones). The *name* is the convention to read; treat a submitter's prose number as a ballpark, not a spec.

## Why MoE is revolutionary for local

This is the single most important idea for people running models on consumer hardware. Look at the ratio:

<div class="diagram diagram--kv">
  <div class="diagram-row"><span class="diagram-label">Total params</span><div class="diagram-bar" style="width:100%"></div></div>
  <div class="diagram-row"><span class="diagram-label">Active / token</span><div class="diagram-bar" style="width:2.4%"></div></div>
</div>

*A 125B-total MoE activates ~3B per token — about 2.4% of the model does the work for each generated character. The other 97.6% is loaded but idle, waiting for the tokens that need it.*

That ratio is what makes the Matrix's headline submission possible. **Qwen3.8-Flash-Next** is a **125B** MoE model with 6,892 experts. On a *single* RTX 4090 (24GB) running the Strata hybrid engine, it keeps **13.4GB of the hot experts in VRAM** and parks the rest in RAM and on NVMe — and it still decodes at **99–128 t/s** (median 108). A dense 125B model would need ~230GB of VRAM and would not fit on any consumer box; a 125B *MoE* fits on one 24GB card because only a sliver is active at a time. That is "125B of intelligence at 3B of speed," and it is the reason MoE changed what is feasible at home.

## The tradeoff: more memory, less compute

The flip side is the constraint that shapes every MoE deployment: **all experts must be resident in memory**, even the ones that are idle. So an MoE model needs *more* total memory than a dense model of the same active size, while needing *less* compute per token.

- **Memory is the bottleneck.** The 125B Flash-Next is a ~50GB object at 3-bit; you cannot avoid loading it all.
- **Compute is cheap.** Only ~3B active per token, so the GPU is rarely the limit.

This is exactly why **hybrid offload works so well for MoE** (the [Multi-GPU & Hybrid](multi-gpu/) guide covers the mechanics): because the idle experts are not being read every token, they can live in slow RAM or on an NVMe SSD with little speed penalty. Only the active experts need fast VRAM. A dense model can't do this — every one of its parameters is hot on every token, so offloading a dense model to RAM collapses its speed (see the 27B `UD-Q2_K_XL` at 13.9 t/s when it nearly fills a 16GB card). MoE turns "doesn't fit" into "fits, and stays fast."

## MTP + speculative decoding

Some models in the Matrix get a second speed boost from **MTP (Multi-Token Prediction)** and the **speculative decoding** it enables.

MTP is a special head, trained alongside the model, that predicts *several* future tokens at once. On its own that is just a faster draft. The power comes from pairing it with **speculative decoding**:

<div class="diagram diagram--flow">
  <div class="diagram-cell">Draft<br><b>MTP head proposes k tokens</b></div>
  <div class="diagram-arrow">→</div>
  <div class="diagram-cell">Verify<br><b>target checks all k in one pass</b></div>
  <div class="diagram-arrow">→</div>
  <div class="diagram-cell">Accept<br><b>keep the valid prefix</b></div>
  <div class="diagram-arrow">↺</div>
</div>

*The small/draft side proposes a handful of tokens; the target model verifies all of them in a single parallel forward pass and keeps the longest correct prefix. Repeat. Several tokens per step, at no quality loss.*

The key insight is that verification is *parallel*: the target model checks k candidate tokens in the same cost as it would one, because a transformer processes a whole sequence in a single pass. So you get k tokens for roughly the price of 1, and the quality is guaranteed by the target model being the one that accepts. No approximation, no degradation — just more tokens per second.

The Matrix shows this in the wild:
- MadGoat's **Qwen3.8-27B FP8** on vLLM runs with **adaptive MTP=8** — a dense 27B model that speculatively drafts up to 8 tokens and verifies them, landing at **120 t/s**.
- PawingUnplug's list includes a **9B MTP** model (`Qwen3.5-9B-…-MTP-Q8_0`).
- Burhan's Ollama setup runs **`gemma4:26b-a4b-it-mtp`** — a MoE *and* MTP model in one.

MTP is most valuable when your model has one (it is a training-time feature, not something you add later), and it compounds beautifully with MoE: a big-but-light model that also drafts ahead.

## Which architecture should I pick?

Walk it from your constraint, not from the parameter count:

<div class="diagram diagram--stack">
  <div class="diagram-cell">Maximum <b>speed on a small card</b> → a small dense (4B/8B) or a MoE at low bits. The 4B dense at 96 t/s and the 35B-A3B at 54 t/s are the archetypes.</div>
  <div class="diagram-arrow">↓</div>
  <div class="diagram-cell">Maximum <b>quality in limited VRAM</b> → a large MoE. This is the 125B-at-3B-speed trick: big knowledge, small per-token cost, hybrid-offload friendly.</div>
  <div class="diagram-arrow">↓</div>
  <div class="diagram-cell">Long <b>context</b> → pick a model with a large *native* window first (see [Context Extension](context-extension/)); architecture matters less than the trained limit here.</div>
  <div class="diagram-arrow">↓</div>
  <div class="diagram-cell"><b>Agentic / coding throughput</b> → favor MTP models; speculative decoding is a free speed multiplier for high-volume work.</div>
</div>

The honest summary: **MoE wins on quality-per-VRAM** — it is how you get flagship-level intelligence onto consumer hardware. **Dense wins on predictability** — its speed is a clean function of its size, with no routing to reason about. If your card is small and your ambition is big, MoE is the lever. If you want simple, always-fast, low-memory behavior, a small dense model is the calm choice.

## How this fits the Matrix

The data splits into the two architectures in plain sight, and now you can read each row:

**Dense** — Qwen3.8-27B (two runs: 120 t/s FP8 on 2× R9700, 13.9 t/s `UD-Q2_K_XL` on 16GB), Qwen3.5-4B (96.4 t/s), DeepSeek-R1-8B (84.4 t/s), and the 9B coder/MTP models. Speed tracks total size, exactly as the dense rule predicts.

**MoE** — Qwen3.6-MoE-35B-A3B (`I-Nano`, 12.7GB, **54.4 t/s**) and Qwen3.8-Flash-Next, the 125B model (**13.4GB VRAM** hybrid at **99–128 t/s**; also a `Q4_K_M` run on 2× w7900 at ~35 t/s). Note the inversion that is the whole point: the *biggest* model in the data (125B) decodes *faster* than the mid-size dense 27B, because only a few billion of its parameters are active per token.

**MTP** — appears on the 27B (vLLM `MTP=8`), the 9B model, and `gemma4:26b-a4b-it-mtp`, the speculative-decoding boost layered on top of both architectures.

When you submit your own setup, name the architecture the way the data does — total *and* active params for MoE (`35B-A3B`, `125B`), plus an MTP note where present — and the next reader can see at a glance why your speeds are the way they are. The memory side of the story (why context length eats VRAM regardless of architecture) is the [KV Cache](kv-cache/) guide, and the engines that make all of this run are in [Backends](backends/).
