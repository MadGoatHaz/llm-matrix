# Community Submissions, Hardware Feedback & Thread Evolution

**Rather than running rigid polls right out of the gate, this thread is designed to gather real-world, operational data from the community.** Automated benchmarks and leaderboards miss how setups actually behave day-to-day — I want to know what you're actually loading up, what you use it for, and how you have it tuned.

Use this space to share your daily drivers, niche workflow solutions, hardware limits, and suggestions on how to improve this living guide.

<hr>

**Quick Navigation:**

<ul>
<li>📝 What I Want to Hear From You</li>
<li>📋 Standardized Submission Template</li>
<li>💡 Thread Feedback &amp; Suggested Changes</li>
<li>✅ Example Submissions (What Good Looks Like)</li>
</ul>

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
<summary>📋 Standardized Submission Template (Copy/Paste This)</summary>

To keep submissions consistent and allow aggregation into the <strong>Master Matrix (Post #1)</strong>, use this format when posting your setup:

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
[/COMMUNITY-SUBMISSION]</code></pre>

<em>(You don't have to fill out every line if you're just dropping casual thoughts, but using the structured block makes it easy to integrate your numbers directly into the master matrix. New fields: <code>os_driver</code>, <code>weight_precision</code>, <code>prefill_tps</code>, <code>ttft_cold</code>, <code>power_draw</code> — all optional but help with hardware-specific recommendations.)</em>

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

<em>These are the kinds of details that make the matrix useful. The more specific you can be about context limits, KV settings, and real-world quirks, the more value your submission adds to the community.</em>

</details>
