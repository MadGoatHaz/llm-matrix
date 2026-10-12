# Reference, Templates & Community Data

*The deep-dive resource. Submission templates, backend guides, hardware notes, and the full community data index. Post #1 is the front door — this is the workshop.*

**Quick Navigation:**
- 📋 Submission Templates (Quick + Full)
- ⚙️ Backend Selection Guide
- 🖥️ Hardware Vendor Notes
- 📦 Running Non-GGUF / Hybrid Models
- ⚡ KV Cache Quantization Rule
- ⚡ Real-World Constraints
- 📊 Community Data Viewport (All Submissions)
- 📅 Full Changelog
- ℹ️ How Data Gets Integrated

<hr>

<details>
<summary>📋 Submission Templates — Share Your Setup</summary>

The matrix runs on community data. Here's how to add yours.

<strong>Quick Submit (30 seconds):</strong>

<pre><code>[QUICK-SUBMIT]
gpu: [Your GPU model + VRAM]
model: [Model name + quant]
use_case: [What you use it for]
verdict: [One sentence: does it work? any quirks?]
[/QUICK-SUBMIT]</code></pre>

*That's it. If you have 30 seconds, this is enough to get your data into the matrix. No template gymnastics required. Use Quick Submit for casual reports; use Full Submit when you have benchmark numbers, context test results, or specific launch configs you want captured.*

<strong>Full Submit (for detailed data):</strong>

<pre><code>[COMMUNITY-SUBMISSION]
tier: [≤16GB | 16-24GB | 24-32GB | 48-64GB | 96-128GB | 196-256GB+]
hardware: [e.g., 2x RX 7900 XTX 24GB, 4x MI210, 1x RTX 4060 Ti 16GB, Mac Studio 64GB]
backend: [vLLM | llama.cpp | LM Studio | Ollama | Unsloth Desktop | llama-swap | Colibri | Strata | Radiance | Other]
os_driver: [Linux/CUDA | Linux/ROCm | Linux/Vulkan | Windows/CUDA | Windows/WSL2 | macOS/Metal | Other]
model_name: [Full model repository or exact filename]
quant_package: [e.g., AutoRound W4A16, GGUF Q4_K_M, EXL2 4.0bpw, FP8, I-Nano, NVFP4]
weight_precision: [W4A16 | W8A8 | FP8 | BF16 | Q4_K_M | Q8_0 | Other]
download_url: [Hugging Face or model source link]
primary_use_case: [e.g., Agentic coding, Deep reasoning, Creative writing, RAG, Translation]
stable_context_tested: [Actual token count tested without OOM or coherence collapse]
kv_cache_setting: [Native FP16/BF16 | FP8 | INT8 | INT4 | Q8_0]
engine_mode: [VRAM-only | Hybrid (VRAM+RAM) | Hybrid (VRAM+RAM+SSD) | CPU+GPU]
throughput_tps: [Decode tok/s]
prefill_tps: [Prefill tok/s (if measured)]
ttft_cold: [Seconds for first token after cold load]
power_draw: [Watts at peak (if measured)]
setup_notes: [Launch flags, rope/yarn config, host RAM offload, prompt prefill behavior, quirks]
[/COMMUNITY-SUBMISSION]</code></pre>

<strong>Optional fields:</strong> You don't have to fill out every line. <code>os_driver</code>, <code>weight_precision</code>, <code>prefill_tps</code>, <code>ttft_cold</code>, <code>power_draw</code>, <code>download_url</code>, and <code>engine_mode</code> are all optional — but they're what make hardware-specific recommendations and dashboard filtering possible. At minimum, include <code>hardware</code>, <code>model_name</code>, <code>quant_package</code>, and <code>throughput_tps</code>.

<strong>The <code>engine_mode</code> field:</strong> If you're running a hybrid setup — Strata-style VRAM+RAM+SSD offload, or CPU+GPU layer splitting — set <code>engine_mode</code> explicitly. It tells the matrix what's actually running where. A 125B MoE on a single 24GB card via Strata is a fundamentally different data point than a 27B dense model in pure VRAM, and the index only works if that distinction is captured.

<strong>What a good submission looks like:</strong>

*Example A — Consumer AMD (llama-swap):*

<pre><code>[COMMUNITY-SUBMISSION]
tier: ≤16GB
hardware: 1x Radeon VII 16GB HBM2 (gfx906), 32-core EPYC host, 67GB RAM
backend: llama-swap (llama.cpp subprocess, ROCm)
os_driver: Linux/ROCm
model_name: samuelcardillo/Carnice-Qwen3.6-MoE-35B-A3B
quant_package: GGUF I-Nano
weight_precision: I-Nano (~2.5bpw)
download_url: https://huggingface.co/samuelcardillo/Carnice-Qwen3.6-MoE-35B-A3B
primary_use_case: LLM-assisted coding / technical documentation
stable_context_tested: 65536 tokens (NIAH hit YES at 65k)
kv_cache_setting: Q8_0 (quantized)
throughput_tps: 54.4 decode
prefill_tps: 215
ttft_cold: 19.3s
power_draw: 150W peak
setup_notes: MoE A3B — fits 12.7GB incl. KV. 9B active params ≈ 9B compute. Fast cold load.
[/COMMUNITY-SUBMISSION]</code></pre>

*Example B — Multi-GPU AMD (Radiance / vLLM):*

<pre><code>[COMMUNITY-SUBMISSION]
tier: 48-64GB
hardware: 2x AMD R9700 (48GB total)
backend: vLLM (magiccodingman/vllm-radiance, adaptive MTP=8)
os_driver: Linux/ROCm
model_name: d0xin/Swift-Qwen3.8-27B-Uncensored-FP8
quant_package: FP8
weight_precision: FP8 (native)
download_url: https://huggingface.co/d0xin/Swift-Qwen3.8-27B-Uncensored-FP8
primary_use_case: Coding, Security Research (DoS attack tracking)
stable_context_tested: ~240k tokens
kv_cache_setting: FP16 (unquantized)
throughput_tps: 120 (code) / 70 (chat)
prefill_tps: N/A
ttft_cold: N/A
power_draw: N/A
setup_notes: Uncensored variant for security work. Adaptive MTP=8 for speculative speed. Standard Qwen-based models get "nervy" on DoS content.
[/COMMUNITY-SUBMISSION]</code></pre>

*Example C — Hybrid Offload (Strata):*

<pre><code>[COMMUNITY-SUBMISSION]
tier: 24-32GB (hybrid: VRAM+RAM+SSD)
hardware: 1x RTX 4090 24GB, Ryzen 9 5900X, 128GB DDR4-3600, Samsung 990 Pro NVMe
backend: Strata 0.1.42
os_driver: Windows 11 + WSL2/Ubuntu 24.04 (96GB via .wslconfig)
model_name: Qwen/Qwen3.8-Flash-Next (GGUF IQ3_S)
quant_package: GGUF IQ3_S (ISTA-DASLab GSQ-RCO)
weight_precision: IQ3_S
download_url: https://huggingface.co/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF
primary_use_case: Agentic coding via OpenAI-compatible API
stable_context_tested: 131072 configured; >=106,493 observed in live sessions
kv_cache_setting: int8 (engine-native)
engine_mode: Hybrid (VRAM+RAM+SSD)
throughput_tps: 99-128 decode (median 108)
prefill_tps: 825-3600 (median ~2800 with 90% prompt cache)
power_draw: 450W stock cap
setup_notes: 125B MoE on single 24GB card. 6892 experts: 13.4GB VRAM, rest RAM, lookup NVMe. MTP=4+lookup=3. Prompt cache 90% hits → 0.3-0.8s resume on 50k contexts. WSL2 needs explicit .wslconfig RAM.
[/COMMUNITY-SUBMISSION]</code></pre>

*The more specific you can be about context limits, KV settings, and real-world quirks, the more value your submission adds to the community.*

</details>

<details>
<summary>⚙️ Backend Selection Guide — Which Runtime?</summary>

*The model is only half the equation. How you serve it determines your speed, features, and flexibility.*

<div class="md-table"><table style="text-align:left">
<thead>
<tr>
<th style="text-align:left">Backend</th>
<th style="text-align:left">Best For</th>
<th style="text-align:left">Model Formats</th>
<th style="text-align:left">Multi-GPU</th>
<th style="text-align:left">Learning Curve</th>
<th style="text-align:left">Key Features</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left"><strong>Unsloth Desktop</strong></td>
<td style="text-align:left">All-in-one: run, chat, train, serve</td>
<td style="text-align:left">GGUF, safetensors, FP8, MLX</td>
<td style="text-align:left">Single GPU (multi-GPU via vLLM mode)</td>
<td style="text-align:left">🟢 Minimal</td>
<td style="text-align:left">llama.cpp + vLLM + MLX engines, no-code fine-tuning, image/video gen, TTS/STT, OpenAI API server, LAN serving, agent integrations, fully offline</td>
</tr>
<tr>
<td style="text-align:left"><strong>Ollama</strong></td>
<td style="text-align:left">Beginners, quick start, always-on assistant</td>
<td style="text-align:left">GGUF only</td>
<td style="text-align:left">Limited (single GPU)</td>
<td style="text-align:left">🟢 Minimal</td>
<td style="text-align:left">One-command model management, OpenAI-compatible API, model auto-download</td>
</tr>
<tr>
<td style="text-align:left"><strong>LM Studio</strong></td>
<td style="text-align:left">Visual interface, beginners to intermediate</td>
<td style="text-align:left">GGUF only</td>
<td style="text-align:left">Limited</td>
<td style="text-align:left">🟢 Minimal</td>
<td style="text-align:left">GUI model browser, chat interface, one-click server, no terminal needed</td>
</tr>
<tr>
<td style="text-align:left"><strong>llama.cpp</strong></td>
<td style="text-align:left">Maximum hardware flexibility, AMD/Vulkan/Metal</td>
<td style="text-align:left">GGUF</td>
<td style="text-align:left">Yes (tensor split, layer offload)</td>
<td style="text-align:left">🟡 Moderate</td>
<td style="text-align:left">Runs everywhere (CPU, GPU, hybrid), quantized KV cache, RoPE/YaRN, batch processing</td>
</tr>
<tr>
<td style="text-align:left"><strong>llama-swap</strong></td>
<td style="text-align:left">Multi-model serving on single GPU</td>
<td style="text-align:left">GGUF</td>
<td style="text-align:left">Single GPU (auto-swap)</td>
<td style="text-align:left">🟡 Moderate</td>
<td style="text-align:left">Auto model loading/unloading, OpenAI API, ideal for "always-on" multi-model setups</td>
</tr>
<tr>
<td style="text-align:left"><strong>vLLM</strong></td>
<td style="text-align:left">Production serving, maximum throughput</td>
<td style="text-align:left">Safetensors, FP8, W4A16 AutoRound, GGUF</td>
<td style="text-align:left">Yes (tensor parallel)</td>
<td style="text-align:left">🔴 Steep</td>
<td style="text-align:left">Continuous batching, PagedAttention, speculative decoding (MTP), multi-client, OpenAI API</td>
</tr>
<tr>
<td style="text-align:left"><strong>TensorRT-LLM</strong></td>
<td style="text-align:left">NVIDIA-only maximum performance</td>
<td style="text-align:left">FP16, FP8, INT4</td>
<td style="text-align:left">Yes (tensor parallel)</td>
<td style="text-align:left">🔴 Steep</td>
<td style="text-align:left">Kernel-level optimization, INCEPTION mode, best tok/s on NVIDIA</td>
</tr>
<tr>
<td style="text-align:left"><strong>MLX</strong></td>
<td style="text-align:left">Apple Silicon native</td>
<td style="text-align:left">MLX format, GGUF</td>
<td style="text-align:left">Single GPU (unified)</td>
<td style="text-align:left">🟡 Moderate</td>
<td style="text-align:left">Leverages unified memory, quantized kernels, Python-native</td>
</tr>
<tr>
<td style="text-align:left"><strong>Colibri</strong></td>
<td style="text-align:left">CPU inference, extreme RAM</td>
<td style="text-align:left">Safetensors, GGUF</td>
<td style="text-align:left">CPU only</td>
<td style="text-align:left">🟡 Moderate</td>
<td style="text-align:left">For 1TB+ RAM systems, niche model serving without GPU</td>
</tr>
<tr>
<td style="text-align:left"><strong>Strata</strong></td>
<td style="text-align:left">Hybrid VRAM+RAM+SSD offload for 100B+ MoE models</td>
<td style="text-align:left">GGUF (IQ3_S, Q4_K_M, higher)</td>
<td style="text-align:left">Single GPU + system RAM + NVMe</td>
<td style="text-align:left">🟡 Moderate</td>
<td style="text-align:left">One-click install, OpenAI/Anthropic API, prompt cache (90% hits), MTP speculative decoding, runs 125B on a single 24GB card. WSL2 requires .wslconfig RAM allocation. <a href="https://github.com/Niko1221/Strata" rel="noopener nofollow ugc">GitHub</a></td>
</tr>
<tr>
<td style="text-align:left"><strong>Radiance</strong></td>
<td style="text-align:left">AMD-optimized high-throughput inference (RDNA3/4)</td>
<td style="text-align:left">IQ4, FP8 PLE, W4A16</td>
<td style="text-align:left">Multi-GPU (AMD)</td>
<td style="text-align:left">🟡 Moderate</td>
<td style="text-align:left">200+ tok/s decode with MTP on dual R9700. 5200-6200 tok/s prefill. Native amdgpu backend. Everything in VRAM+RAM, no disk. <a href="https://github.com/magiccodingman/vllm-radiance" rel="noopener nofollow ugc">GitHub</a></td>
</tr>
</tbody>
</table></div>

<strong>Quick Decision:</strong>

<ul>
<li><em>Just want to chat with an AI?</em> → <strong>Unsloth Desktop</strong> (all-in-one) or <strong>Ollama</strong> (minimalist)</li>
<li><em>Running on AMD and want it to just work?</em> → <strong>llama.cpp</strong> (ROCm) or <strong>llama-swap</strong></li>
<li><em>Apple Mac?</em> → <strong>MLX</strong> or <strong>llama.cpp</strong> (Metal)</li>
<li><em>Serving multiple users / agents?</em> → <strong>vLLM</strong></li>
<li><em>Maximum speed on NVIDIA?</em> → <strong>TensorRT-LLM</strong> or <strong>vLLM</strong> (FP8)</li>
<li><em>One GPU, multiple models, auto-switching?</em> → <strong>llama-swap</strong></li>
<li><em>1TB RAM, no GPU needed?</em> → <strong>Colibri</strong> or <strong>llama.cpp</strong> (CPU)</li>
<li><em>Running 100B+ MoE on a single consumer GPU?</em> → <strong>Strata</strong> (hybrid VRAM+RAM+SSD)</li>
<li><em>Maximum throughput on AMD RDNA3/4 (R9700, MI300X)?</em> → <strong>Radiance</strong></li>
</ul>

<strong>The Strata &amp; Radiance distinction:</strong> Strata is about <em>capacity</em> — it lets one modest GPU run models far bigger than its VRAM by tiering weights across RAM and NVMe. Radiance is about <em>throughput</em> — it squeezes maximum tokens per second out of AMD silicon when the model already fits in VRAM+RAM. They solve different problems, and a serious AMD build can use both in different roles.

<p><em>For frontends, agent harnesses, and orchestration tools that pair with your local models, see the <strong>Supporting Software &amp; Ecosystem</strong> section in Post #1.</em></p>

<p><strong>The Golden Rule:</strong> Start with the simplest backend that meets your needs. You can always migrate to a more powerful one later. Your model weights (GGUF or Safetensors) are portable across backends.</p>

</details>

<details>
<summary>🖥️ Hardware Vendor Notes (NVIDIA / AMD / Apple)</summary>

*The same model runs very differently on three kinds of silicon. Here's what to know before you buy — and what the community has confirmed in practice.*

<details>
<summary>NVIDIA — the reference ecosystem</summary>

CUDA is the reference implementation: every backend in the guide above supports it, and when a new quant format or feature lands, it lands on CUDA first.

<strong>CUDA requirements:</strong>

<ul>
<li>Current NVIDIA driver (backends bundle their own CUDA runtime — you rarely need the full toolkit installed)</li>
<li>Linux: easiest serving path (vLLM, TensorRT-LLM, llama.cpp all mature). Windows: fine for desktop use; WSL2 adds a memory-allocation quirk (see Strata section)</li>
<li>Multi-GPU: NVLink on data-center cards; PCIe tensor-parallel on consumer cards (expect a bandwidth tax on very large models)</li>
</ul>

<strong>Compute capability — what your card can actually do:</strong>

<div class="md-table"><table style="text-align:left">
<thead>
<tr>
<th style="text-align:left">Generation</th>
<th style="text-align:left">Cards</th>
<th style="text-align:left">Compute Capability</th>
<th style="text-align:left">FP8</th>
<th style="text-align:left">NVFP4</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left">Turing (2018)</td>
<td style="text-align:left">RTX 20xx, T4</td>
<td style="text-align:left">7.5</td>
<td style="text-align:left">❌</td>
<td style="text-align:left">❌</td>
</tr>
<tr>
<td style="text-align:left">Ampere (2020)</td>
<td style="text-align:left">RTX 30xx, A100</td>
<td style="text-align:left">8.0 / 8.6</td>
<td style="text-align:left">❌ (INT8 only)</td>
<td style="text-align:left">❌</td>
</tr>
<tr>
<td style="text-align:left">Ada (2022)</td>
<td style="text-align:left">RTX 40xx, L40</td>
<td style="text-align:left">8.9</td>
<td style="text-align:left">✅ native</td>
<td style="text-align:left">❌</td>
</tr>
<tr>
<td style="text-align:left">Hopper (2022)</td>
<td style="text-align:left">H100</td>
<td style="text-align:left">9.0</td>
<td style="text-align:left">✅ native</td>
<td style="text-align:left">❌</td>
</tr>
<tr>
<td style="text-align:left">Blackwell (2025)</td>
<td style="text-align:left">RTX 50xx, B200</td>
<td style="text-align:left">12.0</td>
<td style="text-align:left">✅ native</td>
<td style="text-align:left">✅ hardware-accelerated</td>
</tr>
</tbody>
</table></div>

<ul>
<li><strong>Ada (40xx) and newer</strong> is the floor for native FP8 — the format that makes 27B models near-lossless in half the memory of BF16.</li>
<li><strong>Blackwell (50xx)</strong> is the first consumer line with hardware NVFP4 dequant — the emerging 4-bit float format (see Non-GGUF section).</li>
<li><strong>Ampere and older</strong>: use AutoRound W4A16 or INT8 — FP8 checkpoints will not accelerate for you.</li>
<li><strong>TensorRT-LLM is NVIDIA-only</strong> and remains the single-card tok/s king when you can absorb the setup cost.</li>
</ul>

</details>

<details>
<summary>AMD — best $/VRAM, two real paths</summary>

AMD has two viable inference paths: <strong>ROCm</strong> (Linux, the main road) and <strong>Vulkan</strong> (cross-OS fallback, including Windows). llama.cpp runs well on both; vLLM-class serving is ROCm-only.

<strong>Card-by-card notes (community-confirmed):</strong>

<div class="md-table"><table style="text-align:left">
<thead>
<tr>
<th style="text-align:left">Card</th>
<th style="text-align:left">VRAM</th>
<th style="text-align:left">Target</th>
<th style="text-align:left">Notes</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left">Radeon VII</td>
<td style="text-align:left">16GB HBM2</td>
<td style="text-align:left">gfx906</td>
<td style="text-align:left">Aged but loved. ~225W, HBM bandwidth, community ROCm patches. The budget 24/7 always-on pick (see Example A — 35B MoE at 54 tok/s).</td>
</tr>
<tr>
<td style="text-align:left">RX 7900 XT</td>
<td style="text-align:left">20GB</td>
<td style="text-align:left">gfx1100</td>
<td style="text-align:left">RDNA3. Best value entry into 27B Q4 territory. ROCm mature.</td>
</tr>
<tr>
<td style="text-align:left">RX 7900 XTX</td>
<td style="text-align:left">24GB</td>
<td style="text-align:left">gfx1101</td>
<td style="text-align:left">The 27B sweet spot — full Q4/W4A16 with room for serious context. Dual-card builds are the AMD multi-GPU workhorse.</td>
</tr>
<tr>
<td style="text-align:left">R9700</td>
<td style="text-align:left">24GB</td>
<td style="text-align:left">RDNA4</td>
<td style="text-align:left">Current-gen. <strong>Radiance</strong> pulls 200+ tok/s decode with MTP on a dual R9700 — the highest consumer AMD throughput in the matrix.</td>
</tr>
<tr>
<td style="text-align:left">MI210 / MI250</td>
<td style="text-align:left">32 / 64GB HBM2</td>
<td style="text-align:left">Data center</td>
<td style="text-align:left">Used-market price/performance. 4x MI210 is a proven 128GB serving box (see community submissions). ECC, 24/7 rated.</td>
</tr>
<tr>
<td style="text-align:left">MI300X</td>
<td style="text-align:left">192GB HBM3</td>
<td style="text-align:left">gfx942</td>
<td style="text-align:left">70B+ models fully in VRAM, no offload. The single-card data-center king. Radiance + MTP is the tuned serving path.</td>
</tr>
<tr>
<td style="text-align:left">v620</td>
<td style="text-align:left">Workstation class</td>
<td style="text-align:left">Pro line</td>
<td style="text-align:left">Professional/workstation card aimed at headless 24/7 serving. Pro driver support, ECC options. Less community benchmark data so far — submissions welcome.</td>
</tr>
</tbody>
</table></div>

<strong>AMD recommendations:</strong>

<ul>
<li><strong>One card, many models, always on:</strong> <strong>llama-swap</strong> — auto-swap keeps a hot model in VRAM and pages the rest from disk with an OpenAI API on top.</li>
<li><strong>Maximum performance on RDNA3/4:</strong> <strong>Radiance</strong> — the tuned vLLM fork. This is where dual R9700 and MI300X builds live their best lives.</li>
<li><strong>General purpose:</strong> llama.cpp (ROCm) — the most forgiving path; if something works on Vulkan, it probably works on ROCm faster.</li>
<li>AMD remains the best $/VRAM ratio for multi-GPU builds — two 7900 XTX (48GB) costs less than one 4090 and serves bigger models.</li>
</ul>

</details>

<details>
<summary>Apple — unified memory, zero config</summary>

<strong>How unified memory works:</strong> On M-series Silicon, system RAM and GPU memory are the same pool. There's no PCIe copy, no separate VRAM ceiling — a 64GB Mac Studio effectively has 64GB of "VRAM." The trade: memory bandwidth is high but not HBM-high, and you can't scale to a second GPU. A $4K Mac Studio gives you 64GB — more model headroom than a 4090 — at a fraction of the power draw.

<strong>MLX</strong> is the native framework: Python-first, quantized kernels, built for the unified-memory model. It's the default engine behind Apple Silicon serving in <strong>Unsloth Desktop</strong>, which supports Apple out of the box.

<strong>Mac Studio tiers (community reference):</strong>

<div class="md-table"><table style="text-align:left">
<thead>
<tr>
<th style="text-align:left">Config</th>
<th style="text-align:left">Unified Memory</th>
<th style="text-align:left">Realistically Runs</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left">M4 Max</td>
<td style="text-align:left">36–128GB</td>
<td style="text-align:left">27B at Q4–Q8 with context headroom; 70B at Q3–Q4 (tight)</td>
</tr>
<tr>
<td style="text-align:left">M3 Ultra</td>
<td style="text-align:left">96–512GB</td>
<td style="text-align:left">70B+ in FP8; 120B+ MoE at low quant; the consumer "server" tier</td>
</tr>
</tbody>
</table></div>

<ul>
<li>Decode speed on Apple trails a modern discrete GPU at equivalent model size — but for chat-sized contexts and MoE models (low active params), it's surprisingly competitive at a fraction of the wattage.</li>
<li>No multi-GPU scaling, no CUDA, no TensorRT. Your backends are MLX, llama.cpp (Metal), and Unsloth Desktop.</li>
<li>Long-context KV is the binding constraint — unified memory holds it, but bandwidth sets the ceiling. Quantize KV only per the rule in Section 5.</li>
</ul>

</details>

<p><strong>Cross-vendor note — Strata:</strong> Hybrid VRAM+RAM+SSD offload is vendor-agnostic. A single 24GB NVIDIA card, a 24GB AMD card, or a 64GB Apple unified pool — paired with 128GB of system RAM and fast NVMe — can run 125B+ MoE models at 100+ tok/s. If you have lots of RAM and not much VRAM, Strata changes the game on every vendor. See the Non-GGUF / Hybrid section for how it works.</p>

</details>

<details>
<summary>📦 Running Non-GGUF & Hybrid Models (AutoRound, FP8, Strata, Radiance)</summary>

*GGUF is the most portable format, but it's not the only game. If you're serving on vLLM-class infrastructure, native precision formats give you better quality per bit — and hybrid runtimes let one modest GPU run models it was never meant to hold.*

<strong>Format comparison:</strong>

<div class="md-table"><table style="text-align:left">
<thead>
<tr>
<th style="text-align:left">Format</th>
<th style="text-align:left">Precision</th>
<th style="text-align:left">Native Support</th>
<th style="text-align:left">Best For</th>
<th style="text-align:left">Notes</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left">GGUF (Q4_K_M, IQ3_S…)</td>
<td style="text-align:left">2.5–8 bpw</td>
<td style="text-align:left">llama.cpp, LM Studio, Ollama, llama-swap, Strata</td>
<td style="text-align:left">Consumer, hybrid offload, portability</td>
<td style="text-align:left">The universal format. Widest backend support. IQ-variants squeeze more quality per bit at the low end.</td>
</tr>
<tr>
<td style="text-align:left">AutoRound W4A16</td>
<td style="text-align:left">4-bit weights / 16-bit activations</td>
<td style="text-align:left">vLLM</td>
<td style="text-align:left">Dense models on a single 24GB card</td>
<td style="text-align:left">Best quality-per-bit for 27B-class dense models — the "full model on one consumer GPU" answer pre-hybrid.</td>
</tr>
<tr>
<td style="text-align:left">FP8 (E4M3)</td>
<td style="text-align:left">8-bit</td>
<td style="text-align:left">vLLM, TensorRT-LLM, Radiance (FP8 PLE)</td>
<td style="text-align:left">Ada+ / RDNA4+ serving, near-lossless quality</td>
<td style="text-align:left">~2x the memory of W4, close to BF16 quality. The production default on modern silicon.</td>
</tr>
<tr>
<td style="text-align:left">NVFP4 / MXFP4</td>
<td style="text-align:left">4-bit float, per-block scaling</td>
<td style="text-align:left">vLLM (Blackwell); MXFP4 cross-vendor (emerging)</td>
<td style="text-align:left">RTX 50xx / B200 class</td>
<td style="text-align:left">Emerging. 2x FP8's memory efficiency at near-INT4 quality. Checkpoint availability is still lab-flagship only.</td>
</tr>
</tbody>
</table></div>

<strong>vLLM launch commands:</strong>

<pre><code># FP8 native — 2-GPU tensor parallel (e.g., dual R9700 via Radiance, or dual NVIDIA)
vllm serve d0xin/Swift-Qwen3.8-27B-Uncensored-FP8 \
  --tensor-parallel-size 2 \
  --max-model-len 262144

# AutoRound W4A16 — single 24GB GPU, full 27B model
vllm serve &lt;auto-round-w4a16-checkpoint&gt; \
  --quantization compressed-tensors \
  --max-model-len 131072 \
  --gpu-memory-utilization 0.92

# Radiance (AMD) — adaptive MTP speculative decoding
vllm serve &lt;model&gt; \
  --tensor-parallel-size 2 \
  --speculative-config '{"method": "mtp", "num_draft_tokens": 8}'</code></pre>

<strong>Strata — hybrid VRAM+RAM+SSD:</strong>

<p>Strata is a one-click runtime that turns three tiers of storage into one model pool. The way it works with MoE models:</p>

<ul>
<li><strong>VRAM tier:</strong> attention layers, shared experts, and the <em>hot</em> MoE experts (the ones your workload actually hits) live in GPU memory — ~13GB of a 125B model's 6892 experts, in one community build.</li>
<li><strong>RAM tier:</strong> warm experts sit in DDR. Dual-rank 3600+ keeps the lookup fast.</li>
<li><strong>SSD tier:</strong> cold experts are paged from NVMe on demand. A fast 990 Pro class drive is the difference between "feels instant" and "stutters on new topics."</li>
<li><strong>Prompt cache:</strong> ~90% hit rate on repeated conversation prefixes → 0.3–0.8s resume on 50k-token contexts.</li>
<li><strong>MTP speculative decoding</strong> (draft + verify) pushes decode to 99–128 tok/s on a single 24GB card.</li>
<li><strong>API:</strong> OpenAI- and Anthropic-compatible, so your existing agent stacks point at it unchanged.</li>
</ul>

<p><strong>WSL2 note:</strong> Windows users running Strata under WSL2 must set an explicit RAM cap in <code>.wslconfig</code> (e.g., <code>memory=96GB</code>). WSL2's default (half of host RAM) silently starves the RAM tier and the hybrid stops behaving like a hybrid. One of the most common "it works for them but not me" issues in the submissions.</p>

<p><a href="https://github.com/Niko1221/Strata" rel="noopener nofollow ugc">Strata on GitHub</a></p>

<strong>Radiance — AMD high-throughput serving:</strong>

<p>Radiance is a tuned vLLM fork with a native amdgpu backend, optimized for RDNA3/RDNA4. Where Strata optimizes for <em>capacity</em>, Radiance optimizes for <em>throughput</em>:</p>

<ul>
<li>200+ tok/s decode with adaptive MTP on dual R9700 (community-verified, Example B)</li>
<li>5200–6200 tok/s prefill — large-context ingestion is the standout number</li>
<li>Everything stays in VRAM+RAM; no disk tier. If the model doesn't fit, that's not Radiance's problem to solve — use Strata for that.</li>
<li>Supports FP8 PLE, IQ4, and W4A16 weights</li>
</ul>

<p><a href="https://github.com/magiccodingman/vllm-radiance" rel="noopener nofollow ugc">Radiance on GitHub</a></p>

<strong>NVFP4 / MXFP4 — the emerging 4-bit float:</strong>

<ul>
<li><strong>NVFP4</strong> is NVIDIA's 4-bit float with 16-element per-block scaling, hardware-accelerated on Blackwell (RTX 50xx, B200). <strong>MXFP4</strong> is the OCP microscaling standard — the same idea, cross-vendor (AMD, Intel).</li>
<li>They deliver ~2x the memory efficiency of FP8 at quality close to well-calibrated INT4 — the best of both rows in the format table.</li>
<li>Checkpoint availability is the bottleneck: currently lab-flagship models only. The moment a 27B–70B NVFP4 release becomes routine, the 24GB tier effectively doubles in capacity.</li>
<li>Matrix position: tracked, not yet standard. Submissions of NVFP4 runs are actively wanted.</li>
</ul>

<strong>Which format should I use?</strong>

<ul>
<li><strong>Your backend is llama.cpp / Ollama / LM Studio / llama-swap / Strata?</strong> → GGUF. It's the only format they take. Q4_K_M for quality, IQ3_S when you need the size.</li>
<li><strong>vLLM on Ada or Blackwell, and FP8 fits your VRAM?</strong> → FP8. Near-lossless, production-proven.</li>
<li><strong>vLLM and you need 2x the memory efficiency?</strong> → AutoRound W4A16. The single-24GB-card answer for 27B dense.</li>
<li><strong>Blackwell and a lab released NVFP4 for your model?</strong> → Take it. It's the format curve bending in your favor.</li>
<li><strong>AMD on Radiance?</strong> → FP8 PLE first, IQ4 / W4A16 when you need headroom.</li>
<li><strong>The rule of thumb:</strong> weight precision follows your VRAM budget; KV precision follows your use case (Section 5). Don't quantize one to compensate for the other.</li>
</ul>

</details>

<details>
<summary>⚡ The KV Cache Rule: When To Quantize (And When NOT To)</summary>

<blockquote>
<strong>Baseline: keep the KV cache at FP16/BF16.</strong> Quantize it only when context demand exceeds what unquantized KV can hold in your VRAM. KV quantization trades long-context coherence for capacity — it's a lever, not a setting.
</blockquote>

<strong>Do NOT quantize KV when:</strong>

<ul>
<li><strong>You're not context-bound.</strong> If FP16 KV fits with headroom to spare, there's nothing to gain. The quantization cost (coherence drift) is real; the benefit is imaginary.</li>
<li><strong>Your workload is coherence-critical.</strong> Research RAG, agentic coding over large repos, multi-step reasoning — these live and die on retrieval quality at 100k+ tokens. Quantized KV degrades exactly the part these tasks depend on.</li>
<li><strong>You're running a small model.</strong> On 4B–9B models, KV is a small fraction of total VRAM. The savings are negligible and the quality cost isn't.</li>
</ul>

<strong>Quantizing KV IS acceptable when:</strong>

<ul>
<li><strong>Large MoE/dense model, KV is the binding constraint</strong> on context length — you've hit the wall and more context is worth some drift.</li>
<li><strong>Creative writing / roleplay</strong> — minor long-context drift is within tolerance for the genre; community RP setups routinely run INT8/Q8 KV.</li>
<li><strong>Multi-client serving</strong> — per-client KV footprint determines how many concurrent sessions you can hold; FP8 KV roughly doubles your client ceiling.</li>
<li><strong>Batch / unattended runs</strong> — nothing is reviewing output quality in real time, and capacity lets the batch finish at all.</li>
</ul>

<strong>Precision scaling — take the smallest step that works:</strong>

<ol>
<li><strong>FP8 KV</strong> — halves the KV footprint, minimal quality impact. The first move in almost every case.</li>
<li><strong>INT8 / Q8_0</strong> — similar footprint, slightly more drift. Common in llama.cpp-based stacks (see Example A: Q8_0 at 65k with NIAH hit).</li>
<li><strong>INT4 KV</strong> — quarter the footprint. Last resort; expect measurable coherence decay past 32–64k tokens.</li>
</ol>

<p>Model weights and KV cache are independent dials. A Q4-weighted model with FP16 KV is a perfectly sane configuration — and often the right one for long-context work.</p>

<strong>What the community data shows:</strong> s1ugh34d's finding — <em>server-side KV is often already quantized</em>. Many vLLM-class deployments ship with FP8 (or lower) KV as the engine default, and some engines quantize KV without announcing it. Before you assume you're running "FP16 KV," check what your engine is actually doing — <code>kv_cache_setting</code> in your submission should reflect the <em>real</em> dtype, not the launch flag.</p>

</details>

<details>
<summary>⚡ Real-World Constraints — Power, Thermals, PCIe, RAM</summary>

*Spec sheets don't mention what actually stops a build from working. These are the constraints that show up in community submissions week after week.*

<div class="md-table"><table style="text-align:left">
<thead>
<tr>
<th style="text-align:left">Constraint</th>
<th style="text-align:left">Why It Matters</th>
<th style="text-align:left">Typical Limit</th>
<th style="text-align:left">Mitigation</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left"><strong>Power</strong></td>
<td style="text-align:left">Sustained inference load, not burst. Two 4090-class cards draw ~700W at the slots alone; the platform adds 200–400W more</td>
<td style="text-align:left">1000–1600W quality PSU for 2–4 card builds</td>
<td style="text-align:left">Power caps / undervolts (nvidia-smi, amd-smi), 80+ Platinum units, meter your wall draw</td>
</tr>
<tr>
<td style="text-align:left"><strong>Thermals</strong></td>
<td style="text-align:left">Boost clocks decay under sustained load; dense cards in closed cases throttle within 30–60 min</td>
<td style="text-align:left">Case airflow, not raw component quality</td>
<td style="text-align:left">High-CFM intake/exhaust, blower-style cards for tight builds, power cap before you touch clock curves</td>
</tr>
<tr>
<td style="text-align:left"><strong>PCIe lanes</strong></td>
<td style="text-align:left">x16/x8/x4 splits gate CPU offload bandwidth; NVMe drives can share chipset lanes with GPUs</td>
<td style="text-align:left">16 lanes per GPU on desktop; x8/x8 on many 4-slot boards</td>
<td style="text-align:left">Map your lane budget before buying, M.2 on CPU-direct slots, risers that preserve x8</td>
</tr>
<tr>
<td style="text-align:left"><strong>System RAM</strong></td>
<td style="text-align:left">The second tier for hybrid offload; CPU+GPU inference lives and dies by it</td>
<td style="text-align:left">64–256GB DDR4/DDR5 dual-rank</td>
<td style="text-align:left">Strata-style tiering; fast dual-rank kits beat big slow kits for expert lookups</td>
</tr>
<tr>
<td style="text-align:left"><strong>Physical space</strong></td>
<td style="text-align:left">3–4 slot cards, long PCBs, E-ATX requirements for 2+ big GPUs</td>
<td style="text-align:left">Full-size ATX minimum for 2+ high-end cards</td>
<td style="text-align:left">SFF builds with external GPU options; measure clearance before ordering</td>
</tr>
<tr>
<td style="text-align:left"><strong>OS maturity</strong></td>
<td style="text-align:left">Driver/backend support varies wildly: Linux is the most mature serving target; Windows is fine for desktop; WSL2 has the RAM-allocation quirk; macOS is Metal-only</td>
<td style="text-align:left">Linux first for anything you serve 24/7</td>
<td style="text-align:left">Pin known-good driver versions, test the full stack on Linux before committing hardware</td>
</tr>
<tr>
<td style="text-align:left"><strong>Storage</strong></td>
<td style="text-align:left">Model repos are 10–80GB each; Strata's SSD tier demands fast NVMe; cold-load TTFT scales with drive speed</td>
<td style="text-align:left">1–4TB NVMe for a serious model library</td>
<td style="text-align:left">Multiple NVMe drives, separate OS/model/cache volumes, RAID 0 for the Strata cold tier</td>
</tr>
</tbody>
</table></div>

<p><strong>How hybrid changes the power equation:</strong> With Strata-style offload, the GPU carries only attention plus hot experts while RAM and NVMe absorb the rest. Total system draw drops (the card idles more between expert lookups) even as model size scales up. A 125B MoE on a 450W-capped 4090 + 128GB DDR4 (Example C) sips less power than a dense 70B held in pure VRAM — which is why hybrid builds are the sleeper pick for 24/7 always-on serving.</p>

</details>

<details>
<summary>📊 Community Data Viewport — All Submissions Indexed</summary>

*Auto-generated index of all community submissions. Multiple views of the same data — pick the angle that answers your question.*

🌐 For interactive filtering, sorting, and comparison: <a href="https://madgoathaz.github.io/llm-matrix/" rel="noopener nofollow ugc">Open the Dashboard</a>

The static views below are regenerated weekly from the submission data. The dashboard is always current; these tables are the snapshot.

<details>
<summary>View by Tier</summary>

*The same six VRAM brackets used by the Master Matrix in Post #1.*

<strong>Tier 1: ≤16GB</strong>

<div class="md-table"><table style="text-align:left">
<thead>
<tr>
<th style="text-align:left">Submitter</th>
<th style="text-align:left">Hardware</th>
<th style="text-align:left">Model</th>
<th style="text-align:left">Quant</th>
<th style="text-align:left">Backend</th>
<th style="text-align:left">Decode tok/s</th>
<th style="text-align:left">Context</th>
<th style="text-align:left">KV</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left" colspan="8">[Auto-generated by tools/generate.py — run weekly]</td>
</tr>
</tbody>
</table></div>

<strong>Tier 2: 16–24GB</strong>

<div class="md-table"><table style="text-align:left">
<thead>
<tr>
<th style="text-align:left">Submitter</th>
<th style="text-align:left">Hardware</th>
<th style="text-align:left">Model</th>
<th style="text-align:left">Quant</th>
<th style="text-align:left">Backend</th>
<th style="text-align:left">Decode tok/s</th>
<th style="text-align:left">Context</th>
<th style="text-align:left">KV</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left" colspan="8">[Auto-generated by tools/generate.py — run weekly]</td>
</tr>
</tbody>
</table></div>

<strong>Tier 3: 24–32GB</strong>

<div class="md-table"><table style="text-align:left">
<thead>
<tr>
<th style="text-align:left">Submitter</th>
<th style="text-align:left">Hardware</th>
<th style="text-align:left">Model</th>
<th style="text-align:left">Quant</th>
<th style="text-align:left">Backend</th>
<th style="text-align:left">Decode tok/s</th>
<th style="text-align:left">Context</th>
<th style="text-align:left">KV</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left" colspan="8">[Auto-generated by tools/generate.py — run weekly]</td>
</tr>
</tbody>
</table></div>

<strong>Tier 4: 48–64GB</strong>

<div class="md-table"><table style="text-align:left">
<thead>
<tr>
<th style="text-align:left">Submitter</th>
<th style="text-align:left">Hardware</th>
<th style="text-align:left">Model</th>
<th style="text-align:left">Quant</th>
<th style="text-align:left">Backend</th>
<th style="text-align:left">Decode tok/s</th>
<th style="text-align:left">Context</th>
<th style="text-align:left">KV</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left" colspan="8">[Auto-generated by tools/generate.py — run weekly]</td>
</tr>
</tbody>
</table></div>

<strong>Tier 5: 96–128GB</strong>

<div class="md-table"><table style="text-align:left">
<thead>
<tr>
<th style="text-align:left">Submitter</th>
<th style="text-align:left">Hardware</th>
<th style="text-align:left">Model</th>
<th style="text-align:left">Quant</th>
<th style="text-align:left">Backend</th>
<th style="text-align:left">Decode tok/s</th>
<th style="text-align:left">Context</th>
<th style="text-align:left">KV</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left" colspan="8">[Auto-generated by tools/generate.py — run weekly]</td>
</tr>
</tbody>
</table></div>

<strong>Tier 6: 196–256GB+</strong>

<div class="md-table"><table style="text-align:left">
<thead>
<tr>
<th style="text-align:left">Submitter</th>
<th style="text-align:left">Hardware</th>
<th style="text-align:left">Model</th>
<th style="text-align:left">Quant</th>
<th style="text-align:left">Backend</th>
<th style="text-align:left">Decode tok/s</th>
<th style="text-align:left">Context</th>
<th style="text-align:left">KV</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left" colspan="8">[Auto-generated by tools/generate.py — run weekly]</td>
</tr>
</tbody>
</table></div>

</details>

<details>
<summary>View by Hardware Vendor</summary>

*The same data, sliced by silicon — NVIDIA, AMD, and Apple side by side.*

<div class="md-table"><table style="text-align:left">
<thead>
<tr>
<th style="text-align:left">Submitter</th>
<th style="text-align:left">Vendor</th>
<th style="text-align:left">Hardware</th>
<th style="text-align:left">Model</th>
<th style="text-align:left">Backend</th>
<th style="text-align:left">Decode tok/s</th>
<th style="text-align:left">Context</th>
<th style="text-align:left">Power Draw</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left" colspan="8">[Auto-generated by tools/generate.py — run weekly]</td>
</tr>
</tbody>
</table></div>

</details>

<details>
<summary>View by Backend</summary>

*Which runtime is producing which results — the best way to sanity-check a backend choice for your hardware.*

<div class="md-table"><table style="text-align:left">
<thead>
<tr>
<th style="text-align:left">Submitter</th>
<th style="text-align:left">Backend</th>
<th style="text-align:left">Hardware</th>
<th style="text-align:left">Model</th>
<th style="text-align:left">Decode tok/s</th>
<th style="text-align:left">Prefill tok/s</th>
<th style="text-align:left">TTFT (cold)</th>
<th style="text-align:left">Context</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left" colspan="8">[Auto-generated by tools/generate.py — run weekly]</td>
</tr>
</tbody>
</table></div>

</details>

<details>
<summary>View by Speed</summary>

*Sorted by decode throughput, fastest first. The "what's actually fast" view — independent of model size, so read the model column before drawing conclusions.*

<div class="md-table"><table style="text-align:left">
<thead>
<tr>
<th style="text-align:left">Rank</th>
<th style="text-align:left">Submitter</th>
<th style="text-align:left">Hardware</th>
<th style="text-align:left">Model</th>
<th style="text-align:left">Backend</th>
<th style="text-align:left">Decode tok/s</th>
<th style="text-align:left">Prefill tok/s</th>
<th style="text-align:left">Power Draw</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left" colspan="8">[Auto-generated by tools/generate.py — run weekly]</td>
</tr>
</tbody>
</table></div>

</details>

<details>
<summary>All Submissions (Chronological)</summary>

*The complete index in submission order — the raw feed the other views are cut from.*

<div class="md-table"><table style="text-align:left">
<thead>
<tr>
<th style="text-align:left">#</th>
<th style="text-align:left">Date</th>
<th style="text-align:left">Submitter</th>
<th style="text-align:left">Hardware</th>
<th style="text-align:left">Model + Quant</th>
<th style="text-align:left">Backend</th>
<th style="text-align:left">Engine Mode</th>
<th style="text-align:left">Verdict</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left" colspan="8">[Auto-generated by tools/generate.py — run weekly]</td>
</tr>
</tbody>
</table></div>

</details>

</details>

<details>
<summary>📅 Full Changelog</summary>

*The complete version history of this guide and the matrix it feeds.*

<div class="md-table"><table style="text-align:left">
<thead>
<tr>
<th style="text-align:left">Version</th>
<th style="text-align:left">Date</th>
<th style="text-align:left">What Changed</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left"><strong>v1.0</strong></td>
<td style="text-align:left">2026-08</td>
<td style="text-align:left">Initial matrix release. Six-tier VRAM system (≤16GB → 196-256GB+), core submission template, Master Matrix in Post #1, basic backend guide (Ollama, LM Studio, llama.cpp, vLLM).</td>
</tr>
<tr>
<td style="text-align:left"><strong>v2.0</strong></td>
<td style="text-align:left">2026-09</td>
<td style="text-align:left">Strata (hybrid VRAM+RAM+SSD) and Radiance (AMD high-throughput) added to the backend table. Hardware vendor notes (NVIDIA / AMD / Apple). KV cache quantization rule. Real-world constraints section. Community dashboard launch. TensorRT-LLM, MLX, Colibri, Unsloth Desktop rows completed.</td>
</tr>
<tr>
<td style="text-align:left"><strong>v2.1</strong></td>
<td style="text-align:left">2026-10</td>
<td style="text-align:left"><code>engine_mode</code> field added to the Full Submit template. Non-GGUF format guide (AutoRound, FP8, NVFP4/MXFP4) with vLLM launch commands. Community Data Viewport with five static views (tier / vendor / backend / speed / chronological). Confidence levels (✅ 📡📡 📡 📐) and entry lifecycle (🟢 🟡 🔴) applied to all matrix data. Post #2 restructured as the Reference post.</td>
</tr>
</tbody>
</table></div>

</details>

<details>
<summary>ℹ️ How Your Submission Becomes Matrix Data</summary>

*Here's the pipeline. No black box — every step is visible.*

<strong>The flow:</strong>

<ol>
<li><strong>You submit</strong> — Quick or Full, below this post. That's the whole ask.</li>
<li><strong>OP reviews weekly</strong> — submissions are read, questions are asked in-thread when a number looks off, and valid entries are parsed into the dataset.</li>
<li><strong>It appears in the index</strong> — your entry shows up in the Community Dashboard and in the Viewport tables above (Section 7), credited to you.</li>
<li><strong>Promotion to the Master Matrix</strong> — when an entry is confirmed by <strong>2+ independent sources</strong> (matching hardware, model, and behavior) <em>or</em> is <strong>personally tested by OP</strong>, it gets promoted into the Master Matrix in Post #1. The front door only shows data that has survived contact with reality.</li>
</ol>

<strong>Confidence levels — what the badges in the matrix mean:</strong>

<div class="md-table"><table style="text-align:left">
<thead>
<tr>
<th style="text-align:left">Badge</th>
<th style="text-align:left">Meaning</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left">✅ <strong>OP-verified</strong></td>
<td style="text-align:left">Personally tested on OP's hardware. The strongest claim in the matrix.</td>
</tr>
<tr>
<td style="text-align:left">📡📡 <strong>Community (2+)</strong></td>
<td style="text-align:left">Reported by two or more independent submitters with consistent results. Matrix-standard.</td>
</tr>
<tr>
<td style="text-align:left">📡 <strong>Community (1)</strong></td>
<td style="text-align:left">Single source, not yet corroborated. Treated as a lead, not a fact.</td>
</tr>
<tr>
<td style="text-align:left">📐 <strong>Calculated</strong></td>
<td style="text-align:left">Derived from published specs (VRAM math, bandwidth estimates) — not measured on real hardware.</td>
</tr>
</tbody>
</table></div>

<strong>Entry lifecycle — where an entry is in its life:</strong>

<ul>
<li>🟢 <strong>Current</strong> — active, accurate, recommended. This is what you're looking for.</li>
<li>🟡 <strong>Watch</strong> — something changed (driver update, backend release, model revision); revalidation is pending. Usable, but check the notes.</li>
<li>🔴 <strong>Superseded</strong> — replaced by a newer entry. Kept for history and attribution, not for recommendation.</li>
</ul>

<strong>What gets highlighted vs. standard entries:</strong>

<ul>
<li><strong>Highlighted</strong> (featured in Post #1's community picks): first-of-tier reports, 2+ verifications of a new configuration, performance outliers that beat the current tier record, and setups that change the recommendation math (like the Strata 125B-on-24GB entry).</li>
<li><strong>Standard</strong>: everything else — indexed in the Viewport and dashboard, fully credited, and eligible for promotion the moment it's corroborated. No submission is too small to matter; a Quick Submit that confirms someone else's numbers is what turns 📡 into 📡📡.</li>
</ul>

<p><strong>Your name is always credited. Your data is always attributed.</strong></p>

<strong>What we're improving next</strong> (feedback welcome in-thread):

<ul>
<li>Metrics coverage — TTFT prefill latency, PCIe bandwidth bottlenecks, watts-per-token, speculative draft pairings, NIAH pass rates at specific context lengths</li>
<li>VRAM tier brackets — do the current six reflect how people actually build?</li>
<li>Deployment recipes — Docker Compose, systemd units, multi-GPU launch command collections</li>
<li>Vendor depth — per-GPU ROCm versions, Vulkan flags, Metal kernel notes</li>
<li>Model categories and serving patterns — vision/audio/coding splits, draft+verify workflows, round-robin vs. sticky sessions</li>
</ul>

</details>
