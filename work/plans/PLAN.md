# The Local AI Stack — Development Plan

**Version:** 1.0
**Date:** 2026-10-12
**Status:** Approved for execution (single source of truth for all implementation work)
**Author:** general (Architectural Planning Agent)
**Companion docs:** `VISION.md` (philosophy), `HANDOVER.md` (point-in-time snapshot), `work/research_prompts.md` (guide content spec)

---

## 1. Executive Summary

**Where we are.** The Local AI Stack is a working, live product: a 5-page static website on GitHub Pages (`madgoathaz.github.io/llm-matrix/`) fed by a clean, stdlib-only Python 3.14 pipeline (`pull → diff → parse → parse_thread → generate_site`). It organizes 12 real community submissions from 5 contributors across 2 GPU vendors and 5 inference backends. The *data engine* is solid and the *front door* (homepage, matrix, community, about) is live. What is missing is the *knowledge layer*: all 8 guide pages are empty "Coming Soon" cards, and the tools that answer the project's core question — "what should I run, on what I have, for what I need?" — do not exist yet. There is no CI/CD, no test suite, no dependency manifest, and a few hygiene gaps (a missing OG image, stale READMEs, a dangling worktree).

**Where we're going.** We're turning a data table into a complete, genuinely useful reference: (1) **eight researched, human-readable guides** that teach quantization, file formats, architectures, KV cache, context, backends, and multi-GPU/hybrid strategies — the educational heart of the product; (2) **decision tools** (a recommendation engine, a comparison view, a launch-command generator, shareable filters) that turn the data into an answer for the individual reader; and (3) **sustainable automation** (tests, CI, a weekly scheduled pull, a community submission form, data-quality validation) so the resource keeps evolving without heroic manual effort. Every phase ends in a deployable, never-half-broken state.

**What makes this plan different.** It is *user-value-first*: the guides and the recommendation engine **are** the product — the data table is the substrate, not the point. It is *grounded in reality*: it is written against the actual 5-page / 826-line-generator / 12-submission codebase (not the out-of-sync 15-page fantasy in the earlier website plan, which we used only as an IA reference). And it is *execution-ready*: every unit of work is a self-contained, verifiable **chunk** with a specific ID, exact file paths, concrete acceptance criteria, and explicit dependencies — sized for a single agent task so work can be fanned out and merged cleanly.

**The two audiences (north star for every decision).**
- **The Learner** — "Why is my 125B model only using 3B of it? What's a quant? What's eating my VRAM?" → served by **Phase 1 (Guides)**.
- **The Decider** — "I have a 24GB card and 128GB RAM. What should I run for coding?" → served by **Phase 2 (Recommend / Compare / Launch commands / Filters)**.

A good site serves both without forcing one to scroll past the other. When any tradeoff arises, we ask: *does this save a real person time?*

---

## 2. Guiding Principles

These are non-negotiable quality gates. A chunk that violates one is not done.

### 2.1 Quality & professionalism — no hacks
- **No band-aids.** If a solution requires `sed`-ing generated HTML, `eval`, string-hacking, or a "temporary" special case, it is the wrong solution. Refactor the generator/template instead.
- **The generator is the single writer of HTML.** Hand-editing a generated `*.html` is forbidden; content changes go through `content/**` + `tools/site/`.
- **One design system.** All styling lives in `css/style.css` (tokens + components). No inline styles, no per-page CSS blobs. All shared behavior lives in `js/main.js`.
- **Boring, reliable technology.** Static files, GitHub Pages, Python. We do not introduce a build step, a JS framework, a database, or a server — ever.
- **Reversible & reviewable.** Every change is small enough to review in a single diff. Big migrations are split into steps that each leave the site live.

### 2.2 User-centric — built for people, not engineers
- **Answer the core question.** Every feature is judged on: does it help a person figure out *what to run, on what they have, for what they need*?
- **Meet people where they are.** A $300-GPU newcomer and a 4-GPU homelabber both get a clear path. "Start Here" in 30 seconds; deep guides for the curious.
- **Show real numbers.** VRAM formulas, tok/s, power draw. No hand-waving. Every claim ties to a real submission or the research.
- **Honest tradeoffs.** "Fast but power-hungry," "fits your card but loses context." No hype, no vendor spin.
- **Credit the community.** Contributor names are shown, not hidden. People feel seen.
- **Flag uncertainty.** Fast-moving topics (NVFP4, Strata, MTP) are explicitly marked "new / evolving," never presented as settled.

### 2.3 Maintainability — it must evolve weekly
- **The field moves; we move with it.** Adding a new backend/quant/tier = edit `tools/schema.json` + re-run. No frontend changes for new data values.
- **Stable data contract.** `data/submissions.json`'s schema is versioned and tested. Generators and the client read a documented shape.
- **Tested pipeline.** `pull/diff/parse/parse_thread` (stdlib) and `generate_site` (content) are covered by an automated suite that runs in CI.
- **Documented operations.** The weekly cycle, the CI, and the contribution path are written down and current (not stale).

### 2.4 Accessibility & performance (baked in, not bolted on)
- **WCAG 2.1 AA** on every page: contrast ≥ 4.5:1, keyboard navigable, semantic landmarks, ≥ 44px touch targets, no motion without a reduce-motion fallback.
- **Performance budget:** LCP < 2.5s, CLS < 0.1, INP < 200ms; page HTML < 100KB, CSS < 60KB, JS < 30KB. No render-blocking assets.

---

## 3. Current State Assessment

### 3.1 What exists and works (verified 2026-10-12)

| Area | State | Detail |
|---|---|---|
| **Website** | ✅ Live | 5 flat pages at repo root: `index.html` (homepage), `matrix.html` (data table + filters), `community.html` (contributor cards), `guides.html` (8 "Coming Soon" cards), `about.html`. Dark mode, mobile responsive. |
| **Design system** | ✅ Solid | `css/style.css` (479 lines): CSS custom-property tokens, nav + mobile toggle, cards, stats, tables (ellipsis + tooltip), filters, badges, hero, guide/contributor cards, breakpoints. |
| **Client JS** | ✅ Working | `js/main.js` (119 lines): nav toggle, active-link by pathname, tier-group-aware table sort, search + 3-select filters, reset. Vanilla, no deps. |
| **Generator** | ⚠️ Monolith | `tools/generate_site.py` (826 lines): reads `submissions.json` + `schema.json`, writes all 5 pages + `data.json`. Inline HTML templates, `html_escape` on all data, template-submission filter, `normalize_backend()`. **Not modular** — the main technical debt. |
| **Data pipeline** | ✅ Working | `pull.py` (171L, 4 monitored threads, browser UA + curl fallback), `diff.py` (129L), `parse.py` (424L → `submissions.json`), `parse_thread.py` (154L → benchmarks/hardware/category). Stdlib-only. |
| **Config** | ✅ Current | `tools/schema.json` **v2.1** (6 tiers, 5 vendors, 12 backends, 7 os_drivers, 22 quants, 7 kv types, 15 use cases, 5 engine modes, 4 confidence, 4 lifecycle, 4 monitored threads). `tools/tags.json` (manual curation: highlights, confidence overrides, forum feedback). |
| **Data** | ✅ 12 rows | 12 submissions, 2 skipped templates. 5 contributors (s1ugh34d×5, MadGoat×3, PawingUnplug×2, digitalscream×1, Burhan×1). 2 vendors (AMD×10, NVIDIA×2). 5 backends (llama-swap×6, vLLM×2, llama.cpp×2, Strata×1, Ollama×1). Tiers t1×6, t4×4, t3×1, t2×1. |
| **Git** | ✅ In sync | `main` == `origin/main` at `2da203b` (13 commits). **No unpushed commits** (recon's "3 unpushed" was stale — verified). One worktree `entertaining-puck` (clean, 3 commits behind main, at `c6d87f5`). |
| **Runtime** | ✅ 3.14 | Python 3.14.7. No `pyproject.toml`, no test suite, no CI/CD. |

### 3.2 Submission data model (the contract everything builds on)

Canonical shape of one entry in `data/submissions.json` (schema v2.1):

```
id            "post_2_madgoat_1"
source        { post_number, post_id, username, submitted_at }
type          "full" | "quick"
raw           { …original [COMMUNITY-SUBMISSION] fields, verbatim… }
tier          "t1"…t6"
hardware      { description, vendor }
backend       "llama-swap (…)"        # normalize_backend() → canonical
model         { name, url }
quant         "GGUF I-Nano"
weight_precision  "I-Nano (~2.5bpw)"
use_cases     "LLM-assisted coding / …"
context       { stable, kv_cache }
performance   { decode_tps, prefill_tps, ttft_cold, power_w }
engine_mode   "" | "Hybrid (VRAM+RAM+SSD)" | …
notes         "…"
confidence    "community-reported"
lifecycle     "current"
highlight     false
tags          []
```

**Known data-quality gaps** (drive Phase 3 validation + guide accuracy):
- `engine_mode` is empty on 11/12 submissions (only 1 hybrid flagged).
- **Zero Apple/MLX submissions** — the biggest demographic gap.
- `use_cases` is free text (not enum-normalized) → hard to filter/rank reliably.
- Template detection has edge cases (partially-filled templates).

### 3.3 Gaps → where they land in this plan

| Gap | Phase | Chunk |
|---|---|---|
| `og-image.png` missing (broken forum thumbnail) | 0 | P0-2 |
| Dangling `entertaining-puck` worktree | 0 | P0-1 |
| Stale `README.md` / `tools/README.md` | 0 | P0-5 |
| No `pyproject.toml` | 0 | P0-3 |
| No test suite | 0 → 3 | P0-4 (skeleton) → P3-2 (full) |
| 8 empty guide pages (core content) | 1 | P1-0…P1-9 |
| Monolithic 826-line generator | 1 | P1-0 |
| No comparison / recommend / launch-cmd | 2 | P2-1…P2-3 |
| Filters not shareable; no row detail | 2 | P2-4, P2-5 |
| A11y / mobile / perf not verified | 2 | P2-6, P2-7 |
| No CI/CD; weekly cycle manual | 3 | P3-1, P3-3 |
| No data-quality validation | 3 | P3-5 |
| No community submission path | 3 | P3-4 |
| No charts / custom domain / API | 4 | P4-1…P4-5 |

---

## 4. Phased Roadmap

Sequenced so the site is **always live and improving, never half-broken**. Each phase ends in a deployable state. Phases are ordered by *user value*: hygiene first (so we build on a clean foundation), then the guides (the heart), then the decision tools (the other half of the core question), then automation (sustainability), then growth.

> **Architecture decision (applies to all phases):** the 5 existing pages stay at the repo root (`index.html`, `matrix.html`, `community.html`, `about.html`) to avoid breaking the live site. The **guides** move into a `guides/` directory with clean URLs (`guides/<slug>/index.html`), and the old flat `guides.html` becomes a redirect stub to `guides/`. The 826-line monolith `generate_site.py` is refactored into a **`tools/site/` package** (see P1-0). The data pipeline (`pull/diff/parse/parse_thread`) stays stdlib-only; the content generator may use the single `markdown` dependency (see §5.1).

### Phase 0 — Foundation & Hygiene (immediate)
*Goal: a clean, documented, tested foundation. ~1 day of work. No user-facing feature, but everything after it is safer.*

- **P0-1** Git & worktree hygiene (verify push state, remove the stale `entertaining-puck` worktree + branch)
- **P0-2** Generate `og-image.png` (+ committed `og-image.svg` source) — fixes the broken forum onebox
- **P0-3** Add `pyproject.toml` (pin Python 3.14, project metadata, tool config, the one `markdown` dep)
- **P0-4** Establish the test-suite skeleton (`tests/`, stdlib `unittest`)
- **P0-5** Refresh stale `README.md` + `tools/README.md`

### Phase 1 — Guide Content (the core value delivery)
*Goal: the 8 researched guides are live — the educational heart of the product. This is the biggest value jump.*

- **P1-0** Guide architecture foundation (refactor `generate_site.py` → `tools/site/` package; `content/guides/` dir; markdown converter + front-matter)
- **P1-1 … P1-8** Author the 8 guides (one chunk each, in learning-path order): Quantization Basics → File Formats → Quantization Methods → Model Architectures → KV Cache → Context Extension → Backends Deep Dive → Multi-GPU & Hybrid
- **P1-9** Guides index live + nav dropdown (replace "Coming Soon" cards with real links)

### Phase 2 — UX & Usability (the Decider's tools)
*Goal: answer "what should I run?" directly. The data becomes a decision.*

- **P2-1** Recommendation engine (the core product feature)
- **P2-2** Comparison view (2–4 setups, diff-highlighted)
- **P2-3** Launch command generator
- **P2-4** Shareable filters (URL-synced, + use-case & engine-mode axes)
- **P2-5** Matrix row → detail panel
- **P2-6** Accessibility + mobile audit (WCAG 2.1 AA)
- **P2-7** Performance budget enforcement

### Phase 3 — Automation & Sustainability
*Goal: the weekly cycle runs itself; quality is enforced in CI; the community can feed the data.*

- **P3-1** CI/CD (GitHub Actions: test + generate + validate on every push/PR)
- **P3-2** Full automated test suite (golden-file regression for all pages)
- **P3-3** Scheduled weekly data pull (opens a reviewed PR)
- **P3-4** Community submission form (static, generates the forum block)
- **P3-5** Data-quality validation (`tools/validate.py` + CI)

### Phase 4 — Growth & Polish
*Goal: differentiate and scale. Nice-to-haves that compound value.*

- **P4-1** Charts & visualizations (pure SVG, generated)
- **P4-2** Custom domain (CNAME + HTTPS)
- **P4-3** Advanced filtering (multi-select, saved views)
- **P4-4** Data API (stable, versioned JSON contracts)
- **P4-5** Community contribution workflow (onboarding, changelog automation, privacy-friendly analytics)

---

## 5. Technical Standards

### 5.1 Dependency policy (a reasoned, explicit decision)
- **Data pipeline stays stdlib-only** (`pull.py`, `diff.py`, `parse.py`, `parse_thread.py`). This preserves the project's core strength and keeps the weekly cycle dependency-free.
- **Content generator uses exactly one third-party dep: `markdown`** (pure Python, no build step, ~5KB, battle-tested), declared + pinned in `pyproject.toml`. Rationale: hand-rolling a markdown parser for tables + fenced code + `<details>` pass-through is exactly the "hacked-around" anti-pattern this project rejects. `markdown` (extensions: `tables`, `fenced_code`, `sane_lists`, `toc`) is the right tool for the guide layer. **Contingency:** if a truly zero-dep build is ever mandated, a minimal converter in `tools/site/markdown.py` supporting our constrained subset is the documented fallback.
- **Client side: zero JS dependencies.** Vanilla JS in `js/main.js` only. No chart libs, no frameworks. (Charts in P4-1 are inline SVG generated by Python, not a client library.)

### 5.2 Code quality
- **PEP 8** for all Python; `python -m py_compile` clean on every tool.
- **The generator is modular.** `tools/site/` package: `template.py` (page shell), `markdown.py` (md→HTML + front-matter), `pages/` (one module per data page), `guides.py` (guide renderer). `tools/generate_site.py` is a thin entry point. No 800-line files.
- **`html.escape()` on every interpolated data value** (XSS-safe). No f-string brace leaks.
- **Idempotent generator:** overwrites only the paths it owns; never touches `content/`, `assets/`, `tools/`. A page that fails to render is **reported, not silently skipped**.
- **Type hints + docstrings** on all public functions.
- **No dead code.** Superseded files (e.g., legacy `tools/generate.py`) are removed or clearly marked, not left to rot.

### 5.3 Documentation standards
- `README.md` (root) = the front door: what this is, the weekly cycle, how to run it, links to guides/forum. **Current, never stale.**
- `tools/README.md` = per-tool reference (the 5 tools, schema.json, tags.json, how to extend).
- `work/plans/PLAN.md` (this file) = the execution source of truth.
- Every new feature ships with a short "how it works" note (in the About page or a doc).
- Forum posts (`forum/Post1.md`, `Post2.md`) stay in sync with the site.

### 5.4 Testing requirements
- **Framework: stdlib `unittest`** (no new test dep; runs via `python -m unittest discover -s tests` and in CI).
- **Coverage targets:**
  - `schema.json` structure (all enums present, tiers ordered, version field).
  - `submissions.json` invariants (every row has required keys; tier ∈ schema; vendor ∈ schema; no `raw`-only rows leak).
  - `parse.py` edge cases (template filtering, tier normalization, backend normalization).
  - **Golden-file regression:** every generated page's HTML is stable across a no-op regenerate (catches drift/accidental rewrites).
  - Structural checks per page: nav + footer present, OG tags valid, no `{{` template leaks, tag balance (via `html.parser`).
- A red test **blocks** the weekly commit and the CI deploy.

### 5.5 Accessibility requirements (WCAG 2.1 AA)
- Contrast ≥ 4.5:1 (body), 3:1 (large text/UI).
- Full keyboard operability (nav, filters, tables, detail panel, compare).
- Semantic landmarks (`<nav>`, `<main>`, `<footer>`), one `<h1>` per page, logical heading order.
- All images/icons have `alt`; icon-only buttons have `aria-label`.
- Touch targets ≥ 44×44px.
- `prefers-reduced-motion` respected (no forced animation).
- **Gate:** Lighthouse Accessibility ≥ 95 on every page.

### 5.6 Performance budget
- **LCP < 2.5s, CLS < 0.1, INP < 200ms** on a mid-phone over 4G.
- Page HTML < 100KB, `style.css` < 60KB, `main.js` < 30KB (gzip).
- No render-blocking CSS/JS; JS deferred.
- **Gate:** Lighthouse Performance ≥ 90 on every page.

### 5.7 Design system
- Single `css/style.css`: tokens → reset → layout → components → responsive. New visual patterns get a **named component class** (`.card`, `.callout`, `.chip`, `.diagram--*`, `.detail-panel`), not inline styles.
- **CSS-only diagrams** (no images/SVG files) for concept visuals: KV-cache growth, MoE routing, offload stack (VRAM→RAM→SSD), tensor/pipeline split, precision ladder, context-extension scale. Authored as `<div class="diagram diagram--kv">…</div>` in guide markdown; styled in `site.css`.
- Dark mode is the default (and only) theme for v1.

---

## 6. Chunk Breakdown (for implementation)

Each chunk is **self-contained, verifiable, and sized for a single agent task**. Execution order is top-to-bottom; **Dependencies** list what must be done first. "Acceptance" is the definition of done for that chunk.

> Legend: `NEW` = create, `MOD` = modify, `DEL` = delete. All paths relative to repo root.

---

### Phase 0 — Foundation & Hygiene

#### P0-1 — Git & worktree hygiene
- **Description:** Verify the repo is fully pushed and remove the stale worktree. Confirmed: `main` == `origin/main` (no unpushed commits). The `entertaining-puck` worktree is clean but 3 commits behind main and redundant.
- **Files:** (git operations; no source files)
  - `DEL` worktree `.kilo/worktrees/entertaining-puck`
  - `DEL` branch `entertaining-puck`
- **Acceptance:**
  - `git log origin/main..main` is empty (nothing unpushed).
  - `git worktree list` shows only the main worktree.
  - `git branch` no longer lists `entertaining-puck`.
  - `git status` clean on main.
- **Dependencies:** none.

#### P0-2 — Generate `og-image.png` (fix broken forum thumbnail)
- **Description:** The OG meta tag on every page references `og-image.png`, which doesn't exist → the forum onebox card has no thumbnail. Author a crisp brand image. Because the pipeline is stdlib/static, we commit a **static asset** (created once, not generated per-run).
- **Files:**
  - `NEW` `og-image.svg` — 1200×630 brand image: dark background (`--bg`), "📊 The Local AI Stack" wordmark, tagline "Models, Hardware, Backends & Community Data," accent bar. Authorable, scalable, committed.
  - `NEW` `og-image.png` — 1200×630 rasterization of the SVG (one-off conversion via `rsvg-convert`/`cairosvg`/`ImageMagick` on the maintainer's machine; the PNG is then committed as a static asset).
- **Acceptance:**
  - `og-image.png` exists at exactly 1200×630.
  - `og-image.svg` is committed as the editable source.
  - Fetching `https://madgoathaz.github.io/llm-matrix/og-image.png` returns 200 (not 404).
  - Forum onebox (featured link) renders the thumbnail.
- **Dependencies:** none.

#### P0-3 — Add `pyproject.toml`
- **Description:** Declare the project properly: metadata, Python requirement, the single content dep, and tool config. Makes the tooling installable/testable/reproducible.
- **Files:**
  - `NEW` `pyproject.toml`
- **Acceptance:**
  - `[project]` has `name = "local-ai-stack"`, `version`, `description`, `requires-python = ">=3.14"`, `license`.
  - `dependencies = ["markdown>=3.6,<4"]` (the single content dep; data pipeline stays stdlib).
  - `[project.optional-dependencies] dev = []` reserved (no test dep needed — we use stdlib `unittest`).
  - `[tool.unittest]` / runner notes and a `[build-system]` are present and valid.
  - `python -c "import markdown"` works after `pip install -e .` in a clean venv.
- **Dependencies:** none.

#### P0-4 — Test-suite skeleton
- **Description:** Stand up `tests/` with stdlib `unittest` and a first set of real, green assertions that lock in the current invariants. This is the seed P3-2 will grow.
- **Files:**
  - `NEW` `tests/__init__.py`
  - `NEW` `tests/test_schema.py` — validates `schema.json` (version present, 6 tiers ordered, all enums non-empty, `monitored_threads` well-formed).
  - `NEW` `tests/test_data.py` — validates `submissions.json` invariants (12 rows, required keys present, tier/vendor/backend ∈ schema, no template rows leaked).
  - `NEW` `tests/test_generate.py` — runs the generator into a temp dir; asserts all 5 pages + `data.json` are written, tag balance holds, no `{{` leaks.
- **Acceptance:**
  - `python -m unittest discover -s tests -v` runs and is **green**.
  - Each test file has ≥ 3 meaningful assertions (not just "doesn't crash").
  - Tests are deterministic (no network, no time-dependence).
- **Dependencies:** P0-3 (so `markdown` import is resolvable for the generator test).

#### P0-5 — Refresh stale documentation
- **Description:** `README.md` references a `dashboard/` dir and `generate.py` that no longer exist; `tools/README.md` references `generate.py` (superseded by `generate_site.py`) and the old single-page flow. Bring both current.
- **Files:**
  - `MOD` `README.md` — rewrite "What's Here" (root pages, not `dashboard/`), the weekly cycle (`pull → diff → parse → parse_thread → generate_site`), the 5-page site, the 8-guide roadmap, the GitHub Pages URL, and a pointer to `work/plans/PLAN.md`.
  - `MOD` `tools/README.md` — fix the file table (add `parse_thread.py`, `generate_site.py`; mark `generate.py` legacy/removed), fix the data-flow diagram, fix the deploy note (GitHub Pages from `/`, not `dashboard/`), add the "extend" workflow (edit `schema.json` → re-run).
- **Acceptance:**
  - No reference to a non-existent `dashboard/` dir or `generate.py` as the active generator.
  - The weekly-cycle commands in both files match the tools that actually exist.
  - A newcomer can clone, read the README, and run the pipeline successfully.
- **Dependencies:** none (can run parallel with P0-1…P0-4).

---

### Phase 1 — Guide Content (the core value delivery)

#### P1-0 — Guide architecture foundation (refactor the monolith)
- **Description:** The 826-line `generate_site.py` is the key technical debt. Refactor it into a clean, modular `tools/site/` package that (a) reproduces the existing 5 pages **byte-stably** and (b) adds the machinery to render markdown guide pages. This is the foundation all 8 guides build on — do it first and verify no regression.
- **Files:**
  - `NEW` `tools/site/__init__.py`
  - `NEW` `tools/site/template.py` — the page shell: `<head>` (title, description, **OG tags**, depth-relative CSS/JS paths), shared nav (with a Guides dropdown slot), shared footer. Computes the correct `./`/`../`/`../../` prefix per page depth.
  - `NEW` `tools/site/markdown.py` — wraps the `markdown` package (`tables`, `fenced_code`, `sane_lists`, `toc`); parses a small **front-matter** block (`title`, `description`, `nav`, `icon`, `related`, `og_image`); renders body to HTML; passes raw `<div class="diagram">` through.
  - `NEW` `tools/site/pages/__init__.py`, `tools/site/pages/homepage.py`, `matrix.py`, `community.py`, `guides_index.py`, `about.py` — one module per existing page, moved out of the monolith (logic unchanged).
  - `NEW` `tools/site/guides.py` — generic guide renderer: reads `content/guides/<slug>.md`, builds the shell, writes `guides/<slug>/index.html`, wires Related links.
  - `NEW` `content/guides/.gitkeep` — authored-content directory (separates hand-written input from generated output).
  - `MOD` `tools/generate_site.py` — becomes a **thin entry point** that calls the `tools/site` package and writes all pages + `data.json`.
  - `MOD` `css/style.css` — add `.diagram` base + the diagram sub-classes used by guides, `.callout`, `.progressive` (`<details>` styling), guide-page layout, and the nav Guides-dropdown.
  - `MOD` `js/main.js` — generalize active-link detection for dir-based URLs; add Guides-dropdown toggle.
- **Acceptance:**
  - `python tools/generate_site.py` produces **all 5 existing pages + `data.json`** with output **byte-identical** to the current monolith's output (golden-file check) — i.e., zero visible regression.
  - `tools/site/` has no file > ~300 lines; `generate_site.py` is < 60 lines.
  - `tools/site/template.py` correctly computes relative asset paths for a page at depth 2 (e.g., a future `guides/quantization/index.html`).
  - A **proof-of-concept** `content/guides/_sample.md` renders end-to-end to a temp `guides/_sample/index.html` (then removed) — proving the guide pipeline works before we author real content.
  - Tests (P0-4) still green; add a test that the refactor is regression-free.
- **Dependencies:** P0-3 (markdown dep), P0-4 (tests to prove no regression).

#### P1-1 — Guide: Quantization Basics
- **Description:** The most common source of confusion. Teaches what a quant is, the naming code (W4A16, FP8, Q4_K_M), the precision ladder, and the VRAM formula. **Content spec: `work/research_prompts.md` Prompt 1** (1500–2000 words, comparison table of precision levels, worked VRAM examples, "which quant should I use" decision guide).
- **Files:**
  - `NEW` `content/guides/quantization.md` — front-matter + body: 30-second version → what quantization is (CSS diagram: FP16 2B → INT4 0.5B per weight) → the naming code (table) → the precision ladder (CSS staircase) → symmetric/asymmetric + group sizes → **the VRAM formula** (worked example tied to a real Matrix submission) → "which quant should I pick" (decision cards) → tie-back → related.
- **Acceptance:**
  - Renders at `/guides/quantization/` via the generator.
  - Has the 30-second callout, ≥ 1 CSS diagram, ≥ 1 comparison table, and a "which should I use" decision section.
  - Every number ties to a real submission or the research; uncertain items are flagged.
  - Cross-links (Related) to `file-formats` and `quantization-methods`.
  - Word count 1400–2100; a11y + perf gates (P2-6/7) pass on this page.
- **Dependencies:** P1-0.

#### P1-2 — Guide: File Formats
- **Description:** GGUF vs safetensors vs MLX — what's inside, which to download, and can you convert. **Spec: Prompt 2** (1200–1500 words, comparison table).
- **Files:**
  - `NEW` `content/guides/file-formats.md` — 30-sec → "what's inside a model file" → 3 format cards (GGUF / Safetensors / MLX) → "which do I download" decision table (by backend) → the "shards" explainer → size estimation (reuse VRAM formula, cross-link) → conversion rules → tie-back → related.
- **Acceptance:** Renders at `/guides/file-formats/`; 3 format cards + download decision table + conversion section; cross-links to `quantization` and `backends`; word count 1100–1600.
- **Dependencies:** P1-0.

#### P1-3 — Guide: Quantization Methods
- **Description:** How quants are *made* and why one 4-bit beats another. **Spec: Prompt 3** (2000–2500 words — the deep one; RTN, GPTQ, AWQ, AutoRound, SmoothQuant, NVFP4/MXFP4, GGUF K-quant family).
- **Files:**
  - `NEW` `content/guides/quantization-methods.md` — 30-sec → each method as a card (RTN / GPTQ / AWQ / AutoRound / SmoothQuant / NVFP4+MXFP4 [flag: new] / GGUF K-quants + I-Nano/UD) → **comparison table** (method | precision | quality vs FP16 | speed | VRAM | backends | when to use) → "research vs production" flags → tie-back → related.
- **Acceptance:** Renders at `/guides/quantization-methods/`; ≥ 7 method cards + the master comparison table; NVFP4/MXFP4 explicitly flagged "new/evolving"; word count 1900–2600; cross-links to `quantization`, `file-formats`, `backends`.
- **Dependencies:** P1-0 (and reads naturally after P1-1).

#### P1-4 — Guide: Model Architectures
- **Description:** Dense vs MoE, what "A3B" means, and why a 125B model runs at 3B speed; plus MTP and speculative decoding. **Spec: Prompt 4** (1500–2000 words).
- **Files:**
  - `NEW` `content/guides/model-architectures.md` — 30-sec → Dense (examples from the Matrix) → MoE (**CSS diagram**: token → router → few lit experts) → "A3B decoded" → why MoE is revolutionary for local (CSS: total vs active params) → the tradeoff (more memory, less compute) → MTP + speculative decoding (**CSS diagram**: draft→verify loop) → "which architecture to pick" → tie-back → related.
- **Acceptance:** Renders at `/guides/model-architectures/`; ≥ 2 CSS diagrams (MoE routing, speculative decode); uses real Matrix model names; word count 1400–2100; cross-links to `kv-cache`, `backends`.
- **Dependencies:** P1-0.

#### P1-5 — Guide: KV Cache
- **Description:** The silent memory eater — why context length eats VRAM, and when to quantize the KV cache. **Spec: Prompt 5** (1500–2000 words, worked formula).
- **Files:**
  - `NEW` `content/guides/kv-cache.md` — 30-sec → what it is (separate from weights) → why it grows linearly (**CSS bar chart**: 4k→32k→128k→256k) → **the formula** (worked example: 27B @ 32k FP16) → KV quantization (FP8/INT8/INT4) → **when to quantize** vs **when NOT to** (two lists) → PagedAttention (vLLM) card → prompt caching (Strata) card → practical rule → tie-back → related.
- **Acceptance:** Renders at `/guides/kv-cache/`; ≥ 1 CSS diagram (linear growth) + the worked formula + the two "when (not) to quantize" lists; ties to the Matrix `kv_cache` column; word count 1400–2100; cross-links to `context-extension`, `multi-gpu`.
- **Dependencies:** P1-0.

#### P1-6 — Guide: Context Extension
- **Description:** Running models beyond their native context — RoPE, YaRN, NTK, and the honest limits. **Spec: Prompt 6** (1200–1500 words).
- **Files:**
  - `content/guides/context-extension.md` — 30-sec → RoPE in one breath → what happens past native context ("lost in the middle") → YaRN (scaling factor, how to set in llama.cpp/vLLM) → NTK (how it differs) → **the honest rule** (CSS scale: native → 2× → 4× → 8× with color-coded quality) → which models have large *native* context (no extension needed) → the VRAM cost (cross-link KV) → tie-back → related.
- **Acceptance:** Renders at `/guides/context-extension/`; CSS scale diagram + the "2× safe / 4× degrades / 8× risky" rule + native-context model list; word count 1100–1600; cross-links to `kv-cache`, `model-architectures`.
- **Dependencies:** P1-0.

#### P1-7 — Guide: Backends Deep Dive
- **Description:** The most-referenced page — every inference engine compared. **Spec: Prompt 7** (2500–3000 words — the longest guide; all 11 backends).
- **Files:**
  - `NEW` `content/guides/backends.md` — 30-sec → **the master comparison table** (11 backends × Formats · GPU/OS · key strength · best for · avoid when) → one card per backend (llama.cpp, llama-swap, Ollama, LM Studio, Unsloth Desktop, vLLM, TensorRT-LLM, Strata [flag], Radiance, MLX, Colibri) each with an **exact getting-started command** → "pick your backend" decision tree (CSS) → the golden rules → performance expectations per tier → tie-back → related.
- **Acceptance:** Renders at `/guides/backends/`; all 11 backend cards + the master table + a decision tree + a concrete command per backend; Strata/NVFP4 flagged as evolving; word count 2400–3100; cross-links to `file-formats`, `multi-gpu`.
- **Dependencies:** P1-0.

#### P1-8 — Guide: Multi-GPU & Hybrid
- **Description:** Making big models fit — tensor/pipeline parallel, layer offload, and the Strata hybrid (VRAM+RAM+SSD). **Spec: Prompt 8** (2000–2500 words).
- **Files:**
  - `NEW` `content/guides/multi-gpu.md` — 30-sec → the basic problem (70B FP16 ≈ 140GB) → **three split strategies** (tensor / pipeline / layer offload, each a card + CSS diagram) → the interconnect matters (NVLink / XGMI) → practical NVIDIA setups (table) → practical AMD setups (table, tied to a real 2×R9700 submission) → **the hybrid revolution (Strata)** (CSS: VRAM→RAM→SSD stack) → CPU+GPU hybrids (Colibri, 1TB-RAM path) → "what do I actually need?" decision guide → tie-back → related.
- **Acceptance:** Renders at `/guides/multi-gpu/`; ≥ 3 CSS diagrams (tensor/pipeline/offload stack); NVIDIA + AMD setup tables tied to real submissions; word count 1900–2600; cross-links to `kv-cache`, `backends`, `model-architectures`.
- **Dependencies:** P1-0.

#### P1-9 — Guides index live + nav dropdown
- **Description:** Turn the guides hub into a real table of contents and make the guides discoverable from the nav. Replaces the 8 "Coming Soon" cards.
- **Files:**
  - `NEW` `content/guides/index.md` — the guides index: grouped cards in 3 clusters (Fundamentals: quantization, file-formats, quantization-methods · The Model & Its Memory: model-architectures, kv-cache, context-extension · Running It: backends, multi-gpu) + a "not sure where to start?" decision list.
  - `MOD` `tools/site/pages/guides_index.py` — render from `content/guides/index.md` (live cards, not "Coming Soon").
  - `MOD` `tools/site/template.py` — add the **Guides dropdown** to the shared nav (lists all 8 guides; accordion on mobile).
  - `MOD` `index.html` generator (homepage) — the "Explore the Guides" grid now links to the 8 live guide URLs.
  - `MOD` `guides.html` → becomes a **redirect stub** to `guides/` (meta refresh + canonical) for back-compat with any existing links.
- **Acceptance:**
  - `/guides/` shows all 8 guide cards as **live links** (no "Coming Soon").
  - The nav Guides dropdown lists all 8 and highlights the active guide.
  - Homepage "Explore the Guides" links resolve.
  - Old `guides.html` URL redirects to `guides/` (no 404).
- **Dependencies:** P1-1 … P1-8 (all guides authored).

---

### Phase 2 — UX & Usability (the Decider's tools)

#### P2-1 — Recommendation engine (the core product feature)
- **Description:** Directly answers "What should I run, on what I have, for what I need?" The user states their **VRAM tier** + **use case** (optional: vendor, context need); the tool returns **ranked matching community setups** with honest tradeoffs. This is the highest-value feature on the site.
- **Files:**
  - `NEW` `content/recommend.md` (front-matter + the explainer/UX copy) + the interactive module.
  - `NEW` `tools/site/pages/recommend.py` — renders `/recommend/` (generated).
  - `MOD` `js/main.js` (or `NEW` `js/recommend.js`) — client-side ranking: filter `data.json` by tier + use-case (normalize the free-text `use_cases` against `schema.use_cases`), score by relevance (tier match, use-case match, backend fit, speed, confidence), render ranked result cards with a "why this matched" line and a link to the Matrix row.
  - `MOD` `tools/site/template.py` — add `Recommend` to the nav + homepage.
  - `MOD` homepage generator — a prominent "🎯 Find My Model" CTA → `/recommend/`.
- **Acceptance:**
  - Picking a tier + use case returns a ranked list of real submissions, each with a one-line "why" and a link to its Matrix row.
  - Normalizing free-text use cases works (e.g., "LLM-assisted coding" → "Agentic Coding").
  - Zero matches → a helpful "no community setup yet for that combo — here's the closest + how to submit one" fallback (links to P3-4 form).
  - Fully client-side (no server); works offline from `data.json`.
  - A11y + perf gates pass.
- **Dependencies:** P1-0 (generator architecture), P0-4 (tests). *This is the top Phase-2 priority.*

#### P2-2 — Comparison view
- **Description:** Side-by-side 2–4 setups with differences highlighted — "which of these is better for me?"
- **Files:**
  - `NEW` `tools/site/pages/compare.py` — renders `/compare/` (generated).
  - `MOD` `js/main.js` — compare logic: read `?a=&b=&c=&d=` (submission IDs) from the URL; render a diff table (rows = attributes, columns = setups) with **differing cells accent-tinted**; a short factual "takeaway" line; "copy launch command" per column (see P2-3).
  - `MOD` matrix page — add a **compare checkbox** per row; "Compare (N) →" builds the `/compare/?a=&b=` deep link.
  - `MOD` `tools/site/template.py` — add `Compare` to nav.
- **Acceptance:**
  - Selecting 2–4 Matrix rows → `/compare/` shows them side-by-side with differences highlighted.
  - Selection is a **shareable URL** (deep link restores the comparison on load).
  - Arriving with no selection shows a picker (dropdowns of all submissions).
  - A11y + perf gates pass.
- **Dependencies:** P1-0, P2-3 (launch-command map reused).

#### P2-3 — Launch command generator
- **Description:** Turn any submission into a representative, copy-able CLI command for its backend — makes the tool feel concrete. Clearly labeled "example command" (not a guarantee).
- **Files:**
  - `NEW` `js/commands.js` (or a section in `main.js`) — a **backend → command template** map (llama.cpp, Ollama, vLLM, Strata, Radiance, MLX, Colibri, etc.) that fills in the submission's model/quant/context.
  - `MOD` matrix + compare + recommend pages — a "Copy launch command" button per submission (uses `navigator.clipboard`).
- **Acceptance:**
  - Each of the 12 submissions yields a plausible, backend-correct command (e.g., `llama-server -m <model>.gguf -ngl 99 -c 32768`, `vllm serve <model> --tensor-parallel-size 2`).
  - The button is labeled "example command" and the command is copy-able.
  - Unknown/`Other` backends degrade gracefully (show model + a "check the guide" note, no fabricated flag).
- **Dependencies:** P1-0. (Used by P2-2 and P2-5.)

#### P2-4 — Shareable filters (URL-synced)
- **Description:** The Matrix/Community filters currently can't be shared. Make filter state live in the URL (deep-linkable) and add the missing axes.
- **Files:**
  - `MOD` `js/main.js` — on filter change, `history.replaceState` writes `?tier=&vendor=&backend=&use_case=&mode=&q=`; on load, read the query string and restore state.
  - `MOD` matrix + community page generators — add **Use Case** and **Engine Mode** filter selects (from `schema.json`); keep existing Tier/Vendor/Backend/Search.
- **Acceptance:**
  - Any filter combination produces a **shareable URL** that restores the exact view on load.
  - All 5–6 filter axes work and combine correctly (AND logic).
  - Empty result states are handled ("no setups match — clear filters").
- **Dependencies:** P1-0.

#### P2-5 — Matrix row → detail panel
- **Description:** A data row is thin. Clicking it opens a slide-in panel with the *full* submission — turning a row into a mini case study.
- **Files:**
  - `MOD` matrix page generator — each row gets a clickable affordance (row + `ⓘ`) with `data-*` carrying the full submission.
  - `MOD` `css/style.css` — `.detail-panel` (slide-in, focus-trapped, ESC-to-close).
  - `MOD` `js/main.js` — open/populate/close the panel; show complete hardware, all notes, the user's quote, KV + power, the **original forum deep link** (`/t/256443/#post-N`), and a "Copy launch command" button (P2-3).
- **Acceptance:**
  - Clicking any row opens a panel with the full submission + a working forum deep link.
  - Keyboard-accessible (focus trap, ESC closes, restores focus).
  - A11y + perf gates pass.
- **Dependencies:** P1-0, P2-3.

#### P2-6 — Accessibility + mobile audit (WCAG 2.1 AA)
- **Description:** A real, documented audit of **all** pages (5 main + 8 guides + new Phase-2 pages) against WCAG 2.1 AA and mobile breakpoints, with fixes.
- **Files:**
  - `MOD` `css/style.css` — fix contrast to ≥ 4.5:1, touch targets ≥ 44px, focus-visible styles, `prefers-reduced-motion`.
  - `MOD` `js/main.js` — keyboard support for nav dropdown, filters, detail panel, compare.
  - `MOD` page generators — semantic landmarks, one `<h1>`, logical heading order, `aria-*` on interactive controls, `alt` on icons.
- **Acceptance:**
  - **Lighthouse Accessibility ≥ 95** on every page (documented in a report at `work/scratch/a11y_audit.md`).
  - Fully keyboard-operable; no focus traps; screen-reader labels present.
  - Verified at 360 / 768 / 1024 px (no horizontal scroll, diagrams stack cleanly).
- **Dependencies:** P1-9, P2-1 … P2-5 (all pages exist to audit).

#### P2-7 — Performance budget enforcement
- **Description:** Enforce the §5.6 budget across all pages; eliminate render-blocking and bloat.
- **Files:**
  - `MOD` `css/style.css` / `js/main.js` — minify targets, defer non-critical JS, inline only critical CSS if needed.
  - `MOD` generators — ensure no large inline payloads; `data.json` loaded efficiently.
- **Acceptance:**
  - **Lighthouse Performance ≥ 90** on every page (report at `work/scratch/perf_audit.md`).
  - LCP < 2.5s, CLS < 0.1, INP < 200ms on a throttled mid-phone.
  - HTML < 100KB, CSS < 60KB, JS < 30KB (gzip) per page.
- **Dependencies:** P1-9, P2-1 … P2-6.

---

### Phase 3 — Automation & Sustainability

#### P3-1 — CI/CD (GitHub Actions)
- **Description:** Enforce quality on every push/PR and keep GitHub Pages in sync. No more "hope the manual run worked."
- **Files:**
  - `NEW` `.github/workflows/ci.yml` — on `push` + `pull_request` to `main`: set up Python 3.14 → `pip install -e .` → `python -m unittest discover -s tests` → `python tools/validate.py` (P3-5) → `python tools/generate_site.py` (into a temp dir) → structural checks (tag balance, no `{{` leaks, all nav/footer/OG present) → **fail the build on any regression**.
  - `NEW` `.github/workflows/deploy.yml` (or a job in `ci.yml`) — on green `main`: commit generated outputs + `git push` (or use the Pages source) so the live site matches the repo.
- **Acceptance:**
  - A PR that breaks a test, a schema invariant, or a generated page **fails CI** and cannot merge.
  - Pushing green `main` updates the live GitHub Pages site.
  - CI runs in < 3 min.
- **Dependencies:** P0-4 (tests), P3-5 (validator). *Start with tests-only; add the validator when P3-5 lands.*

#### P3-2 — Full automated test suite (grow the skeleton)
- **Description:** Expand P0-4 into a robust suite, including **golden-file regression** so any accidental change to a generated page is caught.
- **Files:**
  - `MOD` `tests/test_generate.py` — add golden-file checks: regenerate all pages, diff against committed baselines in `tests/golden/` (update deliberately via a documented command).
  - `NEW` `tests/test_parse.py` — `parse.py` edge cases: template filtering, tier normalization (longest-first), `normalize_backend`, multi-submission posts.
  - `NEW` `tests/test_markdown.py` — front-matter parsing, raw-HTML diagram pass-through, table rendering.
  - `NEW` `tests/golden/` — baseline HTML for each page.
- **Acceptance:**
  - `python -m unittest discover -s tests` is green with meaningful coverage of parse + generate + markdown.
  - A deliberate edit to a generated page is **caught** by the golden-file test.
  - Golden baselines are regenerated via a single documented command (no hand-editing).
- **Dependencies:** P0-4, P1-0 (stable generator output to golden against).

#### P3-3 — Scheduled weekly data pull
- **Description:** Automate the weekly cycle's first step. A scheduled workflow pulls the forum, runs the pipeline, and **opens a PR** with the new submissions for human review — never auto-merges raw data.
- **Files:**
  - `NEW` `.github/workflows/weekly-pull.yml` — cron (weekly): `pull.py` (with the browser-UA / curl fallback) → `diff.py` (report) → `parse.py` + `parse_thread.py` → `generate_site.py` → open a PR titled "Weekly rollup YYYY-MM-DD" with the diff summary. Uses `GITHUB_TOKEN` for the PR.
- **Acceptance:**
  - The scheduled run produces a reviewable PR containing new/changed submissions and the regenerated site.
  - A human reviews + merges (the maintainer stays in the loop; "community owns the data, the maintainer organizes it").
  - A failed pull (e.g., forum 403) is reported in the PR/run log, not silently dropped.
- **Dependencies:** P3-1 (CI infra), P0-1 (clean git state).

#### P3-4 — Community submission form
- **Description:** Lower the barrier to contributing. A **static** form (no server) that produces a ready-to-paste `[COMMUNITY-SUBMISSION]` block for the forum thread.
- **Files:**
  - `NEW` `content/submit.md` + `NEW` `tools/site/pages/submit.py` — renders `/submit/`.
  - `NEW` `js/submit.js` — form fields (tier, hardware, vendor, backend, model, quant, use case, context, KV, speed, power, notes) → assembles the exact `[COMMUNITY-SUBMISSION]` text → "Copy for the forum" button + a link to the thread.
- **Acceptance:**
  - Filling the form produces a correctly-formatted `[COMMUNITY-SUBMISSION]` block matching what `parse.py` expects.
  - "Copy" puts it on the clipboard; a link takes the user to the forum thread to post it.
  - No server, no account, no storage (pure static + client JS).
  - A11y + perf gates pass.
- **Dependencies:** P1-0.

#### P3-5 — Data-quality validation
- **Description:** A dedicated validator that surfaces data gaps (the known issues: no Apple submissions, empty `engine_mode`, free-text use cases) so quality problems are visible, not silent.
- **Files:**
  - `NEW` `tools/validate.py` — checks `submissions.json` against `schema.json`: required fields present, enum conformance, tier/vendor/backend validity, use-case normalization coverage, and reports **gaps** (e.g., "0 Apple/MLX submissions," "11/12 engine_mode empty," "N un-normalizable use cases"). Exit non-zero on hard errors, warn on gaps.
  - `MOD` `.github/workflows/ci.yml` — run `validate.py` (from P3-1).
  - `NEW` `tests/test_validate.py`.
- **Acceptance:**
  - `python tools/validate.py` runs clean and prints a data-quality report (counts by vendor/tier/backend + the known gaps).
  - A malformed submission (bad enum, missing field) **fails** validation (non-zero exit) and blocks CI.
  - The report is usable by the maintainer to drive curation (e.g., recruit Apple submissions).
- **Dependencies:** P0-4, P3-1.

---

### Phase 4 — Growth & Polish

#### P4-1 — Charts & visualizations
- **Description:** Make the data visible. Pure **inline SVG** generated by Python (no client chart library, keeping the no-dep client promise).
- **Files:**
  - `NEW` `tools/site/charts.py` — SVG generators: **speed vs VRAM** scatter (x = tier/VRAM, y = decode tok/s, point = submission), **context length** bar chart, **vendor/tier distribution** bars.
  - `MOD` homepage + matrix generators — embed 2–3 charts in relevant sections.
- **Acceptance:**
  - ≥ 2 meaningful, data-driven SVG charts render (scalable, crisp, dark-theme styled).
  - No external chart library; SVG is inlined in the generated HTML.
  - Charts update automatically when new submissions land (data-driven, not hard-coded).
- **Dependencies:** P1-0, P2-1 (charts reinforce the recommend/matrix story).

#### P4-2 — Custom domain
- **Description:** Move from `madgoathaz.github.io/llm-matrix/` to a clean custom domain (e.g., `localaistack.dev`).
- **Files:**
  - `NEW` `CNAME` — the domain (committed to repo root; GitHub Pages serves it over HTTPS).
  - `MOD` all generators + `template.py` — update `og:url`, canonical, and absolute links to the custom domain.
- **Acceptance:**
  - The site is reachable at the custom domain over HTTPS.
  - The old `madgoathaz.github.io/llm-matrix/` URL **redirects** (301) to the new domain (no broken bookmarks).
  - OG tags + forum featured link updated to the new domain.
- **Dependencies:** P0-2 (OG image), P1-9 (stable URLs). *Domain purchase is a maintainer action outside the repo.*

#### P4-3 — Advanced filtering
- **Description:** Power-user filtering: multi-select, saved views, and extra axes (quant, context range, power).
- **Files:**
  - `MOD` matrix generator + `js/main.js` — multi-select filter chips, "save view" (localStorage + shareable URL), quant/context/power axes.
- **Acceptance:**
  - Users can combine multiple values per axis (OR within an axis, AND across axes).
  - A saved view persists and is shareable via URL.
  - Performance stays within budget (P2-7) as the dataset grows.
- **Dependencies:** P2-4 (URL-synced filters).

#### P4-4 — Data API
- **Description:** Formalize the JSON the site already emits as a **stable, versioned data API** for third-party tooling (scripts, other sites, research).
- **Files:**
  - `MOD` generators — emit clean, documented data files: `data/api/v1/submissions.json`, `data/api/v1/schema.json`, `data/api/v1/benchmarks.json`, `data/api/v1/hardware.json` (versioned, stable shapes).
  - `NEW` `data/api/README.md` — the API contract (fields, versions, changelog).
- **Acceptance:**
  - Versioned JSON endpoints with stable, documented schemas.
  - A breaking change bumps the version (v1 → v2) rather than silently breaking consumers.
  - Documented in `data/api/README.md`.
- **Dependencies:** P3-5 (validation keeps the API trustworthy).

#### P4-5 — Community contribution workflow
- **Description:** Make contributing effortless and the project self-sustaining: onboarding, changelog automation, and privacy-friendly analytics.
- **Files:**
  - `MOD` about + community generators — a clear "how to contribute" path (form → forum → appears here within a week) + enriched contributor profiles.
  - `NEW` `tools/changelog.py` — auto-generate a changelog from git history + the weekly diff (new submissions, new guides).
  - `NEW` (optional) privacy-friendly analytics (e.g., Plausible) — **off by default**, maintainer opt-in.
- **Acceptance:**
  - A new contributor can go from "I have a setup" to "it's on the site" following written steps.
  - The changelog is auto-generated and current.
  - Analytics (if enabled) are privacy-friendly and clearly disclosed.
- **Dependencies:** P3-4 (form), P3-3 (weekly cycle).

---

## 7. Risk Register

| # | Risk | Type | Likelihood | Impact | Mitigation |
|---|---|---|---|---|---|
| R1 | **Guide inaccuracy** on fast-moving topics (NVFP4, Strata, MTP) erodes trust | Technical/Content | Med | High | Research prompt flags uncertainty; every guide carries "new/evolving" callouts; weekly refresh; accuracy gate (§5.4) ties numbers to real submissions. |
| R2 | **Monolith refactor (P1-0) breaks the live site** | Technical | Med | High | Golden-file regression test proves byte-stable output *before* merging; the refactor is isolated and reversible; site stays live at each step. |
| R3 | **Root-URL / guides-URL migration breaks bookmarks** | Scope | Low | Med | Existing 5 pages stay put; only `guides.html` → `guides/` changes, with a redirect stub; custom domain (P4-2) adds a 301. |
| R4 | **Forum pull gets blocked (403)** on the scheduled run | Technical | Med | Med | `pull.py` already has browser-UA + curl fallback; weekly-pull PR **reports** failures instead of silently dropping data; human in the loop. |
| R5 | **Scope creep** in Phase 2 (recommend/compare/detail) delays the guides | Scope | Med | High | **Guides (Phase 1) are the top priority** and land before Phase 2; each Phase-2 feature is a bounded chunk with a clear "done." |
| R6 | **Data sparsity** (12 submissions, 0 Apple) makes recommend/charts thin | Data | High | Med | Honest empty/fallback states; data-quality validation (P3-5) surfaces gaps; submission form (P3-4) + forum CTA grow the set; guides don't depend on data volume. |
| R7 | **Single-maintainer bus factor** | Maintenance | Med | High | Everything is documented (README, tools/README, this plan, API README); CI enforces quality; the weekly cycle is automated; any contributor can pick up a chunk. |
| R8 | **Free-text `use_cases`** breaks recommend/ranking reliability | Technical | Med | Med | Normalize use cases against `schema.use_cases` in P2-1; flag un-normalizable ones in P3-5; guide the submission form (P3-4) toward structured values. |
| R9 | **CSS diagrams break across breakpoints** | Technical | Low | Med | Mobile-first; tested at 360/768/1024 (P2-6); diagrams degrade to stacked boxes on narrow screens. |
| R10 | **Adding the `markdown` dep** surprises a "stdlib-only" purist | Scope | Low | Low | Explicitly scoped & documented (§5.1): data pipeline stays stdlib; only the content layer uses one pure-Python dep; a stdlib fallback is documented. |

---

## 8. Definition of Done

### 8.1 Per-phase completion gates

**Phase 0 — Foundation & Hygiene:** DONE when
- [ ] `git worktree list` shows only main; `entertaining-puck` removed; nothing unpushed.
- [ ] `og-image.png` (1200×630) + `og-image.svg` committed; forum onebox renders a thumbnail.
- [ ] `pyproject.toml` valid; `pip install -e .` works in a clean venv (Python ≥ 3.14).
- [ ] `python -m unittest discover -s tests` is green (skeleton).
- [ ] `README.md` + `tools/README.md` are current (no stale `dashboard/`/`generate.py` refs).

**Phase 1 — Guide Content:** DONE when
- [ ] `tools/site/` package exists; `generate_site.py` is a thin entry point; **no file > ~300 lines**.
- [ ] All **8 guides** authored from `research_prompts.md`, live at `/guides/<slug>/`, each with: 30-second callout, ≥ 1 CSS diagram, ≥ 1 table, a "which should I use" close, Related links, and uncertainty flags.
- [ ] `/guides/` index shows 8 live cards (no "Coming Soon"); nav Guides dropdown works.
- [ ] Existing 5 pages are **regression-free** (golden-file test green).
- [ ] Every guide's numbers trace to a real submission or the research.

**Phase 2 — UX & Usability:** DONE when
- [ ] `/recommend/` answers "tier + use case → ranked setups with honest tradeoffs."
- [ ] `/compare/` shows 2–4 diff-highlighted setups from a shareable URL.
- [ ] Every submission yields a labeled, copy-able launch command.
- [ ] Matrix/Community filters are URL-synced + shareable; row → detail panel works.
- [ ] **Lighthouse Accessibility ≥ 95** and **Performance ≥ 90** on every page; budgets met.

**Phase 3 — Automation & Sustainability:** DONE when
- [ ] CI runs tests + validator + generator on every push/PR and **blocks** regressions.
- [ ] Golden-file regression catches accidental page changes.
- [ ] The weekly scheduled pull opens a reviewable PR (human merges).
- [ ] `/submit/` produces a correct, copy-able `[COMMUNITY-SUBMISSION]` block.
- [ ] `tools/validate.py` reports data quality (incl. the known gaps) and fails on hard errors.

**Phase 4 — Growth & Polish:** DONE when
- [ ] ≥ 2 data-driven SVG charts render and auto-update.
- [ ] Custom domain live over HTTPS with a 301 from the old URL.
- [ ] Advanced filtering (multi-select + saved views) works within the perf budget.
- [ ] A versioned, documented data API exists.
- [ ] Contribution path is end-to-end clear; changelog auto-generates.

### 8.2 Overall quality gates (apply to every merge)
1. **Tests green** — `python -m unittest discover -s tests`.
2. **Validator green** — `python tools/validate.py` (no hard errors).
3. **Generator clean** — `python tools/generate_site.py` writes all pages; no `{{` leaks; tag balance holds; golden files stable.
4. **A11y ≥ 95, Perf ≥ 90** — Lighthouse on every public page.
5. **No hand-edited generated HTML** — all changes flow through `content/**` + `tools/site/`.
6. **Docs current** — README/tools/README reflect reality.
7. **User-value check** — the change makes it easier for a person to answer "what should I run, on what I have, for what I need?"

---

*This plan is the single source of truth for implementation. Execute chunks top-to-bottom within each phase; respect the stated dependencies. When in doubt, optimize for the reader's time saved — that is the project's only success metric.*
