# Deep Research Prompt — Local LLM Educational Content

> **How to use this file:** Copy everything below the line into your preferred deep-research tool (or feed it to a capable model with web access). It is written to be self-contained: the tool should not need any other context. The output it produces is the raw material we adapt into the website's guide pages (see `work/website_plan.md`, Section 4, for the page that consumes each topic).

---

## CONTEXT (read first)

We are building **The Local LLM Matrix** — a free, community-driven website (`https://madgoathaz.github.io/llm-matrix/`) born from a Level1Techs forum thread. It helps people run large language models on their **own hardware** (consumer and prosumer GPUs: NVIDIA, AMD, Apple, Intel — from a $19 card to 256GB+ rigs). The site has a data table of real community submissions, and we are now adding a **layer of educational guide pages** that explain the concepts behind that data.

**The reader we are writing for — "smart beginner":**
- Technically literate: knows what a GPU, VRAM, system RAM, a terminal, and a file are. Comfortable with a PC.
- **Not** an ML researcher. Does *not* know what "W4A16," "KV cache," "MoE," "GGUF," or "tensor parallelism" mean. We must teach from first principles.
- Motivated by *practical* questions: "What should I run on my hardware?" "Why is my model slow / why does it not fit?" "Is this quant worth the quality loss?"
- Values: real numbers, honest tradeoffs, and "what does this mean for MY setup." Dislikes hand-waving, marketing fluff, and academic formalism without a payoff.

**What we need from you:** comprehensive, accurate, well-organized **reference material** on the nine topics below. We will adapt your output into scannable web guides (cards, comparison tables, CSS diagrams, "30-second version" summaries). So give us the *substance* — the definitions, the mechanisms, the numbers, the tradeoffs, and the practical guidance — and we will handle the presentation.

---

## OUTPUT FORMAT REQUIREMENTS

For **each** topic, produce a **self-contained section** that:

1. **Uses clear headings and subheadings** (H2 for the topic, H3/H4 for sub-concepts) so we can lift sections directly into page cards.
2. **Leads with a one- or two-sentence plain-English summary** ("the 30-second version") before any detail.
3. **Follows the 4-part shape for every core concept:**
   - **What it is** (1 sentence)
   - **Why it matters** (1 sentence)
   - **How it works** (2–3 sentences)
   - **When to care about it** (practical, setup-specific guidance)
4. **Includes specific numbers** wherever they exist: VRAM formulas, bytes-per-parameter, tok/s ranges, quality deltas, context lengths, power draw. Concrete > abstract.
5. **Includes comparison tables** where a concept is one of several options (e.g., quant methods, file formats, backends, parallelism strategies).
6. **Closes each concept with "when to care about this"** — always tied back to a real hardware/use-case decision.
7. **Flags uncertainty and active development** explicitly (e.g., "NVFP4 is new and rapidly evolving," "Strata is in beta"). Do **not** present moving targets as settled fact.
8. **Cites sources** where possible: paper names (e.g., the GPTQ, AWQ, SmoothQuant, YaRN, PagedAttention papers), GitHub repos, official docs URLs, vendor pages. A "Sources" list per topic is ideal.
9. **Writes at the "smart beginner" level** defined above — technical literacy yes, LLM-specific knowledge no. Define every jargon term on first use.
10. **Uses analogies** where they genuinely clarify (e.g., MoE as a hospital with specialists), but never at the cost of accuracy.

**Accuracy bar:** This is a reference people will act on (buying hardware, choosing a quant, configuring a server). When you are unsure of a number or a capability, **say so** rather than guessing. Distinguish clearly between *established* facts, *widely-reported* facts, and *speculative/emerging* claims.

---

## TOPICS TO RESEARCH

### Topic 1 — Quantization Fundamentals

Teach the *what* and *why* of quantization before any specific method.

Cover:
- **What is quantization** in the context of LLMs (reducing the precision used to store weights and/or activations).
- **Why we quantize** (fit bigger models in less VRAM; also speed and bandwidth gains).
- **The core tradeoff** (quality loss vs. memory savings vs. speed gain) — and how severe the quality loss typically is at each bit width.
- **The precision levels**, with a clear comparison table: **FP32, FP16, BF16, FP8 (E4M3/E5M2), INT8, INT4** — for each: bytes per value, typical use, quality expectation, which hardware/era it belongs to.
- **Decoding the naming code:**
  - What does **"W4A16"** mean? (4-bit *weights*, 16-bit *activations*) — and why separating weight vs. activation precision matters.
  - What does **"W8A8"** mean? (8-bit weights *and* 8-bit activations)
  - Other common notations people see (e.g., "4.0 bpw," "Q4_0," "FP8") — a quick glossary.
- **Symmetric vs. asymmetric quantization** — the difference, and when each is used.
- **Group quantization** — what "G128," "G64," "block size" mean; why quantizing in small groups (with per-group scales) beats one global scale.
- **A worked VRAM example** — show the math for a couple of real models at a couple of precisions (e.g., a 27B model at FP16 vs. FP8 vs. INT4; a 35B-A3B MoE at Q4).

Deliverable: a reader who finishes this can look at any "quant" name in our data table and know roughly how much VRAM it implies and what quality to expect.

---

### Topic 2 — Quantization Methods (How the Quant Is Made)

The *method* determines quality at a given bit width. Cover each, with its mechanism, quality, speed, VRAM, backend support, and when to use it.

Cover each of these (as its own sub-section, all feeding one big comparison table):

- **RTN (Round-To-Nearest):** the simplest — just round each weight to the nearest representable value. Its limitations (error accumulation, quality at 4-bit).
- **GPTQ:** Hessian-based / second-order error compensation. How it works (processes weights in blocks, corrects each weight's rounding error against the damage to the model's outputs). Quality vs. RTN. Compute cost to produce.
- **AWQ (Activation-Aware Quantization):** the insight that a small set of "salient" weights (the ones large activations hit) matter disproportionately; AWQ protects/scales those and quantizes the rest. Why this often beats GPTQ at the same bit width for some models, and that it's cheap to produce (no heavy Hessian).
- **AutoRound:** gradient-based optimization that searches for the optimal round-up/round-down decision per weight (with clipping). How it differs from GPTQ/AWQ. Why it's popular for W4A16 and widely used in vLLM-style releases.
- **SmoothQuant:** a mathematically-equivalent transform that migrates quantization difficulty *from activations to weights* (so both can be stored/computed in 8-bit). How it enables practical **W8A8**. (Note it's primarily an *inference-serving* technique for NVIDIA.)
- **The GGUF quant family** (the llama.cpp world) — explain each and rank them:
  - **Q4_0, Q4_K_M, Q5_K_M, Q6_K, Q8_0** (the "K-quant" block format; what the "K" and "M" mean)
  - **IQ2_XXS, IQ3_XS, IQ3_S, IQ4_XS** (the "importance-matrix" / imatrix quantizations — what an *imatrix* is and why it lets very low bits hold up better)
  - **I-Nano** (the ultra-low ~2-bit "nano" format — what it is, when it's usable, its quality floor)
  - **UD-Q2_K_XL / UD-Q4_K_XL / UD-Q8_K_XL** (the "uncensored-distribution" / dynamic-range variants — what they are and why the "XL" range helps)
  - A clear **quality hierarchy** (best→worst) and a **quality-per-byte** note (which low-bit formats punch above their weight).
- **NVFP4 / MXFP4** — the new 4-bit *microscaling* formats (NVIDIA NVFP4; the OCP MX / Microscaling family incl. MXFP4). How they differ from plain INT4 (per-block scaling factors, the "microscale" trick), what hardware supports them (which GPUs/generations), and why they're being called "the golden ticket" for 4-bit. **Flag clearly that these are new and the ecosystem is still settling.**

For **each method** include: quality impact, speed impact, VRAM savings, which backends/formats support it, and when to reach for it. Close with one **master comparison table** (method × [quality, speed, VRAM, backends, best-for]).

Deliverable: a reader who can explain *why* two 4-bit files of the same model differ in quality, and pick a method for their backend.

---

### Topic 3 — File Formats (How Models Are Packaged)

Cover the major container formats, what's inside each, and the decision of which to download.

Cover:
- **GGUF** — the single-file format for llama.cpp and its derivatives. What's inside (weights + metadata + tokenizer, all in one file). Why it's portable (one file, self-describing). Its limitations (historically no native FP8; the K-quant/imatrix ecosystem; how it's made). When you want it.
- **Safetensors** — the multi-file format for PyTorch / vLLM / most server stacks. What's inside (tensors + shape/dtype metadata, no arbitrary code — the safety story). Why it's the standard for training and inference servers. What the **shard files** are (`model-00001-of-00008.safetensors`) and why a big model is split (and that the loader reassembles it, so it's not a problem for the user). When you want it.
- **MLX format** — Apple Silicon's native format. How it differs (built for unified memory / Metal; the `.mlx` layout). When you want it.
- **Other formats people encounter** — a brief note on any others relevant to local inference (e.g., how Ollama/Unsloth package things, EXL2, GPQA/legacy formats) so a reader isn't blindsided.
- **"When to use which"** — a decision table mapping *backend/OS* → *format to download* (llama.cpp/Ollama/LM Studio/Unsloth-GGUF → GGUF; vLLM/TensorRT-LLM/Strata → safetensors, often FP8; MLX → MLX).
- **Model-size / VRAM estimation** — the formula and how to use it: `VRAM ≈ (params × bytes_per_weight) ÷ 1024³ + KV_cache + overhead`. Show 2–3 worked examples. Explain the "overhead" and why the real number is a bit higher than the raw weight math.

Deliverable: a reader who knows what they're downloading, why it's in that format, and can estimate the VRAM a file will need.

---

### Topic 4 — Model Architectures

Cover dense vs. MoE vs. hybrid, and the two "magic" features that let big models run fast locally.

Cover:
- **Dense models** — every parameter is active for every token. Examples (e.g., a 27B dense model). The cost: VRAM and compute both scale with *total* parameters.
- **MoE (Mixture of Experts)** — the model contains many "expert" sub-networks; a *router* activates only a subset per token.
  - **What "A3B" means** — e.g., "35B-A3B" = ~35B *total* parameters but only ~3B *active* per token. Define "active" vs. "total."
  - **Why MoE matters for local** — the key insight: a 125B-total / 3B-active model has *huge* weights (needs the memory to hold them) but *small* per-token compute (so it decodes fast). This is why "125B" models run at consumer-friendly speeds. Make this the headline.
  - The tradeoff: MoE needs more *memory bandwidth/capacity* (all experts must be resident) even though it uses less *compute*.
- **Hybrid architectures** — models that mix dense and MoE layers (or combine other design choices). When you'll see them and what to expect.
- **MTP (Multi-Token Prediction)** — what it is (extra heads that predict several future tokens at once / a draft head), how it was trained in, and **which current models ship it** (e.g., Gemma `…-mtp`, the Qwen "NEO-MAX-MTP" style entries, any others you can confirm).
- **Speculative decoding** — the *draft-then-verify* pattern in plain terms: a fast small model (or an MTP head, or an n-gram cache) proposes several tokens, the big model verifies them in one parallel pass, and you get a big decode-speedup for free when the draft is often right. How MTP and n-gram tables each accelerate inference. The acceptance-rate concept.

Deliverable: a reader who can read a model name like "Qwen3.8-Flash-Next 125B A3B MTP" and understand what each token of that name predicts about memory, speed, and capabilities.

---

### Topic 5 — KV Cache (The Memory Eater)

The #1 reason long context chokes a small card. Teach it fully.

Cover:
- **What the KV cache is** — for each token in the context, the model stores the attention **Key** and **Value** vectors so it doesn't recompute them. It's per-conversation memory, separate from (and in addition to) the model weights.
- **Why it grows with context length** — it's *linear*: more tokens = more stored K/V. A CSS-friendly way to describe the growth curve.
- **How much VRAM it eats** — the formula: `KV ≈ layers × kv_heads × head_dim × seq_len × 2 × bytes_per_element` (explain each factor; note GQA/MQA reduce `kv_heads`). Work a concrete example showing how a 27B model's KV at, say, 64k vs 128k vs 256k tokens can approach or exceed the weight size. This is the "why my 16GB card dies at 64k" answer.
- **Why it's separate from weights** — weights are fixed at load; KV is dynamic and grows as you talk.
- **KV cache quantization** — FP8 KV, INT8 KV, INT4 KV (and the GGUF `q8_0` KV). What you save in VRAM and the quality impact of each (FP8 ≈ negligible, INT8 small, INT4 more noticeable).
- **When TO quantize KV** — creative writing, casual chat, VRAM-constrained cards, long context where FP16 KV won't fit.
- **When NOT to quantize KV** — coding, RAG, math, and long-context precision work where the model must reliably hold and retrieve detail (agentic coding that can't lose the thread).
- **PagedAttention** — vLLM's technique for storing KV in fixed-size "pages" (like OS virtual memory) to eliminate fragmentation and enable efficient continuous batching. One clear explanation of why it matters for serving.
- **Prompt caching** — how reusing a cached KV prefix (e.g., a long system prompt / few-shot block) can give a very high hit rate (people report ~90%) and why that dramatically changes cost/speed for agents that repeat a prefix. Tie to hybrid engines like Strata.

Deliverable: a reader who can predict their KV memory for a given context length and make a defensible quantize-don't-quantize decision for their use case.

---

### Topic 6 — Context Extension (Going Beyond Native Length)

Cover how models are stretched past their trained context, and the cost.

Cover:
- **RoPE (Rotary Position Embedding)** — the base mechanism in modern transformers; how it encodes position; why the *range it was trained on* acts as a soft/hard wall.
- **What happens when you exceed native context** — quality degradation, the "lost in the middle" phenomenon (models attend poorly to the middle of very long inputs), and the practical symptom (forgets the start of a long document).
- **YaRN (Yet another RoPE handling)** — the current go-to extension method. How it works (a scaling factor + adjusted rope + light fine-tuning of the positional math). The "scaling factor" concept. When to use it. The practical guidance: if a model is 32k native, what can you expect pushing to 64k / 128k with YaRN, and the quality cost at each step.
- **NTK (Nucleus Transform Kernel / NTK-aware scaling)** — the earlier approach; how it differs from YaRN (interpolating the RoPE base frequency); when it's "good enough."
- **The honest rule of thumb** — a clear scale: ~2× native is usually safe, ~4× starts to degrade, beyond that you're gambling. State it plainly.
- **Native long-context models** — which current models ship 128k / 256k / 1M context *natively* (so you don't need to stretch at all), with their real names.

Deliverable: a reader who can look at a model's native context, decide if their needed context fits, and know which extension method to reach for and what to expect.

---

### Topic 7 — Backends Deep Dive (When to Use What)

The single most practical guide. For **each** backend, cover: what it is, formats it supports, GPUs/OS it runs on, key features, performance characteristics, **when to choose it**, and **when NOT to**.

Cover each of these (each as its own sub-section):
- **llama.cpp** — the universal baseline engine. GGUF. Runs on CPU, NVIDIA (CUDA), AMD (ROCm/Vulkan), Apple (Metal). CPU+GPU hybrid offload. The reference point everything is compared to.
- **llama-swap** — multi-model auto-swapping on a single GPU; exposes an OpenAI-compatible API; the "run many models, one card" tool.
- **Ollama** — "Docker for LLMs"; the easiest on-ramp; GGUF under the hood; limited advanced features; great for casual use.
- **LM Studio** — GUI wrapper around llama.cpp; a model browser; the point-and-click option.
- **Unsloth Desktop** — the all-in-one (run + fine-tune + serve); multiple formats (GGUF/safetensors/FP8/MLX); a llama.cpp core with a vLLM-style backend option.
- **vLLM** — the production server. Continuous batching, PagedAttention, high throughput; safetensors / FP8 / AutoRound; multi-GPU tensor parallelism; the choice for serious serving.
- **TensorRT-LLM** — NVIDIA's maximum-performance option; kernel-level / graph optimization; the most setup, the most speed, NVIDIA-only.
- **Strata** — the hybrid offload engine; runs 125B+ models on consumer hardware across VRAM + RAM + SSD; prompt caching. **Flag: relatively new / beta, fast-moving.**
- **Radiance** — AMD-optimized; targets RDNA3/4; leverages MTP; the "200 tok/s on AMD" story. **Flag: AMD-specific, emerging.**
- **MLX** — Apple Silicon native; uses unified memory; the default for Macs.
- **Colibri** — CPU-only inference; the path for big-RAM (e.g., 1TB) systems without a GPU.

Then produce:
- **One master comparison matrix** — backends as rows; columns = Formats · GPU/OS · Best strength · Best for · Avoid when.
- **A "pick your backend" decision flow** — Apple? / one AMD card / multi-GPU NVIDIA / production serving / model-bigger-than-VRAM / just-want-it-to-work → the recommendation for each.

Deliverable: a reader who can choose the right backend for their hardware and use case in under a minute, and understand the tradeoffs.

---

### Topic 8 — Multi-GPU & Hybrid Setups

Cover how to split a model across more than one card, and how to run a model bigger than any single card.

Cover:
- **Tensor parallelism** — splitting each layer's weight matrices across GPUs so all cards compute *together* on every token. How it works, why it's the fastest multi-GPU mode, and that it needs a fast interconnect. (This is what vLLM does with `--tensor-parallel-size N`.)
- **Pipeline parallelism** — splitting the model by *stages* (e.g., layers 1–20 on GPU A, 21–40 on GPU B) so cards work *in sequence*. When it's used and its latency tradeoff vs. tensor parallel.
- **Layer offload** — keeping some layers in VRAM and spilling the rest to system RAM; the per-layer speed cost. How llama.cpp-style `-nvl`/GPU-layer control does this.
- **Interconnects matter** — **NVLink** (NVIDIA) vs. **PCIe** (and PCIe generation/width); **AMD XGMI / Infinity Fabric** as the AMD equivalent. Why a slow bus can tank tensor-parallel throughput. A plain-English "bus width = how fast the cards talk" explanation.
- **Practical multi-GPU setups** — a table for common configs and what fits / how to split:
  - 2× 24GB (48GB total)
  - 4× 24GB (96GB total)
  - 8× 24GB (192GB total)
  - and the AMD equivalents (e.g., 2× R9700 32GB).
- **Hybrid (Strata-style) VRAM + RAM + SSD** — when this makes sense (model > total VRAM), the bandwidth tradeoff at each tier (VRAM fast / RAM slower / SSD slowest), and the rule of keeping the "hot" parts in VRAM. Tie to MoE (why a 125B-A3B model is a great hybrid candidate).

Deliverable: a reader with 2+ GPUs (or a model too big for one card) who knows which parallelism/offload strategy to use and what speed to expect.

---

### Topic 9 — The L1Techs Community Context

This is the *soul* of the site — capture what makes this community distinctive, so the guides and the About page feel authentic rather than generic.

Cover (this is more qualitative; draw on the thread's culture):
- **What makes this community different** — it's *hardware enthusiasts*, not just AI researchers. People who care about the silicon as much as the model.
- **The range** — from a **$19 GPU** to **256GB+ enterprise-style rigs**. The full spectrum of budgets is represented and respected.
- **AMD vs. NVIDIA culture** — the healthy rivalry; that AMD (ROCm/Radiance) is a first-class citizen here, not an afterthought; the "we'll make it work on AMD" energy.
- **The "pleb tier" appreciation** — the community's respect for low-budget setups (capture the spirit of a quote like Calvin's praising the humble builds). Being able to run something good on cheap hardware is celebrated, not mocked.
- **The eval culture** — people who actually *test* (e.g., lhl's "tens of billions of tokens" of evals). Data over vibes. NIAH (needle-in-a-haystack) tests, real context probing.
- **The niche use cases** — the "why would anyone do this?" projects that show the range (e.g., manoreken2's translation of a text from **481 BCE**). Local LLMs as a tool for genuinely weird, personal, and valuable things.

Deliverable: a set of authentic, specific observations (with real usernames/quotes where available) that let us write an About page and guide asides that sound like *this* community, not a generic AI blog.

---

## FINAL NOTES FOR THE RESEARCH TOOL

- **Depth over breadth per section** — each of the nine topics should stand alone as a complete mini-reference. We will trim for the web, so err on the side of *including* the nuance.
- **Numbers are gold** — if a real benchmark, formula, or spec exists, include it. If you can't verify a number, label it as approximate or unverified.
- **Flag the moving parts** — NVFP4/MXFP4, Strata, Radiance, MTP, and speculative decoding are all fast-moving. Mark them clearly so we can add "check latest" notes.
- **Be concrete about hardware** — name real GPUs and tiers (e.g., "a 24GB RTX 4090," "2× AMD R9700 32GB," "a 16GB Radeon VII") so the guidance maps to the rows in our data table.
- **End each topic with a "Sources" list** (papers, repos, docs, vendor pages).
- **Deliver as clean markdown** with the heading structure above, so we can lift sections directly into guide pages.

*That's the brief. Produce the full reference material for all nine topics.*
