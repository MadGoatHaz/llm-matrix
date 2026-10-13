---
title: File Formats: GGUF, Safetensors, and MLX
description: What's actually inside a model file, the three formats that matter for local inference, which one to download for your backend, and how (and whether) they convert.
icon: 📦
related: quantization, backends
---

# File Formats: GGUF, Safetensors, and MLX

<div class="callout"><p><b>The 30-second version:</b> A model file is its weights (99%+ of the bytes) plus config, tokenizer, and metadata — packaged in a *format*. Three formats matter for local inference: <b>GGUF</b> (single file, quantized, the standard for llama.cpp/Ollama/LM Studio/Strata), <b>safetensors</b> (sharded, full-precision or FP8, the standard for vLLM and the PyTorch world), and <b>MLX</b> (Apple Silicon's unified-memory format). The rule that decides everything: <b>your backend picks the format, not the other way around.</b></p></div>

## What's inside a model file

Before comparing containers, know what they hold. Every model file packages four things:

- **Weights** — the trained numbers. 99%+ of the file's size, and the part quantization touches (see [Quantization Basics](quantization/)).
- **Config** — architecture parameters: layer counts, attention heads, vocabulary size, native context length.
- **Tokenizer** — the mapping between text and tokens. Without it the model is just numbers.
- **Metadata** — quantization details, chat template, license, and (in GGUF) the tensor layout itself.

The *format* is the container for these four. The same model in three formats is three different download — and only one of them will run on your backend.

## The three formats that matter

### GGUF — the all-rounder

<div class="callout callout--info"><p><b>One file, every quant, every consumer backend.</b> The default choice for local LLMs.</p></div>

GGUF is the unified file format born out of llama.cpp (the successor of the older GGML format). Weights, config, tokenizer, and metadata all live in a single file — no stitching, no index, no surprises. It carries the entire GGUF quantization ladder, from `Q8_0` down through `Q4_K_M`, `IQ3_S`, and `I-Nano`, which is why it is the format of choice for bandwidth-constrained and VRAM-constrained machines.

The Matrix is a good snapshot of the ecosystem: **{{gguf_count}} of {{submission_count}} community submissions run GGUF** — through llama.cpp, llama-swap, Ollama, and Strata. Its main limitation is that it is a *quants-first* format: the FP8 weight ecosystem lives in safetensors, not GGUF. So if a model is only published as native FP8, GGUF is not where you'll find it.

### Safetensors — the PyTorch/vLLM standard

<div class="callout callout--info"><p><b>Sharded, full-precision or FP8.</b> What training tools output and what vLLM serves.</p></div>

Safetensors is the tensor container of the PyTorch world — "safe" because, unlike old pickle files, it executes no code when loaded. Big models arrive as **multiple shards** (more below) with an index file mapping each tensor to its shard. This is the format of full-precision (FP16/BF16) and FP8 checkpoints, and the home of the `W4A16`-style quants (GPTQ, AWQ, AutoRound) that vLLM and TensorRT-LLM serve.

Both of the Matrix's vLLM submissions — MadGoat's and digitalscream's `Swift-Qwen3.8-27B-Uncensored-FP8` on 2× R9700 — run safetensors. If you fine-tune, you will also *produce* safetensors: it is the standard training output.

### MLX — the Apple Silicon native

<div class="callout callout--warning"><p><b>The unified-memory format for Macs.</b> No MLX submissions in the Matrix today — the ecosystem's biggest data gap.</p></div>

MLX is Apple's array framework and its native model format, built around the fact that a Mac's CPU and GPU share one pool of memory. It carries its own 4-bit and 8-bit quant sets, and it is what you run when you use MLX (or Unsloth Desktop on Metal) on Apple Silicon. Models are commonly published as safetensors and converted to MLX for Mac use.

Honest caveat: the Matrix has **no MLX submissions yet** — the community data skews NVIDIA and AMD. If you run a Mac, your experience is underrepresented here, which is exactly why an MLX submission from you would be valuable.

| | GGUF | Safetensors | MLX |
|---|---|---|---|
| File layout | Single file | Multiple shards + index | Single set (Apple layout) |
| Quant support | Full GGUF ladder (Q8→I-Nano) | FP16/BF16/FP8, GPTQ/AWQ/AutoRound | MLX 4-bit / 8-bit |
| Backends that read it | llama.cpp, Ollama, LM Studio, llama-swap, Strata | vLLM, TensorRT-LLM, PyTorch fine-tuning | MLX, Unsloth Desktop (Metal) |
| Best for | Consumer GPUs, tight VRAM | Serving, FP8, training | Apple Silicon |

## Which format do I download?

The decision is made for you by the backend you run:

| Your backend | Download this |
|---|---|
| llama.cpp / llama-swap | GGUF |
| Ollama | GGUF (Ollama pulls them for you) |
| LM Studio | GGUF |
| Strata | GGUF |
| vLLM / TensorRT-LLM | Safetensors (FP8, AWQ, GPTQ, …) |
| MLX / Mac | MLX |
| Fine-tuning | Safetensors |

If you are not sure which backend to run, that is a [Backends](backends/) question — answer it first, and the format follows. Never download a format "just in case": a 27B model is 15–26&nbsp;GB per format, and they are not interchangeable.

## Shards: why big models come in boxes

A 70B model in FP16 is ~140&nbsp;GB. File systems, download managers, and disk quotas all choke on single files that big — so the safetensors world splits models into **shards**: `model-00001-of-00008.safetensors` through `…-00008…`, each around 16&nbsp;GB, plus a small index JSON that tells the loader which tensor lives in which shard. You download them all; the loader stitches them in memory transparently.

GGUF sidesteps the problem entirely with a single file — one of the practical reasons it won the consumer space. (A 70B at Q4_K_M is a single ~40&nbsp;GB file; at I-Nano-class bits it shrinks further. The per-size math is the same VRAM formula from the [Quantization Basics](quantization/) guide — it works for disk space too.)

## Can I convert between formats?

Yes — in one direction. The rule is: **you can quantize down from full precision; you cannot un-quantize up.**

- **Safetensors → GGUF:** well supported and the most common conversion in the wild. llama.cpp ships `convert_hf_to_gguf.py`, and tools like Unsloth produce the "dynamic" GGUF quants. Nearly every GGUF file on Hugging Face — including the `unsloth/` and `bartowski/` repos the Matrix submissions point at — started life as a safetensors checkpoint.
- **Safetensors → MLX:** a standard step for Mac users, via `mlx.convert`.
- **GGUF → safetensors:** not recommended. A GGUF file already had bits thrown away by quantization; there is nothing to recover. If you need the full-precision original, go back to the source checkpoint.

So the practical flow is: find the model's safetensors (or its MLX conversion), then produce the GGUF quant your backend wants. Converting is cheap; downloading three formats is not.

## How this fits the Matrix

The Matrix's quant column is really *format + level* combined: "GGUF Q4_K_M", "FP8", "GGUF I-Nano". Now you can read each row's packaging — and you know why the data skews GGUF ({{gguf_count}} of {{submission_count}} submissions) with the FP8/safetensors rows concentrated in the vLLM setups. When you submit your own, name the format and the level together, and the next person can pick the right file for their backend.
