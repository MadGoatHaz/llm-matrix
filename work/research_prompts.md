# Research Prompts — Guide Content Generation

Each prompt below is self-contained. Copy the text inside the code block and feed it to a research AI (or a capable model with web access). The output is the raw material to adapt into the website's guide pages.

**How to use:**
1. Pick a prompt (one per guide page)
2. Feed it to your research AI
3. Adapt the output into web-friendly format (headings, paragraphs, tables, code blocks)
4. Add the content to `tools/generate_site.py`
5. Re-run `generate_site.py` and push

---

## Prompt 1: Quantization Basics

```
Write a comprehensive guide article titled 'Understanding LLM Quantization: A Practical Guide' for an audience of technically literate people (they know what a GPU is, what VRAM is, what a 'model' is) who are NEW to running large language models locally.

Cover:
1. What is quantization? (The core idea: reducing numerical precision. Analogy: JPEG compression. 2 paragraphs max.)
2. Why we quantize (fit bigger models in less VRAM, faster inference)
3. Precision levels explained: FP32 → FP16 → BF16 → FP8 → INT8 → INT4 (what each means, how much memory each saves)
4. What 'W4A16' means (4-bit Weights, 16-bit Activations) and other common notations
5. How to estimate VRAM needs: the formula (params × bytes_per_param ÷ 1024³). Worked examples: 7B at Q4, 27B at W4A16, 70B at FP8
6. Quality hierarchy: which quant levels are 'safe' vs 'degraded' (general guidance)
7. 'Which quant should I use?' decision guide: if you have X VRAM and want Y quality → use Z
8. Common misconceptions (more quantization isn't always worse; context matters; the model matters as much as the quant)

Include: a comparison table of precision levels (bits, memory multiplier, typical quality impact, use case). Target length: 1500-2000 words. Tone: authoritative but accessible. Every paragraph should teach something actionable.
```

## Prompt 2: File Formats

```
Write a guide article titled 'Model File Formats: GGUF, Safetensors, and MLX' for technically literate beginners to local LLMs.

Cover:
1. What's actually inside a model file? (weights, config, tokenizer, metadata)
2. GGUF: what it is, single-file format, made for llama.cpp, what quant types it supports, when to use it, limitations (no FP8, no multi-file)
3. Safetensors: what it is, multi-file shards, the PyTorch/vLLM standard, when to use it, why training tools output this
4. MLX: Apple's native format, unified memory optimization, when to use it
5. Comparison table: format | files | backends that read it | quant support | best for
6. 'Which format do I need?' decision guide based on your hardware + backend
7. Can you convert between formats? (GGUF↔safetensors: yes with tools. safetensors→MLX: yes. GGUF→safetensors: lossy/not recommended)
8. File size expectations: a 7B model in each format, a 70B model in each format

Target length: 1200-1500 words. Include the comparison table.
```

## Prompt 3: Quantization Methods

```
Write a guide article titled 'How Quants Are Made: Quantization Methods Explained' for people who understand what quantization IS but want to know HOW different quants are created and why some are better than others.

Cover each method:
1. RTN (Round-To-Nearest): The baseline. Just round each weight. Fast to create, lowest quality. When it's acceptable.
2. GPTQ: Hessian-based. Uses calibration data to minimize error. Better than RTN. Slower to generate. What '128 calibration samples' means.
3. AWQ (Activation-Aware Quantization): Observes which weights matter most (based on activation patterns) and protects them. Often the best quality at 4-bit. Why it's popular for vLLM deployments.
4. AutoRound: Gradient-based optimization. Iteratively finds optimal rounding targets. The method behind many 'W4A16-AutoRound' models on HuggingFace. How it differs from GPTQ/AWQ.
5. SmoothQuant: Migrates quantization difficulty from weights to activations. Enables W8A8 (both at 8-bit). How the 'smoothing' works.
6. NVFP4 / MXFP4 (Microscaling): The new generation. 4-bit with per-block scaling. Hardware-native on Blackwell (RTX 50xx) and upcoming AMD. Why they're called 'the golden ticket.' Current status (early adoption).
7. GGUF-specific methods: Q4_K_M, Q5_K_M, Q6_K, Q8_0, IQ3_S, IQ4_XS, I-Nano, UD (unique device) variants. What the K (k-quant) means. What UD means. The quality hierarchy.

Include: A comparison table (method | precision | quality vs FP16 | speed impact | VRAM savings | backends that support it | when to use). 
Flag: which are 'research/experimental' vs 'production ready.'
Target length: 2000-2500 words.
```

## Prompt 4: Model Architectures

```
Write a guide article titled 'Model Architectures: Dense, MoE, and Why Your 125B Model Runs at 3B Speed' for people choosing models for local use.

Cover:
1. Dense models: Every parameter active every token. Examples: Qwen3.8-27B, DeepSeek-V4-Pro. The straightforward (expensive) approach.
2. MoE (Mixture of Experts): Only a subset of 'expert' sub-networks active per token. The total parameter count is large (125B) but active params are small (3B). Examples: Qwen3.8-Flash-Next, Ornith-35B-A3B.
3. What 'A3B' means: 3B Active parameters (out of 35B total). The naming convention.
4. Why MoE is revolutionary for local AI: 125B total intelligence at 3B active speed. Fits in less VRAM than you'd expect because inactive experts can live in slow memory.
5. The tradeoff: MoE models need MORE total memory (all experts must be loaded somewhere) but LESS compute per token. This is why hybrid offload (Strata) works so well for MoE.
6. MTP (Multi-Token Prediction): A special head that predicts multiple future tokens. Enables speculative decoding. Which models have it. The speed boost it provides.
7. Speculative decoding explained: The draft-verify pattern. How MTP and n-gram tables accelerate inference without quality loss.
8. 'Which architecture should I pick?' guide: For speed → small dense. For quality → large MoE. For long context → models with large native context. For agentic work → MTP models.

Target length: 1500-2000 words.
```

## Prompt 5: KV Cache

```
Write a guide article titled 'The KV Cache: Why Your Context Length Eats Your VRAM' for people who are confused about why increasing context length causes OOM errors.

Cover:
1. What the KV cache IS: For every token in your input context, the model stores 'Key' and 'Value' vectors for every attention head. These are reused for every subsequent token generated.
2. Why it grows linearly: 1000 tokens of context = 1000 sets of K/V stored. 100,000 tokens = 100,000 sets. It never shrinks during generation.
3. The formula: KV_size = num_layers × num_kv_heads × head_dim × seq_len × 2 (K and V) × bytes_per_element. Worked example for a 27B model at 32k context in FP16.
4. Why it's separate from model weights: Weights are loaded once. KV cache grows with every token you process.
5. KV cache quantization: Storing K/V in FP8 (half the memory) or INT8 or INT4 (quarter). The quality tradeoff.
6. WHEN to quantize KV: Creative writing, casual chat, roleplay, VRAM-constrained exploration, batch/unattended workloads.
7. WHEN NOT to quantize KV: Agentic coding, RAG/needle-in-haystack, math/reasoning, any task needing precise long-context recall.
8. PagedAttention (vLLM): How vLLM manages KV cache in 'pages' for efficient memory use. Why it matters for multi-user serving.
9. Prompt caching (Strata): How caching previously-computed KV for repeated prompt prefixes gives 90%+ hit rates on agent workloads. Why this makes long-context agents practical.
10. Practical rule: 'If your workload needs precision at length, keep KV in FP16/BF16. If you're stretching VRAM limits and can tolerate fuzzy recall, drop to FP8.'

Target length: 1500-2000 words. Include the worked formula example.
```

## Prompt 6: Context Extension

```
Write a guide article titled 'Going Longer: Context Extension with RoPE, YaRN, and NTK' for people who want to run models beyond their native context window.

Cover:
1. What limits a model's context: Position embeddings (specifically RoPE - Rotary Position Embeddings). The model is 'trained' to expect positions up to N.
2. What happens when you exceed native context: The model hasn't seen those position values. Quality degrades. 'Lost in the middle' effect. Eventually complete failure.
3. YaRN (Yet another RoPE handling): Scales the RoPE frequencies to extend context. The 'scaling factor' (e.g., 2x, 4x). How to set it in llama.cpp/vLLM. Quality retention is generally good up to 2x native.
4. NTK-aware scaling: An alternative that modifies the interpolation of RoPE. Often used in llama.cpp. Slightly different tradeoffs than YaRN.
5. Practical guidance: 
   - Model has 32k native → YaRN 2x = 64k (good quality) → YaRN 4x = 128k (degraded) → YaRN 8x = 256k (risky)
   - Model has 128k native → YaRN 2x = 256k (good) → YaRN 4x = 512k (degraded)
   - Model has 256k native → probably don't need extension
6. Which current models have large NATIVE context (no extension needed): Qwen3.8 family (256k-1M), Gemma 4 (256k), DeepSeek V4 (1M), GLM 5.3 (1M)
7. When you actually NEED extension vs when you should just pick a model with larger native context
8. The VRAM cost: extending context = more KV cache = more VRAM. The extension is only as good as your memory allows.

Target length: 1200-1500 words.
```

## Prompt 7: Backends Deep Dive

```
Write a comprehensive guide titled 'Choosing Your Backend: Every Local LLM Inference Engine Compared' for people deciding HOW to run their models.

For EACH backend, provide: What it is (1 sentence) | Formats supported | Hardware support | Key features | Performance notes | When to use | When NOT to use | Getting started (exact command)

Backends to cover:
1. llama.cpp — The universal engine. GGUF. Runs on CPU/GPU/Metal/Vulkan/ROCm. The baseline.
2. llama-swap — Multi-model auto-swapping on single GPU. OpenAI API. 'Always-on' setups.
3. Ollama — The 'Docker for LLMs.' Easiest start. GGUF. Limited features. Great for quick testing.
4. LM Studio — GUI wrapper. Model browser. One-click server. Beginner-friendly.
5. Unsloth Desktop — All-in-one: run, chat, train, serve. Multiple formats. The complete local AI workstation.
6. vLLM — The production server. Continuous batching. PagedAttention. Multi-GPU tensor parallel. FP8/AutoRound. The choice for serious deployment.
7. TensorRT-LLM — NVIDIA's max-performance option. Kernel-level optimization. INCEPTION mode. Steep learning curve.
8. Strata — The hybrid offload engine. 125B+ MoE on consumer hardware. VRAM+RAM+SSD. Prompt caching. One-click install.
9. Radiance — AMD-optimized. RDNA3/4 (R9700, MI300X). MTP speculative decoding. 200+ tok/s. The AMD answer to vLLM.
10. MLX — Apple Silicon native. Unified memory. The Mac choice.
11. Colibri — CPU-only inference. For 1TB+ RAM systems. No GPU needed.

End with:
- A decision matrix table: 'I want to [use case] on [hardware type] → use [backend]'
- 'The golden rules': (1) Start simple (Ollama/Unsloth), (2) Graduate to llama.cpp for control, (3) Move to vLLM/Radiance for production, (4) Use Strata for big MoE on small GPUs
- Performance expectations: what 'good' looks like for each tier

Target length: 2500-3000 words. This is the longest guide.
```

## Prompt 8: Multi-GPU & Hybrid

```
Write a guide titled 'Making Big Models Fit: Multi-GPU and Hybrid Offload Strategies' for people whose model doesn't fit in one GPU's VRAM.

Cover:
1. The basic problem: A 70B model in FP16 needs ~140GB. No consumer GPU has that. So what do you do?
2. Tensor parallelism: Split the model's layers across multiple GPUs. Each GPU holds a portion. They communicate every layer. Requires fast interconnect (NVLink for NVIDIA, XGMI for AMD). Best for: 2-8 identical GPUs.
3. Pipeline parallelism: Split by stages (first half on GPU 1, second half on GPU 2). Less communication overhead. Good for: non-identical GPUs.
4. Layer offload: Put some layers in system RAM. The GPU processes what it can, RAM holds the overflow. Speed cost: PCIe bandwidth (much slower than VRAM bandwidth). When it's acceptable.
5. Practical NVIDIA setups:
   - 2x RTX 3090/4090 (48GB): tensor parallel, runs most 27-70B models
   - 4x RTX 3090/4090 (96GB): runs 70B+ comfortably
   - 8x (192GB+): runs anything
   - NVLink: 2-way on 3090/4090. Required for best tensor parallel performance.
6. Practical AMD setups:
   - 2x R9700 (64GB): Radiance backend, tensor split
   - 4x R9700 (128GB): Serious local AI
   - 4x MI210 (128GB): Datacenter-class
   - XGMI/Infinity Fabric: AMD's inter-GPU link
7. The hybrid revolution (Strata):
   - Not multi-GPU — it's ONE GPU + lots of RAM + fast SSD
   - 125B MoE model: ~13GB experts in VRAM, rest in RAM, lookup table on NVMe
   - Why MoE makes this work (only active experts need fast access)
   - The bandwidth tradeoff (RAM is ~50GB/s vs VRAM ~1000GB/s)
   - When this beats multi-GPU (cost, power, simplicity)
8. CPU+GPU hybrids:
   - 1TB RAM systems running 671B models at 1 tok/s
   - When this makes sense (unattended batch work, niche tasks)
   - Colibri, llama.cpp CPU mode
9. 'What do I actually need?' decision guide:
   - Model fits in 1 GPU → just run it
   - Model needs 2 GPUs → tensor parallel (NVLink/XGMI if available)
   - Model is MoE + you have lots of RAM → Strata hybrid
   - Model is huge (100B+ dense) + you have a server → multi-GPU tensor parallel
   - You have 1TB RAM + no big GPUs → CPU+GPU hybrid (accept 1-5 tok/s)

Target length: 2000-2500 words.
```
