# The Best Local LLM Matrix

**A vram-first reference for running local models on real silicon.**

This thread tracks suggested models, mapped by:

- **Usable VRAM footprint** — organized across 6 VRAM tiers, from single consumer GPUs to enterprise clusters
- **Optimal quantization architecture & weight precision** (minimum GPU compute requirement)
- **Context headroom** via unquantized KV caching

### Quick Navigation

- 🚀 Start Here: Quick GPU Lookup
- 🎯 Use-Case Index
- 📋 How This Thread Is Managed
- ⚡ KV Cache Quantization Rule
- 🖥️ Hardware Vendor Notes
- 📦 Running Non-GGUF Models
- 🧰 Supporting Software & Ecosystem
- 📊 The Master Matrix (6 Tiers)
- ⚠️ Technical Architecture Note
- 🔬 Community Verified Data
- ⚡ Real-World Constraints
- 📅 Changelog
- 🔗 Related Threads

<hr>

<details>
<summary>🚀 Start Here: Quick GPU Lookup — Find Your Tier</summary>

*Not sure which tier you're in? Find your GPU below. This maps specific hardware to the matrix tiers so you can jump straight to your options.*

<div class="md-table">
<table>
<thead>
<tr>
<th style="text-align:left">Your GPU</th>
<th style="text-align:left">VRAM</th>
<th style="text-align:left">Your Tier</th>
<th style="text-align:left">Jump To</th>
</tr>
</thead>
<tbody>
<tr>
<td colspan="4" style="text-align:left"><strong>Tier 1: ≤ 16 GB</strong></td>
</tr>
<tr>
<td style="text-align:left">RTX 4060 Ti 16GB</td>
<td style="text-align:left">16 GB</td>
<td style="text-align:left">Tier 1</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td style="text-align:left">RTX 3060 12GB</td>
<td style="text-align:left">12 GB</td>
<td style="text-align:left">Tier 1</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td style="text-align:left">RTX A2000</td>
<td style="text-align:left">16 GB</td>
<td style="text-align:left">Tier 1</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td style="text-align:left">RX 7600 XT</td>
<td style="text-align:left">16 GB</td>
<td style="text-align:left">Tier 1</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td style="text-align:left">Radeon VII</td>
<td style="text-align:left">16 GB HBM2</td>
<td style="text-align:left">Tier 1</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td style="text-align:left">Apple M1/M2 16GB</td>
<td style="text-align:left">16 GB Unified</td>
<td style="text-align:left">Tier 1</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td style="text-align:left">RTX 3050 8GB</td>
<td style="text-align:left">8 GB</td>
<td style="text-align:left">Tier 1 (tight)</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td style="text-align:left">RX 7600</td>
<td style="text-align:left">8 GB</td>
<td style="text-align:left">Tier 1 (tight)</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td colspan="4" style="text-align:left"><strong>Tier 2: 16 – 24 GB</strong></td>
</tr>
<tr>
<td style="text-align:left">RTX 4080 16GB</td>
<td style="text-align:left">16 GB</td>
<td style="text-align:left">Tier 2</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td style="text-align:left">RTX 3080 20GB</td>
<td style="text-align:left">20 GB</td>
<td style="text-align:left">Tier 2</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td style="text-align:left">RX 7900 XT</td>
<td style="text-align:left">20 GB</td>
<td style="text-align:left">Tier 2</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td style="text-align:left">RTX A4000</td>
<td style="text-align:left">16 GB</td>
<td style="text-align:left">Tier 2</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td style="text-align:left">Radeon Pro W7900</td>
<td style="text-align:left">28 GB</td>
<td style="text-align:left">Tier 2</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td style="text-align:left">Apple M2/M3 32GB</td>
<td style="text-align:left">32 GB Unified</td>
<td style="text-align:left">Tier 2</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td style="text-align:left">RTX 4070 Ti Super</td>
<td style="text-align:left">16 GB</td>
<td style="text-align:left">Tier 2</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td colspan="4" style="text-align:left"><strong>Tier 3: 24 – 32 GB</strong></td>
</tr>
<tr>
<td style="text-align:left">RTX 3090</td>
<td style="text-align:left">24 GB</td>
<td style="text-align:left">Tier 3</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td style="text-align:left">RTX 4090</td>
<td style="text-align:left">24 GB</td>
<td style="text-align:left">Tier 3</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td style="text-align:left">RX 7900 XTX</td>
<td style="text-align:left">24 GB</td>
<td style="text-align:left">Tier 3</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td style="text-align:left">RTX A5000</td>
<td style="text-align:left">24 GB</td>
<td style="text-align:left">Tier 3</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td style="text-align:left">2x RTX 3060 16GB</td>
<td style="text-align:left">32 GB</td>
<td style="text-align:left">Tier 3</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td style="text-align:left">2x RX 7600 XT</td>
<td style="text-align:left">32 GB</td>
<td style="text-align:left">Tier 3</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td style="text-align:left">Apple M1/M2/M3 36-38GB</td>
<td style="text-align:left">36-38 GB Unified</td>
<td style="text-align:left">Tier 3</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td style="text-align:left">Radeon AI Pro R9700</td>
<td style="text-align:left">32 GB</td>
<td style="text-align:left">Tier 3</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td colspan="4" style="text-align:left"><strong>Tier 4: 48 – 64 GB</strong></td>
</tr>
<tr>
<td style="text-align:left">2x RTX 3090/4090</td>
<td style="text-align:left">48 GB</td>
<td style="text-align:left">Tier 4</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td style="text-align:left">2x RX 7900 XTX</td>
<td style="text-align:left">48 GB</td>
<td style="text-align:left">Tier 4</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td style="text-align:left">4x RTX A4000</td>
<td style="text-align:left">64 GB</td>
<td style="text-align:left">Tier 4</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td style="text-align:left">2x MI210</td>
<td style="text-align:left">64 GB</td>
<td style="text-align:left">Tier 4</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td style="text-align:left">Mac Studio M2/M4 Ultra 64GB</td>
<td style="text-align:left">64 GB Unified</td>
<td style="text-align:left">Tier 4</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td style="text-align:left">2x RTX A5000</td>
<td style="text-align:left">48 GB</td>
<td style="text-align:left">Tier 4</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td style="text-align:left">2x R9700</td>
<td style="text-align:left">64 GB</td>
<td style="text-align:left">Tier 4</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td colspan="4" style="text-align:left"><strong>Tier 5: 96 – 128 GB</strong></td>
</tr>
<tr>
<td style="text-align:left">4x RTX 3090/4090</td>
<td style="text-align:left">96 GB</td>
<td style="text-align:left">Tier 5</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td style="text-align:left">4x MI210</td>
<td style="text-align:left">128 GB</td>
<td style="text-align:left">Tier 5</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td style="text-align:left">2x A100 80GB</td>
<td style="text-align:left">160 GB</td>
<td style="text-align:left">Tier 5</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td style="text-align:left">8x RTX A4000</td>
<td style="text-align:left">128 GB</td>
<td style="text-align:left">Tier 5</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td style="text-align:left">4x RTX A5000</td>
<td style="text-align:left">96 GB</td>
<td style="text-align:left">Tier 5</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td style="text-align:left">2x MI250</td>
<td style="text-align:left">128 GB</td>
<td style="text-align:left">Tier 5</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td style="text-align:left">4x R9700</td>
<td style="text-align:left">128 GB</td>
<td style="text-align:left">Tier 5</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td style="text-align:left">4x AMD Instinct v620</td>
<td style="text-align:left">96 GB</td>
<td style="text-align:left">Tier 5</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td colspan="4" style="text-align:left"><strong>Tier 6: 196 – 256 GB+</strong></td>
</tr>
<tr>
<td style="text-align:left">8x RTX 3090/4090</td>
<td style="text-align:left">192 GB</td>
<td style="text-align:left">Tier 6</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td style="text-align:left">8x A100 80GB</td>
<td style="text-align:left">640 GB</td>
<td style="text-align:left">Tier 6</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td style="text-align:left">8x H100 80GB</td>
<td style="text-align:left">640 GB</td>
<td style="text-align:left">Tier 6</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td style="text-align:left">4x MI300X</td>
<td style="text-align:left">256 GB</td>
<td style="text-align:left">Tier 6</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td style="text-align:left">8x MI210</td>
<td style="text-align:left">256 GB</td>
<td style="text-align:left">Tier 6</td>
<td style="text-align:left">📊</td>
</tr>
<tr>
<td style="text-align:left">Mac Studio M2/M4 Ultra 192-256GB</td>
<td style="text-align:left">192-256 GB Unified</td>
<td style="text-align:left">Tier 6</td>
<td style="text-align:left">📊</td>
</tr>
</tbody>
</table>
</div>

*Don't see your card? The tier is determined by total available VRAM (or unified memory for Apple). If you're between tiers, plan for the lower one and you'll have more KV headroom.*

</details>

<details>
<summary>🎯 Use-Case Index — Find the Best Model for Your Task</summary>

*Looking for a specific capability rather than a VRAM tier? Use this cross-reference to find the best model for what you actually need to do.*

<div class="md-table">
<table>
<thead>
<tr>
<th style="text-align:left">Use Case</th>
<th style="text-align:left">Best Pick (Any Tier)</th>
<th style="text-align:left">Budget Pick (≤24GB)</th>
<th style="text-align:left">Power User (96GB+)</th>
<th style="text-align:left">Notes</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left"><strong>Agentic Coding / Repo Editing</strong></td>
<td style="text-align:left">Swift-1.5-Qwen3.8-27b (W4A16)</td>
<td style="text-align:left">Swift-1.5-Qwen3.8-27b (Q4_K_M GGUF)</td>
<td style="text-align:left">Swift-1.5-Qwen3.8-27b (FP8, 256k ctx)</td>
<td style="text-align:left">Keep KV unquantized. MTP speculative decoding helps latency.</td>
</tr>
<tr>
<td style="text-align:left"><strong>Deep Reasoning / Math / Logic</strong></td>
<td style="text-align:left">Ornith-1.5-35B-A3B (MTP)</td>
<td style="text-align:left">Ornith-1.5-9B (W4A16)</td>
<td style="text-align:left">Ornith-1.5-35B-A3B (BF16 KV)</td>
<td style="text-align:left">Chain-of-thought models are sensitive to KV quantization.</td>
</tr>
<tr>
<td style="text-align:left"><strong>Long-Document RAG / NIAH</strong></td>
<td style="text-align:left">Swift-1.5-Qwen3.8-27b (1m YaRN)</td>
<td style="text-align:left">Carnice-Qwen3.6-MoE-35B-A3B (65k)</td>
<td style="text-align:left">Swift-1.5-Qwen3.8-Flash-Next (1m)</td>
<td style="text-align:left">FP16/BF16 KV critical past 32k tokens.</td>
</tr>
<tr>
<td style="text-align:left"><strong>Creative Writing / Roleplay</strong></td>
<td style="text-align:left">Gemma-4-26B-A4B-it</td>
<td style="text-align:left">Gemma-4-E4B-Opus (Q4_K_M)</td>
<td style="text-align:left">Gemma-4-31B-it</td>
<td style="text-align:left">KV quantization acceptable here. FP8 KV fine.</td>
</tr>
<tr>
<td style="text-align:left"><strong>Fast Chat / General Assistant</strong></td>
<td style="text-align:left">Qwen3.5-4B (Q4_K_M)</td>
<td style="text-align:left">Qwen3.5-4B (Q4_K_M)</td>
<td style="text-align:left">Any Tier 1 model on surplus GPUs</td>
<td style="text-align:left">96+ tok/s on 16GB. Always-loaded resident.</td>
</tr>
<tr>
<td style="text-align:left"><strong>Multimodal (Vision/Video)</strong></td>
<td style="text-align:left">DeepSeek-V4-Flash-Vision-Exp</td>
<td style="text-align:left">— (needs 156GB+)</td>
<td style="text-align:left">DeepSeek-V4-Flash-Vision-Exp</td>
<td style="text-align:left">No consumer-tier option yet.</td>
</tr>
<tr>
<td style="text-align:left"><strong>Complex Agent Systems / Tool Use</strong></td>
<td style="text-align:left">GLM-5.3-Flash</td>
<td style="text-align:left">— (needs 176GB+)</td>
<td style="text-align:left">GLM-5.3-Flash</td>
<td style="text-align:left">1m native context. No YaRN needed.</td>
</tr>
<tr>
<td style="text-align:left"><strong>Speculative Decoding / Max Throughput</strong></td>
<td style="text-align:left">Qwen3.8-Flash-Next NVFP4 (lhl's top pick &lt;128GB)</td>
<td style="text-align:left">—</td>
<td style="text-align:left">Swift-1.5-Qwen3.8-Flash-Next (pure VRAM)</td>
<td style="text-align:left">N-gram table adds 95GB. See architecture note. Strata enables this on single-GPU consumer hardware via hybrid offload.</td>
</tr>
<tr>
<td style="text-align:left"><strong>Niche Domain Translation</strong></td>
<td style="text-align:left">DeepSeek-V4-Pro (Q8_K_XL, CPU+GPU)</td>
<td style="text-align:left">—</td>
<td style="text-align:left">DeepSeek-V4-Pro (1TB RAM hybrid)</td>
<td style="text-align:left">Model selection &gt;&gt; parameter count for niche domains.</td>
</tr>
<tr>
<td style="text-align:left"><strong>Uncensored / Security Research</strong></td>
<td style="text-align:left">Swift-Qwen3.8-27B-Uncensored-FP8</td>
<td style="text-align:left">—</td>
<td style="text-align:left">Swift-Qwen3.8-27B-Uncensored-FP8 (2x R9700)</td>
<td style="text-align:left">Standard Qwen models get "nervy" on security content.</td>
</tr>
</tbody>
</table>
</div>

</details>

<details>
<summary>📋 How This Thread Is Managed &amp; Maintained</summary>

1. **Weekly Rollups:** Every weekend, community submissions, poll shifts, and verified results are reviewed.
2. **Major Release Fast-Tracks:** When a significant open-weight release drops, it will be tested. Once context behavior is validated (either through hands-on testing or verified member submissions/DMs), the matrix will be updated accordingly.
3. **Direct Submissions & DMs:** If you have dialled in an unlisted model, post it using the template in Post #2 or send a DM with your suggestions.
4. **Tier Promotions:** Models that consistently receive verified community data across multiple hardware configurations are promoted from "Community Verified" into the Master Matrix.
5. **Data Viewport / Index:** A structured catalog of all submissions is being developed to make the thread data mentally organizable. If you've built a parsing tool or index script for this thread, DM me or post it — I want to avoid duplicate effort and integrate the best solution. (Requested by s1ugh34d, post #27.)

</details>

<details>
<summary>⚡ The KV Cache Quantization Rule: When to Use It (and When NOT To)</summary>

> **Baseline Recommendation:** Default to **unquantized (FP16/BF16) KV cache** whenever VRAM allows. Every primary context limit listed in the matrix below assumes full-precision KV cache.

Quantizing the KV cache to FP8 or FP4 halves or quarters its memory footprint, but it introduces numerical noise into the attention mechanisms. Whether that degradation matters depends entirely on the workload:

- **When you SHOULD NOT quantize KV Cache:**
  - **Agentic Coding & Repo Editing:** Quantized KV cache introduces subtle token hallucinations, misses syntax rules, and breaks multi-hop file references.
  - **Deterministic Logic, Math & Deep Reasoning:** Attention sinks and drift cause chain-of-thought models to lose coherence during long generation steps.
  - **Needle-in-a-Haystack (NIAH) & Technical RAG:** Critical facts buried in large documents are often skipped or misattributed once context scales past 32k tokens.

- **When KV Cache Quantization IS Acceptable:**
  - **Creative Writing & Long-Form Fiction:** Gist and narrative momentum matter more than verbatim recall. Minor attention drift rarely breaks a story.
  - **Casual Chatbots & Roleplay:** Conversational flow is tolerant of minor precision loss.
  - **VRAM-Constrained Exploration:** When stretching a card beyond its native capacity is the only way to run a task, and fuzzy recall is acceptable.
  - **Batch/Unattended Workloads:** When throughput-per-dollar matters more than per-token precision (e.g., overnight document translation, large-scale summarization).

If a workload requires precision, scale context via **model weight quantization (such as AutoRound W4A16) combined with RoPE/YaRN** (if going over the native model context), while keeping the KV cache in native FP16/BF16.

</details>

<details>
<summary>🖥️ Hardware Vendor Notes (NVIDIA / AMD / Apple)</summary>

**Easiest start on any platform:** **Unsloth Desktop** is the recommended all-in-one app — it runs GGUF, safetensors, and FP8 models on NVIDIA CUDA, AMD ROCm/Vulkan, Intel Vulkan, and Apple Metal/MLX, with chat, no-code fine-tuning, and an OpenAI-compatible API server built in. **Ollama** and **LM Studio** remain solid lighter-weight alternatives if you prefer minimal overhead.

<details>
<summary>NVIDIA (CUDA)</summary>

All models in this matrix are tested and verified on NVIDIA hardware. W4A16 AutoRound quants require compute capability 7.0+ (Turing or newer). FP8 weights require 8.9+ (Ada/Hopper). Multi-GPU tensor parallelism works out of the box with vLLM and llama.cpp.

</details>

<details>
<summary>AMD (ROCm / Vulkan)</summary>

Fully supported via llama.cpp (ROCm backend for gfx906+, Vulkan for older) and vLLM (ROCm builds). Key notes:
- **Radeon VII** (gfx906, 16GB HBM2): Excellent for ≤16GB tier models. Community-verified at 54–96 tok/s decode on Q4 models. HBM2 bandwidth (800 GB/s) makes it competitive with RTX 3060 12GB for inference.
- **RX 7900 XT** (gfx1100, 20GB): Sits in the 16–24GB tier.
- **RX 7900 XTX** (gfx1100, 24GB): Full ROCm support. Handles 24–32GB tier comfortably.
- **MI210 / MI250 / MI300X**: Datacenter cards. MI210 is FP16-only (no FP8), so W4A16 AutoRound is the optimal quant. 4x MI210 = 256GB VRAM.
- **llama-swap** is the recommended container for AMD multi-model serving (see community data below).

</details>

<details>
<summary>Apple (Metal / Unified Memory)</summary>

Unified memory means VRAM = system RAM. A 64GB Mac Studio can run models that need 48–64GB "VRAM" since there's no separate GPU memory wall. Metal backend in llama.cpp and MLX for native Apple Silicon inference. No tensor parallelism needed — single GPU address space.

</details>

</details>

<details>
<summary>📦 Running Non-GGUF Models (AutoRound / Safetensors / FP8)</summary>

AutoRound W4A16 models are **not** single .GGUF files. They are distributed as HuggingFace Safetensors shards (typically 4–10 files) and require a compatible inference backend:

**Option A: vLLM (Recommended for W4A16 AutoRound)**

```
pip install vllm

vllm serve <huggingface-repo-id> \
  --quantization auto-round-w4a16 \
  --max-model-len 262144 \
  --gpu-memory-utilization 0.90 \
  --port 8000
```

**Option B: llama.cpp (for GGUF alternatives)**

If you prefer llama.cpp, look for the GGUF quant of the same base model (e.g., `unsloth/<model>-GGUF`). You lose the AutoRound optimization but gain single-file portability and broader hardware support (Vulkan, Metal, CPU offload).

**Option C: LM Studio / Ollama**

These tools primarily support GGUF. For AutoRound W4A16, use vLLM directly or check if the model author has published a GGUF conversion.

**Option D: Unsloth Desktop (All-in-One)**

Unsloth Desktop natively supports GGUF, safetensors, FP8, and MLX formats, with llama.cpp as the core engine and vLLM as the deployment backend. It works on NVIDIA CUDA, AMD ROCm/Vulkan, Intel Vulkan, and Apple Metal/MLX — one app for any package format in this matrix.

**Option E: Strata (Hybrid VRAM+RAM+SSD Offload)**

```
# Strata enables running 100B+ MoE models on consumer hardware
# by splitting experts across VRAM, system RAM, and NVMe.
# One-click install for Windows/Linux. OpenAI/Anthropic API on localhost.

# Install (one-click)
# See: https://github.com/Niko1221/Strata

# Key features:
# - 6892 experts: ~13.4GB in VRAM, rest in RAM, lookup on NVMe
# - Prompt cache: ~90% hit rate on agent workloads
# - MTP speculative decoding (MTP=4 + lookup=3)
# - Works with GGUF IQ3_S, Q4_K_M, and higher
# - Single 24GB GPU + 128GB RAM can run 125B models at 100+ tok/s

# WSL2 note: Must allocate RAM via .wslconfig (e.g., 96GB)
# or the engine cannot load the RAM-resident experts.
```

**Option F: Radiance (AMD-Optimized vLLM Fork)**

```
# Radiance is an AMD-specific inference engine optimized for
# RDNA3/RDNA4 GPUs (R9700, R9600D, MI300X).
# Achieves 200+ tok/s decode with MTP on dual R9700.

# Key features:
# - Native amdgpu backend (no Vulkan fallback)
# - MTP speculative decoding
# - FP8 PLE (Prompt Lookup Engine) support
# - 5200-6200 tok/s prefill on dual R9700
# - Everything in VRAM + system RAM, no disk tier needed

# See: https://github.com/magiccodingman/vllm-radiance
```

**Format Comparison:**

<div class="md-table">
<table>
<thead>
<tr>
<th style="text-align:left">Format</th>
<th style="text-align:left">Files</th>
<th style="text-align:left">Backend</th>
<th style="text-align:left">Best For</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left">GGUF (Q4_K_M)</td>
<td style="text-align:left">1 file</td>
<td style="text-align:left">llama.cpp, LM Studio, Ollama</td>
<td style="text-align:left">Portability, AMD/Vulkan, CPU offload</td>
</tr>
<tr>
<td style="text-align:left">AutoRound W4A16</td>
<td style="text-align:left">4–10 safetensors</td>
<td style="text-align:left">vLLM</td>
<td style="text-align:left">Maximum quality at 4-bit, NVIDIA</td>
</tr>
<tr>
<td style="text-align:left">FP8 (native)</td>
<td style="text-align:left">4–10 safetensors</td>
<td style="text-align:left">vLLM, TensorRT-LLM</td>
<td style="text-align:left">Ada/Hopper/MI300, best speed/quality</td>
</tr>
</tbody>
</table>
</div>

**Emerging: NVFP4 / MXFP4**

*The next frontier in 4-bit quantization. NVFP4 (NVIDIA) and MXFP4 (microscaling, cross-vendor) offer better quality-per-bit than W4A16 AutoRound or GGUF Q4_K_M, with native hardware acceleration on Blackwell (RTX 50xx) and upcoming MI300/MI400 chips. Community consensus (Strawberry, lhl): "NVFP4 → MXFP4 is the real golden ticket" — Flash-Next in NVFP4 is already the top pick at the 96-128GB tier. Expect these formats to dominate the matrix within 6-12 months as more models ship native MXFP4 checkpoints.*

</details>

<details>
<summary>🧰 Supporting Software &amp; Ecosystem — Frontends, Agents, and Tools</summary>

*The inference engine is only half your stack. These are the frontends, agent harnesses, and utility tools the community recommends pairing with your local models. None of these run the model themselves — they give you a better way to talk to it.*

<details>
<summary>💬 All-in-One Apps (Run + Chat + Manage)</summary>

<div class="md-table">
<table>
<thead>
<tr>
<th style="text-align:left">App</th>
<th style="text-align:left">Platforms</th>
<th style="text-align:left">What It Does</th>
<th style="text-align:left">Best For</th>
<th style="text-align:left">Link</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left"><strong>Unsloth Desktop</strong></td>
<td style="text-align:left">macOS, Windows, Ubuntu/Debian, WSL</td>
<td style="text-align:left">Run AND train models locally. GGUF, safetensors, FP8, MLX. llama.cpp + vLLM backends. Chat with parallel sessions, self-healing tool calls, code execution. No-code fine-tuning (LoRA). Image/video generation. TTS/STT. OpenAI-compatible API server. LAN serving. Fully offline, no telemetry.</td>
<td style="text-align:left">The complete local AI workstation. Best "one app does everything" option.</td>
<td style="text-align:left"><a href="https://unsloth.ai/download">unsloth.ai/download</a></td>
</tr>
<tr>
<td style="text-align:left"><strong>Ollama</strong></td>
<td style="text-align:left">macOS, Windows, Linux</td>
<td style="text-align:left">Lightweight model runner. CLI-first. GGUF models. One-command pull and run. OpenAI-compatible API.</td>
<td style="text-align:left">Minimalist setup, scripting, API-first workflows</td>
<td style="text-align:left"><a href="https://ollama.com">ollama.com</a></td>
</tr>
<tr>
<td style="text-align:left"><strong>LM Studio</strong></td>
<td style="text-align:left">macOS, Windows, Linux</td>
<td style="text-align:left">GUI model browser + chat. GGUF/MLX. One-click server.</td>
<td style="text-align:left">Visual model management, quick testing</td>
<td style="text-align:left"><a href="https://lmstudio.ai">lmstudio.ai</a></td>
</tr>
</tbody>
</table>
</div>

</details>

<details>
<summary>💬 Chat Frontends (Talk to Any Local/Remote AI)</summary>

<div class="md-table">
<table>
<thead>
<tr>
<th style="text-align:left">App</th>
<th style="text-align:left">Platforms</th>
<th style="text-align:left">Connects To</th>
<th style="text-align:left">Standout Feature</th>
<th style="text-align:left">Link</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left"><strong>Chatbox</strong></td>
<td style="text-align:left">Windows, macOS, Linux, iOS, Android, Web</td>
<td style="text-align:left">Ollama, any OpenAI-compatible API (vLLM, LM Studio, Unsloth Desktop), Anthropic, OpenAI, Gemini, 20+ providers</td>
<td style="text-align:left">Beautiful UI, file/image/code understanding, web search, Agent Mode with MCP, desktop knowledge base. Data stays on-device.</td>
<td style="text-align:left"><a href="https://chatboxai.app">chatboxai.app</a></td>
</tr>
<tr>
<td style="text-align:left"><strong>Open WebUI</strong></td>
<td style="text-align:left">Web (Docker/self-host)</td>
<td style="text-align:left">Ollama, any OpenAI-compatible API</td>
<td style="text-align:left">Self-hosted web interface, multi-user, RAG built-in, community model sharing</td>
<td style="text-align:left"><a href="https://openwebui.com">openwebui.com</a></td>
</tr>
<tr>
<td style="text-align:left"><strong>LibreChat</strong></td>
<td style="text-align:left">Web (self-host)</td>
<td style="text-align:left">Any OpenAI-compatible, Anthropic, Google, 30+</td>
<td style="text-align:left">Multi-model comparison, agents, file upload, collaborative spaces</td>
<td style="text-align:left"><a href="https://www.librechat.ai">librechat.ai</a></td>
</tr>
</tbody>
</table>
</div>

</details>

<details>
<summary>👨‍💻 Agentic Coding Harnesses</summary>

<div class="md-table">
<table>
<thead>
<tr>
<th style="text-align:left">Tool</th>
<th style="text-align:left">Platform</th>
<th style="text-align:left">What It Does</th>
<th style="text-align:left">Best For</th>
<th style="text-align:left">Link</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left"><strong>Kilo Code</strong></td>
<td style="text-align:left">VS Code, JetBrains, CLI, Cloud</td>
<td style="text-align:left">Open-source (MIT) agentic coding assistant. Code/Architect/Debug/Ask modes. Understands whole codebase. MCP support. 500+ models including local. Auto model routing. Zero inference markup.</td>
<td style="text-align:left">Best open-source agentic coding experience. Pairs perfectly with local models via OpenAI-compatible API.</td>
<td style="text-align:left"><a href="https://kilocode.ai">kilocode.ai</a></td>
</tr>
<tr>
<td style="text-align:left"><strong>Cursor</strong></td>
<td style="text-align:left">Desktop app (VS Code fork)</td>
<td style="text-align:left">AI-native code editor. Multi-file editing, tab completion, agent mode.</td>
<td style="text-align:left">Polished commercial experience (uses cloud AI by default, can point to local)</td>
<td style="text-align:left"><a href="https://cursor.sh">cursor.sh</a></td>
</tr>
<tr>
<td style="text-align:left"><strong>Continue</strong></td>
<td style="text-align:left">VS Code, JetBrains</td>
<td style="text-align:left">Open-source AI code assistant. Configurable — point to any local model. Context-aware chat + autocomplete.</td>
<td style="text-align:left">Lightweight, fully local, open-source</td>
<td style="text-align:left"><a href="https://continue.dev">continue.dev</a></td>
</tr>
<tr>
<td style="text-align:left"><strong>Cline</strong></td>
<td style="text-align:left">VS Code</td>
<td style="text-align:left">Open-source autonomous coding agent. File edits, terminal commands, web browsing. MCP.</td>
<td style="text-align:left">Agentic autonomy in your editor, works with local models</td>
<td style="text-align:left"><a href="https://cline.bot">cline.bot</a></td>
</tr>
</tbody>
</table>
</div>

</details>

<details>
<summary>🤖 General-Purpose Agent Frameworks</summary>

<div class="md-table">
<table>
<thead>
<tr>
<th style="text-align:left">Framework</th>
<th style="text-align:left">What It Does</th>
<th style="text-align:left">Local Model Support</th>
<th style="text-align:left">Link</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left"><strong>Hermes</strong></td>
<td style="text-align:left">General-purpose autonomous agent. Multi-step task execution, tool use, web browsing, file operations.</td>
<td style="text-align:left">Yes — any OpenAI-compatible endpoint (vLLM, Ollama, Unsloth Desktop)</td>
<td style="text-align:left">(community project)</td>
</tr>
<tr>
<td style="text-align:left"><strong>AutoGPT</strong></td>
<td style="text-align:left">Autonomous agent platform. Goal-driven task decomposition and execution.</td>
<td style="text-align:left">Yes — via Ollama or OpenAI-compatible API</td>
<td style="text-align:left"><a href="https://agpt.co">agpt.co</a></td>
</tr>
<tr>
<td style="text-align:left"><strong>CrewAI</strong></td>
<td style="text-align:left">Multi-agent orchestration. Define teams of agents with roles and tools.</td>
<td style="text-align:left">Yes — any LLM provider including local</td>
<td style="text-align:left"><a href="https://crewai.com">crewai.com</a></td>
</tr>
<tr>
<td style="text-align:left"><strong>LangChain / LlamaIndex</strong></td>
<td style="text-align:left">Frameworks for building LLM applications. RAG, chains, agents, memory.</td>
<td style="text-align:left">Yes — extensive local model integrations</td>
<td style="text-align:left"><a href="https://langchain.com">langchain.com</a> / <a href="https://llamaindex.ai">llamaindex.ai</a></td>
</tr>
</tbody>
</table>
</div>

</details>

<details>
<summary>🔀 Orchestration &amp; Routing</summary>

<div class="md-table">
<table>
<thead>
<tr>
<th style="text-align:left">Tool</th>
<th style="text-align:left">What It Does</th>
<th style="text-align:left">Best For</th>
<th style="text-align:left">Link</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left"><strong>LiteLLM</strong></td>
<td style="text-align:left">Unified API proxy. Route requests across multiple models/servers. Load balancing, fallback, budgeting.</td>
<td style="text-align:left">Multi-model deployments, A/B testing, production routing</td>
<td style="text-align:left"><a href="https://litellm.ai">litellm.ai</a></td>
</tr>
<tr>
<td style="text-align:left"><strong>Portkey</strong></td>
<td style="text-align:left">AI gateway. Caching, rate limiting, analytics, model routing.</td>
<td style="text-align:left">Production AI infrastructure</td>
<td style="text-align:left"><a href="https://portkey.ai">portkey.ai</a></td>
</tr>
<tr>
<td style="text-align:left"><strong>MCP (Model Context Protocol)</strong></td>
<td style="text-align:left">Standard protocol for connecting LLMs to tools, data sources, and actions.</td>
<td style="text-align:left">Extending your local model's capabilities with structured tool access</td>
<td style="text-align:left"><a href="https://modelcontextprotocol.io">modelcontextprotocol.io</a></td>
</tr>
</tbody>
</table>
</div>

</details>

*The community's favorite "stack" for agentic coding with local models: **Unsloth Desktop** (or vLLM) as the backend + **Kilo Code** in VS Code as the harness + **Chatbox** for quick general chat. For multi-agent workflows, add **LiteLLM** as a routing layer and **CrewAI** or **Hermes** as the orchestrator.*

</details>

<details>
<summary>📊 The Master Matrix (Current Consensus) — 6 VRAM Tiers</summary>

**How to read the matrix:**

- **Status** (confidence): ✅ = OP personally tested & verified · 📡 = community-reported (single source) · 📡📡 = community-reported (multiple sources) · 📐 = calculated from architecture specs (not yet tested)
- **Lifecycle** (recommendation): 🟢 Current = actively recommended, up to date · 🟡 Watch = newer alternative emerging, still viable · 🔴 Superseded = replaced by a better option in this matrix

> **🔀 Hybrid / Offload Setups:** With engines like **Strata** and **Radiance**, the VRAM tier alone no longer defines what you can run. A 125B MoE model in IQ3_S runs on a single 24GB GPU + 128GB RAM (Kif's setup). A Flash-Next W4A16 runs on 4x AMD v620 with 50GB system RAM for the PLE table (SgtAwesomesauce). When you see a "hybrid" entry, the VRAM column shows GPU memory only — total system memory requirement is noted in the use case or setup notes.

<details>
<summary>
Tier 1: ≤ 16 GB VRAM (Single Consumer GPU / Entry Workstation)
</summary>
<p><em>Target Hardware: RTX 4060 Ti 16GB, RTX 3060 12GB (tight), RTX A2000, RX 7600 XT, Radeon VII 16GB, Apple 16GB Unified.</em></p>
<div class="md-table">
<table>
<thead>
<tr>
<th style="text-align:left">Status</th>
<th style="text-align:left">Model &amp; Base Repo</th>
<th style="text-align:left">Preferred Package / Quant</th>
<th style="text-align:left">Weight Precision</th>
<th style="text-align:left">Static Model VRAM</th>
<th style="text-align:left">Usable KV Headroom</th>
<th style="text-align:left">Max Native Context</th>
<th style="text-align:left">Max YaRN / RoPE Context</th>
<th style="text-align:left">Best Use Case</th>
<th style="text-align:left">Lifecycle</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left">✅</td>
<td style="text-align:left"><a href="https://huggingface.co/ornith-ai/Ornith-1.5-9B" rel="noopener nofollow ugc">Ornith-1.5-9B</a></td>
<td style="text-align:left"><a href="https://huggingface.co/letechlead/Ornith-1.5-9B-INT4-W4A16-AutoRound" rel="noopener nofollow ugc">letechlead/Ornith-1.5-9B-INT4-W4A16-AutoRound</a></td>
<td style="text-align:left">W4A16 (INT4 weights, FP16 activations)</td>
<td style="text-align:left">~5.6 GB</td>
<td style="text-align:left">~9.5 GB</td>
<td style="text-align:left"><strong>256k</strong></td>
<td style="text-align:left"><strong>1m</strong></td>
<td style="text-align:left">General Reasoning, Coding, Long Context</td>
<td style="text-align:left">🟢 Current</td>
</tr>
<tr>
<td style="text-align:left">📡📡</td>
<td style="text-align:left"><a href="https://huggingface.co/Qwen/Qwen3.5-4B" rel="noopener nofollow ugc">Qwen3.5-4B</a></td>
<td style="text-align:left"><a href="https://huggingface.co/bartowski/Qwen_Qwen3.5-4B-GGUF" rel="noopener nofollow ugc">bartowski/Qwen_Qwen3.5-4B-GGUF (Q4_K_M)</a></td>
<td style="text-align:left">Q4_K_M (GGUF)</td>
<td style="text-align:left">~5.4 GB</td>
<td style="text-align:left">~10.6 GB</td>
<td style="text-align:left"><strong>65k</strong></td>
<td style="text-align:left">N/A</td>
<td style="text-align:left">Fast Generalist, Always-Loaded Resident (96.4 tok/s on Radeon VII)</td>
<td style="text-align:left">🟢 Current</td>
</tr>
<tr>
<td style="text-align:left">📡</td>
<td style="text-align:left"><a href="https://huggingface.co/samuelcardillo/Carnice-Qwen3.6-MoE-35B-A3B" rel="noopener nofollow ugc">Carnice-Qwen3.6-MoE-35B-A3B</a></td>
<td style="text-align:left"><a href="https://huggingface.co/samuelcardillo/Carnice-Qwen3.6-MoE-35B-A3B" rel="noopener nofollow ugc">samuelcardillo/Carnice-Qwen3.6-MoE-35B-A3B (I-Nano)</a></td>
<td style="text-align:left">I-Nano (~2.5bpw GGUF)</td>
<td style="text-align:left">~12.7 GB</td>
<td style="text-align:left">~3.3 GB</td>
<td style="text-align:left"><strong>65k</strong></td>
<td style="text-align:left">N/A</td>
<td style="text-align:left">High-Throughput MoE on 16GB (54.4 tok/s, NIAH YES at 65k)</td>
<td style="text-align:left">🟡 Watch</td>
</tr>
</tbody>
</table>
</div>
<p><em>The 16GB tier is about fitting the most intelligence into the least silicon. Ornith-1.5-9B gives you the best reasoning-per-GB with 256k native context. The MoE options (Carnice, Gemma-4-E4B) trade some peak quality for dramatically higher throughput — ideal for always-loaded server residents. If you need 30k+ context on a dense model, the Qwen3.8-27B UD-Q2_K_XL fits but decode speed collapses to ~14 tok/s.</em></p>
</details>

<details>
<summary>
Tier 2: 16 – 24 GB VRAM (Single Prosumer GPU)
</summary>
<p><em>Target Hardware: RTX 4080 16GB, RTX 3080 20GB, RX 7900 XT 20GB, RTX A4000 16GB, Radeon Pro W7900 28GB, Apple 32GB Unified.</em></p>
<div class="md-table">
<table>
<thead>
<tr>
<th style="text-align:left">Status</th>
<th style="text-align:left">Model &amp; Base Repo</th>
<th style="text-align:left">Preferred Package / Quant</th>
<th style="text-align:left">Weight Precision</th>
<th style="text-align:left">Static Model VRAM</th>
<th style="text-align:left">Usable KV Headroom</th>
<th style="text-align:left">Max Native Context</th>
<th style="text-align:left">Max YaRN / RoPE Context</th>
<th style="text-align:left">Best Use Case</th>
<th style="text-align:left">Lifecycle</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left">✅</td>
<td style="text-align:left"><a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AutoRound" rel="noopener nofollow ugc">Swift-1.5-Qwen3.8-27b</a></td>
<td style="text-align:left"><a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AutoRound" rel="noopener nofollow ugc">ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AutoRound</a></td>
<td style="text-align:left">W4A16 (INT4 weights, FP16 activations)</td>
<td style="text-align:left">~20 GB</td>
<td style="text-align:left">~4-8 GB</td>
<td style="text-align:left"><strong>256k</strong></td>
<td style="text-align:left"><strong>1m</strong></td>
<td style="text-align:left">Heavy Code Refactoring, Logic, Agentic Workflows</td>
<td style="text-align:left">🟢 Current</td>
</tr>
<tr>
<td style="text-align:left">📐</td>
<td style="text-align:left"><a href="https://huggingface.co/google/gemma-4-26B-A4B-it" rel="noopener nofollow ugc">Gemma-4-26B-A4B-it</a></td>
<td style="text-align:left"><a href="https://huggingface.co/google/gemma-4-26B-A4B-it" rel="noopener nofollow ugc">Community W4A16 / Q4_K_M GGUF</a></td>
<td style="text-align:left">W4A16 or Q4_K_M</td>
<td style="text-align:left">~14 GB</td>
<td style="text-align:left">~10-14 GB</td>
<td style="text-align:left"><strong>256k</strong></td>
<td style="text-align:left">N/A</td>
<td style="text-align:left">Instruction Following, Analysis, MoE Efficiency</td>
<td style="text-align:left">🟢 Current</td>
</tr>
<tr>
<td style="text-align:left">📡</td>
<td style="text-align:left"><a href="https://huggingface.co/Qwen/Qwen3.6-27B" rel="noopener nofollow ugc">Qwen3.6-27B</a></td>
<td style="text-align:left"><a href="https://huggingface.co/Qwen/Qwen3.6-27B" rel="noopener nofollow ugc">Qwen3.6-27b-q4_KM (Ollama/GGUF)</a></td>
<td style="text-align:left">Q4_K_M (GGUF)</td>
<td style="text-align:left">~18 GB</td>
<td style="text-align:left">~4-8 GB</td>
<td style="text-align:left"><strong>128k</strong></td>
<td style="text-align:left">N/A</td>
<td style="text-align:left">Document Q&amp;A, Deep Research, Creative Writing (52k stable on 20GB)</td>
<td style="text-align:left">🟡 Watch</td>
</tr>
</tbody>
</table>
</div>
<p><em>The new 16-24GB tier captures the sweet spot for single prosumer cards. Swift-1.5-Qwen3.8-27b in W4A16 is the headline pick — full 256k context with room to spare on a 24GB card. Gemma-4-26B-A4B-it gives you MoE efficiency (only 4B active params) for faster inference when you don't need dense-model quality. Ollama users can grab Qwen3.6-27b Q4_K_M for a zero-config start.</em></p>
</details>

<details>
<summary>
Tier 3: 24 – 32 GB VRAM (Dual 16GB / Single 24-32GB)
</summary>
<p><em>Target Hardware: 2x 16GB GPUs, RTX 3090/4090 24GB, RX 7900 XTX 24GB, 2x RTX A4000, RTX A5000 24GB, 36GB Mac Unified.</em></p>
<div class="md-table">
<table>
<thead>
<tr>
<th style="text-align:left">Status</th>
<th style="text-align:left">Model &amp; Base Repo</th>
<th style="text-align:left">Preferred Package / Quant</th>
<th style="text-align:left">Weight Precision</th>
<th style="text-align:left">Static Model VRAM</th>
<th style="text-align:left">Usable KV Headroom</th>
<th style="text-align:left">Max Native Context</th>
<th style="text-align:left">Max YaRN / RoPE Context</th>
<th style="text-align:left">Best Use Case</th>
<th style="text-align:left">Lifecycle</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left">✅</td>
<td style="text-align:left"><a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AutoRound" rel="noopener nofollow ugc">Swift-1.5-Qwen3.8-27b</a></td>
<td style="text-align:left"><a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AutoRound" rel="noopener nofollow ugc">ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AutoRound</a></td>
<td style="text-align:left">W4A16 (INT4 weights, FP16 activations)</td>
<td style="text-align:left">~20 GB</td>
<td style="text-align:left">~10-18 GB</td>
<td style="text-align:left"><strong>256k</strong></td>
<td style="text-align:left"><strong>1m</strong></td>
<td style="text-align:left">Heavy Code Refactoring, Deep Codebase Context, Agentic Coding</td>
<td style="text-align:left">🟢 Current</td>
</tr>
<tr>
<td style="text-align:left">📡</td>
<td style="text-align:left"><a href="https://huggingface.co/d0xin/Swift-Qwen3.8-27B-Uncensored-FP8" rel="noopener nofollow ugc">Swift-Qwen3.8-27B-Uncensored-FP8</a></td>
<td style="text-align:left"><a href="https://huggingface.co/d0xin/Swift-Qwen3.8-27B-Uncensored-FP8" rel="noopener nofollow ugc">d0xin/Swift-Qwen3.8-27B-Uncensored-FP8</a></td>
<td style="text-align:left">FP8 (native)</td>
<td style="text-align:left">~28 GB</td>
<td style="text-align:left">~0-4 GB (tight)</td>
<td style="text-align:left"><strong>256k</strong></td>
<td style="text-align:left"><strong>1m</strong></td>
<td style="text-align:left">Uncensored Coding, Security Research (120t/s on 2x R9700)</td>
<td style="text-align:left">🟢 Current</td>
</tr>
<tr>
<td style="text-align:left">📐</td>
<td style="text-align:left"><a href="https://huggingface.co/google/gemma-4-26B-A4B-it" rel="noopener nofollow ugc">Gemma-4-26B-A4B-it</a></td>
<td style="text-align:left"><a href="https://huggingface.co/google/gemma-4-26B-A4B-it" rel="noopener nofollow ugc">Community W4A16 / AutoRound INT4</a></td>
<td style="text-align:left">W4A16</td>
<td style="text-align:left">~14 GB</td>
<td style="text-align:left">~18-28 GB</td>
<td style="text-align:left"><strong>256k</strong></td>
<td style="text-align:left">N/A</td>
<td style="text-align:left">Instruction Following, Analysis, Long Context</td>
<td style="text-align:left">🟢 Current</td>
</tr>
<tr>
<td style="text-align:left">📡</td>
<td style="text-align:left"><a href="https://huggingface.co/deepseek-ai/DeepSeek-4.1-Flash" rel="noopener nofollow ugc">DeepSeek-4.1-Flash</a></td>
<td style="text-align:left"><a href="https://huggingface.co/deepseek-ai/DeepSeek-4.1-Flash" rel="noopener nofollow ugc">NVFP4 (medium) / W4A16</a></td>
<td style="text-align:left">NVFP4</td>
<td style="text-align:left">~28 GB</td>
<td style="text-align:left">~0-8 GB (tight)</td>
<td style="text-align:left"><strong>256k</strong></td>
<td style="text-align:left"><strong>1m</strong></td>
<td style="text-align:left">Top eval performer for agentic coding (lhl: "slightly edged out qwen38fn, glm53f in quality AND speed")</td>
<td style="text-align:left">🟢 Current</td>
</tr>
</tbody>
</table>
</div>
<p><em>At 24-32GB you unlock serious agentic workloads. The Swift-1.5-27b W4A16 is the default recommendation — 256k context, 1m with YaRN, excellent code quality. The Uncensored-FP8 variant is the pick for security research and anything where standard alignment gets in the way. Gemma-4-26B remains the best instruction-follower in the tier if your workload is analysis rather than generation.</em></p>
</details>

<details>
<summary>
Tier 4: 48 – 64 GB VRAM (Dual 24-32GB / Quad 16GB)
</summary>
<p><em>Target Hardware: 2x RTX 3090/4090 (48GB), 2x RX 7900 XTX (48GB), 4x RTX A4000 (64GB), 2x MI210 (64GB), Mac Studio 64GB.</em></p>
<div class="md-table">
<table>
<thead>
<tr>
<th style="text-align:left">Status</th>
<th style="text-align:left">Model &amp; Base Repo</th>
<th style="text-align:left">Preferred Package / Quant</th>
<th style="text-align:left">Weight Precision</th>
<th style="text-align:left">Static Model VRAM</th>
<th style="text-align:left">Usable KV Headroom</th>
<th style="text-align:left">Max Native Context</th>
<th style="text-align:left">Max YaRN / RoPE Context</th>
<th style="text-align:left">Best Use Case</th>
<th style="text-align:left">Lifecycle</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left">📐</td>
<td style="text-align:left"><a href="https://huggingface.co/google/gemma-4-31B-it" rel="noopener nofollow ugc">Gemma-4-31B-it</a></td>
<td style="text-align:left"><a href="https://huggingface.co/google/gemma-4-31B-it" rel="noopener nofollow ugc">Community W4A16 / AutoRound INT4</a></td>
<td style="text-align:left">W4A16</td>
<td style="text-align:left">~18 GB</td>
<td style="text-align:left">~30-46 GB</td>
<td style="text-align:left"><strong>256k</strong></td>
<td style="text-align:left"><strong>1m</strong></td>
<td style="text-align:left">Long Document Ingestion</td>
<td style="text-align:left">🟢 Current</td>
</tr>
<tr>
<td style="text-align:left">📡</td>
<td style="text-align:left"><a href="https://huggingface.co/ornith-ai/Ornith-1.5-35B-A3B" rel="noopener nofollow ugc">Ornith-1.5-35B-A3B</a></td>
<td style="text-align:left"><a href="https://huggingface.co/SergiioB/Ornith-1.5-35B-A3B-AutoRound-W4A16-sym-G128-MTP-BF16" rel="noopener nofollow ugc">SergiioB/Ornith-1.5-35B-A3B-AutoRound-W4A16-sym-G128-MTP-BF16</a></td>
<td style="text-align:left">W4A16 sym G128 + MTP (BF16)</td>
<td style="text-align:left">~22 GB</td>
<td style="text-align:left">~26-42 GB</td>
<td style="text-align:left"><strong>256k</strong></td>
<td style="text-align:left"><strong>1m</strong></td>
<td style="text-align:left">High-Throughput Reasoning (MTP speculative)</td>
<td style="text-align:left">🟢 Current</td>
</tr>
<tr>
<td style="text-align:left">✅</td>
<td style="text-align:left"><a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AutoRound" rel="noopener nofollow ugc">Swift-1.5-Qwen3.8-27b</a></td>
<td style="text-align:left"><a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AutoRound" rel="noopener nofollow ugc">ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AutoRound</a></td>
<td style="text-align:left">W4A16 (INT4 weights, FP16 activations)</td>
<td style="text-align:left">~20 GB</td>
<td style="text-align:left">~28-44 GB</td>
<td style="text-align:left"><strong>256k</strong></td>
<td style="text-align:left"><strong>1m</strong></td>
<td style="text-align:left">Deep Codebase Context, Multi-Agent Serving</td>
<td style="text-align:left">🟢 Current</td>
</tr>
<tr>
<td style="text-align:left">📡</td>
<td style="text-align:left"><a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AutoRound" rel="noopener nofollow ugc">Swift-1.5-Qwen3.8-27b (FP8)</a></td>
<td style="text-align:left"><a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AutoRound" rel="noopener nofollow ugc">FP8 native (via vLLM)</a></td>
<td style="text-align:left">FP8 (native)</td>
<td style="text-align:left">~28 GB</td>
<td style="text-align:left">~20-36 GB</td>
<td style="text-align:left"><strong>256k</strong></td>
<td style="text-align:left"><strong>1m</strong></td>
<td style="text-align:left">Maximum Speed/Quality on Ada/Hopper (256k ctx verified)</td>
<td style="text-align:left">🟢 Current</td>
</tr>
<tr>
<td style="text-align:left">📡</td>
<td style="text-align:left"><a href="https://huggingface.co/bartowski/Qwen3.8-Flash-Next-GGUF" rel="noopener nofollow ugc">Qwen3.8-Flash-Next (Q4_K_M GGUF)</a></td>
<td style="text-align:left"><a href="https://huggingface.co/bartowski/Qwen3.8-Flash-Next-GGUF" rel="noopener nofollow ugc">bartowski/Qwen3.8-Flash-Next-GGUF (Q4_K_M)</a></td>
<td style="text-align:left">Q4_K_M (GGUF)</td>
<td style="text-align:left">~48 GB (2x W7900)</td>
<td style="text-align:left">~262k stable</td>
<td style="text-align:left"><strong>256k</strong></td>
<td style="text-align:left"><strong>1m</strong></td>
<td style="text-align:left">Coding on AMD dual-GPU (PawingUnplug: 35t/s, 750W)</td>
<td style="text-align:left">🟢 Current</td>
</tr>
</tbody>
</table>
</div>
<p><em>48-64GB is where multi-GPU consumer setups (2x 3090/4090, 2x 7900 XTX) become genuinely powerful. You can run a 27B model with 30+ GB of KV headroom — meaning 256k+ context at full precision. The Ornith-1.5-35B-A3B with MTP speculative decoding is the throughput king. FP8 Swift-1.5 on Ada/Hopper cards gives you the best speed/quality ratio if your GPU supports it.</em></p>
</details>

<details>
<summary>
Tier 5: 96 – 128 GB VRAM (Workstation Multi-GPU / High-Density Compute)
</summary>
<p><em>Target Hardware: 4x–6x 24GB GPUs, 8x RTX A4000 (128GB), 4x MI210 (128GB), 2x A100 80GB, 2x 48GB Ada/Ampere.</em></p>
<div class="md-table">
<table>
<thead>
<tr>
<th style="text-align:left">Status</th>
<th style="text-align:left">Model &amp; Base Repo</th>
<th style="text-align:left">Preferred Package / Quant</th>
<th style="text-align:left">Weight Precision</th>
<th style="text-align:left">Static Model VRAM</th>
<th style="text-align:left">Usable KV Headroom</th>
<th style="text-align:left">Max Native Context</th>
<th style="text-align:left">Max YaRN / RoPE Context</th>
<th style="text-align:left">Best Use Case</th>
<th style="text-align:left">Lifecycle</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left">✅</td>
<td style="text-align:left"><a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AutoRound" rel="noopener nofollow ugc">Swift-1.5-Qwen3.8-27b</a></td>
<td style="text-align:left"><a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AutoRound" rel="noopener nofollow ugc">ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AutoRound</a></td>
<td style="text-align:left">W4A16 (INT4 weights, FP16 activations)</td>
<td style="text-align:left">~20 GB</td>
<td style="text-align:left">~76-108 GB</td>
<td style="text-align:left"><strong>256k</strong></td>
<td style="text-align:left"><strong>1m</strong></td>
<td style="text-align:left">Extreme RAG &amp; Repository Ingestion, Multi-Client Serving</td>
<td style="text-align:left">🟢 Current</td>
</tr>
<tr>
<td style="text-align:left">📐</td>
<td style="text-align:left"><a href="https://huggingface.co/Qwen/Qwen3.8-Flash-Next" rel="noopener nofollow ugc">Qwen3.8-Flash-Next</a></td>
<td style="text-align:left"><a href="https://huggingface.co/Intel/Qwen3.8-Flash-Next-W4A16-RTN-AutoRound" rel="noopener nofollow ugc">Intel/Qwen3.8-Flash-Next-W4A16-RTN-AutoRound</a></td>
<td style="text-align:left">W4A16 RTN + n-gram table</td>
<td style="text-align:left">~168 GB (pure VRAM) / ~73 GB (host offload)</td>
<td style="text-align:left">~23-55 GB*</td>
<td style="text-align:left"><strong>256k</strong></td>
<td style="text-align:left"><strong>1m</strong></td>
<td style="text-align:left">Fast Agentic Workflows, Speculative Decoding</td>
<td style="text-align:left">🟡 Watch</td>
</tr>
<tr>
<td style="text-align:left">✅</td>
<td style="text-align:left"><a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-Flash-Next-W4A16-AutoRound" rel="noopener nofollow ugc">Swift-1.5-Qwen3.8-Flash-Next</a></td>
<td style="text-align:left"><a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-Flash-Next-W4A16-AutoRound" rel="noopener nofollow ugc">ukisai/Swift-1.5-Qwen3.8-Flash-Next-W4A16-AutoRound</a></td>
<td style="text-align:left">W4A16 + n-gram table</td>
<td style="text-align:left">~168 GB (pure VRAM) / ~73 GB (host offload)</td>
<td style="text-align:left">~23-55 GB*</td>
<td style="text-align:left"><strong>256k</strong></td>
<td style="text-align:left"><strong>1m</strong></td>
<td style="text-align:left">Swift Fine-tune: Fast Agentic + Coding, Speculative Decoding</td>
<td style="text-align:left">🟢 Current</td>
</tr>
<tr>
<td style="text-align:left">📡</td>
<td style="text-align:left"><a href="https://huggingface.co/ornith-ai/Ornith-1.5-35B-A3B" rel="noopener nofollow ugc">Ornith-1.5-35B-A3B</a></td>
<td style="text-align:left"><a href="https://huggingface.co/SergiioB/Ornith-1.5-35B-A3B-AutoRound-W4A16-sym-G128-MTP-BF16" rel="noopener nofollow ugc">SergiioB/Ornith-1.5-35B-A3B-AutoRound-W4A16-sym-G128-MTP-BF16</a></td>
<td style="text-align:left">W4A16 sym G128 + MTP (BF16)</td>
<td style="text-align:left">~22 GB</td>
<td style="text-align:left">~74-106 GB</td>
<td style="text-align:left"><strong>256k</strong></td>
<td style="text-align:left"><strong>1m</strong></td>
<td style="text-align:left">High-Throughput Production Serving, Multi-Tenant</td>
<td style="text-align:left">🟢 Current</td>
</tr>
<tr>
<td style="text-align:left">📡📡</td>
<td style="text-align:left"><a href="https://huggingface.co/Qwen/Qwen3.8-Flash-Next" rel="noopener nofollow ugc">Qwen3.8-Flash-Next (NVFP4)</a></td>
<td style="text-align:left"><a href="https://huggingface.co/Qwen/Qwen3.8-Flash-Next" rel="noopener nofollow ugc">NVFP4 (medium)</a></td>
<td style="text-align:left">NVFP4</td>
<td style="text-align:left">~96 GB</td>
<td style="text-align:left">~32-64 GB</td>
<td style="text-align:left"><strong>256k</strong></td>
<td style="text-align:left"><strong>1m</strong></td>
<td style="text-align:left">Top pick at &lt;128GB tier (lhl: "run a lot of tokens through this, extremely fast, quite a good coder")</td>
<td style="text-align:left">🟢 Current</td>
</tr>
<tr>
<td style="text-align:left">📡</td>
<td style="text-align:left"><a href="https://huggingface.co/wtdcode/Qwen3.8-Flash-Next-AWQ-W4A16" rel="noopener nofollow ugc">Qwen3.8-Flash-Next (W4A16 AWQ)</a></td>
<td style="text-align:left"><a href="https://huggingface.co/wtdcode/Qwen3.8-Flash-Next-AWQ-W4A16" rel="noopener nofollow ugc">wtdcode/Qwen3.8-Flash-Next-AWQ-W4A16</a></td>
<td style="text-align:left">W4A16 AWQ</td>
<td style="text-align:left">~73 GB + 50 GB system RAM</td>
<td style="text-align:left">~840k tokens total capacity</td>
<td style="text-align:left"><strong>256k</strong></td>
<td style="text-align:left"><strong>1m</strong></td>
<td style="text-align:left">AMD v620 4x deployment, agentic coding (SgtAwesomesauce: 68-92 tok/s, 1200 prefill, 3.5s TTFT)</td>
<td style="text-align:left">🟢 Current</td>
</tr>
</tbody>
</table>
</div>
<p><em>96-128GB transforms local inference into a production serving environment. The Swift-1.5-27b becomes trivially easy to run with 100+ GB of KV headroom — you're no longer context-limited, you're client-limited. The Flash-Next models unlock speculative decoding with n-gram lookahead, but require either 128GB system RAM (offload mode) or full 168GB VRAM (pure mode). This is the tier for multi-tenant serving and extreme RAG.</em></p>
<p>*See "Technical Architecture Note" below for Qwen Flash-Next n-gram table offload details.</p>
</details>

<details>
<summary>
Tier 6: 196 – 256 GB+ VRAM (Enterprise Nodes &amp; Full Workstation Clusters)
</summary>
<p><em>Target Hardware: 8x 24GB GPUs (192GB), 8x 32GB/48GB/80GB Enterprise Nodes, 4x MI210 (256GB), 8x A100/H100.</em></p>
<div class="md-table">
<table>
<thead>
<tr>
<th style="text-align:left">Status</th>
<th style="text-align:left">Model &amp; Base Repo</th>
<th style="text-align:left">Preferred Package / Quant</th>
<th style="text-align:left">Weight Precision</th>
<th style="text-align:left">Static Model VRAM</th>
<th style="text-align:left">Usable KV Headroom</th>
<th style="text-align:left">Max Native Context</th>
<th style="text-align:left">Max YaRN / RoPE Context</th>
<th style="text-align:left">Best Use Case</th>
<th style="text-align:left">Lifecycle</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left">📐</td>
<td style="text-align:left"><a href="https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-Vision-Exp" rel="noopener nofollow ugc">DeepSeek-V4-Flash-Vision-Exp</a></td>
<td style="text-align:left"><a href="https://huggingface.co/Intel/DeepSeek-V4-Flash-Vision-Exp-W4A16-AutoRound" rel="noopener nofollow ugc">Intel/DeepSeek-V4-Flash-Vision-Exp-W4A16-AutoRound</a></td>
<td style="text-align:left">W4A16 (INT4 weights, FP16 activations)</td>
<td style="text-align:left">~156 GB</td>
<td style="text-align:left">~40-100 GB</td>
<td style="text-align:left"><strong>1m</strong></td>
<td style="text-align:left">N/A</td>
<td style="text-align:left">Multimodal Document &amp; Video Analysis</td>
<td style="text-align:left">🟢 Current</td>
</tr>
<tr>
<td style="text-align:left">📐</td>
<td style="text-align:left"><a href="https://huggingface.co/zai-org/GLM-5.3-Flash" rel="noopener nofollow ugc">GLM-5.3-Flash</a></td>
<td style="text-align:left"><a href="https://huggingface.co/Intel/GLM-5.3-Flash-W4A16-AutoRound" rel="noopener nofollow ugc">Intel/GLM-5.3-Flash-W4A16-AutoRound</a></td>
<td style="text-align:left">W4A16 (INT4 weights, FP16 activations)</td>
<td style="text-align:left">~176 GB</td>
<td style="text-align:left">~20-80 GB</td>
<td style="text-align:left"><strong>1m</strong></td>
<td style="text-align:left">N/A</td>
<td style="text-align:left">Complex Agent Systems</td>
<td style="text-align:left">🟢 Current</td>
</tr>
<tr>
<td style="text-align:left">✅</td>
<td style="text-align:left"><a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-Flash-Next-W4A16-AutoRound" rel="noopener nofollow ugc">Swift-1.5-Qwen3.8-Flash-Next</a></td>
<td style="text-align:left"><a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-Flash-Next-W4A16-AutoRound" rel="noopener nofollow ugc">ukisai/Swift-1.5-Qwen3.8-Flash-Next-W4A16-AutoRound</a></td>
<td style="text-align:left">W4A16 + n-gram table</td>
<td style="text-align:left">~168 GB</td>
<td style="text-align:left">~28-88 GB*</td>
<td style="text-align:left"><strong>256k</strong></td>
<td style="text-align:left"><strong>1m</strong></td>
<td style="text-align:left">Multi-Million Token Ingestion, Swift Fine-tune Agentic</td>
<td style="text-align:left">🟢 Current</td>
</tr>
<tr>
<td style="text-align:left">📐</td>
<td style="text-align:left"><a href="https://huggingface.co/Qwen/Qwen3.8-Flash-Next" rel="noopener nofollow ugc">Qwen3.8-Flash-Next</a></td>
<td style="text-align:left"><a href="https://huggingface.co/Intel/Qwen3.8-Flash-Next-W4A16-RTN-AutoRound" rel="noopener nofollow ugc">Intel/Qwen3.8-Flash-Next-W4A16-RTN-AutoRound</a></td>
<td style="text-align:left">W4A16 RTN + n-gram table</td>
<td style="text-align:left">~168 GB</td>
<td style="text-align:left">~28-88 GB*</td>
<td style="text-align:left"><strong>256k</strong></td>
<td style="text-align:left"><strong>1m</strong></td>
<td style="text-align:left">Multi-Million Token Ingestion</td>
<td style="text-align:left">🟡 Watch</td>
</tr>
<tr>
<td style="text-align:left">✅</td>
<td style="text-align:left"><a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AutoRound" rel="noopener nofollow ugc">Swift-1.5-Qwen3.8-27b</a></td>
<td style="text-align:left"><a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AutoRound" rel="noopener nofollow ugc">ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AutoRound</a></td>
<td style="text-align:left">W4A16 (INT4 weights, FP16 activations)</td>
<td style="text-align:left">~20 GB</td>
<td style="text-align:left">~176-236 GB</td>
<td style="text-align:left"><strong>256k</strong></td>
<td style="text-align:left"><strong>1m</strong></td>
<td style="text-align:left">Complete Library &amp; Git Ingestion, Multi-Client Farm</td>
<td style="text-align:left">🟢 Current</td>
</tr>
<tr>
<td style="text-align:left">📡</td>
<td style="text-align:left"><a href="https://huggingface.co/unsloth/DeepSeek-V4-Pro-0813-GGUF" rel="noopener nofollow ugc">DeepSeek-V4-Pro-0813</a></td>
<td style="text-align:left"><a href="https://huggingface.co/unsloth/DeepSeek-V4-Pro-0813-GGUF" rel="noopener nofollow ugc">unsloth/DeepSeek-V4-Pro-0813-GGUF (UD-Q8_K_XL)</a></td>
<td style="text-align:left">Q8_K_XL (GGUF)</td>
<td style="text-align:left">~400 GB+ (CPU+GPU hybrid)</td>
<td style="text-align:left">N/A (RAM-bound)</td>
<td style="text-align:left"><strong>16k</strong></td>
<td style="text-align:left">N/A</td>
<td style="text-align:left">Niche Translation, Ultra-Long Document Fidelity</td>
<td style="text-align:left">🟢 Current</td>
</tr>
</tbody>
</table>
</div>
<p><em>196GB+ is enterprise territory. You're running models that simply cannot fit on consumer hardware — 671B parameter MoE models, multimodal vision models, and the full Flash-Next stack. The DeepSeek-V4-Pro in Q8_K_XL on a CPU+GPU hybrid (1TB RAM) is the niche king for domain-specific tasks. For general workloads, the Swift-1.5-27b with 200+ GB of KV headroom can ingest entire codebases and document libraries in a single context window.</em></p>
<p>*See "Technical Architecture Note" below for Qwen Flash-Next n-gram table offload details.</p>
</details>

</details>

<details>
<summary>⚠️ Technical Architecture Note: Qwen Flash-Next N-gram Lookahead &amp; Memory Offload</summary>
<p>Qwen3.8-Flash-Next (and the Swift-1.5 fine-tune) implements a high-throughput n-gram lookahead speculative table. This structure requires approximately <strong>95 GB of unquantized index memory</strong> in addition to the <strong>~73 GB base W4A16 model weights</strong>:</p>
<ol>
<li><strong>Host RAM Offload Mode (Tier 5 / 96-128 GB VRAM):</strong>
<ul>
<li><strong>VRAM Allocation:</strong> Only the ~73 GB model weights live on the GPUs.</li>
<li><strong>System RAM Requirement:</strong> The ~95 GB n-gram table is mapped directly to pinned host memory over PCIe. Your host machine must have at least 128 GB of system RAM.</li>
<li><strong>Bus Requirement:</strong> PCIe Gen4 x4, PCIe Gen3 x8 or higher per card is strongly recommended to prevent host-to-device speculative verification latency from bottlenecking token throughput.</li>
</ul>
</li>
<li><strong>Pure VRAM Mode (Tier 6 / 196+ GB VRAM):</strong>
<ul>
<li><strong>VRAM Allocation:</strong> Can load both the weights (~73 GB) and the n-gram table (~95 GB) entirely in GPU memory, consuming ~168 GB of static VRAM before allocating the first token of KV cache.</li>
</ul>
</li>
</ol>
<p><strong>Swift-1.5-Qwen3.8-Flash-Next</strong> inherits this architecture. The Swift fine-tune modifies the language model weights but retains the n-gram speculative table structure, so the same offload considerations apply.</p>
</details>

<details>
<summary>🔬 Community Verified Data — Real-World Benchmarks</summary>

<details>
<summary>Radeon VII 16GB HBM2 — llama-swap (s1ugh34d)</summary>

*Tested: 2026-09-18. Backend: llama-swap → llama.cpp (ROCm, gfx906). 32-core EPYC host, 67GB RAM.*

<div class="md-table">
<table>
<thead>
<tr>
<th style="text-align:left">Model</th>
<th style="text-align:left">Quant</th>
<th style="text-align:left">Decode tok/s</th>
<th style="text-align:left">Prefill tok/s</th>
<th style="text-align:left">VRAM Peak</th>
<th style="text-align:left">Cold-Load TTFT</th>
<th style="text-align:left">Power Peak</th>
<th style="text-align:left">NIAH 65k</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left">Carnice-Qwen3.6-MoE-35B-A3B</td>
<td style="text-align:left">I-Nano</td>
<td style="text-align:left"><strong>54.4</strong></td>
<td style="text-align:left">215</td>
<td style="text-align:left">12.7 GB</td>
<td style="text-align:left">19.3 s</td>
<td style="text-align:left">150 W</td>
<td style="text-align:left">YES</td>
</tr>
<tr>
<td style="text-align:left">Gemma-4-E4B-Opus</td>
<td style="text-align:left">Q4_K_M</td>
<td style="text-align:left"><strong>86.7</strong></td>
<td style="text-align:left">408</td>
<td style="text-align:left">4.9 GB</td>
<td style="text-align:left">0.2 s</td>
<td style="text-align:left">214 W</td>
<td style="text-align:left">YES (49k)</td>
</tr>
<tr>
<td style="text-align:left">Qwen3.8-27B</td>
<td style="text-align:left">UD-Q2_K_XL</td>
<td style="text-align:left"><strong>13.9</strong></td>
<td style="text-align:left">79</td>
<td style="text-align:left">13.8 GB</td>
<td style="text-align:left">4.4 s</td>
<td style="text-align:left">233 W</td>
<td style="text-align:left">YES (49k)</td>
</tr>
<tr>
<td style="text-align:left">DeepSeek-R1-0528-Qwen3-8B</td>
<td style="text-align:left">Q4_K_M</td>
<td style="text-align:left"><strong>84.4</strong></td>
<td style="text-align:left">490</td>
<td style="text-align:left">7.4 GB</td>
<td style="text-align:left">3.1 s</td>
<td style="text-align:left">268 W</td>
<td style="text-align:left">YES (16k cap)</td>
</tr>
<tr>
<td style="text-align:left">Qwen3.5-4B</td>
<td style="text-align:left">Q4_K_M</td>
<td style="text-align:left"><strong>96.4</strong></td>
<td style="text-align:left">468</td>
<td style="text-align:left">5.4 GB</td>
<td style="text-align:left">5.0 s</td>
<td style="text-align:left">225 W</td>
<td style="text-align:left">YES (65k)</td>
</tr>
</tbody>
</table>
</div>

**Key finding:** VRAM barely moved from 8k→65k context on loaded models (e.g., Qwen3.5-4B: +88 MB). Weights dominate; KV cache is aggressively quantized server-side (Q8/FP8). These are throughput-optimized, not precision-RAG setups.

</details>

<details>
<summary>Dual R9700 48GB — vLLM (digitalscream)</summary>

*Model: d0xin/Swift-Qwen3.8-27B-Uncensored-FP8. Backend: vLLM (magiccodingman/vllm-radiance, adaptive MTP=8).*
- **120 tok/s** code generation, **70 tok/s** chat
- Stable context: ~240k tokens
- KV cache: FP16 (unquantized)
- Use case: Coding, security research (DoS attack tracking)

</details>

<details>
<summary>96GB Dual-System — vLLM + LiteLLM (Patrick_M)</summary>

*Model: Swift-Qwen3.8-27B FP8. Hardware: 2x 96GB VRAM systems. Load-balanced via LiteLLM.*
- Context: 256k
- "So much faster and more responsive than standard Qwen3.8"
- Multi-agent workload distribution across systems

</details>

<details>
<summary>CPU+GPU Hybrid 1TB RAM — llama.cpp / Colibri (manoreken2)</summary>

*Hardware: 1x RTX 5090 (32GB) + IceLake Xeon (1024GB RAM). Niche: 2500–1000 year old Chinese historical documents → Modern Japanese.*

<div class="md-table">
<table>
<thead>
<tr>
<th style="text-align:left">Model</th>
<th style="text-align:left">Quant</th>
<th style="text-align:left">Throughput</th>
<th style="text-align:left">Verdict</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left">DeepSeek-R1:671B-0528</td>
<td style="text-align:left">Q8_0</td>
<td style="text-align:left">~1 tok/s</td>
<td style="text-align:left">Best fidelity, occasional nonsense tangents</td>
</tr>
<tr>
<td style="text-align:left">DeepSeek-V4-Pro-0813</td>
<td style="text-align:left">UD-Q8_K_XL</td>
<td style="text-align:left">~1 tok/s</td>
<td style="text-align:left"><strong>Best overall</strong> — faithful, less clutter</td>
</tr>
<tr>
<td style="text-align:left">DeepSeek-V3.1 Terminus</td>
<td style="text-align:left">Q8_0</td>
<td style="text-align:left">~1 tok/s</td>
<td style="text-align:left">Good</td>
</tr>
<tr>
<td style="text-align:left">DeepSeek-V3.2</td>
<td style="text-align:left">UD-Q8_K_XL</td>
<td style="text-align:left">~1 tok/s</td>
<td style="text-align:left">Literal translation style, hard to read</td>
</tr>
<tr>
<td style="text-align:left">GLM-5.2</td>
<td style="text-align:left">UD-Q6_K_XL</td>
<td style="text-align:left">~1 tok/s</td>
<td style="text-align:left">Literal, not suitable</td>
</tr>
<tr>
<td style="text-align:left">Kimi-K2.6</td>
<td style="text-align:left">UD-Q8_K_XL</td>
<td style="text-align:left">~1 tok/s</td>
<td style="text-align:left">Youth slang tone, not suitable</td>
</tr>
<tr>
<td style="text-align:left">Qwen3:235B-A22B-Thinking</td>
<td style="text-align:left">Q4</td>
<td style="text-align:left">~1 tok/s</td>
<td style="text-align:left">Sloppy, many incorrect outputs</td>
</tr>
<tr>
<td style="text-align:left">Nemotron-3-Super:120B</td>
<td style="text-align:left">—</td>
<td style="text-align:left">—</td>
<td style="text-align:left">Unusable for this task</td>
</tr>
<tr>
<td style="text-align:left">GPT-OSS:120B</td>
<td style="text-align:left">—</td>
<td style="text-align:left">—</td>
<td style="text-align:left">Lacks Asian historical knowledge</td>
</tr>
</tbody>
</table>
</div>

**Lesson:** For ultra-niche domain translation, model selection matters far more than parameter count. A focused 671B model with the right training data outperforms larger generalists.

</details>

<details>
<summary>2x R9700 64GB — llama.cpp (PawingUnplug)</summary>

*Models: Kwaipilot KAT-Coder-V2.5-Dev (Q5_K_M), Qwen3-Embedding-8B (Q8_0), Qwen3.5-9B Defiant Fable Uncensored NEO-MAX-MTP (Q8_0).*
- Context: ~262k stable, FP16 KV
- Throughput: ~50t/s chat
- Power: ~600W
- Also: 2x W7900 running Qwen3.8-Flash-Next Q4_K_M at 35t/s, 750W, 262k context

</details>

<details>
<summary>4x AMD v620 96GB — vLLM ROCm (SgtAwesomesauce)</summary>

*Model: Qwen3.8-Flash-Next W4A16 (wtdcode/AWQ variant). Backend: vLLM with custom ROCm recipe (leapdragon/vllm-rdna2-recipe).*
- Context: 245K stable, FP16/BF16 KV, total KV capacity ~840k tokens
- Throughput: 68-92 tok/s decode, 1200 tok/s prefill @ 0ctx
- TTFT cold: 3.5s
- Power: ~900W full system
- Key settings: DENSE_INT8=1, MTP=0 (collapses under multi-thread), GPUUTIL=0.98, MAXLEN=262144, PLE table ples_fp8, ~50GB system RAM
- Note: "Quantized PLE doesn't seem to have any meaningful impact on quality"

</details>

<details>
<summary>1x RTX 4090 + 128GB RAM — Strata (Kif)</summary>

*Model: Qwen3.8-Flash-Next 125B (IQ3_S GGUF, ISTA-DASLab GSQ-RCO). Backend: Strata 0.1.42 (dedicated Flash-Next engine, OpenAI/Anthropic API).*
- Hardware: RTX 4090 24GB, Ryzen 9 5900X, 128GB DDR4-3600 (4x32GB dual-rank), Samsung 990 Pro NVMe
- OS: Windows 11 + WSL2/Ubuntu 24.04 (96GB allocated via .wslconfig)
- Context: 131k configured, &gt;=106k observed in live agent sessions
- KV: int8 (engine-native quantized KV)
- Throughput: 99-128 tok/s decode (median 108), 825-3600 prefill (median ~2800 with 90% prompt cache hits)
- Power: 450W stock cap
- Architecture: 6892 experts (~13.4GB) in VRAM, rest in RAM, lookup table on NVMe. VRAM: 23471/24564 MiB. MTP=4 + lookup=3, pcie_frac 0.35.
- **Key insight:** "With hybrid offload engines (Strata), the VRAM tier alone no longer describes what actually fits — this 125B IQ3_S run is RAM+SSD-bound, not VRAM-bound."
- Prompt cache: ~90% hit rate → agent follow-ups on 50k contexts resume in 0.3-0.8s

</details>

<details>
<summary>2x R9700 64GB — Radiance 1.3.0 (digitalscream)</summary>

*Model: Swift 1.5 Flash Next (IQ4 weights, FP8 PLE). Source: https://huggingface.co/StillDeadcode/swift1.5-qwen3.8-next-flash-fp8-iq4r-moe. Backend: Radiance 1.3.0 (amdgpu).*
- Hardware: 2x R9700 32GB, Threadripper 3960X, 128GB DDR4
- Context: 262,144 configured; &gt;=200,000 tokens observed in live agent sessions
- KV: FP8
- Throughput: **200t/s+ decode** (with MTP), **5200-6200t/s prefill**
- Power: 500-600W during inference, GPUs at 330W cap each
- Setup: "Everything running in VRAM and system RAM, no disk tier"
- User quote: "This thing is nuts. It sometimes takes longer to get to the solution than 27B, but it's better at finding the RIGHT solution and much much better at understanding vaguely-defined requirements. The fact that it's hitting 200t/s+ with MTP, rather than DFlash2, is incredible in itself."

</details>

</details>

<details>
<summary>⚡ Real-World Constraints — Power, Thermals, PCIe, and Space</summary>

*VRAM is only part of the equation. Here's what actually limits real deployments:*

<div class="md-table">
<table>
<thead>
<tr>
<th style="text-align:left">Constraint</th>
<th style="text-align:left">Why It Matters</th>
<th style="text-align:left">Tier Affected</th>
<th style="text-align:left">Mitigation</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left"><strong>Power Draw</strong></td>
<td style="text-align:left">A 4090 pulls 450W under load. 4x = 1800W just for GPUs. Your PSU and electrical circuit must handle it.</td>
<td style="text-align:left">Tier 4-6</td>
<td style="text-align:left">Use W4A16 quants (lower compute = lower power). Power-limit cards to 70-80% for 20% speed loss but 40% power savings.</td>
</tr>
<tr>
<td style="text-align:left"><strong>Thermals / Noise</strong></td>
<td style="text-align:left">24GB cards run hot. 4+ GPUs in a consumer case = thermal throttling. Water cooling or server chassis needed.</td>
<td style="text-align:left">Tier 4-6</td>
<td style="text-align:left">Server-grade chassis (4U/8U), custom water loops, or blade servers. AMD MI cards are passively cooled for server use.</td>
</tr>
<tr>
<td style="text-align:left"><strong>PCIe Lanes</strong></td>
<td style="text-align:left">Multi-GPU tensor parallelism needs NVLink (NVIDIA) or xGMI (AMD) for fast inter-GPU comms. PCIe 4.0 x16 per card is the minimum.</td>
<td style="text-align:left">Tier 4-6</td>
<td style="text-align:left">Check motherboard GPU slot spacing. Not all boards support 4x x16. Consumer boards often drop to x8/x8 with 2+ cards.</td>
</tr>
<tr>
<td style="text-align:left"><strong>System RAM</strong></td>
<td style="text-align:left">Host RAM offload (Flash-Next n-gram table, CPU+GPU hybrid) needs 128GB-1TB+ system RAM.</td>
<td style="text-align:left">Tier 5-6</td>
<td style="text-align:left">DDR4/DDR5 ECC for server builds. Apple unified memory sidesteps this entirely.</td>
</tr>
<tr>
<td style="text-align:left"><strong>Physical Space</strong></td>
<td style="text-align:left">8-GPU rigs need 8U+ racks or large ATX cases. Consumer builds top out at 2-4 GPUs practically.</td>
<td style="text-align:left">Tier 5-6</td>
<td style="text-align:left">Server chassis, blade enclosures, or Mac Studio (dense unified memory).</td>
</tr>
<tr>
<td style="text-align:left"><strong>OS / Driver Maturity</strong></td>
<td style="text-align:left">ROCm lags CUDA by 6-12 months for new features. Vulkan is universal but slower. Metal is Apple-only.</td>
<td style="text-align:left">All tiers</td>
<td style="text-align:left">NVIDIA = easiest. AMD = great for inference, harder for training. Apple = zero-config but limited to Apple models.</td>
</tr>
<tr>
<td style="text-align:left"><strong>Storage / Model Downloads</strong></td>
<td style="text-align:left">A single 27B W4A16 model is ~20GB. A 671B Q8 model is ~700GB. Keep 2-4TB NVMe for model libraries.</td>
<td style="text-align:left">All tiers</td>
<td style="text-align:left">Use HuggingFace cache dirs. llama-swap auto-manages model loading/unloading.</td>
</tr>
</tbody>
</table>
</div>

</details>

<details>
<summary>📅 Changelog — Matrix Update History</summary>

*Track what changed and when. Most recent first.*

<div class="md-table">
<table>
<thead>
<tr>
<th style="text-align:left">Date</th>
<th style="text-align:left">Version</th>
<th style="text-align:left">Changes</th>
<th style="text-align:left">Trigger</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left">2026-10-12</td>
<td style="text-align:left">v2.1</td>
<td style="text-align:left">Added R9700 + AMD v620 to GPU lookup. Added Strata (hybrid offload) and Radiance (AMD) as engine options. Added NVFP4/MXFP4 emerging format note. Added DeepSeek-4.1-Flash to Tier 3, Flash-Next NVFP4 to Tier 5, Flash-Next AWQ to Tier 5, Flash-Next Q4_K_M to Tier 4. Added "Hybrid/Offload" concept note. Added 4 new community data entries (PawingUnplug, SgtAwesomesauce, Kif/Strata, digitalscream/Radiance).</td>
<td style="text-align:left">Community submissions (posts #20-#28), Strata release, NVFP4 adoption</td>
</tr>
<tr>
<td style="text-align:left">2026-09-28</td>
<td style="text-align:left">v2.0</td>
<td style="text-align:left">Added 16-24GB tier (Tier 2). Added Weight Precision column. Added GPU Quick-Lookup, Use-Case Index, Confidence Indicators, Status Badges, Tier Tradeoff Notes, Real-World Constraints, Changelog. Added Swift-1.5-Qwen3.8-27b and Swift-1.5-Qwen3.8-Flash-Next. Added AMD/Apple hardware notes. Added Non-GGUF guide.</td>
<td style="text-align:left">Community feedback (posts #3-#18), new model releases</td>
</tr>
<tr>
<td style="text-align:left">2026-09-18</td>
<td style="text-align:left">v1.0</td>
<td style="text-align:left">Initial matrix: 5 tiers, 14 model entries, KV cache rule, Qwen Flash-Next architecture note.</td>
<td style="text-align:left">OP curation</td>
</tr>
</tbody>
</table>
</div>

</details>

<details>
<summary>🔗 Related Threads on L1Techs</summary>

- [Why your local LLM feels dumber than it is](https://forum.level1techs.com/t/why-your-local-llm-feels-dumber-than-it-is/253917) — Implementation-spec impact on perceived model quality
- [Qwen3.8-Flash-Next Q6_K on 3× Radeon Instinct MI50 16GB](https://forum.level1techs.com/t/qwen3-8-flash-next-q6-k-on-3x-radeon-instinct-mi50-16gb/256455) — AMD datacenter multi-GPU
- [Dual R9700 llama.cpp Rocm tensor-split, working P2P on Proxmox, Qwen3.8-27B](https://forum.level1techs.com/t/dual-r9700-llama-cpp-rocm-tensor-split-working-p2p-on-proxmox-qwen-3-8-27b/254183) — AMD P2P on virtualized host
- [I have 4x 6000 Blackwell and serve 10 devs and 40 office workers with it](https://forum.level1techs.com/t/i-have-4x-6000-blackwell-and-serve-10-devs-and-40-office-workers-with-it/254269) — Production multi-user serving
- [Sanity check my Qwen3.8 5090 Results; new to Local AI](https://forum.level1techs.com/t/sanity-check-my-qwen-3-8-5090-results-new-to-local-ai/254299) — Consumer Blackwell benchmarks

</details>
