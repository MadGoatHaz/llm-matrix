---
title: Guides
description: The complete educational series for local LLMs — quantization, file formats, model architectures, KV cache, context extension, inference backends, and multi-GPU strategies.
date: 2026-10-12
author: The Local AI Stack
tags: guides, index
difficulty: all-levels
icon: 📚
---

# The Local AI Stack: Guides

Eight guides, organized in learning-path order. Start at the top if you are new; jump to the section that matches your question if you are not.

The data these guides are built on: **{{submission_count}} community submissions** from **{{contributor_count}} contributors**, across **{{vendor_count}} hardware vendors** and **{{backend_count}} backends** — last updated **{{last_updated}}**.

## Fundamentals

The building blocks: what the numbers mean, what is inside the file, and how the quants are made.

<div class="card-grid">
  <a class="guide-card" href="quantization/">
    <div class="guide-icon">🔢</div>
    <h3>Quantization Basics</h3>
    <p>What are W4A16, FP8, Q4_K_M? The precision ladder, the VRAM formula, and which level to pick for your workload.</p>
    <div class="guide-meta"><span class="badge badge-green">Beginner</span></div>
  </a>
  <a class="guide-card" href="file-formats/">
    <div class="guide-icon">📦</div>
    <h3>File Formats</h3>
    <p>GGUF vs safetensors vs MLX. What is inside a model file, which one to download for your backend, and how they convert.</p>
    <div class="guide-meta"><span class="badge badge-green">Beginner</span></div>
  </a>
  <a class="guide-card" href="quantization-methods/">
    <div class="guide-icon">⚙️</div>
    <h3>Quantization Methods</h3>
    <p>RTN, GPTQ, AWQ, AutoRound, SmoothQuant, NVFP4/MXFP4, and the GGUF K-quant family. How quants are made and why one 4-bit beats another.</p>
    <div class="guide-meta"><span class="badge badge-blue">Intermediate</span></div>
  </a>
</div>

## The Model & Its Memory

How the model is built, what eats your VRAM, and how to stretch the context window.

<div class="card-grid">
  <a class="guide-card" href="model-architectures/">
    <div class="guide-icon">🧠</div>
    <h3>Model Architectures</h3>
    <p>Dense vs Mixture-of-Experts. What "A3B" means. Why a 125B model runs at 3B speed, and how MTP + speculative decoding make it faster.</p>
    <div class="guide-meta"><span class="badge badge-blue">Intermediate</span></div>
  </a>
  <a class="guide-card" href="kv-cache/">
    <div class="guide-icon">💾</div>
    <h3>KV Cache</h3>
    <p>The silent memory eater. Why context length costs VRAM, the formula that predicts it, and when to quantize the cache.</p>
    <div class="guide-meta"><span class="badge badge-blue">Intermediate</span></div>
  </a>
  <a class="guide-card" href="context-extension/">
    <div class="guide-icon">📏</div>
    <h3>Context Extension</h3>
    <p>RoPE, YaRN, NTK. Pushing models beyond their native window — and the honest 2×/4×/8× quality rule.</p>
    <div class="guide-meta"><span class="badge badge-blue">Intermediate</span></div>
  </a>
</div>

## Running It

The engines and the hardware strategies that make it all work.

<div class="card-grid">
  <a class="guide-card" href="backends/">
    <div class="guide-icon">⚡</div>
    <h3>Backends Deep Dive</h3>
    <p>llama.cpp, llama-swap, Ollama, LM Studio, Unsloth Desktop, vLLM, TensorRT-LLM, Strata, Radiance, MLX, and Colibri. Every engine compared, with the exact command to start.</p>
    <div class="guide-meta"><span class="badge badge-purple">Advanced</span></div>
  </a>
  <a class="guide-card" href="multi-gpu/">
    <div class="guide-icon">🖥️</div>
    <h3>Multi-GPU &amp; Hybrid</h3>
    <p>Tensor parallel, pipeline parallel, layer offload, and the Strata hybrid (VRAM+RAM+SSD). Making big models fit on consumer hardware.</p>
    <div class="guide-meta"><span class="badge badge-purple">Advanced</span></div>
  </a>
</div>

## Not sure where to start?

- **"I just want a model running."** → [Quantization Basics](quantization/) to understand what you are downloading, then [Backends](backends/) to pick your engine.
- **"My model is too big for my GPU."** → [Multi-GPU & Hybrid](multi-gpu/) for the split strategies, [KV Cache](kv-cache/) for the memory math.
- **"Why is my 125B model slow?"** → [Model Architectures](model-architectures/) to understand MoE and active parameters.
- **"What format do I download?"** → [File Formats](file-formats/) — the backend picks the format, not the other way around.
- **"I want to run longer contexts."** → [Context Extension](context-extension/) for RoPE scaling, [KV Cache](kv-cache/) for the VRAM cost.
- **"Which quant should I use?"** → [Quantization Basics](quantization/) for the decision guide, [Quantization Methods](quantization-methods/) for why one 4-bit beats another.
