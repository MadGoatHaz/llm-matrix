# 📊 Community Data Viewport

*A community index of all submissions from the **Local LLM Matrix** thread. Last updated: 2026-10-12 | 13 submissions*

> 🌐 **Interactive Dashboard:** [Browse, filter, and compare all setups](https://YOUR-USERNAME.github.io/llm-matrix-dashboard/)
> 
> 💬 **The full discussion lives here on the forum.** Submit your own setup using the template in Post #2.

---

<details>
<summary>📊 View by Tier</summary>

<details>
<summary>≤16GB (8 entries)</summary>
<div class="md-table">
<table>
<thead><tr><th>User</th><th>Hardware</th><th>Backend</th><th>Model</th><th>Quant</th><th>Speed</th><th>Context</th></tr></thead>
<tbody>
<tr>
<td>MadGoat</td>
<td>[e.g., 2x RX 7900 XTX 24GB, 4x MI210, 1x RTX 4060 </td>

<td>[vLLM | llama.cpp | LM Studio | Ollama | Unsloth Desktop | llama-swap | Colibri | Other]</td>
<td>[Full model repository or exact fil</td>
<td>[e.g., AutoRound W4A16, G</td>
<td>[Decode tok/s]</td>
<td>[Actual token c</td>
</tr>
<tr>
<td>MadGoat</td>
<td>1x Radeon VII 16GB HBM2 (gfx906), 32-core EPYC hos</td>

<td>llama-swap (llama.cpp subprocess, ROCm)</td>
<td>samuelcardillo/Carnice-Qwen3.6-MoE-</td>
<td>GGUF I-Nano</td>
<td>54.4 decode</td>
<td>65536 tokens (N</td>
</tr>
<tr>
<td>Burhan</td>
<td>1x RTX-4000 Ada SFF (20 GB)</td>

<td>Ollama</td>
<td>* Qwen3.6-27b-q4_KM</td>
<td>[e.g., AutoRound W4A16, G</td>
<td>~20-30 t/s</td>
<td>* 52k Qwen3.6-2</td>
</tr>
<tr>
<td>s1ugh34d</td>
<td>Radeon VII 16GB HBM2 (gfx906), 32-core EPYC host, </td>

<td>llama-swap (llama.cpp subprocess, ROCm/ROCm backends)</td>
<td>samuelcardillo/Carnice-Qwen3.6-MoE-</td>
<td>GGUF I-Nano</td>
<td>54.4 tps decode</td>
<td>65536 tokens na</td>
</tr>
<tr>
<td>s1ugh34d</td>
<td>Radeon VII 16GB HBM2 (gfx906)</td>

<td>llama-swap (llama.cpp subprocess)</td>
<td>deadbydawn101/gemma-4-E4B-Agentic-O</td>
<td>GGUF Q4_K_M</td>
<td>86.7 tps decode</td>
<td>49152 tokens (N</td>
</tr>
<tr>
<td>s1ugh34d</td>
<td>Radeon VII 16GB HBM2 (gfx906)</td>

<td>llama-swap (llama.cpp subprocess)</td>
<td>unsloth/Qwen3.8-27B-GGUF (UD-Q2_K_X</td>
<td>GGUF UD-Q2_K_XL</td>
<td>13.9 tps decode</td>
<td>49152 tokens (N</td>
</tr>
<tr>
<td>s1ugh34d</td>
<td>Radeon VII 16GB HBM2 (gfx906)</td>

<td>llama-swap (llama.cpp subprocess)</td>
<td>MaziyarPanahi/DeepSeek-R1-0528-Qwen</td>
<td>GGUF Q4_K_M</td>
<td>84.4 tps decode</td>
<td>16384 tokens (n</td>
</tr>
<tr>
<td>s1ugh34d</td>
<td>Radeon VII 16GB HBM2 (gfx906)</td>

<td>llama-swap (llama.cpp subprocess)</td>
<td>bartowski/Qwen_Qwen3.5-4B-GGUF</td>
<td>GGUF Q4_K_M</td>
<td>96.4 tps decode</td>
<td>65536 tokens (n</td>
</tr>
</tbody>
</table>
</div>
</details>
<details>
<summary>24-32GB (1 entries)</summary>
<div class="md-table">
<table>
<thead><tr><th>User</th><th>Hardware</th><th>Backend</th><th>Model</th><th>Quant</th><th>Speed</th><th>Context</th></tr></thead>
<tbody>
<tr>
<td>MadGoat</td>
<td>1x RTX 4090 24GB, Ryzen 9 5900X, 128GB DDR4-3600, </td>

<td>Strata 0.1.42</td>
<td>Qwen/Qwen3.8-Flash-Next (GGUF IQ3_S</td>
<td>GGUF IQ3_S (ISTA-DASLab G</td>
<td>99-128 decode (</td>
<td>131072 configur</td>
</tr>
</tbody>
</table>
</div>
</details>
<details>
<summary>48-64GB (3 entries)</summary>
<div class="md-table">
<table>
<thead><tr><th>User</th><th>Hardware</th><th>Backend</th><th>Model</th><th>Quant</th><th>Speed</th><th>Context</th></tr></thead>
<tbody>
<tr>
<td>MadGoat</td>
<td>2x AMD R9700 (48GB total)</td>

<td>vLLM (magiccodingman/vllm-radiance, adaptive MTP=8)</td>
<td>d0xin/Swift-Qwen3.8-27B-Uncensored-</td>
<td>FP8</td>
<td>120 (code) / 70</td>
<td>~240k tokens</td>
</tr>
<tr>
<td>digitalscream</td>
<td>2 x R9700</td>

<td>vLLM</td>
<td>d0xin/Swift-Qwen3.8-27B-Uncensored-</td>
<td>FP8</td>
<td>120t/s code, 70</td>
<td>~240k</td>
</tr>
<tr>
<td>PawingUnplug</td>
<td>2 x w7900</td>

<td>llamacpp</td>
<td>Qwen3.8-Flash-Next-Q4_K_M</td>
<td></td>
<td>~35t/s chat</td>
<td>~262k</td>
</tr>
</tbody>
</table>
</div>
</details>
</details>

<details>
<summary>🖥️ View by Hardware Vendor</summary>

<details>
<summary>AMD (9 entries)</summary>
<div class="md-table">
<table>
<thead><tr><th>User</th><th>Hardware</th><th>Backend</th><th>Model</th><th>Quant</th><th>Speed</th><th>Context</th></tr></thead>
<tbody>
<tr>
<td>MadGoat</td>
<td>1x Radeon VII 16GB HBM2 (gfx906), 32-core EPYC hos</td>

<td>llama-swap (llama.cpp subprocess, ROCm)</td>
<td>samuelcardillo/Carnice-Qwen3.6-MoE-</td>
<td>GGUF I-Nano</td>
<td>54.4 decode</td>
<td>65536 tokens (N</td>
</tr>
<tr>
<td>MadGoat</td>
<td>2x AMD R9700 (48GB total)</td>

<td>vLLM (magiccodingman/vllm-radiance, adaptive MTP=8)</td>
<td>d0xin/Swift-Qwen3.8-27B-Uncensored-</td>
<td>FP8</td>
<td>120 (code) / 70</td>
<td>~240k tokens</td>
</tr>
<tr>
<td>digitalscream</td>
<td>2 x R9700</td>

<td>vLLM</td>
<td>d0xin/Swift-Qwen3.8-27B-Uncensored-</td>
<td>FP8</td>
<td>120t/s code, 70</td>
<td>~240k</td>
</tr>
<tr>
<td>s1ugh34d</td>
<td>Radeon VII 16GB HBM2 (gfx906), 32-core EPYC host, </td>

<td>llama-swap (llama.cpp subprocess, ROCm/ROCm backends)</td>
<td>samuelcardillo/Carnice-Qwen3.6-MoE-</td>
<td>GGUF I-Nano</td>
<td>54.4 tps decode</td>
<td>65536 tokens na</td>
</tr>
<tr>
<td>s1ugh34d</td>
<td>Radeon VII 16GB HBM2 (gfx906)</td>

<td>llama-swap (llama.cpp subprocess)</td>
<td>deadbydawn101/gemma-4-E4B-Agentic-O</td>
<td>GGUF Q4_K_M</td>
<td>86.7 tps decode</td>
<td>49152 tokens (N</td>
</tr>
<tr>
<td>s1ugh34d</td>
<td>Radeon VII 16GB HBM2 (gfx906)</td>

<td>llama-swap (llama.cpp subprocess)</td>
<td>unsloth/Qwen3.8-27B-GGUF (UD-Q2_K_X</td>
<td>GGUF UD-Q2_K_XL</td>
<td>13.9 tps decode</td>
<td>49152 tokens (N</td>
</tr>
<tr>
<td>s1ugh34d</td>
<td>Radeon VII 16GB HBM2 (gfx906)</td>

<td>llama-swap (llama.cpp subprocess)</td>
<td>MaziyarPanahi/DeepSeek-R1-0528-Qwen</td>
<td>GGUF Q4_K_M</td>
<td>84.4 tps decode</td>
<td>16384 tokens (n</td>
</tr>
<tr>
<td>s1ugh34d</td>
<td>Radeon VII 16GB HBM2 (gfx906)</td>

<td>llama-swap (llama.cpp subprocess)</td>
<td>bartowski/Qwen_Qwen3.5-4B-GGUF</td>
<td>GGUF Q4_K_M</td>
<td>96.4 tps decode</td>
<td>65536 tokens (n</td>
</tr>
<tr>
<td>PawingUnplug</td>
<td>2 x w7900</td>

<td>llamacpp</td>
<td>Qwen3.8-Flash-Next-Q4_K_M</td>
<td></td>
<td>~35t/s chat</td>
<td>~262k</td>
</tr>
</tbody>
</table>
</div>
</details>
<details>
<summary>Mixed (1 entries)</summary>
<div class="md-table">
<table>
<thead><tr><th>User</th><th>Hardware</th><th>Backend</th><th>Model</th><th>Quant</th><th>Speed</th><th>Context</th></tr></thead>
<tbody>
<tr>
<td>MadGoat</td>
<td></td>

<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
</tr>
</tbody>
</table>
</div>
</details>
<details>
<summary>NVIDIA (3 entries)</summary>
<div class="md-table">
<table>
<thead><tr><th>User</th><th>Hardware</th><th>Backend</th><th>Model</th><th>Quant</th><th>Speed</th><th>Context</th></tr></thead>
<tbody>
<tr>
<td>MadGoat</td>
<td>[e.g., 2x RX 7900 XTX 24GB, 4x MI210, 1x RTX 4060 </td>

<td>[vLLM | llama.cpp | LM Studio | Ollama | Unsloth Desktop | llama-swap | Colibri | Other]</td>
<td>[Full model repository or exact fil</td>
<td>[e.g., AutoRound W4A16, G</td>
<td>[Decode tok/s]</td>
<td>[Actual token c</td>
</tr>
<tr>
<td>MadGoat</td>
<td>1x RTX 4090 24GB, Ryzen 9 5900X, 128GB DDR4-3600, </td>

<td>Strata 0.1.42</td>
<td>Qwen/Qwen3.8-Flash-Next (GGUF IQ3_S</td>
<td>GGUF IQ3_S (ISTA-DASLab G</td>
<td>99-128 decode (</td>
<td>131072 configur</td>
</tr>
<tr>
<td>Burhan</td>
<td>1x RTX-4000 Ada SFF (20 GB)</td>

<td>Ollama</td>
<td>* Qwen3.6-27b-q4_KM</td>
<td>[e.g., AutoRound W4A16, G</td>
<td>~20-30 t/s</td>
<td>* 52k Qwen3.6-2</td>
</tr>
</tbody>
</table>
</div>
</details>
</details>

<details>
<summary>⚙️ View by Backend</summary>

<details>
<summary> (1 entries)</summary>
<div class="md-table">
<table>
<thead><tr><th>User</th><th>Hardware</th><th>Backend</th><th>Model</th><th>Quant</th><th>Speed</th><th>Context</th></tr></thead>
<tbody>
<tr>
<td>MadGoat</td>
<td></td>

<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
</tr>
</tbody>
</table>
</div>
</details>
<details>
<summary>Ollama (1 entries)</summary>
<div class="md-table">
<table>
<thead><tr><th>User</th><th>Hardware</th><th>Backend</th><th>Model</th><th>Quant</th><th>Speed</th><th>Context</th></tr></thead>
<tbody>
<tr>
<td>Burhan</td>
<td>1x RTX-4000 Ada SFF (20 GB)</td>

<td>Ollama</td>
<td>* Qwen3.6-27b-q4_KM</td>
<td>[e.g., AutoRound W4A16, G</td>
<td>~20-30 t/s</td>
<td>* 52k Qwen3.6-2</td>
</tr>
</tbody>
</table>
</div>
</details>
<details>
<summary>Strata 0.1.42 (1 entries)</summary>
<div class="md-table">
<table>
<thead><tr><th>User</th><th>Hardware</th><th>Backend</th><th>Model</th><th>Quant</th><th>Speed</th><th>Context</th></tr></thead>
<tbody>
<tr>
<td>MadGoat</td>
<td>1x RTX 4090 24GB, Ryzen 9 5900X, 128GB DDR4-3600, </td>

<td>Strata 0.1.42</td>
<td>Qwen/Qwen3.8-Flash-Next (GGUF IQ3_S</td>
<td>GGUF IQ3_S (ISTA-DASLab G</td>
<td>99-128 decode (</td>
<td>131072 configur</td>
</tr>
</tbody>
</table>
</div>
</details>
<details>
<summary>[vLLM | llama.cpp | LM Studio | Ollama | Unsloth Desktop | llama-swap | Colibri | Other] (1 entries)</summary>
<div class="md-table">
<table>
<thead><tr><th>User</th><th>Hardware</th><th>Backend</th><th>Model</th><th>Quant</th><th>Speed</th><th>Context</th></tr></thead>
<tbody>
<tr>
<td>MadGoat</td>
<td>[e.g., 2x RX 7900 XTX 24GB, 4x MI210, 1x RTX 4060 </td>

<td>[vLLM | llama.cpp | LM Studio | Ollama | Unsloth Desktop | llama-swap | Colibri | Other]</td>
<td>[Full model repository or exact fil</td>
<td>[e.g., AutoRound W4A16, G</td>
<td>[Decode tok/s]</td>
<td>[Actual token c</td>
</tr>
</tbody>
</table>
</div>
</details>
<details>
<summary>llama-swap (llama.cpp subprocess) (4 entries)</summary>
<div class="md-table">
<table>
<thead><tr><th>User</th><th>Hardware</th><th>Backend</th><th>Model</th><th>Quant</th><th>Speed</th><th>Context</th></tr></thead>
<tbody>
<tr>
<td>s1ugh34d</td>
<td>Radeon VII 16GB HBM2 (gfx906)</td>

<td>llama-swap (llama.cpp subprocess)</td>
<td>deadbydawn101/gemma-4-E4B-Agentic-O</td>
<td>GGUF Q4_K_M</td>
<td>86.7 tps decode</td>
<td>49152 tokens (N</td>
</tr>
<tr>
<td>s1ugh34d</td>
<td>Radeon VII 16GB HBM2 (gfx906)</td>

<td>llama-swap (llama.cpp subprocess)</td>
<td>unsloth/Qwen3.8-27B-GGUF (UD-Q2_K_X</td>
<td>GGUF UD-Q2_K_XL</td>
<td>13.9 tps decode</td>
<td>49152 tokens (N</td>
</tr>
<tr>
<td>s1ugh34d</td>
<td>Radeon VII 16GB HBM2 (gfx906)</td>

<td>llama-swap (llama.cpp subprocess)</td>
<td>MaziyarPanahi/DeepSeek-R1-0528-Qwen</td>
<td>GGUF Q4_K_M</td>
<td>84.4 tps decode</td>
<td>16384 tokens (n</td>
</tr>
<tr>
<td>s1ugh34d</td>
<td>Radeon VII 16GB HBM2 (gfx906)</td>

<td>llama-swap (llama.cpp subprocess)</td>
<td>bartowski/Qwen_Qwen3.5-4B-GGUF</td>
<td>GGUF Q4_K_M</td>
<td>96.4 tps decode</td>
<td>65536 tokens (n</td>
</tr>
</tbody>
</table>
</div>
</details>
<details>
<summary>llama-swap (llama.cpp subprocess, ROCm) (1 entries)</summary>
<div class="md-table">
<table>
<thead><tr><th>User</th><th>Hardware</th><th>Backend</th><th>Model</th><th>Quant</th><th>Speed</th><th>Context</th></tr></thead>
<tbody>
<tr>
<td>MadGoat</td>
<td>1x Radeon VII 16GB HBM2 (gfx906), 32-core EPYC hos</td>

<td>llama-swap (llama.cpp subprocess, ROCm)</td>
<td>samuelcardillo/Carnice-Qwen3.6-MoE-</td>
<td>GGUF I-Nano</td>
<td>54.4 decode</td>
<td>65536 tokens (N</td>
</tr>
</tbody>
</table>
</div>
</details>
<details>
<summary>llama-swap (llama.cpp subprocess, ROCm/ROCm backends) (1 entries)</summary>
<div class="md-table">
<table>
<thead><tr><th>User</th><th>Hardware</th><th>Backend</th><th>Model</th><th>Quant</th><th>Speed</th><th>Context</th></tr></thead>
<tbody>
<tr>
<td>s1ugh34d</td>
<td>Radeon VII 16GB HBM2 (gfx906), 32-core EPYC host, </td>

<td>llama-swap (llama.cpp subprocess, ROCm/ROCm backends)</td>
<td>samuelcardillo/Carnice-Qwen3.6-MoE-</td>
<td>GGUF I-Nano</td>
<td>54.4 tps decode</td>
<td>65536 tokens na</td>
</tr>
</tbody>
</table>
</div>
</details>
<details>
<summary>llamacpp (1 entries)</summary>
<div class="md-table">
<table>
<thead><tr><th>User</th><th>Hardware</th><th>Backend</th><th>Model</th><th>Quant</th><th>Speed</th><th>Context</th></tr></thead>
<tbody>
<tr>
<td>PawingUnplug</td>
<td>2 x w7900</td>

<td>llamacpp</td>
<td>Qwen3.8-Flash-Next-Q4_K_M</td>
<td></td>
<td>~35t/s chat</td>
<td>~262k</td>
</tr>
</tbody>
</table>
</div>
</details>
<details>
<summary>vLLM (1 entries)</summary>
<div class="md-table">
<table>
<thead><tr><th>User</th><th>Hardware</th><th>Backend</th><th>Model</th><th>Quant</th><th>Speed</th><th>Context</th></tr></thead>
<tbody>
<tr>
<td>digitalscream</td>
<td>2 x R9700</td>

<td>vLLM</td>
<td>d0xin/Swift-Qwen3.8-27B-Uncensored-</td>
<td>FP8</td>
<td>120t/s code, 70</td>
<td>~240k</td>
</tr>
</tbody>
</table>
</div>
</details>
<details>
<summary>vLLM (magiccodingman/vllm-radiance, adaptive MTP=8) (1 entries)</summary>
<div class="md-table">
<table>
<thead><tr><th>User</th><th>Hardware</th><th>Backend</th><th>Model</th><th>Quant</th><th>Speed</th><th>Context</th></tr></thead>
<tbody>
<tr>
<td>MadGoat</td>
<td>2x AMD R9700 (48GB total)</td>

<td>vLLM (magiccodingman/vllm-radiance, adaptive MTP=8)</td>
<td>d0xin/Swift-Qwen3.8-27B-Uncensored-</td>
<td>FP8</td>
<td>120 (code) / 70</td>
<td>~240k tokens</td>
</tr>
</tbody>
</table>
</div>
</details>
</details>

<details>
<summary>📋 All Submissions (Chronological)</summary>

<div class="md-table">
<table>
<thead><tr><th>User</th><th>Hardware</th><th>Vendor</th><th>Backend</th><th>Model</th><th>Quant</th><th>Speed</th><th>Context</th></tr></thead>
<tbody>
<tr>
<td>MadGoat</td>
<td>[e.g., 2x RX 7900 XTX 24GB, 4x MI210, 1x RTX 4060 </td>
<td>NVIDIA</td>
<td>[vLLM | llama.cpp | LM Studio | Ollama | Unsloth Desktop | llama-swap | Colibri | Other]</td>
<td>[Full model repository or exact fil</td>
<td>[e.g., AutoRound W4A16, G</td>
<td>[Decode tok/s]</td>
<td>[Actual token c</td>
</tr>
<tr>
<td>MadGoat</td>
<td>1x Radeon VII 16GB HBM2 (gfx906), 32-core EPYC hos</td>
<td>AMD</td>
<td>llama-swap (llama.cpp subprocess, ROCm)</td>
<td>samuelcardillo/Carnice-Qwen3.6-MoE-</td>
<td>GGUF I-Nano</td>
<td>54.4 decode</td>
<td>65536 tokens (N</td>
</tr>
<tr>
<td>MadGoat</td>
<td>2x AMD R9700 (48GB total)</td>
<td>AMD</td>
<td>vLLM (magiccodingman/vllm-radiance, adaptive MTP=8)</td>
<td>d0xin/Swift-Qwen3.8-27B-Uncensored-</td>
<td>FP8</td>
<td>120 (code) / 70</td>
<td>~240k tokens</td>
</tr>
<tr>
<td>MadGoat</td>
<td>1x RTX 4090 24GB, Ryzen 9 5900X, 128GB DDR4-3600, </td>
<td>NVIDIA</td>
<td>Strata 0.1.42</td>
<td>Qwen/Qwen3.8-Flash-Next (GGUF IQ3_S</td>
<td>GGUF IQ3_S (ISTA-DASLab G</td>
<td>99-128 decode (</td>
<td>131072 configur</td>
</tr>
<tr>
<td>MadGoat</td>
<td></td>
<td>Mixed</td>
<td></td>
<td></td>
<td></td>
<td></td>
<td></td>
</tr>
<tr>
<td>digitalscream</td>
<td>2 x R9700</td>
<td>AMD</td>
<td>vLLM</td>
<td>d0xin/Swift-Qwen3.8-27B-Uncensored-</td>
<td>FP8</td>
<td>120t/s code, 70</td>
<td>~240k</td>
</tr>
<tr>
<td>Burhan</td>
<td>1x RTX-4000 Ada SFF (20 GB)</td>
<td>NVIDIA</td>
<td>Ollama</td>
<td>* Qwen3.6-27b-q4_KM</td>
<td>[e.g., AutoRound W4A16, G</td>
<td>~20-30 t/s</td>
<td>* 52k Qwen3.6-2</td>
</tr>
<tr>
<td>s1ugh34d</td>
<td>Radeon VII 16GB HBM2 (gfx906), 32-core EPYC host, </td>
<td>AMD</td>
<td>llama-swap (llama.cpp subprocess, ROCm/ROCm backends)</td>
<td>samuelcardillo/Carnice-Qwen3.6-MoE-</td>
<td>GGUF I-Nano</td>
<td>54.4 tps decode</td>
<td>65536 tokens na</td>
</tr>
<tr>
<td>s1ugh34d</td>
<td>Radeon VII 16GB HBM2 (gfx906)</td>
<td>AMD</td>
<td>llama-swap (llama.cpp subprocess)</td>
<td>deadbydawn101/gemma-4-E4B-Agentic-O</td>
<td>GGUF Q4_K_M</td>
<td>86.7 tps decode</td>
<td>49152 tokens (N</td>
</tr>
<tr>
<td>s1ugh34d</td>
<td>Radeon VII 16GB HBM2 (gfx906)</td>
<td>AMD</td>
<td>llama-swap (llama.cpp subprocess)</td>
<td>unsloth/Qwen3.8-27B-GGUF (UD-Q2_K_X</td>
<td>GGUF UD-Q2_K_XL</td>
<td>13.9 tps decode</td>
<td>49152 tokens (N</td>
</tr>
<tr>
<td>s1ugh34d</td>
<td>Radeon VII 16GB HBM2 (gfx906)</td>
<td>AMD</td>
<td>llama-swap (llama.cpp subprocess)</td>
<td>MaziyarPanahi/DeepSeek-R1-0528-Qwen</td>
<td>GGUF Q4_K_M</td>
<td>84.4 tps decode</td>
<td>16384 tokens (n</td>
</tr>
<tr>
<td>s1ugh34d</td>
<td>Radeon VII 16GB HBM2 (gfx906)</td>
<td>AMD</td>
<td>llama-swap (llama.cpp subprocess)</td>
<td>bartowski/Qwen_Qwen3.5-4B-GGUF</td>
<td>GGUF Q4_K_M</td>
<td>96.4 tps decode</td>
<td>65536 tokens (n</td>
</tr>
<tr>
<td>PawingUnplug</td>
<td>2 x w7900</td>
<td>AMD</td>
<td>llamacpp</td>
<td>Qwen3.8-Flash-Next-Q4_K_M</td>
<td></td>
<td>~35t/s chat</td>
<td>~262k</td>
</tr>
</tbody>
</table>
</div>
</details>

---
*This viewport is auto-generated from thread data. The interactive dashboard provides filtering, sorting, and comparison. All data is community-reported — see the [thread](/t/256443) for full context and discussion.*
