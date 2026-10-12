---
title: Multi-GPU & Hybrid
description: Making big models fit — tensor parallel, pipeline parallel, layer offload, and the Strata hybrid (VRAM+RAM+SSD). Practical NVIDIA and AMD setups tied to real Matrix submissions, plus the CPU+GPU path for 1TB-RAM systems.
date: 2026-10-12
author: The Local AI Stack
tags: multi-gpu, tensor-parallel, pipeline-parallel, layer-offload, hybrid, strata, nvidia, amd, nvlink, xgmi
difficulty: advanced
icon: 🖥️
related: kv-cache, backends, model-architectures
---

# Making Big Models Fit: Multi-GPU and Hybrid Offload Strategies

<div class="callout"><p><b>The 30-second version:</b> A 70B model in FP16 needs ~140&nbsp;GB. No consumer GPU has that. So you split the work. There are three ways: <b>tensor parallel</b> (slice each layer across GPUs, the fastest but needs a fast interconnect), <b>pipeline parallel</b> (split by stages, less communication, works with mismatched GPUs), and <b>layer offload</b> (put overflow layers in system RAM, a speed cost over PCIe). Then there is the <b>hybrid revolution</b>: Strata runs a 125B MoE model on one consumer GPU + lots of RAM + a fast NVMe SSD, because MoE only needs the *active* experts in fast memory. The rule: <b>if the model fits in one GPU, just run it. If it needs two, tensor parallel. If it is a big MoE and you have RAM, Strata. If you have 1TB of RAM and no big GPU, CPU+GPU hybrid at 1–5 t/s.</b></p></div>

## The basic problem

A 70B model in FP16 stores 70&nbsp;billion × 2&nbsp;bytes = 140&nbsp;GB of weights, before KV cache, engine overhead, or activation buffers. No consumer GPU comes close:

| Model | Precision | Weight memory | Closest consumer option |
|---|---|---|---|
| 7B | FP16 | ~14 GB | One 16GB card |
| 27B | FP16 | ~52 GB | Two 24GB cards, or one 48GB card |
| 70B | FP16 | ~130 GB | Two 48GB cards, or four 24GB cards |
| 70B | Q4_K_M | ~40 GB | One 48GB card, or two 24GB cards |
| 125B (MoE) | FP16 | ~233 GB | Fantasy on consumer hardware |
| 125B (MoE) | IQ3_S | ~49 GB total | One 24GB VRAM + 64GB+ RAM (Strata) |
| 671B | Q4_K_M | ~340 GB | 1TB+ RAM system, CPU-only |

The moment a model's memory need exceeds one GPU's VRAM, you have three choices: **add more GPUs**, **offload to system memory**, or **both**.

## Three split strategies

### Tensor parallel

<div class="diagram diagram--flow">
  <div class="diagram-cell">Layer N<br><b>split across GPUs</b></div>
  <div class="diagram-arrow">┬</div>
  <div class="diagram-cell">GPU 1<br>weights 1/2</div>
  <div class="diagram-cell">GPU 2<br>weights 1/2</div>
  <div class="diagram-arrow">┴</div>
  <div class="diagram-cell">All-reduce<br>every layer</div>
</div>

Tensor parallel splits *each layer's weight matrices* across the GPUs. GPU 1 holds the first half of every matrix; GPU 2 holds the second half. After each layer's computation, the GPUs must exchange partial results (an "all-reduce") before the next layer can start. The communication happens **every layer, every token**, which makes the interconnect speed the bottleneck.

**When it works best:** 2–8 identical GPUs with a fast interconnect. NVIDIA 3090/4090 pairs with NVLink, AMD R9700/MI300X pairs with Infinity Fabric (XGMI). The more GPUs, the more communication per step, so the interconnect matters more.

**The speed cost:** With NVLink (900&nbsp;GB/s on 3090/4090) the all-reduce is fast enough that 2-GPU tensor parallel loses maybe 5–10% versus a single GPU with the same total VRAM. Over PCIe 4.0 (32&nbsp;GB/s) the loss is much worse — 30–50% — because the interconnect is 30× slower than the GPU's memory bandwidth. This is why NVLink is "required for best performance" in the NVIDIA world.

**Practical command:**

```bash
# vLLM, 2× 24GB, tensor parallel
vllm serve Qwen/Qwen3.8-70B --tensor-parallel-size 2 --max-model-len 32768

# llama.cpp, 2 GPUs (layer split, not true tensor parallel)
llama-server -m Qwen3.8-70B-Q4_K_M.gguf -ngl 99 -sm tensor -t 2
```

### Pipeline parallel

<div class="diagram diagram--stack">
  <div class="diagram-cell">GPU 1: Layers 0–29 (first half)</div>
  <div class="diagram-arrow">↓ (activation buffer passes forward)</div>
  <div class="diagram-cell">GPU 2: Layers 30–59 (second half)</div>
  <div class="diagram-arrow">↓</div>
  <div class="diagram-cell">Output token</div>
</div>

Pipeline parallel splits the model *by stages*: the first half of the layers live on GPU 1, the second half on GPU 2. Data flows from GPU 1 to GPU 2 once per token (the activation buffer), not once per layer. The communication is much lighter than tensor parallel, so it works over PCIe without a huge penalty.

**When it works best:** Non-identical GPUs (a 24GB card + a 48GB card), or when you do not have NVLink/XGMI. The tradeoff is *bubble time*: while GPU 2 is processing layer 30–59, GPU 1 is idle waiting for the next token. With only 2 stages the bubble is small; with 8 stages it is significant.

**The honest read:** Pipeline parallel is the "good enough" option. It is simpler to set up, more tolerant of hardware mismatches, and fast enough for most use cases. Tensor parallel is the "maximum performance" option, but it demands matching GPUs and a fast interconnect.

### Layer offload

<div class="diagram diagram--stack">
  <div class="diagram-cell">GPU VRAM: Layers 0–15 (hot, in VRAM)</div>
  <div class="diagram-arrow">↕ PCIe 4.0 (~32 GB/s)</div>
  <div class="diagram-cell">System RAM: Layers 16–59 (overflow, in DDR5)</div>
  <div class="diagram-arrow">↕ Memory controller</div>
  <div class="diagram-cell">NVMe SSD: Weights beyond RAM (cold, on disk)</div>
</div>

Layer offload is the simplest strategy: the GPU processes whatever layers fit in VRAM, and the rest live in system RAM. The engine shuttles layer weights over PCIe as needed. The speed cost is the PCIe bandwidth: DDR5 RAM is ~50&nbsp;GB/s, PCIe 4.0 is ~32&nbsp;GB/s, versus ~1000&nbsp;GB/s for GPU VRAM. Every offloaded layer adds latency proportional to its size.

**When it is acceptable:** You are running a model that *mostly* fits in VRAM, with a few layers spilling over. A 27B Q4_K_M (~15&nbsp;GB) on a 16GB card offloads one layer — the speed loss is small. A 70B Q4_K_M (~40&nbsp;GB) on a 24GB card offloads nearly half the model — the speed loss is significant (expect 3–8 t/s instead of 15–25).

**When it is not acceptable:** You are running a dense model where every layer is hot on every token. The PCIe round-trip per layer per token dominates. This is the case where tensor or pipeline parallel with multiple GPUs is the right answer, or where a hybrid MoE engine (Strata) changes the math entirely.

**Practical command:**

```bash
# llama.cpp: offload 20 layers to GPU, rest in RAM
llama-server -m Qwen3.8-70B-Q4_K_M.gguf -ngl 20 -c 16384

# Ollama: automatic layer offload (it figures out what fits)
ollama run qwen3.8-70b:q4_K_M
```

## The interconnect matters

The single biggest performance variable in multi-GPU setups is how fast the GPUs can talk to each other:

| Interconnect | Bandwidth | Available on | Impact on tensor parallel |
|---|---|---|---|
| NVLink 3.0 | 900 GB/s (2-way) | RTX 3090/4090 (2-way bridge) | Minimal loss (5–10%) |
| NVLink 4.0 | 1800 GB/s (4-way) | RTX 5090 (4-way) | Near-zero loss |
| PCIe 4.0 | 32 GB/s | All consumer GPUs | 30–50% loss for tensor parallel |
| PCIe 5.0 | 64 GB/s | 50-series, MI300X | 15–25% loss |
| XGMI / Infinity Fabric | ~180 GB/s (2-way) | AMD R9700, MI300X | 10–20% loss |
| System RAM (DDR5) | ~50 GB/s | All platforms | Layer offload baseline |

The practical rule: **if you are doing tensor parallel, get the fastest interconnect your platform allows.** Two 4090s with an NVLink bridge are a meaningfully different (faster) machine than two 4090s over PCIe. Two R9700s over Infinity Fabric are the AMD equivalent. If you are doing pipeline parallel or layer offload, the interconnect matters less — the communication is lighter and less frequent.

## Practical NVIDIA setups

| Setup | Total VRAM | Interconnect | Runs | Typical use |
|---|---|---|---|---|
| 1× RTX 4090 (24GB) | 24 GB | — | 27B Q4_K_M, 35B-A3B I-Nano | Single-model, consumer |
| 2× RTX 3090/4090 (48GB) | 48 GB | NVLink (2-way) | 70B Q4_K_M, 27B FP8 | Tensor parallel, the sweet spot |
| 4× RTX 3090/4090 (96GB) | 96 GB | NVLink (4-way, 3090 only) | 70B FP16, 125B MoE Q4 | Serious local AI, multi-model |
| 1× RTX 5090 (32GB) | 32 GB | — | 27B FP8, 70B Q4_K_M (offload) | Next-gen single card |
| 2× RTX 5090 (64GB) | 64 GB | NVLink 4.0 | 70B FP8, 125B MoE Q4 | Next-gen tensor parallel |

The 2× 3090/4090 with NVLink is the community's most-cited "big model on a budget" setup: 48GB of VRAM, fast interconnect, and enough headroom for a 70B model at Q4_K_M with room for a long KV cache. The Matrix's MadGoat 27B FP8 submission (120 t/s on 2× R9700) is the AMD parallel of this: two cards, tensor parallel, high throughput.

## Practical AMD setups

| Setup | Total VRAM | Interconnect | Runs | Typical use |
|---|---|---|---|---|
| 1× R9700 (24GB) | 24 GB | — | 27B Q4_K_M, 35B-A3B I-Nano | Single-model, consumer |
| 2× R9700 (48GB) | 48 GB | Infinity Fabric (XGMI) | 27B FP8, 70B Q4_K_M | Tensor parallel, Radiance/vLLM |
| 4× R9700 (96GB) | 96 GB | Infinity Fabric | 70B FP16, 125B MoE | Serious local AI |
| 2× MI300X (192GB) | 192 GB | Infinity Fabric | 70B FP16, 125B+ MoE FP8 | Datacenter-class |
| 4× MI210 (128GB) | 128 GB | Infinity Fabric | 70B FP16, 125B MoE | Budget datacenter |

The Matrix's AMD data is the richest in the set: 10 of 12 submissions are AMD. The two R9700 submissions (MadGoat's 27B FP8 at 120 t/s, and the vllm-radiance MTP=8 variant) show what two R9700s can do: a 27B dense model at production-grade speed, or a 125B MoE model via Strata at interactive speed. The 4× R9700 (96GB) is the "I want to run anything" setup, and the MI300X/MI210 cards are the datacenter answer when you need 128–192GB without a server-grade budget.

**The Radiance note:** AMD's answer to vLLM is the Radiance engine, which adds MTP speculative decoding on top of ROCm tensor parallel. A 2× R9700 Radiance setup with MTP=8 on a compatible model can push past 200 t/s — faster than most NVIDIA 2-GPU setups at the same model size. This is the single biggest reason the Matrix's fastest submissions are AMD.

## The hybrid revolution: Strata

<div class="diagram diagram--stack">
  <div class="diagram-cell" style="border-color: var(--success);">
    <b>VRAM (24GB)</b> — Hot experts + KV cache<br>
    ~1000 GB/s bandwidth
  </div>
  <div class="diagram-arrow">↕ PCIe 4.0 (~32 GB/s)</div>
  <div class="diagram-cell" style="border-color: var(--accent);">
    <b>System RAM (128GB DDR5)</b> — Warm experts<br>
    ~50 GB/s bandwidth
  </div>
  <div class="diagram-arrow">↕ Memory controller</div>
  <div class="diagram-cell" style="border-color: var(--purple);">
    <b>NVMe SSD (2TB)</b> — Cold experts + weight overflow<br>
    ~7 GB/s bandwidth
  </div>
</div>

Strata is not a multi-GPU engine — it is a *single-GPU + big-RAM* engine, and it changes the math for MoE models specifically. The key insight: a 125B MoE model has 125B *total* parameters, but only ~3B are *active* per token. The active experts need to be in fast memory (VRAM); the inactive ones can sit in RAM or on SSD because they are not touched for most tokens.

The result: a 125B MoE model at IQ3_S (~49&nbsp;GB total) runs on a 24GB GPU + 64GB RAM + NVMe SSD. The VRAM holds the hot experts and the KV cache; the RAM holds the warm experts; the SSD holds the cold overflow. The router decides which experts are active for each token, and the engine prefetches the needed experts from RAM/SSD before the token is computed.

**The bandwidth tradeoff, honestly stated:** VRAM is ~1000&nbsp;GB/s, RAM is ~50&nbsp;GB/s, NVMe is ~7&nbsp;GB/s. An expert that lives in RAM is 20× slower to access than one in VRAM. This is why Strata keeps the *most frequently accessed* experts in VRAM and the rest in RAM — the router's access pattern determines the tier placement. For a 125B MoE model with ~6,892 experts and a top-2 routing, the hot set is small enough to fit in 24GB, and the tail is cold enough that the RAM/SSD latency is amortized over many tokens.

**When Strata beats multi-GPU:**
- **Cost.** One 24GB GPU + 128GB DDR5 is a fraction of the price of four 24GB GPUs.
- **Power.** One GPU draws 300W; four draw 1200W. The RAM and SSD add maybe 50W total.
- **Simplicity.** No NVLink, no tensor-parallel configuration, no matching-GPU requirement. One GPU, lots of RAM, a fast SSD.
- **MoE fit.** The hybrid tiering is *designed* for MoE access patterns. A dense model on Strata would be slow, because every layer is hot on every token.

**When Strata loses to multi-GPU:**
- Dense models. Every layer is active, so the RAM/SSD tiers add latency on every token.
- Sub-second latency requirements. The prefetch pipeline adds milliseconds per token that a pure-VRAM multi-GPU setup does not have.
- You already have the GPUs. If you have 2× 48GB cards, tensor parallel is faster than 1× 24GB + Strata for the same model.

The Matrix's Strata submission (MadGoat's 125B Qwen3.8-Flash-Next at IQ3_S, 13.4GB in VRAM, rest in RAM/SSD, 120 t/s decode) is the proof of concept: a datacenter-class model on a consumer GPU, at interactive speed.

## CPU+GPU hybrids: the 1TB-RAM path

When the model is too big for any reasonable GPU configuration — a 671B dense model, a 235B MoE in FP16 — the answer is a system with 1TB+ of RAM and a GPU that handles what it can.

| Setup | RAM | GPU | Speed | Use case |
|---|---|---|---|---|
| EPYC 9004 + 1TB DDR5 | 1 TB | 1× 24GB (hot layers) | 1–3 t/s | Overnight batch, niche tasks |
| Threadripper + 512GB | 512 GB | 1× 48GB | 2–5 t/s | Unattended document processing |
| EPYC + 1TB + 2× 48GB | 1 TB | 2× 48GB (tensor) | 3–8 t/s | Serious CPU+GPU hybrid |

The backends for this tier are **Colibri** (CPU-only) and **llama.cpp in CPU mode** (with a small GPU offload for the hottest layers). 1–5 t/s means a 1,000-token response takes 3–10 minutes — fine for overnight batch jobs, not for interactive chat.

**The honest rule:** interactive workload → get more GPUs or a smaller model. Batch workload → 1–3 t/s is fine, and the 1TB-RAM path is the only way to run the biggest models on consumer hardware.

## What do I actually need?

The decision guide, from "it fits" to "I need a datacenter":

<div class="diagram diagram--stack">
  <div class="diagram-cell">
    <b>Model fits in 1 GPU?</b><br>
    Check the VRAM formula: params × bytes_per_weight. If it fits (with room for KV cache), just run it. No splitting needed.
  </div>
  <div class="diagram-arrow">↓ No</div>
  <div class="diagram-cell">
    <b>Model needs 2 GPUs?</b><br>
    Tensor parallel (NVLink/XGMI if available). vLLM `--tensor-parallel-size 2` or Radiance. The sweet spot for 27–70B models.
  </div>
  <div class="diagram-arrow">↓ No</div>
  <div class="diagram-cell">
    <b>Model is MoE + you have lots of RAM?</b><br>
    Strata hybrid. One GPU + 64–256GB RAM + NVMe. The 125B-on-24GB path.
  </div>
  <div class="diagram-arrow">↓ No</div>
  <div class="diagram-cell">
    <b>Model is huge (100B+ dense) + you have a server?</b><br>
    Multi-GPU tensor parallel (4–8 GPUs). vLLM or TensorRT-LLM. The datacenter path.
  </div>
  <div class="diagram-arrow">↓ No</div>
  <div class="diagram-cell">
    <b>You have 1TB RAM + no big GPUs?</b><br>
    CPU+GPU hybrid. Colibri or llama.cpp CPU mode. Accept 1–5 t/s for batch work.
  </div>
</div>

## How this fits the Matrix

Every row in the [Matrix](../../matrix.html) has an *engine mode* field. The one submission that flags it (MadGoat's 125B Strata) is the hybrid case: `Hybrid (VRAM+RAM+SSD)`. The llama-swap submissions are `VRAM-only` (single GPU). The vLLM 2× R9700 submission is `VRAM-only` with tensor parallel.

When you submit your own setup, **fill in the engine mode**. A 120 t/s number means very different things on a 2× R9700 tensor-parallel vLLM setup versus a 1× 24GB Strata hybrid — the model and quant are the same, but *where the weights live* changes the picture.

The [KV Cache](kv-cache/) guide covers the memory cost of context. The [Backends](backends/) guide covers which engine to use for each split strategy. The [Model Architectures](model-architectures/) guide explains why MoE makes the hybrid path work.
