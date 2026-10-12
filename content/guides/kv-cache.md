---
title: KV Cache
description: Why context length is the silent VRAM eater — what the KV cache is, the formula that predicts its size, when to quantize it and when not to, and the engine tricks (PagedAttention, prompt caching) that make long context practical — with real Matrix numbers.
date: 2026-10-12
author: The Local AI Stack
tags: kv-cache, context, vram, pagedattention, prompt-caching, fp8, int8
difficulty: intermediate
icon: 🧠
related: context-extension, multi-gpu, model-architectures, backends
---

# The KV Cache: Why Your Context Length Eats Your VRAM

<div class="callout"><p><b>The 30-second version:</b> The KV cache is the model's scratchpad. For every token you feed it, the engine stores a <b>Key</b> and a <b>Value</b> vector for each attention head — and it never throws them away. That makes <b>context length a direct, linear VRAM tax</b>: 4k tokens is almost nothing, 32k is a few gigabytes, 256k is tens. A 27B model at 32k in FP16 needs ~<b>8 GiB of cache</b> on top of its weights. The lever you control is <b>KV quantization</b> — store that scratchpad in FP8 (half the size) or INT4 (a quarter) and the long contexts your weights already afford suddenly fit. The rule: <b>precision-critical work (coding, RAG, math) keeps KV at FP16/BF16; VRAM-stretched exploration quantizes it to FP8.</b></p></div>

## What the KV cache is (and isn't)

A transformer computes each new token by *attending* to every token that came before it. For every position in the input, the attention math produces two vectors per head — a **Key** and a **Value** — and the current token's query is matched against all the stored Keys to pull in the relevant Values. Recomputing those Keys and Values from scratch for every new token would be slow, so the engine **caches** them: once a Key/Value pair is computed for a position, it is stored and reused for everything after. That growing pile of stored pairs is the **KV cache**.

The mental model that matters: **the KV cache is not the model.** It is separate from the weights:

- **Weights** are the trained parameters — loaded once at startup, a fixed size (the [Quantization Basics](quantization/) math), and unchanged for the whole session.
- **The KV cache** is working memory — it starts at zero, **grows by one entry for every token you process**, and is the part of your VRAM budget a long prompt quietly consumes.

So two runs of the *exact same model* can have very different footprints, purely from how much context they use. A 27B model at 4k is nearly the same size as at 8k; at 256k it is many times larger. The weights never moved — the cache did.

## Why it grows linearly

The cache is an array indexed by position. 1,000 tokens in the context means 1,000 Key/Value sets stored; 100,000 tokens means 100,000. In the basic case it does not compress, does not evict, and does not shrink while you generate — it only gets bigger. For a 27B model with FP16 KV, the growth looks like this:

<div class="diagram diagram--kv">
  <div class="diagram-row"><span class="diagram-label">4k</span><div class="diagram-bar" style="width:2%"></div></div>
  <div class="diagram-row"><span class="diagram-label">32k</span><div class="diagram-bar" style="width:12.5%"></div></div>
  <div class="diagram-row"><span class="diagram-label">128k</span><div class="diagram-bar" style="width:50%"></div></div>
  <div class="diagram-row"><span class="diagram-label">256k</span><div class="diagram-bar" style="width:100%"></div></div>
</div>

*Same model, FP16 KV: 4k ≈ 1 GiB → 32k ≈ 8 GiB → 128k ≈ 32 GiB → 256k ≈ 64 GiB. Every 4× jump in context is a 4× jump in cache — a 64× jump from 4k to 256k.*

This is the number the Matrix is full of, and it is why "long context" and "big model" compete for the same VRAM. The community data shows the effect in the wild — the same submitter running a line of 16GB cards, all with *quantized* KV, and watch how flat the memory stays:

| Matrix submission | KV setting | What the submitter observed |
|---|---|---|
| Qwen3.5-4B (Q4_K_M) | quantized | VRAM 5,312 MB @4k → 5,312 MB @65k (**+0**) |
| gemma-4-E4B (Q4_K_M) | quantized | ~flat: 4,619 MB @4k → 4,618 MB @49k |
| DeepSeek-R1-8B (Q4_K_M) | quantized | 7,327 → 7,299 MB (flat) |
| Qwen3.8-27B (UD-Q2_K_XL) | quantized | 13,770 → 13,798 MB across 8k → 32k (+28 MB) |

The contrast is the other half of the story: the 48GB multi-GPU runs keep KV in **FP16** and reach ~240k, and the single-card Strata 125B run uses **engine-native int8** KV at 131k. The KV setting in the Matrix's `kv_cache` column is not trivia — it is the knob that decides how far your context can go.

## The formula

The whole thing reduces to one line. For a model with `num_layers` layers, `num_kv_heads` key/value heads, and `head_dim` dimensions per head:

```
KV_size = num_layers × num_kv_heads × head_dim × seq_len × 2 × bytes_per_element
```

The `× 2` is for the Key *and* the Value. Worked out for a 27B dense model (64 layers, 8 KV heads, 128-dim heads) at 32k context in FP16:

```
per token, one layer : 2 × 8 × 128          = 2,048 elements
per token, all layers: 2,048 × 64          = 131,072 elements
in bytes (FP16)    : 131,072 × 2         = 262,144 B  = 256 KiB / token
at 32,768 tokens   : 262,144 × 32,768    = 8.0 GiB
```

**~8 GiB of KV cache** for a 27B model at 32k in FP16. Add the weights on top and you can see the whole budget:

| Setup | Weights | + KV (32k) | Total | Fits |
|---|---|---|---|---|
| 27B FP16, FP16 KV | ~52 GiB | 8 GiB | ~60 GiB | 2–4× R9700-class |
| 27B FP8, FP8 KV | ~26 GiB | 4 GiB | ~30 GiB | 2× R9700 (48 GB) |
| 27B Q4_K_M, INT4 KV | ~15 GiB | 2 GiB | ~17 GiB | a single 24 GB card |

That last row is the punchline: the same 27B model fits on one 24GB card *because* the KV cache is quantized. Without it, 32k of FP16 KV would push a 15GB-weights model over the edge.

## KV cache quantization

Just like the weights, the cache can be stored at lower precision. The trade is memory for a little quality:

| KV precision | bytes/element | 32k for this 27B | Quality read |
|---|---|---|---|
| FP16 / BF16 | 2 | 8 GiB | The reference. Best long-range recall. |
| FP8 / INT8 | 1 | 4 GiB | Near-lossless for most tasks. The default "stretch" choice. |
| INT4 | 0.5 | 2 GiB | Noticeable on precise recall. Use to buy headroom. |

A useful intuition: **KV quantization is usually more forgiving than weight quantization.** The cache is recomputed-style working memory, and attention is fairly robust to it — which is why the 16GB runs above could stretch to 49k–65k *and* keep coherent needle-in-a-haystack hits. But it is not free: at INT4 the precise "find that one fact 40k tokens back" capability degrades first, which is exactly what the next section is about.

## When to quantize — and when not to

The decision is workload-driven, not size-driven:

<div class="diagram diagram--stack">
  <div class="diagram-cell"><b>Quantize the KV</b> (FP8, sometimes INT4) when: creative writing, casual chat, roleplay, VRAM-constrained exploration, batch / unattended workloads, or any time the alternative is an out-of-memory error.</div>
  <div class="diagram-arrow">↓</div>
  <div class="diagram-cell"><b>Keep KV at FP16/BF16</b> when: agentic coding / repo editing, RAG / needle-in-a-haystack, math / multi-step reasoning, or any task that needs precise recall of what is in the context.</div>
</div>

<div class="callout callout--tip"><p><b>Pro tip:</b> If you can only afford one, quantize the <i>weights</i> first and keep the KV clean — weight bits are cheaper to lose. Reach for KV quantization when the weights are already as low as your task tolerates and you still need more context.</p></div>

## Two engine tricks that change the math

### PagedAttention (vLLM)

Naive KV allocation reserves the *maximum* context up front — so a request that only uses 2k still holds 32k of cache, and short requests fragment the memory pool. **PagedAttention** (the reason vLLM is the serving workhorse) manages the cache in small non-contiguous "pages," exactly like an OS virtual-memory pager. Memory is allocated on demand and reclaimed when a request ends, so there is no wasted reservation and no fragmentation. The result is far higher throughput when many requests share a server — the difference between "one big context" and "a busy multi-user box." If you are serving an API to multiple people, this is a large part of why you pick vLLM (see [Backends](backends/)).

### Prompt caching (Strata)

The other lever is not about a *smaller* cache but *reusing* it. Agents repeat the same preamble every turn — a system prompt, tool definitions, project files. **Prompt caching** keeps the already-computed KV for that shared prefix, so the next turn skips re-processing it. The Matrix's 125B Strata run is the proof: **90% prompt-cache hit rate → 0.3–0.8s resume on 50k-token contexts.** You pay the expensive prefill once, then every follow-up is nearly free. This is what makes a long-context *agent* (not just a chat) practical on a single 24GB card — and it is a feature of the hybrid engine, not the model (see [Multi-GPU & Hybrid](multi-gpu/)).

## The practical rule

<div class="callout callout--warning"><p><b>The rule to remember:</b> if your workload needs precision at length, keep the KV in FP16/BF16. If you are stretching VRAM limits and can tolerate fuzzy recall, drop it to FP8. INT4 is the aggressive end — use it to buy context headroom, then verify your actual task (a needle test, a long coding session) still works before you trust it.</p></div>

## How this fits the Matrix

The `kv_cache` column is now a readable signal, not a mystery string. The pattern in the data: **the 16GB single-card runs are all quantized KV** (that is how they reach 49k–65k on a card a dense 27B nearly fills), while **the 48GB multi-GPU runs keep FP16 KV** (they have the headroom and want the recall) and **the hybrid 125B run uses engine-native int8** (the one place INT8 is a free, built-in win). When you submit your own setup, report both the KV precision *and* what you observed as context grew — that flat-VRAM number is the most useful data point in the entire matrix, because it tells the next person exactly how far their context can go. The other half of the context story — *extending a model past its trained window* — is the [Context Extension](context-extension/) guide, and the memory side of running bigger models is [Multi-GPU & Hybrid](multi-gpu/).
