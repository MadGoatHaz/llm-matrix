# The Best Local LLM Matrix

**A vram-first reference for running local models on real silicon.**

This thread tracks suggested models, mapped by:

- **Usable VRAM footprint** — organized across 6 VRAM tiers, from single consumer GPUs to enterprise clusters
- **Optimal quantization architecture & weight precision** (minimum GPU compute requirement)
- **Context headroom** via unquantized KV caching

### Quick Navigation

- 📋 How This Thread Is Managed & Maintained
- ⚡ The KV Cache Quantization Rule
- 🖥️ Hardware Vendor Notes (NVIDIA / AMD / Apple)
- 📦 Running Non-GGUF Models (AutoRound / Safetensors / FP8)
- 📊 The Master Matrix (Current Consensus) — 6 VRAM Tiers
- ⚠️ Technical Architecture Note: Qwen Flash-Next N-gram Lookahead & Memory Offload
- 🔬 Community Verified Data — Real-World Benchmarks
- 🔗 Related Threads on L1Techs

<hr>

<details>
<summary>📋 How This Thread Is Managed & Maintained</summary>

1. **Weekly Rollups:** Every weekend, community submissions, poll shifts, and verified results are reviewed.
2. **Major Release Fast-Tracks:** When a significant open-weight release drops, it will be tested. Once context behavior is validated (either through hands-on testing or verified member submissions/DMs), the matrix will be updated accordingly.
3. **Direct Submissions & DMs:** If you have dialled in an unlisted model, post it using the template in Post #2 or send a DM with your suggestions.
4. **Tier Promotions:** Models that consistently receive verified community data across multiple hardware configurations are promoted from "Community Verified" into the Master Matrix.

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

</details>

<details>
<summary>📊 The Master Matrix (Current Consensus) — 6 VRAM Tiers</summary>

<details>
<summary>
Tier 1: ≤ 16 GB VRAM (Single Consumer GPU / Entry Workstation)
</summary>
<p><em>Target Hardware: RTX 4060 Ti 16GB, RTX 3060 12GB (tight), RTX A2000, RX 7600 XT, Radeon VII 16GB, Apple 16GB Unified.</em></p>
<div class="md-table">
<table>
<thead>
<tr>
<th style="text-align:left">Model &amp; Base Repo</th>
<th style="text-align:left">Preferred Package / Quant</th>
<th style="text-align:left">Weight Precision</th>
<th style="text-align:left">Static Model VRAM</th>
<th style="text-align:left">Usable KV Headroom</th>
<th style="text-align:left">Max Native Context</th>
<th style="text-align:left">Max YaRN / RoPE Context</th>
<th style="text-align:left">Best Use Case</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left"><a href="https://huggingface.co/ornith-ai/Ornith-1.5-9B" rel="noopener nofollow ugc">Ornith-1.5-9B</a></td>
<td style="text-align:left"><a href="https://huggingface.co/letechlead/Ornith-1.5-9B-INT4-W4A16-AutoRound" rel="noopener nofollow ugc">letechlead/Ornith-1.5-9B-INT4-W4A16-AutoRound</a></td>
<td style="text-align:left">W4A16 (INT4 weights, FP16 activations)</td>
<td style="text-align:left">~5.6 GB</td>
<td style="text-align:left">~9.5 GB</td>
<td style="text-align:left"><strong>256k</strong></td>
<td style="text-align:left"><strong>1m</strong></td>
<td style="text-align:left">General Reasoning, Coding, Long Context</td>
</tr>
<tr>
<td style="text-align:left"><a href="https://huggingface.co/Qwen/Qwen3.5-4B" rel="noopener nofollow ugc">Qwen3.5-4B</a></td>
<td style="text-align:left"><a href="https://huggingface.co/bartowski/Qwen_Qwen3.5-4B-GGUF" rel="noopener nofollow ugc">bartowski/Qwen_Qwen3.5-4B-GGUF (Q4_K_M)</a></td>
<td style="text-align:left">Q4_K_M (GGUF)</td>
<td style="text-align:left">~5.4 GB</td>
<td style="text-align:left">~10.6 GB</td>
<td style="text-align:left"><strong>65k</strong></td>
<td style="text-align:left">N/A</td>
<td style="text-align:left">Fast Generalist, Always-Loaded Resident (96.4 tok/s on Radeon VII)</td>
</tr>
<tr>
<td style="text-align:left"><a href="https://huggingface.co/samuelcardillo/Carnice-Qwen3.6-MoE-35B-A3B" rel="noopener nofollow ugc">Carnice-Qwen3.6-MoE-35B-A3B</a></td>
<td style="text-align:left"><a href="https://huggingface.co/samuelcardillo/Carnice-Qwen3.6-MoE-35B-A3B" rel="noopener nofollow ugc">samuelcardillo/Carnice-Qwen3.6-MoE-35B-A3B (I-Nano)</a></td>
<td style="text-align:left">I-Nano (~2.5bpw GGUF)</td>
<td style="text-align:left">~12.7 GB</td>
<td style="text-align:left">~3.3 GB</td>
<td style="text-align:left"><strong>65k</strong></td>
<td style="text-align:left">N/A</td>
<td style="text-align:left">High-Throughput MoE on 16GB (54.4 tok/s, NIAH YES at 65k)</td>
</tr>
</tbody>
</table>
</div>
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
<th style="text-align:left">Model &amp; Base Repo</th>
<th style="text-align:left">Preferred Package / Quant</th>
<th style="text-align:left">Weight Precision</th>
<th style="text-align:left">Static Model VRAM</th>
<th style="text-align:left">Usable KV Headroom</th>
<th style="text-align:left">Max Native Context</th>
<th style="text-align:left">Max YaRN / RoPE Context</th>
<th style="text-align:left">Best Use Case</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left"><a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AutoRound" rel="noopener nofollow ugc">Swift-1.5-Qwen3.8-27b</a></td>
<td style="text-align:left"><a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AutoRound" rel="noopener nofollow ugc">ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AutoRound</a></td>
<td style="text-align:left">W4A16 (INT4 weights, FP16 activations)</td>
<td style="text-align:left">~20 GB</td>
<td style="text-align:left">~4-8 GB</td>
<td style="text-align:left"><strong>256k</strong></td>
<td style="text-align:left"><strong>1m</strong></td>
<td style="text-align:left">Heavy Code Refactoring, Logic, Agentic Workflows</td>
</tr>
<tr>
<td style="text-align:left"><a href="https://huggingface.co/google/gemma-4-26B-A4B-it" rel="noopener nofollow ugc">Gemma-4-26B-A4B-it</a></td>
<td style="text-align:left"><a href="https://huggingface.co/google/gemma-4-26B-A4B-it" rel="noopener nofollow ugc">Community W4A16 / Q4_K_M GGUF</a></td>
<td style="text-align:left">W4A16 or Q4_K_M</td>
<td style="text-align:left">~14 GB</td>
<td style="text-align:left">~10-14 GB</td>
<td style="text-align:left"><strong>256k</strong></td>
<td style="text-align:left">N/A</td>
<td style="text-align:left">Instruction Following, Analysis, MoE Efficiency</td>
</tr>
<tr>
<td style="text-align:left"><a href="https://huggingface.co/Qwen/Qwen3.6-27B" rel="noopener nofollow ugc">Qwen3.6-27B</a></td>
<td style="text-align:left"><a href="https://huggingface.co/Qwen/Qwen3.6-27B" rel="noopener nofollow ugc">Qwen3.6-27b-q4_KM (Ollama/GGUF)</a></td>
<td style="text-align:left">Q4_K_M (GGUF)</td>
<td style="text-align:left">~18 GB</td>
<td style="text-align:left">~4-8 GB</td>
<td style="text-align:left"><strong>128k</strong></td>
<td style="text-align:left">N/A</td>
<td style="text-align:left">Document Q&amp;A, Deep Research, Creative Writing (52k stable on 20GB)</td>
</tr>
</tbody>
</table>
</div>
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
<th style="text-align:left">Model &amp; Base Repo</th>
<th style="text-align:left">Preferred Package / Quant</th>
<th style="text-align:left">Weight Precision</th>
<th style="text-align:left">Static Model VRAM</th>
<th style="text-align:left">Usable KV Headroom</th>
<th style="text-align:left">Max Native Context</th>
<th style="text-align:left">Max YaRN / RoPE Context</th>
<th style="text-align:left">Best Use Case</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left"><a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AutoRound" rel="noopener nofollow ugc">Swift-1.5-Qwen3.8-27b</a></td>
<td style="text-align:left"><a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AutoRound" rel="noopener nofollow ugc">ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AutoRound</a></td>
<td style="text-align:left">W4A16 (INT4 weights, FP16 activations)</td>
<td style="text-align:left">~20 GB</td>
<td style="text-align:left">~10-18 GB</td>
<td style="text-align:left"><strong>256k</strong></td>
<td style="text-align:left"><strong>1m</strong></td>
<td style="text-align:left">Heavy Code Refactoring, Deep Codebase Context, Agentic Coding</td>
</tr>
<tr>
<td style="text-align:left"><a href="https://huggingface.co/d0xin/Swift-Qwen3.8-27B-Uncensored-FP8" rel="noopener nofollow ugc">Swift-Qwen3.8-27B-Uncensored-FP8</a></td>
<td style="text-align:left"><a href="https://huggingface.co/d0xin/Swift-Qwen3.8-27B-Uncensored-FP8" rel="noopener nofollow ugc">d0xin/Swift-Qwen3.8-27B-Uncensored-FP8</a></td>
<td style="text-align:left">FP8 (native)</td>
<td style="text-align:left">~28 GB</td>
<td style="text-align:left">~0-4 GB (tight)</td>
<td style="text-align:left"><strong>256k</strong></td>
<td style="text-align:left"><strong>1m</strong></td>
<td style="text-align:left">Uncensored Coding, Security Research (120t/s on 2x R9700)</td>
</tr>
<tr>
<td style="text-align:left"><a href="https://huggingface.co/google/gemma-4-26B-A4B-it" rel="noopener nofollow ugc">Gemma-4-26B-A4B-it</a></td>
<td style="text-align:left"><a href="https://huggingface.co/google/gemma-4-26B-A4B-it" rel="noopener nofollow ugc">Community W4A16 / AutoRound INT4</a></td>
<td style="text-align:left">W4A16</td>
<td style="text-align:left">~14 GB</td>
<td style="text-align:left">~18-28 GB</td>
<td style="text-align:left"><strong>256k</strong></td>
<td style="text-align:left">N/A</td>
<td style="text-align:left">Instruction Following, Analysis, Long Context</td>
</tr>
</tbody>
</table>
</div>
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
<th style="text-align:left">Model &amp; Base Repo</th>
<th style="text-align:left">Preferred Package / Quant</th>
<th style="text-align:left">Weight Precision</th>
<th style="text-align:left">Static Model VRAM</th>
<th style="text-align:left">Usable KV Headroom</th>
<th style="text-align:left">Max Native Context</th>
<th style="text-align:left">Max YaRN / RoPE Context</th>
<th style="text-align:left">Best Use Case</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left"><a href="https://huggingface.co/google/gemma-4-31B-it" rel="noopener nofollow ugc">Gemma-4-31B-it</a></td>
<td style="text-align:left"><a href="https://huggingface.co/google/gemma-4-31B-it" rel="noopener nofollow ugc">Community W4A16 / AutoRound INT4</a></td>
<td style="text-align:left">W4A16</td>
<td style="text-align:left">~18 GB</td>
<td style="text-align:left">~30-46 GB</td>
<td style="text-align:left"><strong>256k</strong></td>
<td style="text-align:left"><strong>1m</strong></td>
<td style="text-align:left">Long Document Ingestion</td>
</tr>
<tr>
<td style="text-align:left"><a href="https://huggingface.co/ornith-ai/Ornith-1.5-35B-A3B" rel="noopener nofollow ugc">Ornith-1.5-35B-A3B</a></td>
<td style="text-align:left"><a href="https://huggingface.co/SergiioB/Ornith-1.5-35B-A3B-AutoRound-W4A16-sym-G128-MTP-BF16" rel="noopener nofollow ugc">SergiioB/Ornith-1.5-35B-A3B-AutoRound-W4A16-sym-G128-MTP-BF16</a></td>
<td style="text-align:left">W4A16 sym G128 + MTP (BF16)</td>
<td style="text-align:left">~22 GB</td>
<td style="text-align:left">~26-42 GB</td>
<td style="text-align:left"><strong>256k</strong></td>
<td style="text-align:left"><strong>1m</strong></td>
<td style="text-align:left">High-Throughput Reasoning (MTP speculative)</td>
</tr>
<tr>
<td style="text-align:left"><a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AutoRound" rel="noopener nofollow ugc">Swift-1.5-Qwen3.8-27b</a></td>
<td style="text-align:left"><a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AutoRound" rel="noopener nofollow ugc">ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AutoRound</a></td>
<td style="text-align:left">W4A16 (INT4 weights, FP16 activations)</td>
<td style="text-align:left">~20 GB</td>
<td style="text-align:left">~28-44 GB</td>
<td style="text-align:left"><strong>256k</strong></td>
<td style="text-align:left"><strong>1m</strong></td>
<td style="text-align:left">Deep Codebase Context, Multi-Agent Serving</td>
</tr>
<tr>
<td style="text-align:left"><a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AutoRound" rel="noopener nofollow ugc">Swift-1.5-Qwen3.8-27b (FP8)</a></td>
<td style="text-align:left"><a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AutoRound" rel="noopener nofollow ugc">FP8 native (via vLLM)</a></td>
<td style="text-align:left">FP8 (native)</td>
<td style="text-align:left">~28 GB</td>
<td style="text-align:left">~20-36 GB</td>
<td style="text-align:left"><strong>256k</strong></td>
<td style="text-align:left"><strong>1m</strong></td>
<td style="text-align:left">Maximum Speed/Quality on Ada/Hopper (256k ctx verified)</td>
</tr>
</tbody>
</table>
</div>
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
<th style="text-align:left">Model &amp; Base Repo</th>
<th style="text-align:left">Preferred Package / Quant</th>
<th style="text-align:left">Weight Precision</th>
<th style="text-align:left">Static Model VRAM</th>
<th style="text-align:left">Usable KV Headroom</th>
<th style="text-align:left">Max Native Context</th>
<th style="text-align:left">Max YaRN / RoPE Context</th>
<th style="text-align:left">Best Use Case</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left"><a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AutoRound" rel="noopener nofollow ugc">Swift-1.5-Qwen3.8-27b</a></td>
<td style="text-align:left"><a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AutoRound" rel="noopener nofollow ugc">ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AutoRound</a></td>
<td style="text-align:left">W4A16 (INT4 weights, FP16 activations)</td>
<td style="text-align:left">~20 GB</td>
<td style="text-align:left">~76-108 GB</td>
<td style="text-align:left"><strong>256k</strong></td>
<td style="text-align:left"><strong>1m</strong></td>
<td style="text-align:left">Extreme RAG &amp; Repository Ingestion, Multi-Client Serving</td>
</tr>
<tr>
<td style="text-align:left"><a href="https://huggingface.co/Qwen/Qwen3.8-Flash-Next" rel="noopener nofollow ugc">Qwen3.8-Flash-Next</a></td>
<td style="text-align:left"><a href="https://huggingface.co/Intel/Qwen3.8-Flash-Next-W4A16-RTN-AutoRound" rel="noopener nofollow ugc">Intel/Qwen3.8-Flash-Next-W4A16-RTN-AutoRound</a></td>
<td style="text-align:left">W4A16 RTN + n-gram table</td>
<td style="text-align:left">~168 GB (pure VRAM) / ~73 GB (host offload)</td>
<td style="text-align:left">~23-55 GB*</td>
<td style="text-align:left"><strong>256k</strong></td>
<td style="text-align:left"><strong>1m</strong></td>
<td style="text-align:left">Fast Agentic Workflows, Speculative Decoding</td>
</tr>
<tr>
<td style="text-align:left"><a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-Flash-Next-W4A16-AutoRound" rel="noopener nofollow ugc">Swift-1.5-Qwen3.8-Flash-Next</a></td>
<td style="text-align:left"><a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-Flash-Next-W4A16-AutoRound" rel="noopener nofollow ugc">ukisai/Swift-1.5-Qwen3.8-Flash-Next-W4A16-AutoRound</a></td>
<td style="text-align:left">W4A16 + n-gram table</td>
<td style="text-align:left">~168 GB (pure VRAM) / ~73 GB (host offload)</td>
<td style="text-align:left">~23-55 GB*</td>
<td style="text-align:left"><strong>256k</strong></td>
<td style="text-align:left"><strong>1m</strong></td>
<td style="text-align:left">Swift Fine-tune: Fast Agentic + Coding, Speculative Decoding</td>
</tr>
<tr>
<td style="text-align:left"><a href="https://huggingface.co/ornith-ai/Ornith-1.5-35B-A3B" rel="noopener nofollow ugc">Ornith-1.5-35B-A3B</a></td>
<td style="text-align:left"><a href="https://huggingface.co/SergiioB/Ornith-1.5-35B-A3B-AutoRound-W4A16-sym-G128-MTP-BF16" rel="noopener nofollow ugc">SergiioB/Ornith-1.5-35B-A3B-AutoRound-W4A16-sym-G128-MTP-BF16</a></td>
<td style="text-align:left">W4A16 sym G128 + MTP (BF16)</td>
<td style="text-align:left">~22 GB</td>
<td style="text-align:left">~74-106 GB</td>
<td style="text-align:left"><strong>256k</strong></td>
<td style="text-align:left"><strong>1m</strong></td>
<td style="text-align:left">High-Throughput Production Serving, Multi-Tenant</td>
</tr>
</tbody>
</table>
</div>
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
<th style="text-align:left">Model &amp; Base Repo</th>
<th style="text-align:left">Preferred Package / Quant</th>
<th style="text-align:left">Weight Precision</th>
<th style="text-align:left">Static Model VRAM</th>
<th style="text-align:left">Usable KV Headroom</th>
<th style="text-align:left">Max Native Context</th>
<th style="text-align:left">Max YaRN / RoPE Context</th>
<th style="text-align:left">Best Use Case</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left"><a href="https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-Vision-Exp" rel="noopener nofollow ugc">DeepSeek-V4-Flash-Vision-Exp</a></td>
<td style="text-align:left"><a href="https://huggingface.co/Intel/DeepSeek-V4-Flash-Vision-Exp-W4A16-AutoRound" rel="noopener nofollow ugc">Intel/DeepSeek-V4-Flash-Vision-Exp-W4A16-AutoRound</a></td>
<td style="text-align:left">W4A16 (INT4 weights, FP16 activations)</td>
<td style="text-align:left">~156 GB</td>
<td style="text-align:left">~40-100 GB</td>
<td style="text-align:left"><strong>1m</strong></td>
<td style="text-align:left">N/A</td>
<td style="text-align:left">Multimodal Document &amp; Video Analysis</td>
</tr>
<tr>
<td style="text-align:left"><a href="https://huggingface.co/zai-org/GLM-5.3-Flash" rel="noopener nofollow ugc">GLM-5.3-Flash</a></td>
<td style="text-align:left"><a href="https://huggingface.co/Intel/GLM-5.3-Flash-W4A16-AutoRound" rel="noopener nofollow ugc">Intel/GLM-5.3-Flash-W4A16-AutoRound</a></td>
<td style="text-align:left">W4A16 (INT4 weights, FP16 activations)</td>
<td style="text-align:left">~176 GB</td>
<td style="text-align:left">~20-80 GB</td>
<td style="text-align:left"><strong>1m</strong></td>
<td style="text-align:left">N/A</td>
<td style="text-align:left">Complex Agent Systems</td>
</tr>
<tr>
<td style="text-align:left"><a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-Flash-Next-W4A16-AutoRound" rel="noopener nofollow ugc">Swift-1.5-Qwen3.8-Flash-Next</a></td>
<td style="text-align:left"><a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-Flash-Next-W4A16-AutoRound" rel="noopener nofollow ugc">ukisai/Swift-1.5-Qwen3.8-Flash-Next-W4A16-AutoRound</a></td>
<td style="text-align:left">W4A16 + n-gram table</td>
<td style="text-align:left">~168 GB</td>
<td style="text-align:left">~28-88 GB*</td>
<td style="text-align:left"><strong>256k</strong></td>
<td style="text-align:left"><strong>1m</strong></td>
<td style="text-align:left">Multi-Million Token Ingestion, Swift Fine-tune Agentic</td>
</tr>
<tr>
<td style="text-align:left"><a href="https://huggingface.co/Qwen/Qwen3.8-Flash-Next" rel="noopener nofollow ugc">Qwen3.8-Flash-Next</a></td>
<td style="text-align:left"><a href="https://huggingface.co/Intel/Qwen3.8-Flash-Next-W4A16-RTN-AutoRound" rel="noopener nofollow ugc">Intel/Qwen3.8-Flash-Next-W4A16-RTN-AutoRound</a></td>
<td style="text-align:left">W4A16 RTN + n-gram table</td>
<td style="text-align:left">~168 GB</td>
<td style="text-align:left">~28-88 GB*</td>
<td style="text-align:left"><strong>256k</strong></td>
<td style="text-align:left"><strong>1m</strong></td>
<td style="text-align:left">Multi-Million Token Ingestion</td>
</tr>
<tr>
<td style="text-align:left"><a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AutoRound" rel="noopener nofollow ugc">Swift-1.5-Qwen3.8-27b</a></td>
<td style="text-align:left"><a href="https://huggingface.co/ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AutoRound" rel="noopener nofollow ugc">ukisai/Swift-1.5-Qwen3.8-27b-W4A16-AutoRound</a></td>
<td style="text-align:left">W4A16 (INT4 weights, FP16 activations)</td>
<td style="text-align:left">~20 GB</td>
<td style="text-align:left">~176-236 GB</td>
<td style="text-align:left"><strong>256k</strong></td>
<td style="text-align:left"><strong>1m</strong></td>
<td style="text-align:left">Complete Library &amp; Git Ingestion, Multi-Client Farm</td>
</tr>
<tr>
<td style="text-align:left"><a href="https://huggingface.co/unsloth/DeepSeek-V4-Pro-0813-GGUF" rel="noopener nofollow ugc">DeepSeek-V4-Pro-0813</a></td>
<td style="text-align:left"><a href="https://huggingface.co/unsloth/DeepSeek-V4-Pro-0813-GGUF" rel="noopener nofollow ugc">unsloth/DeepSeek-V4-Pro-0813-GGUF (UD-Q8_K_XL)</a></td>
<td style="text-align:left">Q8_K_XL (GGUF)</td>
<td style="text-align:left">~400 GB+ (CPU+GPU hybrid)</td>
<td style="text-align:left">N/A (RAM-bound)</td>
<td style="text-align:left"><strong>16k</strong></td>
<td style="text-align:left">N/A</td>
<td style="text-align:left">Niche Translation, Ultra-Long Document Fidelity</td>
</tr>
</tbody>
</table>
</div>
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

</details>

<details>
<summary>🔗 Related Threads on L1Techs</summary>

- [Why your local LLM feels dumber than it is](https://forum.level1techs.com/t/why-your-local-llm-feels-dumber-than-it-is/253917) — Implementation-spec impact on perceived model quality
- [Qwen3.8-Flash-Next Q6_K on 3× Radeon Instinct MI50 16GB](https://forum.level1techs.com/t/qwen3-8-flash-next-q6-k-on-3x-radeon-instinct-mi50-16gb/256455) — AMD datacenter multi-GPU
- [Dual R9700 llama.cpp Rocm tensor-split, working P2P on Proxmox, Qwen3.8-27B](https://forum.level1techs.com/t/dual-r9700-llama-cpp-rocm-tensor-split-working-p2p-on-proxmox-qwen-3-8-27b/254183) — AMD P2P on virtualized host
- [I have 4x 6000 Blackwell and serve 10 devs and 40 office workers with it](https://forum.level1techs.com/t/i-have-4x-6000-blackwell-and-serve-10-devs-and-40-office-workers-with-it/254269) — Production multi-user serving
- [Sanity check my Qwen3.8 5090 Results; new to Local AI](https://forum.level1techs.com/t/sanity-check-my-qwen-3-8-5090-results-new-to-local-ai/254299) — Consumer Blackwell benchmarks

</details>
