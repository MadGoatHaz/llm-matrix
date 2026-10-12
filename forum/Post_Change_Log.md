# Post Change Log

Version history for the Local LLM Matrix forum posts. Each entry records what changed, why, and the date. Previous full post versions are preserved in git history (`git log -- forum/`).

---

## v2.1 — 2026-10-12

### Post1.md (The Hub)
- **Restructured from "reference document" to "front door"**
- Added dashboard banner link (top)
- Added "Find Your Setup in 30 Seconds" section (GPU table + use-case table, non-collapsible)
- Added Community Highlights section (5 notable setups: Kif/Strata, digitalscream/Radiance, lhl/evals, manoreken2/translation, SgtAwesomesauce/v620)
- Added "Add Your Setup" CTA section
- Added Recent Updates / Changelog section
- Added Links footer with GitHub repo reference
- Removed: Hardware Vendor Notes, Non-GGUF guide, Supporting Software, Community Verified Data, Real-World Constraints, Related Threads (all moved to Post2)
- Kept: All 6 tier matrix tables (27 model rows), Technical Architecture Note

### Post2.md (The Reference)
- **Restructured from "submissions guide" to "full reference + workshop"**
- Added: Backend Selection Guide (10 backends including Strata, Radiance)
- Added: Hardware Vendor Notes (nested NVIDIA/AMD/Apple)
- Added: Running Non-GGUF & Hybrid Models (format table, vLLM/Strata/Radiance commands, NVFP4 note)
- Added: KV Cache Quantization Rule (full guidance)
- Added: Real-World Constraints (power, thermals, PCIe, RAM, storage)
- Added: Community Data Viewport section (multi-view index, auto-generated placeholder)
- Added: Full Changelog section
- Added: "How Data Gets Integrated" section (pipeline, confidence levels, lifecycle)
- Kept: Submission Templates (Quick + Full), Example Submissions
- Removed: "Start Here" decision flow (merged into Post1's 30-second section), Thread Feedback section

### bump.md
- Updated to v2.1 content (R9700, Strata, Radiance, NVFP4, DeepSeek 4.1 Flash, hybrid concept)

### Removed
- `post3_viewport.md` — merged into Post2.md as a section
- `bump_v2.md` — superseded by v2.1 bump

---

## v2.0 — 2026-09-28

### Post #1 (was: single reference post)
- Added 16-24GB tier (Tier 2) — renumbered to 6 total tiers
- Added Weight Precision column to all matrix tables
- Added Status (confidence) column: ✅ OP-verified, 📡 Community, 📐 Calculated
- Added Lifecycle column: 🟢 Current, 🟡 Watch, 🔴 Superseded
- Added GPU Quick-Lookup section (40+ GPUs mapped to tiers)
- Added Use-Case Index (10 task types cross-referenced)
- Added Supporting Software & Ecosystem section (all-in-one apps, chat frontends, coding agents, agent frameworks, orchestration)
- Added Hardware Vendor Notes (expanded AMD: Radeon VII, 7900 XT/XTX, R9700, MI210/MI250/MI300X, v620. Apple unified memory.)
- Added Running Non-GGUF Models guide (vLLM, llama.cpp, LM Studio, Unsloth Desktop)
- Added Real-World Constraints section
- Added Changelog section
- Added Community Verified Data section (4 contributors)
- Added ukisai/Swift-1.5-Qwen3.8-27b and Swift-1.5-Qwen3.8-Flash-Next across tiers
- Added Tier Tradeoff Notes (2-3 sentences per tier)
- Changed all sections to `<details>`/`<summary>` collapsible format
- Added emoji-prefixed summaries for visual scanning

### Post #2 (was: submissions + feedback)
- Added "Start Here: New to Local LLMs?" decision flow (4 questions)
- Added Quick Submit template (4 fields, 30 seconds)
- Added Backend Selection Guide (8 backends)
- Added `os_driver`, `weight_precision`, `prefill_tps`, `ttft_cold`, `power_draw` fields to full template
- Added Example Submissions (2 filled examples)
- Changed to `<details>`/`<summary>` collapsible format

### Bump post (v2.0)
- Announced 6-tier restructure, GPU lookup, use-case index, community data integration
- Called out specific contributors

---

## v1.0 — 2026-09-18

### Original Post #1
- 5 tiers (≤16, 24-32, 48-64, 96-128, 196-256+)
- 14 model entries across tiers
- KV Cache Quantization Rule
- Technical Architecture Note (Qwen3.8-Flash-Next n-gram table)
- Management section (weekly rollups, fast-tracks, submissions)
- Table format: Model | Package | VRAM | KV Headroom | Native Ctx | YaRN Ctx | Use Case

### Original Post #2
- Community Submissions intro
- "What I Want to Hear From You" (3 questions)
- Standardized Submission Template (12 fields)
- Thread Feedback & Suggested Changes (3 prompts)

---

## Git History Reference

Full previous versions of all posts are preserved in git:
```bash
# View any previous version:
git log --oneline -- forum/
git show <commit>:forum/post1_matrix.md
git show <commit>:forum/post2_submissions.md
```

Key commits:
- `234ebea` — v2.1 restructure (Post1=Hub, Post2=Reference)
- `c8d55a6` — First full pipeline run (dashboard live)
- `504f156` — L1Techs community branding
- `86e2537` — Dashboard output to repo root
- `8388c08` — Initial commit (tools, schema, forum posts)
