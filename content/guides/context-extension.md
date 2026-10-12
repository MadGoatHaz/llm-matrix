---
title: Context Extension
description: Running models beyond their trained window — how RoPE sets the limit, what "lost in the middle" means, how YaRN and NTK stretch the context, the honest 2×/4×/8× quality rule, and which 2026 models already have big native windows.
date: 2026-10-12
author: The Local AI Stack
tags: context, rope, yarn, ntk, scaling, lost-in-the-middle
difficulty: intermediate
icon: 📏
related: kv-cache, model-architectures, backends
---

# Going Longer: Context Extension with RoPE, YaRN, and NTK

<div class="callout"><p><b>The 30-second version:</b> Every model is trained to expect positions up to some number — 32k, 128k, 1M. That ceiling is set by **RoPE** (Rotary Position Embeddings), the mechanism that tells the model *where* each token sits. Push past it and the model has never seen those positions, so quality degrades — the famous **"lost in the middle"** — and eventually fails. **YaRN** and **NTK** are the two standard ways to stretch the window by rescaling RoPE. The honest rule: <b>2× native is safe, 4× degrades, 8× is risky.</b> And before you reach for any of it — <b>many 2026 models already have 128k–1M native context, so you may not need extension at all.</b></p></div>

## RoPE, in one breath

A transformer does not inherently know the order of its tokens. **RoPE (Rotary Position Encoding)** fixes that by rotating each token's query and key vectors by an amount that depends on its position in the sequence. The rotation is what lets the model tell "the 3rd token" from "the 3,000th" and attend with the right relative offsets. Crucially, the rotation is *trained* over a specific range of positions — the model's **native context length**. A model trained on 32k positions has a RoPE that is only known-good up to 32k.

That trained range is the whole constraint. It is not a hard wall baked into the file size — it is a *geometric* limit on the positions the model learned to reason about. Extension techniques work by gently bending that geometry.

## What happens past the native context

Feed a 32k-trained model a 64k prompt and you are asking it to use position values it never saw during training. Three things tend to follow, in order:

1. **Quiet degradation.** The model still produces fluent text, but its grasp of *where* things are in the sequence loosens. Long-range references get fuzzy.
2. **"Lost in the middle."** The model attends well to the very start and the very end of the context but poorly to the middle. A fact buried at token 30,000 of a 60,000 context is far easier to miss than one at token 100 or 59,900.
3. **Hard failure.** Far enough out, the rotation values leave the trained manifold entirely and the output collapses — repetition, incoherence, or a flat refusal.

None of this is about the model being "too small." It is purely a position-encoding problem, which is why it can be addressed without retraining.

## YaRN: scale the frequencies

**YaRN** ("Yet another RoPE handling") is the current standard for context extension. The insight: RoPE encodes position using a set of rotating frequencies, some fast (fine position detail) and some slow (coarse, long-range structure). When you stretch the context, the *fast* frequencies oscillate too quickly over the new, longer range and stop carrying signal. YaRN's fix is to **interpolate the frequencies** — slow the fast ones down and rescale the whole set — so the rotation stays well-behaved at the longer length. You express this as a **scaling factor**: 2× for double the window, 4× for quadruple.

How to set it:

**llama.cpp** (GGUF — the common local path):

```
llama-server -m model.gguf -c 65536 --rope-scaling yarn --rope-scale 2
```

`-c` is the new context length; `--rope-scaling yarn` selects the method; `--rope-scale 2` is the factor. Flag names have shifted a little across llama.cpp releases (some builds use `--rope-type`), so check `llama-server --help` for yours.

**vLLM** (safetensors — the serving path):

```
vllm serve my-model --max-model-len 65536
```

vLLM reads the `rope_scaling` block from the model's `config.json`. A YaRN setup looks like:

```
"rope_scaling": {
  "rope_type": "yarn",
  "factor": 2.0,
  "original_max_position_embeddings": 32768
}
```

If the checkpoint ships no `rope_scaling` block, vLLM has nothing to rescale — so for the serving path, pick a model whose config already carries it.

## NTK-aware scaling: the llama.cpp alternative

**NTK-aware** scaling is the other common method, and the one you will most often meet in llama.cpp. Where YaRN interpolates the *frequencies*, NTK modifies the *interpolation of the rotation angle itself* — it leaves the low (slow) frequencies unchanged and only bends the high (fast) ones, with a smooth blend in between. In practice the two are close cousins: NTK is a slightly simpler, very effective default in llama.cpp and holds up well at 2×. YaRN tends to have the edge at the more aggressive 4×. Use whichever your engine exposes cleanly; at 2× the difference between them is small.

```
llama-server -m model.gguf -c 65536 --rope-scaling ntk --rope-scale 2
```

## The honest rule

<div class="diagram diagram--kv">
  <div class="diagram-row"><span class="diagram-label">1× · native</span><div class="diagram-bar" style="width:100%"></div></div>
  <div class="diagram-row"><span class="diagram-label">2×</span><div class="diagram-bar" style="width:90%"></div></div>
  <div class="diagram-row"><span class="diagram-label">4×</span><div class="diagram-bar" style="width:60%"></div></div>
  <div class="diagram-row"><span class="diagram-label">8×</span><div class="diagram-bar" style="width:25%"></div></div>
</div>

*Same model, scaled. Bar length ≈ quality retention. **2× is safe** (a clean, useful gain). **4× degrades** (workable for chat, risky for precise recall). **8× is risky** (expect real "lost in the middle" effects and verify hard). Every rung also costs more KV-cache VRAM — see below.*

The practical mapping, for a model with a given native window:

| Native | 2× (safe) | 4× (degraded) | 8× (risky) |
|---|---|---|---|
| 32k | 64k | 128k | 256k |
| 128k | 256k | 512k | 1M |
| 256k | 512k | (probably overkill) | — |

If a cell in that table reads "probably overkill," stop — you do not need it.

## Models that already have big native context

Before you extend anything, check whether you need to. The 2026 flagship family ships with large *trained* windows, so for many tasks the honest answer is "just use the bigger model":

| Model (2026 / Matrix) | Native context | Extension needed? |
|---|---|---|
| DeepSeek-R1-8B (Matrix) | 16k | Often — the small model that wants more room |
| Qwen3.5-4B / Qwen3.6-MoE-35B-A3B (Matrix) | 65k | Rarely |
| Qwen3.8-27B (Matrix) | 256k | No — the ~240k runs are native |
| Qwen3.8-Flash-Next 125B MoE (Matrix) | 128k+ | No |
| Gemma 4 | 256k | No |
| DeepSeek V4 / GLM 5.3 | 1M | No |

The pattern: **the distilled and small models are the ones that actually benefit from extension** (a 16k 8B reaching 32k is a real win); **the flagships already have the window built in**. If your 27B/128k+ model is hitting its limit, the problem is usually not "extend it" — it is "the context is genuinely too long for the task," and a model with a bigger native window is the cleaner fix.

## Do you actually need extension?

- **You need it** when a smaller/older model (16k–32k native) genuinely must see more than it was trained for, and no bigger-native alternative fits your VRAM.
- **You do not need it** when a 128k–1M-native model is available to you — just run it. Extending a 32k model to 128k is usually a worse result than running a model that was *trained* at 128k, because the trained model learned the long-range positions properly.

## The VRAM cost

Extension and the [KV Cache](kv-cache/) are the same coin. Doubling the context **doubles the KV cache** — a 27B at 32k/FP16 (~8 GiB of cache) becomes ~16 GiB at 64k, before a single weight is added. So a context extension is only as good as your memory allows: you can set `-c 131072` freely, but if the resulting KV cache does not fit, you out-of-memory. This is why the two guides pair up — **extension lets you stretch the window; KV quantization lets you afford it.** A YaRN 2× stretch on a model with FP8 KV is a very different VRAM story than the same stretch on FP16 KV.

## How this fits the Matrix

The `context.stable` column is where extension shows up. Read it two ways: a **"native"** note (the 4B and 35B-A3B at 65k, the DeepSeek-8B at its 16k server cap) means the model was used within its trained window; a **configured-beyond-native** note (the 27B at ~240k, the 125B at 131k) means the engine is running it past a smaller trained base — and the cleanest reading of the 2026 data is that most of those big numbers are *native* to the model, not stretched. When you submit, say which it is: the native window, and whether you applied YaRN/NTK at what factor. That single line tells the next person whether your long-context number is earned by the model or borrowed by the encoder. The memory side of that number — what the longer context costs in VRAM — is the [KV Cache](kv-cache/) guide, and the models with the biggest native windows are the [Model Architectures](model-architectures/) story.
