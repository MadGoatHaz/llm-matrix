# Community Submissions, Hardware Feedback & Thread Evolution

**Rather than running rigid polls right out of the gate, this thread is designed to gather real-world, operational data from the community.** Automated benchmarks and leaderboards miss how setups actually behave day-to-day — I want to know what you're actually loading up, what you use it for, and how you have it tuned.

Use this space to share your daily drivers, niche workflow solutions, hardware limits, and suggestions on how to improve this living guide.

<hr>

**Quick Navigation:**

<ul>
<li>🌱 Start Here: New to Local LLMs?</li>
<li>📝 What I Want to Hear From You</li>
<li>📋 Submission Templates (Quick + Full)</li>
<li>⚙️ Backend Selection Guide</li>
<li>🧰 Supporting Software <em>(see Post #1)</em></li>
<li>💡 Thread Feedback &amp; Suggested Changes</li>
<li>✅ Example Submissions</li>
</ul>

<details>
<summary>🌱 Start Here: New to Local LLMs? (Decision Flow)</summary>

*A quick path from "I want to run a local AI" to "I know what to buy and how to set it up." Follow the questions that match your situation.*

<strong>Q1: What's your budget?</strong>

<ul>
<li><strong>Under $500 (used/entry):</strong> Look at Tier 1. A used RTX 3060 12GB or RX 7600 8GB gets you started. You'll run 7-9B models at Q4. Expect 20-40 tok/s. Start with Ollama + LM Studio for zero-config ease.</li>
<li><strong>$500–$1,500 (single modern GPU):</strong> Tier 1-2. RTX 4060 Ti 16GB, RX 7900 XT 20GB, or RTX 4080 16GB. You can run 27B models at Q4/W4A16. This is the sweet spot for most hobbyists.</li>
<li><strong>$1,500–$4,000 (high-end single or dual):</strong> Tier 3. RTX 4090 24GB, RX 7900 XTX 24GB, or 2x mid-range cards. Full 27B models with serious context.</li>
<li><strong>$4,000–$15,000 (multi-GPU workstation):</strong> Tier 4-5. 2-4x high-end GPUs. Production-grade serving, multi-client, extreme context.</li>
<li><strong>$15,000+ (server/enterprise):</strong> Tier 6. 8+ GPUs or Mac Studio Ultra. Running 70B+ models, multimodal, full speculative decoding stacks.</li>
<li><strong>Any budget + lots of RAM (hybrid):</strong> With <strong>Strata</strong>, a single 24GB GPU + 128GB system RAM can run 125B+ MoE models at 100+ tok/s. You don't need massive VRAM if you have fast RAM and NVMe. This changes the game for consumer builds.</li>
</ul>

<strong>Q2: What do you want to DO with it?</strong>

<ul>
<li><strong>Chat / general assistant:</strong> Tier 1 is fine. Qwen3.5-4B or Ornith-1.5-9B. Fast, cheap, always-on.</li>
<li><strong>Coding / agentic workflows:</strong> Tier 2 minimum. Swift-1.5-Qwen3.8-27b is the community pick. You need 256k context for real repo work.</li>
<li><strong>Creative writing / roleplay:</strong> Tier 1-2. Gemma-4 models excel here. KV quantization is acceptable.</li>
<li><strong>Research / RAG / document analysis:</strong> Tier 3+. You need FP16/BF16 KV cache and 100k+ context.</li>
<li><strong>Production serving (multiple users):</strong> Tier 4+. vLLM with multi-GPU tensor parallelism.</li>
</ul>

<strong>Q3: What's your comfort level?</strong>

<ul>
<li><strong>"I just want it to work":</strong> <strong>Unsloth Desktop</strong>. Download it, pick a model from the built-in hub, chat. No commands, no configs, no terminal. You'll be up in 5 minutes. It handles GGUF, safetensors, and FP8 models, works on NVIDIA/AMD/Apple, and gives you an OpenAI-compatible API server for free. (Ollama and LM Studio are lighter alternatives if you want minimal overhead.)</li>
<li><strong>"I'm comfortable with a terminal":</strong> llama.cpp directly, or Ollama with custom models. You can tune context, quantization, and sampling params.</li>
<li><strong>"I want maximum performance":</strong> vLLM with AutoRound W4A16 or FP8 quants. Continuous batching, PagedAttention, speculative decoding. Steeper learning curve, best throughput.
<ul>
<li>For AMD: <strong>Radiance</strong> gives you 200+ tok/s with MTP on R9700s.</li>
<li>For hybrid offload: <strong>Strata</strong> turns a single GPU + big RAM into a 125B model runner.</li>
</ul></li>
<li><strong>"I'm building a product":</strong> vLLM + LiteLLM proxy + Docker. Multi-model routing, load balancing, API-compatible serving.</li>
</ul>

<strong>Q4: NVIDIA, AMD, or Apple?</strong>

<ul>
<li><strong>NVIDIA:</strong> Easiest path. Every backend supports it. CUDA is the reference implementation. If you're new, start here.</li>
<li><strong>AMD:</strong> Great value. ROCm works well for inference (llama.cpp, vLLM). Slightly steeper setup. Best $/VRAM ratio for multi-GPU.</li>
<li><strong>Apple:</strong> Zero-config unified memory. A $4K Mac Studio gives you 64GB "VRAM." No multi-GPU scaling, but incredible simplicity. MLX is the native framework, and <strong>Unsloth Desktop</strong> supports Apple Silicon via MLX out of the box.</li>
</ul>

<p><strong>Still stuck?</strong> Post in the thread with your budget and use case. The community will point you to the right tier and model.</p>

</details>

<details>
<summary>📝 What I Want to Hear From You</summary>

Whether you're pushing multi-GPU tensor parallelism in headless servers or running daily local workflows on consumer cards and unified memory laptops, chime in on:

<ol>
<li><strong>What model &amp; quantization do you actually rely on?</strong>
AutoRound W4A16, GGUF Q4_K_M / IQ4_XS, native FP8, unquantized BF16, EXL2 4.0bpw — whatever you've dialled in.</li>

<li><strong>What is your primary use case?</strong>
Agentic coding, large repo ingestion, technical RAG, multi-step math/logic, casual chat, long-form creative writing, document translation, security research.</li>

<li><strong>How are you serving it?</strong>
<ul>
<li><em>Backend / runtime:</em> vLLM, direct llama.cpp, LM Studio, Ollama, Unsloth Desktop, llama-swap, Colibri, etc.</li>
<li><em>Architecture:</em> Single GPU, multi-GPU split (tensor parallel or row/layer offloading), host RAM offloading, CPU+GPU hybrid, custom RoPE/YaRN factors, speculative decoding (MTP / n-gram).</li>
<li><em>OS / Driver:</em> Linux (which distro), Windows, macOS. CUDA, ROCm, Vulkan, Metal.</li>
</ul></li>

<li><strong>Context &amp; KV behavior</strong>
Did you keep the KV cache unquantized (FP16/BF16), or did you drop to FP8/INT4? Where does the model hold coherence versus fall apart? What's your tested stable context limit?</li>

<li><strong>Performance numbers (optional but valuable)</strong>
Decode tok/s, prefill tok/s, TTFT (cold load), power draw (W), GPU utilization %.</li>
</ol>

</details>

<details>
<summary>📋 Submission Templates (Quick + Full)</summary>

To keep submissions consistent and allow aggregation into the <strong>Master Matrix (Post #1)</strong>, pick the format that matches how much detail you want to share:

<strong>Quick Submit (30 seconds):</strong>

<pre><code>[QUICK-SUBMIT]
gpu: [Your GPU model + VRAM]
model: [Model name + quant]
use_case: [What you use it for]
verdict: [One sentence: does it work? any quirks?]
[/QUICK-SUBMIT]</code></pre>

*That's it. If you have 30 seconds, this is enough to get your data into the matrix. No template gymnastics required.*

*Use Quick Submit for casual reports. Use Full Submit when you have benchmark numbers, context test results, or specific launch configs you want captured in the matrix.*

<strong>Full Submit (for detailed data):</strong>

<pre><code>[COMMUNITY-SUBMISSION]
tier: [≤16GB | 16-24GB | 24-32GB | 48-64GB | 96-128GB | 196-256GB+]
hardware: [e.g., 2x RX 7900 XTX 24GB, 4x MI210, 1x RTX 4060 Ti 16GB, Mac Studio 64GB]
backend: [vLLM | llama.cpp | LM Studio | Ollama | Unsloth Desktop | llama-swap | Colibri | Other]
os_driver: [Linux/CUDA | Linux/ROCm | Linux/Vulkan | Windows/CUDA | macOS/Metal | Other]
model_name: [Full model repository or exact filename]
quant_package: [e.g., AutoRound W4A16, GGUF Q4_K_M, EXL2 4.0bpw, FP8, I-Nano]
weight_precision: [W4A16 | W8A8 | FP8 | BF16 | Q4_K_M | Q8_0 | Other]
download_url: [Hugging Face or model source link]
primary_use_case: [e.g., Agentic coding, Deep reasoning, Creative writing, RAG, Translation]
stable_context_tested: [Actual token count tested without OOM or coherence collapse]
kv_cache_setting: [Native FP16/BF16 | FP8 | INT4 | Q8_0]
throughput_tps: [Decode tok/s]
prefill_tps: [Prefill tok/s (if measured)]
ttft_cold: [Seconds for first token after cold load]
power_draw: [Watts at peak (if measured)]
setup_notes: [Launch flags, rope/yarn config, host RAM offload, prompt prefill behavior, quirks]
engine_mode: [VRAM-only | Hybrid (VRAM+RAM) | Hybrid (VRAM+RAM+SSD) | CPU+GPU]
[/COMMUNITY-SUBMISSION]</code></pre>

<em>(You don't have to fill out every line if you're just dropping casual thoughts, but using the structured block makes it easy to integrate your numbers directly into the master matrix. New fields: <code>os_driver</code>, <code>weight_precision</code>, <code>prefill_tps</code>, <code>ttft_cold</code>, <code>power_draw</code> — all optional but help with hardware-specific recommendations. (New optional field: <code>engine_mode</code> — specifies whether your setup is pure VRAM, hybrid offload (Strata-style), or CPU+GPU. This helps the matrix accurately represent what's actually running where.)</em>

</details>

<details>
<summary>⚙️ Backend Selection Guide — Which Runtime Should You Use?</summary>

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
<td style="text-align:left">One-click install, OpenAI/Anthropic API, prompt cache (90% hits), MTP speculative decoding, runs 125B on a single 24GB card. WSL2 requires .wslconfig RAM allocation. <a href="https://github.com/Niko1221/Strata">GitHub</a></td>
</tr>
<tr>
<td style="text-align:left"><strong>Radiance</strong></td>
<td style="text-align:left">AMD-optimized high-throughput inference (RDNA3/4)</td>
<td style="text-align:left">IQ4, FP8 PLE, W4A16</td>
<td style="text-align:left">Multi-GPU (AMD)</td>
<td style="text-align:left">🟡 Moderate</td>
<td style="text-align:left">200+ tok/s decode with MTP on dual R9700. 5200-6200 tok/s prefill. Native amdgpu backend. Everything in VRAM+RAM, no disk. <a href="https://github.com/magiccodingman/vllm-radiance">GitHub</a></td>
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

<p><em>For frontends, agent harnesses, and orchestration tools that pair with your local models, see the <strong>Supporting Software &amp; Ecosystem</strong> section in Post #1.</em></p>

<p><strong>The Golden Rule:</strong> Start with the simplest backend that meets your needs. You can always migrate to a more powerful one later. Your model weights (GGUF or Safetensors) are portable across backends.</p>

</details>

<details>
<summary>💡 Thread Feedback &amp; Suggested Changes</summary>

This living guide is built for the forum. If there's something missing, unhelpful, or formatted poorly in <strong>Post #1</strong>, let me know:

<ul>
<li><strong>What metrics should this thread track?</strong> Time-To-First-Token prefill latency, PCIe bandwidth bottlenecks, power draw / watts-per-token, speculative draft model pairings, NIAH pass rates at specific context lengths?</li>
<li><strong>VRAM tier restructuring:</strong> Do the current brackets (≤16GB, 16-24GB, 24-32GB, 48-64GB, 96-128GB, 196-256GB+) reflect how you build systems, or should I adjust them?</li>
<li><strong>Deployment examples:</strong> Would container recipes (Docker Compose), systemd service templates, or specific vLLM / llama.cpp multi-GPU launch commands be helpful in collapsible tabs?</li>
<li><strong>AMD / Apple coverage:</strong> Are the vendor notes sufficient, or do you need deeper per-GPU guidance (specific ROCm versions, Vulkan flags, Metal kernel tweaks)?</li>
<li><strong>What am I missing?</strong> Model categories (vision, audio, coding-specific), workflow pairings (draft + verify), or serving patterns (round-robin, sticky sessions)?</li>
</ul>

Drop your configurations, battle-tested setups, and suggestions below!

</details>

<details>
<summary>✅ Example Submissions (What Good Looks Like)</summary>

Here are two examples of well-structured submissions from the thread:

<strong>Example A — Consumer AMD (llama-swap):</strong>

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

<strong>Example B — Multi-GPU NVIDIA (vLLM):</strong>

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

<strong>Example C — Hybrid Offload (Strata):</strong>

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
throughput_tps: 99-128 decode (median 108)
prefill_tps: 825-3600 (median ~2800 with 90% prompt cache)
engine_mode: Hybrid (VRAM+RAM+SSD)
power_draw: 450W stock cap
setup_notes: 125B MoE on single 24GB card. 6892 experts: 13.4GB VRAM, rest RAM, lookup NVMe. MTP=4+lookup=3. Prompt cache 90% hits → 0.3-0.8s resume on 50k contexts. WSL2 needs explicit .wslconfig RAM.
[/COMMUNITY-SUBMISSION]</code></pre>

<em>These are the kinds of details that make the matrix useful. The more specific you can be about context limits, KV settings, and real-world quirks, the more value your submission adds to the community.</em>

</details>
