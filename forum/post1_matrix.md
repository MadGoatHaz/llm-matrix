# The Local LLM Matrix

**A community-driven reference for running local AI models on real silicon.**

Built by the [Level1Techs](https://forum.level1techs.com) Machine Learning, LLMs & AI community.

> 🌐 **[Interactive Dashboard →](https://madgoathaz.github.io/llm-matrix/)** — Filter by GPU, use case, backend, speed. Compare setups. Find your model in 10 seconds.

---

## 🚀 Find Your Setup in 30 Seconds

**What GPU do you have?**

<div class="md-table">
<table>
<thead>
<tr>
<th style="text-align:left">Your GPU</th>
<th style="text-align:left">Your Tier</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left">RTX 4060 Ti 16GB / RTX 3060 12GB / RX 7600 XT / Radeon VII</td>
<td style="text-align:left">Tier 1 (≤16GB)</td>
</tr>
<tr>
<td style="text-align:left">RTX 4080 16GB / RX 7900 XT 20GB / RTX A4000</td>
<td style="text-align:left">Tier 2 (16-24GB)</td>
</tr>
<tr>
<td style="text-align:left">RTX 3090 / RTX 4090 / RX 7900 XTX / R9700</td>
<td style="text-align:left">Tier 3 (24-32GB)</td>
</tr>
<tr>
<td style="text-align:left">2x 3090/4090 / 2x R9700 / 4x A4000 / Mac Studio 64GB</td>
<td style="text-align:left">Tier 4 (48-64GB)</td>
</tr>
<tr>
<td style="text-align:left">4x 3090/4090 / 4x R9700 / 4x MI210 / 2x A100 80GB</td>
<td style="text-align:left">Tier 5 (96-128GB)</td>
</tr>
<tr>
<td style="text-align:left">8x GPUs / 4x MI300X / Mac Studio 192-256GB</td>
<td style="text-align:left">Tier 6 (196GB+)</td>
</tr>
</tbody>
</table>
</div>

*Don't see yours? Total VRAM is what matters. Between tiers? Plan for the lower one.*

**What do you want to do?**

<div class="md-table">
<table>
<thead>
<tr>
<th style="text-align:left">I want to...</th>
<th style="text-align:left">Start with</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left">Code / agentic workflows</td>
<td style="text-align:left">Swift-1.5-Qwen3.8-27b (any tier)</td>
</tr>
<tr>
<td style="text-align:left">Chat / general assistant</td>
<td style="text-align:left">Qwen3.5-4B or Ornith-1.5-9B (Tier 1)</td>
</tr>
<tr>
<td style="text-align:left">Read long documents / RAG</td>
<td style="text-align:left">Swift-1.5-Qwen3.8-27b with 256k+ context</td>
</tr>
<tr>
<td style="text-align:left">Creative writing / roleplay</td>
<td style="text-align:left">Gemma-4-26B-A4B-it (Tier 2-3)</td>
</tr>
<tr>
<td style="text-align:left">Maximum throughput / serving</td>
<td style="text-align:left">Qwen3.8-Flash-Next or Swift-1.5-Flash-Next (Tier 5+)</td>
</tr>
<tr>
<td style="text-align:left">Something niche (translation, etc.)</td>
<td style="text-align:left">Ask in the thread — the community has answers</td>
</tr>
</tbody>
</table>
</div>

---

<details>
<summary>📊 The Master Matrix</summary>

*The full reference. Expand a tier to see all recommended models, quants, and specs.*

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
<summary>🔬 Community Highlights — Impressive Setups From The Thread</summary>

<p>These are the setups that made us go "wait, what?" — real people, real hardware, real results.</p>

<div class="md-table">
<table>
<thead>
<tr>
<th style="text-align:left">Who</th>
<th style="text-align:left">Setup</th>
<th style="text-align:left">What They Did</th>
<th style="text-align:left">Why It's Notable</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left">Kif</td>
<td style="text-align:left">1x RTX 4090 + 128GB RAM</td>
<td style="text-align:left">Ran 125B Flash-Next (IQ3_S) at 108 tok/s via Strata</td>
<td style="text-align:left">Proof that a single consumer GPU + fast RAM can run models that "need" 100GB+ VRAM. 90% prompt cache hits.</td>
</tr>
<tr>
<td style="text-align:left">digitalscream</td>
<td style="text-align:left">2x R9700 32GB (AMD)</td>
<td style="text-align:left">Swift 1.5 Flash Next at 200+ tok/s via Radiance</td>
<td style="text-align:left">AMD's answer to vLLM. 5200-6200 tok/s prefill. "This thing is nuts." 200k+ token live agent sessions.</td>
</tr>
<tr>
<td style="text-align:left">lhl (Patron)</td>
<td style="text-align:left">Multiple systems, 96GB+ VRAM</td>
<td style="text-align:left">Evaluated Flash-Next vs GLM 5.3 vs DeepSeek 4.1 Flash</td>
<td style="text-align:left">"Run tens of billions of tokens through ds41f." DeepSeek 4.1 Flash slightly edged out the others in quality AND speed.</td>
</tr>
<tr>
<td style="text-align:left">manoreken2</td>
<td style="text-align:left">RTX 5090 + 1TB RAM (CPU+GPU hybrid)</td>
<td style="text-align:left">Translating 481 BCE Chinese government documents to Japanese</td>
<td style="text-align:left">671B models at 1 tok/s. Unattended batch. Proved model selection >> parameter count for niche domains.</td>
</tr>
<tr>
<td style="text-align:left">SgtAwesomesauce</td>
<td style="text-align:left">4x AMD v620 (96GB)</td>
<td style="text-align:left">Flash-Next W4A16 with 840k total KV capacity</td>
<td style="text-align:left">Custom ROCm vLLM recipe. 68-92 tok/s. 3.5s cold TTFT. ~900W from the wall.</td>
</tr>
</tbody>
</table>
</div>

<p><em>Full data with all specs: see the <a href="https://forum.level1techs.com/t/256443">thread</a> or the <a href="https://madgoathaz.github.io/llm-matrix/">dashboard</a>.</em></p>

</details>

## 💡 Got a Setup? Add It.

*The matrix is only as good as the data behind it.*

- **30 seconds:** Use the [Quick Submit](#) in Post #2 — just your GPU, model, and what you use it for.
- **5 minutes:** Use the [Full Submit](#) template — add your benchmarks, context tests, power draw.
- **Your name goes in the changelog.** Every submission that gets integrated is credited in the weekly update.

→ **[Post #2: Templates, Guides & Reference](/t/256443/2)**

## 📅 Recent Updates

<details>
<summary>Changelog</summary>

<div class="md-table">
<table>
<thead>
<tr>
<th style="text-align:left">Date</th>
<th style="text-align:left">Version</th>
<th style="text-align:left">What Changed</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align:left">2026-10-12</td>
<td style="text-align:left">v2.1</td>
<td style="text-align:left">R9700 + v620 in GPU lookup. Strata + Radiance added. NVFP4/MXFP4 noted. DeepSeek 4.1 Flash in matrix. Hybrid/offload concept. 4 new community entries.</td>
</tr>
<tr>
<td style="text-align:left">2026-09-28</td>
<td style="text-align:left">v2.0</td>
<td style="text-align:left">16-24GB tier added. Weight Precision column. GPU Quick-Lookup. Use-Case Index. Supporting Software section. AMD/Apple hardware notes. Swift-1.5 models added.</td>
</tr>
<tr>
<td style="text-align:left">2026-09-18</td>
<td style="text-align:left">v1.0</td>
<td style="text-align:left">Initial matrix: 5 tiers, 14 models, KV cache rule, architecture notes.</td>
</tr>
</tbody>
</table>
</div>

</details>

## 🔗 Links

- 🌐 [Interactive Dashboard](https://madgoathaz.github.io/llm-matrix/)
- 📝 [Post #2: Templates, Backends & Reference](/t/256443/2)
- 💬 [Reply below with your setup or questions](/t/256443)
- 🔧 [GitHub (tools & source)](https://github.com/MadGoatHaz/llm-matrix)

---
*The Local LLM Matrix is a community project from [Level1Techs](https://forum.level1techs.com). Data is community-submitted and user-reported. Not an official Level1Techs product.*
