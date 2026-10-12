---
title: Backends Deep Dive
description: Every local LLM inference engine compared — llama.cpp, llama-swap, Ollama, LM Studio, Unsloth Desktop, vLLM, TensorRT-LLM, Strata, Radiance, MLX, and Colibri. What each does, when to use it, the exact command to start, and the golden rules for picking.
date: 2026-10-12
author: The Local AI Stack
tags: backends, inference, llama.cpp, ollama, vllm, strata, radiance, mlx, colibri
difficulty: intermediate
icon: ⚡
related: file-formats, multi-gpu, quantization
extra_scripts: js/commands.js
---

# Choosing Your Backend: Every Local LLM Inference Engine Compared

<div class="callout"><p><b>The 30-second version:</b> A *backend* is the program that loads your model file and turns tokens in, tokens out. It decides what formats you can run, what hardware you can use, how fast things go, and how much control you get. There is no single "best" backend — there is a best one *for your situation*. The short version: <b>Ollama or LM Studio</b> if you want it working in five minutes, <b>llama.cpp</b> if you want control on a single GPU, <b>vLLM or Radiance</b> if you are serving production workloads, and <b>Strata</b> if you are running a big MoE model on a consumer card with lots of RAM. The decision matrix at the end of this guide makes it concrete.</p></div>

<div class="cmd-picker" data-cmd-picker>
  <h2><span class="icon" aria-hidden="true">🚀</span> Try the launch-command generator</h2>
  <p>Pick a backend and get a representative command you can copy. It's the same generator that powers the <span class="icon" aria-hidden="true">🚀</span> buttons on the <a href="../../matrix.html">Matrix</a>, <a href="../../recommend/">Recommend</a>, and <a href="../../compare/">Compare</a> pages — over there it's tailored to a *specific* community submission (its exact model, quant, context, and VRAM); here it shows a generic example for the backend you choose.</p>
  <div class="cmd-picker-row">
    <label for="cmd-picker-select">Backend</label>
    <select id="cmd-picker-select" class="cmd-picker-select">
      <option value="llama.cpp">llama.cpp</option>
      <option value="llama-swap">llama-swap</option>
      <option value="Ollama">Ollama</option>
      <option value="LM Studio">LM Studio</option>
      <option value="vLLM">vLLM</option>
      <option value="Strata">Strata</option>
      <option value="Radiance">Radiance</option>
      <option value="MLX">MLX</option>
      <option value="TensorRT-LLM">TensorRT-LLM</option>
      <option value="Colibri">Colibri</option>
      <option value="Unsloth Desktop">Unsloth Desktop</option>
    </select>
    <button class="btn btn-primary" data-cmd-generate type="button">Generate example</button>
  </div>
  <div class="cmd-picker-output" data-cmd-output></div>
</div>

## Why the backend matters

The model file is the *what*; the backend is the *how*. The same 27B model at Q4_K_M can decode at 14 t/s on a 16GB card through one backend and 54 t/s through another, depending on kernel quality, memory management, and how efficiently the engine moves data between VRAM, RAM, and SSD. The backend also determines which file formats you can use, which GPUs and operating systems it supports, and what performance features are available (continuous batching, PagedAttention, speculative decoding, prompt caching).

The Matrix tracks five backends across its twelve submissions: **llama-swap** (6), **vLLM** (2), **llama.cpp** (2), **Strata** (1), and **Ollama** (1). That distribution tells you what the community is actually running. The eleven engines below are the full landscape as of late 2026.

## The master comparison

This is the table to bookmark. Every backend in the local-inference world, one row each:

| Backend | Formats | GPU / OS | Key Strength | Best For | Avoid When |
|---|---|---|---|---|---|
| **llama.cpp** | GGUF (all quants) | CUDA, ROCm, Vulkan, Metal, CPU | The universal baseline. Every quant, every GPU, every OS. | Single-GPU control, custom builds, benchmarking | Multi-GPU tensor parallel (use vLLM/Radiance), production serving |
| **llama-swap** | GGUF (via llama.cpp) | CUDA, ROCm, Vulkan, Metal | Auto-swaps multiple models on one GPU. OpenAI API. | "Always-on" single-GPU setups, multiple models, OpenAI clients | You need one model at full speed with no swap overhead |
| **Ollama** | GGUF | CUDA, ROCm, Metal, CPU | Five-minute setup. `ollama run <model>`. No config. | Quick testing, casual chat, getting started | Power users who need context flags, KV quant, custom kernels |
| **LM Studio** | GGUF | CUDA, ROCm, Metal, CPU | GUI model browser, one-click server, beginner-friendly. | Visual discovery, non-terminal users, trying models | Scripting, headless servers, multi-model automation |
| **Unsloth Desktop** | GGUF, safetensors, FP8, MLX | CUDA, ROCm, Metal | All-in-one: run, chat, fine-tune, serve. Multiple formats. | The complete local AI workstation, format flexibility | You only need one format and one model |
| **vLLM** | safetensors, FP8, AutoRound, AWQ | CUDA (multi-GPU) | Continuous batching, PagedAttention, tensor parallel, OpenAI API. | Production serving, multi-user, high throughput | Single-GPU consumer cards, GGUF-only workflows |
| **TensorRT-LLM** | safetensors, FP8, NVFP4 | CUDA (NVIDIA only) | Kernel-level optimization, max NVIDIA performance. | Absolute peak NVIDIA throughput, datacenter-grade serving | AMD/Apple, GGUF, anything not NVIDIA |
| **Strata** | GGUF (I-Nano, IQ3_S, K-quants) | CUDA, ROCm, CPU | Hybrid VRAM+RAM+SSD offload. Prompt caching. One-click. | 125B+ MoE on consumer hardware, long-context agents | Dense models that don't benefit from hybrid offload |
| **Radiance** | safetensors, FP8, NVFP4 | ROCm (RDNA3/4), MI300X | AMD-optimized kernels, MTP speculative decoding, 200+ t/s. | AMD multi-GPU, the best AMD answer to vLLM | NVIDIA, Apple, single-GPU consumer AMD |
| **MLX** | MLX format | Apple Silicon (Metal) | Unified memory, native Apple performance. | Mac-only setups, Apple Silicon users | NVIDIA/AMD, non-Apple hardware |
| **Colibri** | GGUF, safetensors | CPU only (no GPU) | Runs on 1TB+ RAM systems. No GPU required. | CPU-only servers, niche batch work, 1–5 t/s is acceptable | Anything needing interactive speed, GPU hardware available |

## One card per backend

Each card below gives the one-sentence identity, the exact getting-started command, and the honest tradeoffs.

### llama.cpp

**The universal engine.** Every local LLM story starts here. It reads GGUF files, runs on virtually every GPU architecture (CUDA, ROCm, Vulkan, Metal) and pure CPU, and exposes a C API that a dozen other tools wrap. It is the reference implementation: if a quant works anywhere, it works in llama.cpp first.

```bash
# Single GPU, all layers offloaded, 32k context
llama-server -m Qwen3.8-27B-Q4_K_M.gguf -ngl 99 -c 32768 --host 0.0.0.0 --port 8080

# AMD (ROCm)
llama-server -m Qwen3.8-27B-Q4_K_M.gguf -ngl 99 -c 16384 --main-gpu 0

# CPU only (no GPU)
llama-server -m Qwen3.8-27B-Q4_K_M.gguf -ngl 0 -c 8192 -t 32
```

**When to use:** Maximum control on a single GPU. Benchmarking. Custom workflows. A quant no other engine supports.

**When to avoid:** Multi-GPU tensor parallel (vLLM/Radiance). Five-minute setup (Ollama/LM Studio). Multi-user serving (vLLM).

The Matrix's llama.cpp submissions (s1ugh34d's 27B UD-Q2_K_XL on a 16GB Radeon VII at 13.9 t/s) show both the power and the pain: raw llama.cpp gives you every flag, but you have to wire up the model path, context length, and GPU offload yourself.

### llama-swap

**Multi-model auto-swapping on one GPU.** llama-swap wraps llama.cpp as a subprocess and adds a model router: when a client requests a model that is not currently loaded, it evicts the current one and loads the new. The result is an "always-on" OpenAI-compatible API that can serve dozens of models from a single GPU without manual intervention.

```bash
# Install
pip install llama-swap

# Run with auto-swap, 24GB GPU
llama-swap --model-dir ./models --host 0.0.0.0 --port 1234

# Request a specific model via the OpenAI API
curl http://localhost:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "Qwen3.8-27B-Q4_K_M", "messages": [{"role": "user", "content": "Hello"}]}'
```

**When to use:** Multiple models on one GPU with no manual swapping. OpenAI-compatible clients (Cursor, Continue, Cline). The most popular backend in the Matrix (6 of 12) because it is the practical answer to "five models on my 24GB card."

**When to avoid:** One model at full speed (swap overhead is small but nonzero). Production multi-user serving (vLLM batching is superior).

### Ollama

**The "Docker for LLMs."** One command to install, one command to run a model, zero configuration. Ollama pulls GGUF models from its registry, manages them locally, and exposes a simple API. It is the fastest path from "I have a GPU" to "I am chatting with a 27B model."

```bash
# Install (Linux)
curl -fsSL https://ollama.com/install.sh | sh

# Run a model (pulls it automatically on first use)
ollama run qwen3.8-27b

# Use a specific quant
ollama run qwen3.8-27b:q4_K_M

# Run as a server (for API access)
ollama serve
```

**When to use:** New to local LLMs. Testing a model in under five minutes. No need for fine-grained context flags, KV quantization, or custom kernels. The on-ramp.

**When to avoid:** Context lengths beyond defaults. KV cache quantization. Production serving. Formats Ollama does not ship (safetensors, FP8). You have outgrown Ollama — move to llama.cpp or vLLM.

### LM Studio

**The GUI wrapper.** LM Studio is a desktop app with a model browser, one-click download, a chat interface, and a built-in server. It wraps llama.cpp under the hood, so the models it runs are the same GGUF files — you just do not have to type the commands.

```bash
# No command needed — it is a GUI app.
# Download from https://lmstudio.ai
# Open the app → "My Models" → search → download → chat or start server.
```

**When to use:** You prefer a visual interface. You are exploring models and want to compare them without reading terminal output. You are on Windows and want the least-friction path.

**When to avoid:** You are on a headless Linux server. You need scripting or API integration beyond what the built-in server offers. You want to fine-tune (use Unsloth Desktop).

### Unsloth Desktop

**The all-in-one workstation.** Unsloth Desktop runs, chats, fine-tunes, and serves models from a single application. It supports multiple formats (GGUF, safetensors, FP8, MLX) and multiple backends (llama.cpp core + vLLM serving), making it the most capable single-package option for a local AI setup.

```bash
# Install
pip install unsloth

# Run a model
unsloth run --model Qwen3.8-27B --quant Q4_K_M --context 32768

# Fine-tune (LoRA)
unsloth finetune --model Qwen3.8-27B --dataset ./my_data --epochs 3

# Serve
unsloth serve --model Qwen3.8-27B --port 8080
```

**When to use:** You want one tool that does everything: run models, chat, fine-tune, and serve. You work across formats (GGUF for inference, safetensors for training). You are on a single machine that is your whole AI lab.

**When to avoid:** You only need to run one model. You are in a production multi-GPU cluster (use vLLM directly). The all-in-one flexibility has a small performance overhead versus a purpose-built engine.

### vLLM

**The production server.** vLLM is the standard for serious LLM deployment. Its two signature features are **continuous batching** (requests are interleaved at the token level, so one slow request does not block others) and **PagedAttention** (KV cache is managed in pages, eliminating fragmentation). It supports multi-GPU tensor parallelism, FP8, and the full safetensors/AutoRound/AWQ format ecosystem.

```bash
# Single GPU
vllm serve Qwen/Qwen3.8-27B --quantization fp8 --max-model-len 32768

# Two GPUs (tensor parallel)
vllm serve Qwen/Qwen3.8-27B --tensor-parallel-size 2 --max-model-len 32768

# Four GPUs
vllm serve Qwen/Qwen3.8-Flash-Next --tensor-parallel-size 4 --quantization fp8
```

**When to use:** Serving multiple users. High throughput, low latency. 2+ GPUs with tensor parallelism. Datacenter or serious homelab. The "grown-up" choice.

**When to avoid:** Single consumer GPU for casual chat (Ollama/llama.cpp is simpler). GGUF-only workflows (vLLM prefers safetensors/FP8). AMD (use Radiance).

The Matrix's vLLM submissions (digitalscream's 27B on 2× R9700 via the vllm-radiance fork at 120 t/s, and MadGoat's 125B MoE) show vLLM at its best: multi-GPU, high throughput, production-grade.

### TensorRT-LLM

**NVIDIA's max-performance option.** TensorRT-LLM compiles your model into optimized CUDA kernels, fusing operations and eliminating memory round-trips. It is the fastest NVIDIA engine available, but it requires a NVIDIA GPU, a model in safetensors/FP8/NVFP4 format, and a willingness to wrestle with a build process.

```bash
# Build and serve (requires TensorRT, CUDA 12+)
trtllm-build --model_dir ./Qwen3.8-27B-FP8 \
  --precision fp8 --use_weight_streaming

trtllm-serve --model_dir ./Qwen3.8-27B-FP8 --port 8000
```

**When to use:** You have NVIDIA hardware and need the absolute highest tokens/second. You are in a datacenter. You are willing to spend time on the build pipeline.

**When to avoid:** You are on AMD, Apple, or a single consumer GPU. You use GGUF. You want a five-minute setup. The learning curve is the highest of any backend here.

### Strata

**The hybrid offload engine.** *New and evolving.* Strata is designed for one specific problem: running 125B+ MoE models on consumer hardware that has one or two GPUs and a lot of system RAM. It splits the model across three memory tiers — VRAM for the hot experts, RAM for the warm ones, and NVMe SSD for the cold — and uses prompt caching to keep the KV cache for repeated agent prefixes in fast memory.

```bash
# One-click install
curl -fsSL https://strata.ai/install.sh | sh

# Run a 125B MoE model with hybrid offload
strata run Qwen3.8-Flash-Next --kv-cache int8 --context 131072

# With prompt caching (for agent workloads)
strata run Qwen3.8-Flash-Next --prompt-cache --kv-cache int8
```

**When to use:** You have a big MoE model (125B+) and a consumer GPU (24–48GB) plus 64–256GB of system RAM. You are running long-context agent workloads where prompt caching gives 90%+ hit rates. This is the backend that makes the Matrix's headline 125B submission possible: 13.4GB in VRAM, the rest in RAM/SSD.

**When to avoid:** You are running a dense model (the hybrid tiers add latency without the MoE benefit). You have a proper multi-GPU setup (vLLM tensor parallel is faster). You need sub-second latency on every token (the RAM/SSD tiers add milliseconds).

<div class="callout callout--warning"><p><b>Strata is new.</b> The engine is moving fast — versions, features, and performance characteristics change frequently. The commands above reflect the 0.1.x line as of late 2026. Verify the current syntax against the Strata docs before relying on it in production.</p></div>

### Radiance

**The AMD answer to vLLM.** Radiance is a ROCm-optimized inference engine built for AMD's RDNA3/RDNA4 consumer GPUs (R9700, RX 7900 series) and the datacenter MI300X. It supports MTP (Multi-Token Prediction) speculative decoding, which lets compatible models verify multiple tokens per step and push past 200 t/s.

```bash
# Two R9700s, tensor parallel, MTP enabled
radiance serve Qwen/Qwen3.8-27B --tensor-parallel 2 \
  --mtp 8 --quantization fp8 --max-model-len 32768

# Single R9700
radiance serve Qwen/Qwen3.8-27B --quantization fp8 --context 16384
```

**When to use:** You have AMD GPUs and want the best performance. You are running 2+ R9700s and want tensor parallel. You want MTP speculative decoding on a compatible model. This is the backend the Matrix's fastest AMD submissions use.

**When to avoid:** You are on NVIDIA (use vLLM or TensorRT-LLM). You have a single AMD GPU and just want simplicity (llama.cpp ROCm works fine). You use GGUF (Radiance prefers safetensors/FP8).

The Matrix's 120 t/s submission (MadGoat's 27B FP8 on 2× R9700 via the vllm-radiance fork) is Radiance-adjacent: the same kernels, the same MTP pipeline, served through a vLLM-compatible interface.

### MLX

**Apple Silicon's native engine.** MLX is a tensor framework designed for Apple's unified memory architecture. Models in MLX format run natively on M-series Macs with no GPU driver layer, no CUDA translation, and no VRAM/RAM boundary — the memory is just memory.

```bash
# Install
pip install mlx-lm

# Generate
mlx_lm.generate --model mlx-community/Qwen3.8-27B-4bit \
  --prompt "Explain KV cache in one sentence."

# Server (OpenAI-compatible)
mlx_lm.server --model mlx-community/Qwen3.8-27B-4bit --port 8080
```

**When to use:** You are on a Mac. You want the best performance Apple Silicon can give. You are running models that fit in unified memory (up to ~128GB on M3 Ultra).

**When to avoid:** You are on NVIDIA or AMD. You need a format MLX does not support. You are running a 125B+ model that exceeds even the largest Mac's memory.

The Matrix has zero MLX submissions — the biggest demographic gap in the data. If you are a Mac user, your setup is the one the community most needs to see.

### Colibri

**CPU-only inference.** Colibri runs LLMs on pure CPU with no GPU. It is designed for systems with 1TB+ of RAM where a GPU is absent, broken, or simply not worth the power draw. Speed is the trade: expect 1–5 tokens/second, which is fine for unattended batch work and not fine for interactive chat.

```bash
# Run a model on CPU
colibri run --model Qwen3.8-27B-Q4_K_M.gguf \
  --threads 64 --context 8192

# Serve (slow, but functional)
colibri serve --model Qwen3.8-27B-Q4_K_M.gguf --port 9000
```

**When to use:** You have a big-RAM server with no GPU. You are running overnight batch jobs (document processing, translation, embeddings) where 1–5 t/s is acceptable. You want zero GPU dependency.

**When to avoid:** You need interactive speed. You have any GPU available. You are running a model too large for your RAM.

## Pick your backend

The decision tree, condensed:

<div class="diagram diagram--stack">
  <div class="diagram-cell"><b>What is your hardware?</b></div>
  <div class="diagram-arrow">↓</div>
  <div class="diagram-cell">Mac (Apple Silicon) → <b>MLX</b></div>
  <div class="diagram-cell">CPU only, 1TB+ RAM → <b>Colibri</b> (accept 1–5 t/s)</div>
  <div class="diagram-cell">NVIDIA / AMD / Vulkan → <b>continue below</b></div>
  <div class="diagram-arrow">↓</div>
  <div class="diagram-cell"><b>How many GPUs?</b></div>
  <div class="diagram-arrow">↓</div>
  <div class="diagram-cell">One GPU → <b>llama.cpp</b> (control) or <b>Ollama</b> (simplicity) or <b>llama-swap</b> (multi-model)</div>
  <div class="diagram-cell">Two+ GPUs, NVIDIA → <b>vLLM</b> (tensor parallel) or <b>TensorRT-LLM</b> (max perf)</div>
  <div class="diagram-cell">Two+ GPUs, AMD → <b>Radiance</b> (MTP + tensor parallel)</div>
  <div class="diagram-arrow">↓</div>
  <div class="diagram-cell"><b>Big MoE model + lots of RAM?</b></div>
  <div class="diagram-arrow">↓</div>
  <div class="diagram-cell">Yes → <b>Strata</b> (hybrid VRAM+RAM+SSD, prompt caching)</div>
  <div class="diagram-cell">No → the single/multi-GPU choice above stands</div>
</div>

## The golden rules

1. **Start simple.** If you are new, use Ollama or LM Studio. Get a model running in five minutes. Understand the feel of local inference before you optimize.
2. **Graduate to llama.cpp.** When you want control — specific context lengths, KV quantization, layer offloading, custom builds — llama.cpp is the engine that gives you every knob.
3. **Move to vLLM or Radiance for production.** When you are serving multiple users, need continuous batching, or have 2+ GPUs, the production engines are worth the setup cost.
4. **Use Strata for big MoE on small GPUs.** This is the one case where the "unusual" backend is the right answer: a 125B MoE model on a 24GB card + 128GB RAM is a Strata job, not a vLLM job.
5. **Match the format to the backend.** GGUF for llama.cpp/Ollama/LM Studio/Strata. Safetensors/FP8 for vLLM/TensorRT-LLM/Radiance. MLX format for MLX. The [File Formats](file-formats/) guide covers what is inside each.

## Performance expectations per tier

What "good" looks like, by the VRAM tier the Matrix uses:

| Tier | VRAM | Dense model | MoE model | Realistic decode speed |
|---|---|---|---|---|
| T1 | ≤16GB | 7–8B Q4_K_M | 35B-A3B I-Nano | 30–100 t/s (dense), 50–60 t/s (MoE) |
| T2 | 16–24GB | 27B Q4_K_M | 35B-A3B Q4_K_M | 15–30 t/s (dense), 40–60 t/s (MoE) |
| T3 | 24–32GB | 27B Q5_K_M / FP8 | 70B-A6B Q4_K_M | 10–25 t/s (dense), 20–40 t/s (MoE) |
| T4 | 48–64GB | 70B Q4_K_M / FP8 | 125B IQ3_S (Strata) | 5–15 t/s (dense), 15–30 t/s (MoE hybrid) |
| T5 | 96–128GB | 70B FP16 / 125B Q4 | 200B+ MoE (vLLM 2×48GB) | 3–10 t/s (dense), 10–20 t/s (MoE) |
| T6 | 196GB+ | 70B+ FP16 | 671B (CPU+GPU hybrid) | 1–5 t/s (CPU), 5–15 t/s (multi-GPU) |

These are the ranges the Matrix data supports. A well-tuned setup at the top of a tier beats a poorly configured one at the bottom of the next tier — the backend and its flags matter as much as the hardware.

## How this fits the Matrix

Every row in the [Matrix](../../matrix.html) carries a backend. The six llama-swap submissions are the "always-on single GPU" answer; the two vLLM submissions are the "multi-GPU production" answer; the Strata submission is the "hybrid MoE" answer; the Ollama and llama.cpp submissions are the "getting started" and "raw control" answers.

When you submit your own setup, name the backend *and* the key flags (context length, KV precision, tensor parallel size, MTP setting). That is what makes a submission useful to the next reader.
