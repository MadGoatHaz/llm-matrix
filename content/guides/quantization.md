---
title: Quantization Basics
description: What quantization actually does, how to read a quant name (Q4_K_M, W4A16, FP8), the VRAM formula checked against real community numbers, and which level to pick for your workload.
icon: 🔢
related: file-formats, quantization-methods
---

# Quantization Basics: What a Quant Actually Does

<div class="callout"><p><b>The 30-second version:</b> Quantization stores a model's weights with fewer bits — 16 bits per weight becomes 8, 4, or even 2.5. A 27B model drops from ~52&nbsp;GB in FP16 to ~15&nbsp;GB at Q4_K_M — a 3.5× reduction with a small, usually acceptable quality loss. The working rules: <b>Q4_K_M is the community workhorse</b>, <b>FP8 is the sweet spot</b> when your hardware supports it natively, and anything below Q3 is a fit-only choice you should verify on your own task. And the model you pick matters more than the quant you pick.</p></div>

## The one-idea version

A language model is, at the hardware level, a very large pile of numbers — its *weights* — that the GPU reads over and over for every token it generates. Those numbers are stored at some precision: 16 bits, 8 bits, 4 bits. **Quantization is simply the act of storing them with fewer bits.** It is the same trick JPEG uses on a photograph: throw away the detail the eye is least likely to notice, keep the shape.

The catch is that a model's "shape" is its behavior. Weights that carry important structure deserve more precision; weights that mostly add flavor can be compressed harder. Every quantization scheme is a different answer to the question *which bits matter?* — and that answer is why two 4-bit files of the same model can behave differently. The deep dive into those schemes lives in [Quantization Methods](quantization-methods/); here we cover what the numbers mean and how they hit your VRAM.

## Why we quantize

Two reasons, in order of importance:

1. **Fit.** VRAM is the bottleneck of local inference. A 70B model in FP16 needs ~130&nbsp;GB — no consumer card has that. At 4-bit it needs ~40&nbsp;GB, and at 8-bit ~65&nbsp;GB. Quantization is the difference between "impossible" and "a couple of cards."
2. **Speed.** Generating a token is mostly *reading weights from memory*, so fewer bytes per weight means more tokens per second. The Matrix data shows the effect is not theoretical: s1ugh34d's `Qwen3.8-27B` at `UD-Q2_K_XL` decodes at **13.9&nbsp;t/s** on a 16GB Radeon VII, while MadGoat's FP8 build of the same model family hits **120&nbsp;t/s** on 2× R9700 — precision changes bandwidth *and* compute.

<div class="diagram diagram--flow">
  <div class="diagram-cell">FP16<br><b>2 bytes</b>/weight</div>
  <div class="diagram-arrow">→</div>
  <div class="diagram-cell">FP8 / INT8<br><b>1 byte</b>/weight</div>
  <div class="diagram-arrow">→</div>
  <div class="diagram-cell">Q4 / INT4<br><b>0.5 byte</b>/weight</div>
  <div class="diagram-arrow">→</div>
  <div class="diagram-cell">Q2 / I-Nano<br><b>~0.3 byte</b>/weight</div>
</div>

*Each step halves (or better) the memory a model needs. The quality cost is not even — see the ladder below.*

## The naming code

The same idea wears three different costumes depending on the ecosystem. Learning to read the label saves you from a lot of mis-downloads:

| Label | How to read it | Where you'll see it |
|---|---|---|
| `W4A16` | **W**eights at 4-bit, **A**ctivations at 16-bit | GPTQ, AWQ, AutoRound (the vLLM/PyTorch world) |
| `W8A8` | 8-bit weights *and* 8-bit activations | SmoothQuant |
| `FP8` / `BF16` | 8-bit / 16-bit *floating point* | Native training and serving checkpoints |
| `Q4_K_M` | GGUF "k-quant", 4-bit, medium precision mix | llama.cpp, Ollama, LM Studio, Strata |
| `IQ3_S`, `I-Nano` | imatrix 3-bit / ~2.5 bits per weight | GGUF |
| `2.5bpw` | 2.5 **b**its **p**er **w**eight — the raw number that matters | Anywhere |

There are two big families: **floating point** (FP16, FP8) and **integer** (INT8, INT4, and GGUF's `Q`/`I` variants). The `W4A16`-style names tell you *what* was quantized (weights vs activations); the GGUF names tell you *how* the low-bit numbers were packed. Both describe the same underlying trade: fewer bits per weight, a little quality left on the table.

## The precision ladder

This is the memory cost of each rung, shown as a share of the FP16 footprint:

<div class="diagram diagram--kv">
  <div class="diagram-row"><span class="diagram-label">FP16 / BF16</span><div class="diagram-bar" style="width:100%"></div></div>
  <div class="diagram-row"><span class="diagram-label">FP8 / Q8_0</span><div class="diagram-bar" style="width:50%"></div></div>
  <div class="diagram-row"><span class="diagram-label">Q5_K_M</span><div class="diagram-bar" style="width:34%"></div></div>
  <div class="diagram-row"><span class="diagram-label">Q4_K_M</span><div class="diagram-bar" style="width:29%"></div></div>
  <div class="diagram-row"><span class="diagram-label">IQ3_S</span><div class="diagram-bar" style="width:22%"></div></div>
  <div class="diagram-row"><span class="diagram-label">Q2_K</span><div class="diagram-bar" style="width:17%"></div></div>
  <div class="diagram-row"><span class="diagram-label">I-Nano</span><div class="diagram-bar" style="width:16%"></div></div>
</div>

And the honest quality read for each:

| Level | Bytes/weight | 27B model needs | Quality (honest read) |
|---|---|---|---|
| FP16 / BF16 | 2.0 | ~52 GB | The reference. Rarely needed for inference; the training standard. |
| FP8 | 1.0 | ~26 GB | Near-lossless on modern models. The 2026 sweet spot where hardware is native. |
| Q8_0 | ~1.0 | ~26 GB | Indistinguishable for most tasks. The "safe" GGUF pick. |
| Q5_K_M | ~0.69 | ~18 GB | Small degradation. The quality pick for 24–48&nbsp;GB cards. |
| Q4_K_M | ~0.57 | ~15 GB | The workhorse. Measurable loss on hard reasoning; best size/quality for most people. |
| IQ3_S | ~0.42 | ~11 GB | Noticeable on reasoning-heavy tasks; fine for chat and summarization. |
| Q2_K | ~0.35 | ~9.6 GB | Fit-only. Verify on your own task before trusting it. |
| I-Nano | ~0.31 (2.5bpw) | ~8.7 GB | The extreme. This is where MoE models shine — see below. |

The quality-vs-size curve is **not linear**. From FP16 down to Q8 it is nearly flat; Q8→Q4 is a small dip; Q4→Q3 is steeper; and below Q3 it depends heavily on the model and the task. Draw the curve and you get a long, flat shoulder and then a cliff — which is exactly why Q4_K_M sits where it does: just past the edge of the shoulder, at a third of the memory.

### The fine print: group sizes, symmetry, and QAT

- **Group size.** Low-bit schemes don't quantize the whole tensor with one scale — they work in small blocks (128 weights is common), each with its own scale and offset. The `_K` in `Q4_K_M` refers to this "k-quant" block structure. Bigger groups = fewer scale parameters = slightly smaller file, slightly coarser fit.
- **Symmetric vs asymmetric.** Symmetric quantization centers the range on zero; asymmetric adds an offset to track the weight distribution better. Most modern GGUF quants are effectively asymmetric via their group scales — you rarely need to choose.
- **QAT (quantization-aware training).** The most accurate quants are made by *training the model with quantization noise in the loop*, so it learns to live at low precision. QAT is rarer in the consumer GGUF world — most published quants are post-training (RTN, GPTQ, AWQ, AutoRound — see [Quantization Methods](quantization-methods/)). The frontier is hardware-native low precision: FP8 training and microscaling formats like MXFP4/NVFP4 are moving from datacenter to consumer cards in 2026 — **new and evolving**, not settled.

## The VRAM formula

The whole discipline reduces to one line:

```
VRAM (GiB) ≈ params × bytes_per_weight ÷ 1024³
```

Add the KV cache and engine overhead on top (the [KV Cache](kv-cache/) guide covers that number), and you can estimate any model before downloading it. Here is the formula checked against real Matrix submissions:

| Model (from the Matrix) | Quant | Formula (weights) | What the Matrix actually observed |
|---|---|---|---|
| Qwen3.5-4B | Q4_K_M | ~2.3 GiB | 5.3 GB at 65k context (s1ugh34d) |
| DeepSeek-R1-0528-Qwen3-8B | Q4_K_M | ~4.5 GiB | 7.4 GB (s1ugh34d) |
| Qwen3.8-27B | UD-Q2_K_XL | ~9.7 GiB | 13.8 GB on a 16GB Radeon VII (s1ugh34d) |
| Qwen3.8-27B | FP8 | ~26 GiB | Runs on 2× R9700, 48 GB total (MadGoat) |
| Qwen3.6-MoE-35B-A3B | I-Nano (2.5bpw) | ~10.2 GiB | 12.7 GB incl. KV, 54.4 t/s (s1ugh34d) |
| Qwen3.8-Flash-Next (125B MoE) | IQ3_S | ~49 GiB total | 13.4 GB in VRAM, rest in RAM/SSD (MadGoat, Strata) |

The gap between formula and observation is KV cache plus overhead — budget 10–30% extra on top of the weight math, and more if you run long context. Notice the last row: the formula says ~49&nbsp;GB, and the *submission* says 13.4&nbsp;GB in VRAM. That is not a math error — it is a hybrid engine keeping only the hot experts in VRAM. The formula tells you the model's *total* memory need; the engine decides where that memory lives.

### VRAM calculator (weights only)

| Model size | FP16 | FP8 | Q4_K_M | Q2_K / I-Nano |
|---|---|---|---|---|
| 4B | 7.5 GB | 3.7 GB | 2.3 GB | 1.3 GB |
| 8B | 14.9 GB | 7.5 GB | 4.5 GB | 2.6 GB |
| 27B | 52 GB | 26 GB | 15.3 GB | 9.6 GB |
| 35B (MoE) | 65 GB | 33 GB | 19.9 GB | 10.2 GB (I-Nano) |
| 70B | 130 GB | 65 GB | 39.7 GB | 24 GB |
| 125B (MoE) | 233 GB | 116 GB | 65 GB | ~49 GB (IQ3_S) |

Read the MoE rows carefully: total parameter counts are huge, so FP16 is fantasy — but at 2.5–3&nbsp;bits per weight a 125B MoE becomes a ~50&nbsp;GB object, and a hybrid engine shrinks the *VRAM* slice of that to a single 24GB card. That is the entire reason the Matrix's headline 125B submission exists.

## Which quant should I pick?

Walk the ladder from your workload, not from the file size:

<div class="diagram diagram--stack">
  <div class="diagram-cell">Agentic coding / reasoning → <b>Q4_K_M floor</b>; Q5_K_M or FP8 if VRAM allows. Keep KV unquantized.</div>
  <div class="diagram-arrow">↓</div>
  <div class="diagram-cell">Chat / writing / Q&amp;A → <b>Q4_K_M</b>; IQ3_S is acceptable when VRAM is tight.</div>
  <div class="diagram-arrow">↓</div>
  <div class="diagram-cell">Long-context exploration → drop one level (<b>IQ3_S</b>) to buy KV headroom; quantize the KV (Q8_0 / int8).</div>
  <div class="diagram-arrow">↓</div>
  <div class="diagram-cell">16 GB or less, maximum fit → prefer <b>MoE at I-Nano/Q2</b> over dense: the 35B-A3B at 54 t/s beats a dense 27B at 14 t/s on the same card.</div>
</div>

Four concrete recommendations, tied to what the community is actually running:

### For agentic coding and reasoning

**Q4_K_M is the floor; go higher if you can.** These workloads stress exactly the capabilities low-bit quantization degrades first — precise recall, multi-step logic. If your card holds Q5_K_M (a 27B at ~18&nbsp;GB fits a 24GB card with room for context), take it. If you have native-FP8 hardware, FP8 is near-lossless and the best quality per byte you can get. And keep the KV cache in FP16 here — quantizing it saves memory you do not have to spend on a coding agent. (Details in the [KV Cache](kv-cache/) guide.)

### For chat, writing, and document Q&A

**Q4_K_M.** It is the reason the format won the consumer world: ~90%+ of FP16 behavior on general tasks at a third of the memory. The Matrix's 4B and 8B Q4_K_M submissions (5.3&nbsp;GB and 7.4&nbsp;GB) are the archetype — small, fast, always-loaded.

### For long-context work

**Trade one quant level for KV headroom.** A 3-bit model with 64k–128k of context usually serves you better than a 4-bit model that runs out of memory at 16k. The s1ugh34d submissions show the pattern: quantized KV keeps VRAM nearly flat from 4k to 65k tokens, which is what makes the big contexts affordable.

### For small cards (16GB and under)

**Pick MoE, then go aggressive on bits.** A 35B-A3B at I-Nano (2.5bpw) fit in 12.7&nbsp;GB *including* KV on a 16GB card and decoded at 54.4&nbsp;t/s — because only ~3B of its parameters are active per token, the low-bit damage matters less. Dense models on 16GB are a speed cliff (see the 27B Q2_K_XL at 13.9&nbsp;t/s in the same data). If you must run dense, use Q3 and verify it on your actual task.

## Common misconceptions

1. **"Q4 is 75% of the model."** No. The degradation curve has a long flat shoulder: Q4_K_M retains most FP16 behavior on general tasks; what you lose is the last 5–10% of capability, concentrated in hard reasoning.
2. **"More quantization is strictly worse."** A Q4 27B beats a FP16 7B on most tasks. *Size beats precision up to a point* — the community's favorite trade.
3. **"The quant *is* the model."** Base-model quality dominates; the quant is a delivery format. A well-quantized new model beats a poorly-quantized old one, every time.
4. **"FP8 is a datacenter thing."** Not in 2026. Consumer Blackwell and RDNA4 hardware do FP8 natively, and the Matrix shows 27B FP8 serving at 120&nbsp;t/s on two R9700s.
5. **"The KV cache is part of the weights."** It is not. Weights are loaded once; the KV cache grows with every token of context. Quantizing weights and quantizing KV are separate decisions with separate tradeoffs.

## How this fits the Matrix

Every row in the [Matrix](../../matrix.html) carries a quant, and now you can read it: the format family (GGUF vs FP8 vs …), the bit level, and the memory the formula predicts. Use the calculator above to sanity-check a submission's numbers before you trust its speed claims — and when your own setup is ready, name both the format *and* the level in your submission.
