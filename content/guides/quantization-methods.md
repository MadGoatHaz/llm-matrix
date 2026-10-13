---
title: Quantization Methods
description: How quants are actually made and why one 4-bit beats another — RTN, GPTQ, AWQ, AutoRound, SmoothQuant, NVFP4/MXFP4, and the GGUF K/I/UD family, with a master comparison table.
date: 2026-10-12
author: The Local AI Stack
tags: quantization, gptq, awq, autoRound, smoothquant, nvfp4, mxfp4, gguf
difficulty: intermediate
icon: ⚙️
related: quantization, file-formats, backends
---

# Quantization Methods: How Quants Are Made

<div class="callout"><p><b>The 30-second version:</b> Two 4-bit files of the same model can feel very different, because *how* the bits were chosen is a real decision. The spectrum runs from **RTN** (round each weight — fast, coarse) through **GPTQ** and **AWQ** (use calibration data to protect the weights that matter), to **AutoRound** (optimize the rounding itself) and **SmoothQuant** (make the activations 8-bit, too). The GGUF world that llama.cpp, Ollama, and Strata read has its own consumer-tuned branch — the **K-quants**, **I-quants**, and **UD** dynamic quants. And the new generation, **NVFP4 / MXFP4**, does 4-bit *floating point* with per-block scaling on native hardware. The working rule: <b>the method matters more at 4 bits than at 8</b> — a well-made 4-bit usually beats a lazy 4-bit by a wide margin.</p></div>

## Why two 4-bits aren't the same

The bit count is your *budget*; the method is how you *spend* it. A model's weights are not equally important — a small fraction of them carry most of the signal, and the rest is texture. The naive approach treats every weight the same and just rounds it. The smarter approaches look at real data, figure out which weights hurt the most when they lose precision, and spend the extra bits (or the scaling) there.

Every method is an answer to the same question — *where do the bits go?* — with a different amount of effort. The more work at *quantization time* (calibration, optimization, hardware-aware scaling), the more quality survives at *inference time*. That is why the flat "Q4 ≈ a small loss" line in [Quantization Basics](quantization/) is only true on average: at 4 bits, the spread between methods is large enough to change your experience.

<div class="diagram diagram--flow">
  <div class="diagram-cell">RTN<br><b>No calibration</b></div>
  <div class="diagram-arrow">→</div>
  <div class="diagram-cell">GPTQ<br><b>Hessian + ~128 samples</b></div>
  <div class="diagram-arrow">→</div>
  <div class="diagram-cell">AWQ<br><b>activation-aware</b></div>
  <div class="diagram-arrow">→</div>
  <div class="diagram-cell">AutoRound<br><b>gradient-optimized</b></div>
  <div class="diagram-arrow">→</div>
  <div class="diagram-cell">NVFP4 / MXFP4<br><b>hardware-native FP4</b></div>
</div>

*Each step spends more work at quantization time to keep more quality at inference time. The GGUF K/I/UD family is a parallel, VRAM-tuned branch of the same idea — covered at the end.*

## The methods

### RTN — Round-To-Nearest

<div class="callout callout--info"><p><b>The baseline.</b> Round each weight to the nearest value on the target grid, with a per-group scale. No calibration, no optimization, no thought — the cheapest compression that exists.</p></div>

RTN is what "just quantize it" means: take a 16-bit weight, pick the closest 4-bit (or 8-bit) value, store that. It runs in minutes and needs no data. The cost is that it is *blind* — it has no idea which weights are load-bearing, so it makes the same relative error everywhere, including on the few that matter most.

That makes RTN the quality floor — perfectly acceptable when the task is forgiving (casual chat, summarization, a prototype) or you just need the model to *fit*. In the GGUF world, plain `Q4_0` and `Q8_0` are essentially RTN with group scales, which is why `Q8_0` (a forgiving target) looks great while a raw 4-bit RTN shows edges. If a file is just "the model, rounded," it is RTN.

### GPTQ

<div class="callout callout--info"><p><b>Hessian-based, calibration-driven.</b> Feeds ~128 short samples of real text through the model, measures which weights hurt the most when rounded (via the loss's curvature), and compensates the neighbors. A clear step up from RTN, at a real time cost.</p></div>

GPTQ upgrades RTN from "round and hope" to "round and fix." The core idea is the **Hessian** — a measure of how sensitive the model's output is to each weight. Weights that sit in a steep part of the loss landscape (a small change there causes a big change in output) are the dangerous ones to round. GPTQ estimates this curvature from a small **calibration set** and then quantizes weights one at a time, shifting the unquantized neighbors to absorb the error it just introduced.

"What does 128 calibration samples mean?" 128 short pieces of representative text (a few hundred tokens each) that the model reads while the algorithm fits. The samples never change the weights permanently — they only mark *where the cliffs are*. The calibration data should match your use case: serve code, calibrate on code. GPTQ's output is the `W4A16`/`W3A16`/`W5A16` family — 4-bit (or 3-bit) weights with 16-bit activations — a standard format in the vLLM/PyTorch serving world. The trade is time: a GPTQ run takes hours, not minutes.

### AWQ — Activation-Aware Quantization

<div class="callout callout--info"><p><b>Protect the 1% that matters.</b> Measures which weights are multiplied by large *activations* and keeps those at higher effective precision, quantizing the rest harder. Often the best 4-bit quality among the classics — and the default pick for vLLM.</p></div>

AWQ starts from an observation GPTQ only hints at: not all weights matter equally, and you can *see* which ones by watching the activations. A weight that always multiplies a big activation is a load-bearer; one that multiplies near-zero activations barely registers. AWQ runs the model on a few hundred calibration samples, finds that small set of sensitive channels (typically ~1%), and **scales them up** before quantization so their relative error shrinks. The scaling is absorbed back into the layer, so at inference time nothing changes except that the sensitive weights survived better.

The result is often the best quality-per-bit at 4-bit among the "classic" methods, and it is popular for vLLM deployments for a practical reason: AWQ produces `W4A16` checkpoints where only the *weights* are 4-bit and the activations stay 16-bit. That means the inference path needs no exotic activation kernels — just fast 4-bit weight loading and standard matmuls — so it is easy to deploy and fast to run. If you want a single "best 4-bit for serving" answer, this is usually it.

### AutoRound

<div class="callout callout--info"><p><b>Optimize the rounding itself.</b> Treats "which side of the grid does each weight land on?" as a trainable problem, solves it iteratively with gradients, and supports *mixed precision* (different bits for different tensors). The engine behind many `W4A16-AutoRound` checkpoints on Hugging Face.</p></div>

AutoRound sits in the same family as GPTQ and AWQ but attacks the problem from a third angle. GPTQ uses second-order (Hessian) information and fixes errors sequentially; AWQ uses activation statistics and rescales channels; AutoRound frames the decision — round each weight *up* or *down*? — as an optimization, refining it with **gradient descent** over many iterations so neighboring weights inform each other.

Its distinguishing power is **mixed precision**. Instead of forcing the whole model to 4-bit, AutoRound can assign more bits to the layers that need them and fewer to the ones that don't, hitting a target file size with the best overall quality. That is why it tends to edge out GPTQ at the aggressive end (3-bit and below), where a uniform bit budget hurts most. The cost, again, is quantization time — this is an optimizer running, not a rounding loop.

### SmoothQuant

<div class="callout callout--info"><p><b>Makes the activations 8-bit, too (W8A8).</b> The hard part of low-bit inference is not the weights — it is the *activations*, which have wild outliers. SmoothQuant mathematically "smooths" those outliers into the weights, so both sides can live in INT8 and run on fast integer kernels.</p></div>

Every method above is about the *weights*. SmoothQuant targets a different bottleneck: **activations** — the intermediate values the model computes, not its stored parameters. They have a notorious problem: a few channels spike to huge values while the rest stay small, which makes 8-bit quantization lossy. You can't round activations the way you round weights; the outliers wreck the scale.

SmoothQuant's trick is a **per-channel smoothing factor**: it divides the spiky activation channels down and multiplies the corresponding weight channels up by the same amount. Mathematically the product is identical — no information is lost — but now the activations are tame enough to quantize to INT8. The result is **W8A8** (8-bit weights *and* 8-bit activations), which unlocks fast INT8 matrix kernels in vLLM and TensorRT-LLM. It is the answer to "I want speed more than I want the absolute smallest file": near-lossless quality at 2× the memory of 4-bit, but with integer-math throughput.

### NVFP4 / MXFP4 (Microscaling)

<div class="callout callout--warning"><p><b>The new generation — early adoption, still evolving.</b> 4-bit *floating point* with a shared exponent per small block ("microscaling"). Near-FP8 quality at half the memory of FP8, and native hardware speed on Blackwell (RTX 50xx) with AMD following. Not settled in 2026 — verify model coverage before you bet on it.</p></div>

The classic methods are all **integer** quantization: snap each weight to a point on a fixed grid. The new generation returns to **floating point** at 4 bits, with a twist that fixes the old problem with tiny floats. Plain 4-bit floats have almost no dynamic range — a handful of values, and they blow up on anything large. **Microscaling** fixes that by giving each small block of weights (e.g. 32) its own shared scale, so a block can be centered and stretched to fit its actual range.

There are two flavors in play in 2026:
- **NVFP4** — NVIDIA's FP4 format, with hardware-native support on Blackwell (the RTX 50xx series). Dedicated FP4 tensor cores make it both small and fast.
- **MXFP4** — the OCP **Microscaling** standard, the industry-wide spec that NVIDIA, AMD, and others are converging on, so a MXFP4 checkpoint is meant to be portable across vendors.

Why "the golden ticket"? It aims for **FP8-level quality at FP4-level memory** — half the footprint of FP8 with near-FP8 accuracy, on hardware that computes it natively. The honest caveat, and why it is flagged: it is **new and evolving**. As of late 2026, tooling is landing but model coverage is patchy — not every model has a well-made release, and the quality of one depends on how carefully the per-block scales were fit. Treat it as the frontier: excellent where it exists, absent where it doesn't.

### The GGUF family: K-quants, I-quants, and UD

<div class="callout callout--info"><p><b>The consumer branch.</b> A separate, VRAM-obsessed quantization system that llama.cpp, Ollama, LM Studio, and Strata all read. It has its own naming, its own hierarchy, and it is where {{gguf_count}} of the Matrix's {{submission_count}} submissions live.</p></div>

The GGUF ecosystem did not adopt GPTQ/AWQ — it built its own methods around a single constraint: *fit a big model into as little VRAM as possible.* Three families matter:

**K-quants** (the `_K` in `Q4_K_M`). A k-quant is a **hierarchical, mixed-precision** scheme: weights are grouped into blocks, and a super-structure with shared scales assigns *more* bits to the tensors that need them and *fewer* to the rest — the same "spend the budget where it matters" idea as AWQ, baked into the file format. The K ladder, best to worst, is `Q8_0` (near-lossless) &gt; `Q6_K` &gt; `Q5_K_M` &gt; `Q4_K_M` &gt; `Q3_K_M` &gt; `Q2_K`; the `_M`/`_S`/`_L` suffixes are medium/small/large variants of the same target, with `_M` the default. **`Q4_K_M` is the workhorse**: the best quality-per-byte for most consumer cards.

**I-quants** (the `I` in `IQ4_XS`, `IQ3_S`). These push lower than the K-quants using an **importance matrix** ("imatrix") — a per-weight score from calibration data that tells the quantizer which weights to protect. That lets `IQ3_S` hold up better than a plain 3-bit, and **`I-Nano`** (~2.5 bits per weight) is the extreme end: it only works well where a few active parts carry the whole load — exactly what MoE models are (see [Model Architectures](model-architectures/)).

**UD — Unsloth Dynamic.** Unsloth's "dynamic" GGUFs assign bits *per tensor* to hit a target file size, giving the best quality at a specific budget (e.g. `UD-Q4_K_XL`, `UD-Q2_K_XL`). The Matrix's 27B-on-16GB submission is one of these — a deliberately mixed-precision quant built to squeeze a dense 27B into a single consumer card.

The thread through all three: the GGUF family optimizes for **size and single-GPU fit**, while the GPTQ/AWQ/AutoRound/SmoothQuant family optimizes for **serving quality and speed**. They are parallel solutions to the same question, aimed at two different machines.

## The master comparison

| Method | Typical precision | Quality vs FP16 | Speed impact | VRAM vs FP16 | Backends | When to use |
|---|---|---|---|---|---|---|
| RTN | INT4 / INT8 | Low–mid (degrades first) | Neutral | 2×–4× | Everywhere (GGUF base) | Quick fit, forgiving tasks |
| GPTQ | W4A16 / W3A16 | Mid–high | Small loss | ~4× | vLLM, TGI, AutoGPTQ | 4-bit serving, quality over raw size |
| AWQ | W4A16 | High (best at 4-bit) | Small loss | ~4× | vLLM, TensorRT-LLM | The default 4-bit pick for serving |
| AutoRound | W4A16 / mixed | High | Small loss | ~3–4× (mixed lower) | vLLM, GPTQ tooling | Lower bits, mixed-precision targets |
| SmoothQuant | W8A8 | High (near-lossless) | Faster (INT8 kernels) | 2× | vLLM, TensorRT-LLM | Max speed at acceptable quality |
| NVFP4 / MXFP4 | FP4 (microscaled) | Very high (near FP8) | Fast (native FP4 cores) | ~8× vs FP16 | Blackwell, vLLM (emerging) | **New/evolving** — low-bit where supported |
| GGUF K-quants (Q4_K_M…) | ~4.5–8 bpw | High (Q4_K_M the workhorse) | Neutral | 2.5–4× | llama.cpp, Ollama, LM Studio, Strata | Consumer GPU, tight VRAM |
| GGUF I-quants (IQ3_S) / I-Nano | ~2.5–3.5 bpw | Mid (imatrix-tuned) / Low (Nano) | Neutral | 4–8× | llama.cpp, Strata | Extreme fit, MoE models |
| UD (Unsloth Dynamic) | mixed (per-tensor) | High | Neutral | variable | llama.cpp, Ollama | Best quality at a target file size |

*bpw = bits per weight. "VRAM vs FP16" is the approximate memory multiplier. NVFP4/MXFP4 are flagged new/evolving; the rest are production-ready in 2026.*

## Research vs production

Which can you rely on today, and which are you early to?

**Production-ready (well-supported, stable):**
- **RTN** — the baseline; everywhere.
- **GPTQ, AWQ, AutoRound** — the classic post-training trio; the backbone of vLLM's W4A16 ecosystem.
- **SmoothQuant** — mature W8A8 in vLLM and TensorRT-LLM.
- **The GGUF family** (K-quants, I-quants, UD) — the consumer standard; the most battle-tested low-bit path in existence.

**New / evolving (verify before you depend on it):**
- **NVFP4 / MXFP4** — the 2026 frontier. Hardware is landing (Blackwell native, AMD converging on the OCP standard), but model coverage and tooling are still patchy. A well-made release is excellent; the absence of one for your model is the more likely scenario right now.

The practical read: if your model has a good **AWQ** or **Q4_K_M** release, that is a safe, proven choice today. Reach for **NVFP4/MXFP4** only when a high-quality release exists *and* your hardware is native to it — otherwise you are paying the early-adopter tax for no gain.

## How this fits the Matrix

The data is a clean snapshot of the split. **{{gguf_count}} of the {{submission_count}} community submissions run the GGUF family** — K/I/UD quants through llama.cpp, Ollama, and Strata: `I-Nano` on the 35B-A3B MoE, `IQ3_S` on the 125B Flash-Next, `Q4_K_M` on the 27B/4B/8B dense models, `Q5_K_M` on the coder, `Q8_0` on the 9B MTP model, and `UD-Q2_K_XL` squeezing a dense 27B into a 16GB card. The **vLLM submissions** (27B FP8 on 2× R9700) run **native FP8** safetensors instead — the serving-side answer to the same "fit a big model" problem.

So the method you see in the Matrix's quant column is not random: **consumer single-GPU runs skew GGUF K/I/UD** (size-first), while **multi-GPU serving skews FP8/AWQ** (quality-and-speed-first). Now that you can read *how* each was made, the next step is knowing which *file* to grab for your backend — that is the [File Formats](file-formats/) guide, and the backends that consume each family are covered in [Backends](backends/).
