# -*- coding: utf-8 -*-
import sys

BASE = "/home/madgoat/Documents/Local LLM Matrix/"

def apply(path, pairs):
    s = open(path, encoding="utf-8").read()
    for i, (old, new) in enumerate(pairs):
        c = s.count(old)
        assert c == 1, f"{path} pair {i}: expected 1 occurrence, found {c}\n---OLD---\n{old[:200]}"
        s = s.replace(old, new)
    open(path, "w", encoding="utf-8").write(s)
    print(f"OK {path} ({len(pairs)} replacements, {len(s.splitlines())} lines)")

# ---------------- POST 1 ----------------
p1 = []

# R1: Quick Navigation entry
p1.append((
"""- 📦 Running Non-GGUF Models
- 📊 The Master Matrix (6 Tiers)""",
"""- 📦 Running Non-GGUF Models
- 🧰 Supporting Software & Ecosystem
- 📊 The Master Matrix (6 Tiers)"""))

# R2: Hardware Vendor Notes — Unsloth Desktop as primary all-in-one, Ollama/LM Studio as alternatives
p1.append((
"""<summary>🖥️ Hardware Vendor Notes (NVIDIA / AMD / Apple)</summary>

<details>
<summary>NVIDIA (CUDA)</summary>""",
"""<summary>🖥️ Hardware Vendor Notes (NVIDIA / AMD / Apple)</summary>

**Easiest start on any platform:** **Unsloth Desktop** is the recommended all-in-one app — it runs GGUF, safetensors, and FP8 models on NVIDIA CUDA, AMD ROCm/Vulkan, Intel Vulkan, and Apple Metal/MLX, with chat, no-code fine-tuning, and an OpenAI-compatible API server built in. **Ollama** and **LM Studio** remain solid lighter-weight alternatives if you prefer minimal overhead.

<details>
<summary>NVIDIA (CUDA)</summary>"""))

# R3: Option D in Running Non-GGUF Models
p1.append((
"""**Option C: LM Studio / Ollama**

These tools primarily support GGUF. For AutoRound W4A16, use vLLM directly or check if the model author has published a GGUF conversion.

**Format Comparison:**""",
"""**Option C: LM Studio / Ollama**

These tools primarily support GGUF. For AutoRound W4A16, use vLLM directly or check if the model author has published a GGUF conversion.

**Option D: Unsloth Desktop (All-in-One)**

Unsloth Desktop natively supports GGUF, safetensors, FP8, and MLX formats, with llama.cpp as the core engine and vLLM as the deployment backend. It works on NVIDIA CUDA, AMD ROCm/Vulkan, Intel Vulkan, and Apple Metal/MLX — one app for any package format in this matrix.

**Format Comparison:**"""))

# R4: New Supporting Software & Ecosystem section before Master Matrix
NEW_SECTION = """<details>
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

"""
p1.append((
"""<details>
<summary>📊 The Master Matrix (Current Consensus) — 6 VRAM Tiers</summary>""",
NEW_SECTION + """<details>
<summary>📊 The Master Matrix (Current Consensus) — 6 VRAM Tiers</summary>"""))

apply(BASE + "updated_forum_post.md", p1)

# ---------------- POST 2 ----------------
p2 = []

# P1: Quick Navigation
p2.append((
"""<li>⚙️ Backend Selection Guide</li>
<li>💡 Thread Feedback &amp; Suggested Changes</li>""",
"""<li>⚙️ Backend Selection Guide</li>
<li>🧰 Supporting Software <em>(see Post #1)</em></li>
<li>💡 Thread Feedback &amp; Suggested Changes</li>"""))

# P2: Q3 "I just want it to work"
p2.append((
"""<li><strong>"I just want it to work":</strong> Ollama or LM Studio. Download a GGUF model, click run. No commands, no configs. You'll be up in 5 minutes.</li>""",
"""<li><strong>"I just want it to work":</strong> <strong>Unsloth Desktop</strong>. Download it, pick a model from the built-in hub, chat. No commands, no configs, no terminal. You'll be up in 5 minutes. It handles GGUF, safetensors, and FP8 models, works on NVIDIA/AMD/Apple, and gives you an OpenAI-compatible API server for free. (Ollama and LM Studio are lighter alternatives if you want minimal overhead.)</li>"""))

# P3: Q4 Apple — Unsloth Desktop via MLX
p2.append((
"""<li><strong>Apple:</strong> Zero-config unified memory. A $4K Mac Studio gives you 64GB "VRAM." No multi-GPU scaling, but incredible simplicity. MLX is the native framework.</li>""",
"""<li><strong>Apple:</strong> Zero-config unified memory. A $4K Mac Studio gives you 64GB "VRAM." No multi-GPU scaling, but incredible simplicity. MLX is the native framework, and <strong>Unsloth Desktop</strong> supports Apple Silicon via MLX out of the box.</li>"""))

# P4: Backend table — Unsloth Desktop row (first)
p2.append((
"""<tbody>
<tr>
<td style="text-align:left"><strong>Ollama</strong></td>""",
"""<tbody>
<tr>
<td style="text-align:left"><strong>Unsloth Desktop</strong></td>
<td style="text-align:left">All-in-one: run, chat, train, serve</td>
<td style="text-align:left">GGUF, safetensors, FP8, MLX</td>
<td style="text-align:left">Single GPU (multi-GPU via vLLM mode)</td>
<td style="text-align:left">🟢 Minimal</td>
<td style="text-align:left">llama.cpp + vLLM + MLX engines, no-code fine-tuning, image/video gen, TTS/STT, OpenAI API server, LAN serving, agent integrations, fully offline</td>
</tr>
<tr>
<td style="text-align:left"><strong>Ollama</strong></td>"""))

# P5: Quick Decision "Just want to chat"
p2.append((
"""<li><em>Just want to chat with an AI?</em> → <strong>Ollama</strong> or <strong>LM Studio</strong></li>""",
"""<li><em>Just want to chat with an AI?</em> → <strong>Unsloth Desktop</strong> (all-in-one) or <strong>Ollama</strong> (minimalist)</li>"""))

# P6: Note after Quick Decision
p2.append((
"""</ul>

<p><strong>The Golden Rule:</strong>""",
"""</ul>

<p><em>For frontends, agent harnesses, and orchestration tools that pair with your local models, see the <strong>Supporting Software &amp; Ecosystem</strong> section in Post #1.</em></p>

<p><strong>The Golden Rule:</strong>"""))

apply(BASE + "updated_post2_submissions.md", p2)
print("ALL DONE")
