"""``guides.html`` — the guides hub.

The eight guide topics as cards. In this phase each is a "Coming Soon" card;
P1-9 replaces them with live links to the authored ``guides/<slug>/`` pages.
"""

from __future__ import annotations

from .. import utils
from ..template import page_shell

#: (icon, name, description) for each of the eight guides.
GUIDES = [
    ("🔢", "Quantization Basics",
     "What are W4A16, FP8, Q4_K_M? How precision affects quality and speed."),
    ("📦", "File Formats",
     "GGUF vs safetensors vs MLX. What's inside a model file and when to use which."),
    ("⚙️", "Quantization Methods",
     "AutoRound, AWQ, GPTQ, RTN, SmoothQuant. How quants are made and their tradeoffs."),
    ("🧠", "Model Architectures",
     "Dense vs MoE. What A3B means. How 125B models run on 24GB."),
    ("💾", "KV Cache",
     "The memory eater. Why context length costs VRAM and when to quantize it."),
    ("📏", "Context Extension",
     "RoPE, YaRN, NTK. Pushing models beyond their native context window."),
    ("⚡", "Backends Deep Dive",
     "vLLM, llama.cpp, Strata, Radiance, Ollama. When to use which."),
    ("🖥️", "Multi-GPU & Hybrid",
     "Tensor parallel, layer offload, VRAM+RAM+SSD. Making big models fit."),
]


def render() -> str:
    """Render the guides hub document.

    Returns:
        The full ``guides.html`` document.
    """
    cards = []
    for icon, name, desc in GUIDES:
        cards.append(f'''
    <div class="guide-card">
      <div class="guide-icon">{icon}</div>
      <h3>{utils.html_escape(name)}</h3>
      <p>{utils.html_escape(desc)}</p>
      <div class="guide-meta"><span class="badge badge-amber">Coming Soon</span></div>
    </div>''')

    body = f'''
  <div class="page-header">
    <h1>Guides</h1>
    <p class="subtitle">Understand the technology behind your setup</p>
  </div>

  <div class="card-grid">
{chr(10).join(cards)}
  </div>

  <div class="card">
    <h3>🚧 Guides are being written</h3>
    <p>Check back soon. In the meantime, the <a href="{utils.FORUM_THREAD}">forum thread</a> has the discussion.</p>
  </div>'''

    title = "Guides — The Local AI Stack"
    desc = ("Understand the technology behind your setup: quantization, file formats, KV cache, "
            "model architectures, context extension, backends, and multi-GPU.")
    return page_shell(title, desc, body)
