# The Local AI Stack — Project Handover

## Current State

As of 2026-10-13: **26 submissions** from **7 contributors**, spanning
**3 hardware vendors** and **7 backends**, **8 live guides**, full CI/CD
(test + lint + build + auto-deploy on every push, plus a scheduled weekly
data pull), the **recommendation engine**, the **compare tool**,
**launch-command generation**, the **submission form**, and the
**versioned data API (v1.3, schema v2.4)**. The site is live at
<https://madgoathaz.github.io/llm-matrix/>.

For the short version, read [`README.md`](README.md); for the philosophy,
read [`VISION.md`](VISION.md). The detailed development history lives in
the maintainer's internal notes (git-ignored), not in this repo.

## What This Is

The Local AI Stack is a community-driven resource for running AI/LLM models on personal hardware. It originated as a forum thread on Level1Techs (a high-end hardware/tech community) and has grown into a multi-component project:

- **A forum thread** where community members submit their hardware setups, model choices, and performance data
- **A static website** (GitHub Pages) that organizes, filters, and displays all that data interactively
- **A set of Python tools** that automate the data pipeline (pull from forum → parse → generate website)
- **A collection of 8 educational guides** (all live) covering quantization, file formats, architectures, KV cache, context extension, backends, and multi-GPU strategies

The project's goal is to be the definitive "go-to" reference for the local AI community — answering "what should I run on my hardware for my use case?" with community-verified data.

## Project Identity

| Element | Value |
|---------|-------|
| Name | The Local AI Stack |
| Tagline | Models, Hardware, Backends & Community Data |
| Forum Thread | https://forum.level1techs.com/t/256443 |
| Forum Category | https://forum.level1techs.com/c/high-performance-computing/deep-machine-learning-ai/155 |
| Website | https://madgoathaz.github.io/llm-matrix/ |
| GitHub Repo | https://github.com/MadGoatHaz/llm-matrix (public) |
| Forum User | MadGoat (thread OP) |
| Data Source | Discourse public JSON API (no auth needed) |

## Directory Structure

```
.
├── about.html                  # Generated: About page (project description, L1Techs connection, contribution info)
├── community.html              # Generated: Community page (contributor cards showing each person's submissions)
├── data.json                   # Generated: The canonical dataset (carries the data API `version`)
├── guides.html                 # Generated: Redirect stub → /guides/ (keeps old links working)
├── index.html                  # Generated: Homepage (hero, stats, charts, community highlights, how it works)
├── matrix.html                 # Generated: Full data table with filters (tier, vendor, backend, search)
├── og-image.png                # 1200×630 OG image for forum onebox cards (og-image.svg is the editable source)
├── README.md                   # Project README — the public front door
├── VISION.md                   # What the project is and why
│
├── guides/                     # Generated: the 8 deep-dive guides (guides/<slug>/index.html) + the index
├── recommend/                  # Generated: the recommendation engine page
├── compare/                    # Generated: the side-by-side comparison page
├── submit/                     # Generated: the static community submission form
├── api/                        # Generated: the data API documentation page
│
├── css/
│   └── style.css               # Design system: CSS custom properties/tokens, layout, cards, tables, filters, badges, hero, mobile breakpoints
│
├── js/
│   ├── main.js                 # Shared interactivity: nav toggle, active-link, table sort, search+filters, reset, detail panel
│   ├── recommend.js            # The recommendation engine (client-side, island-baked data)
│   ├── compare.js              # The compare view (winner markers + tradeoffs)
│   ├── commands.js             # The launch-command generator
│   └── submit.js               # The submission form assembler
│
├── data/
│   ├── benchmarks.json         # Parsed: Performance data from Crucible thread (TTFT, throughput)
│   ├── category_threads.json   # Parsed: New thread titles/URLs from ML,LLMs&AI category
│   ├── hardware.json           # Parsed: GPU configs, builds from Show Off Your AI Rig thread
│   ├── last_seen.json          # Baseline for diff.py (tracks what's been seen since last pull)
│   ├── submissions.json        # Parsed: Canonical dataset from main thread [COMMUNITY-SUBMISSION] blocks
│   │
│   └── raw/
│       ├── category_latest.json  # Raw Discourse JSON: ML,LLMs&AI category feed
│       ├── crucible_latest.json  # Raw Discourse JSON: Crucible LLM Bench thread
│       ├── latest.json           # Raw Discourse JSON: copy of main (backward compat for parse.py)
│       ├── main_latest.json      # Raw Discourse JSON: The Local AI Stack main thread
│       └── rigs_latest.json      # Raw Discourse JSON: Show Off Your AI Rig thread
│
├── forum/
│   ├── Post1.md                # "The Hub" — front door: orientation, dashboard link, GPU lookup, use-case finder, full matrix (6 tiers, 27 models), community highlights, CTA
│   ├── Post2.md                # "The Reference" — workshop: submission templates, backend guide, hardware notes, non-GGUF guide, KV cache rule, constraints, data viewport, changelog, integration process
│   ├── Post_Change_Log.md      # Version history for all forum posts (v1.0 → v2.0 → v2.1)
│   └── bump.md                 # v2.1 bump post: announces updates, drives traffic back to the thread
│
├── tools/
│   ├── README.md               # Tools documentation
│   ├── diff.py                 # Compares data/raw/latest.json against data/last_seen.json; shows new/updated/removed posts
│   ├── generate_site.py        # Generates the 5-page website (index, matrix, community, guides, about) + data.json
│   ├── parse.py                # Extracts [COMMUNITY-SUBMISSION] blocks from main thread → data/submissions.json
│   ├── parse_thread.py         # Parses secondary threads (crucible→benchmarks, rigs→hardware, category→threads)
│   ├── pull.py                 # Fetches all monitored threads from Discourse API → data/raw/{id}_latest.json
│   ├── schema.json             # Editable config: tiers, vendors, backends, quants, use cases, engine modes, confidence, lifecycle, monitored_threads
│   └── tags.json               # Manual curation layer: per-submission overrides + forum feedback tracking
│
├── templates/
│   └── .gitkeep                  # Reserved for future use
│
└── .gitignore
```

The maintainer keeps a git-ignored internal workspace (development logs,
plans, research notes, scratch space) outside the public repo — it is not
part of the site and not referenced by any public document.

## The Data Pipeline

### Flow
```
Discourse API (thread JSON)
    → tools/pull.py (fetches + saves to data/raw/)
    → tools/diff.py (shows what's new since last pull)
    → tools/parse.py (extracts [COMMUNITY-SUBMISSION] blocks → data/submissions.json)
    → tools/parse_thread.py (parses secondary threads: benchmarks, hardware, category)
    → tools/generate_site.py (renders multi-page website from data)
    → git push (GitHub Pages auto-deploys)
```

### Running the Weekly Cycle
```bash
cd "/home/madgoat/Documents/Local LLM Matrix"
python tools/pull.py              # Fetch all monitored threads
python tools/diff.py              # See what's new
# ... review new data, update tools/schema.json or tools/tags.json if needed ...
python tools/parse.py             # Parse main thread submissions
python tools/parse_thread.py      # Parse secondary threads
python tools/generate_site.py     # Generate website
git add . && git commit -m "Weekly update $(date +%Y-%m-%d)" && git push
```

### Current Pipeline Status
- `pull.py`: Works. Fetches 4 threads (main, crucible, rigs, category). Uses browser User-Agent to avoid 403 bot protection. Note: may still get 403 in some cases; use `curl` fallback if needed.
- `diff.py`: Works. Shows new/updated/removed posts. Compares against `data/last_seen.json`.
- `parse.py`: Works. Extracts submissions, filters templates, normalizes tiers, applies tag overrides. Known issue: some non-standard field names from individual users may not be captured.
- `parse_thread.py`: Works. Extracts basic data from secondary threads (keyword-based detection for benchmarks and hardware).
- `generate_site.py` / `python -m tools.site`: Works. Generates the full site (homepage, matrix, community, guides index + the 8 guides, about, recommend, compare, submit, api) + data.json + the versioned data API. All values HTML-escaped. Template submissions filtered out.

## The Website

### Pages
| Page | File | Purpose | Status |
|------|------|---------|--------|
| Homepage | index.html | Landing, live stats, charts, community highlights, how it works | ✅ Live |
| Matrix | matrix.html | Full data table with filters (tier, vendor, backend, search) + detail panels + launch commands | ✅ Live |
| Compare | compare/index.html | Side-by-side 2–4 setups with winner markers and a tradeoff read | ✅ Live |
| Recommend | recommend/index.html | The core tool: ranked community setups for your hardware + use case | ✅ Live |
| Community | community.html | Contributor cards showing each person's submissions | ✅ Live |
| Submit | submit/index.html | The static form that builds a ready-to-post submission block | ✅ Live |
| Guides | guides/index.html + guides/<slug>/ | The 8 deep-dive guides | ✅ Live |
| Data API | api/index.html | Documentation for the versioned JSON data contract | ✅ Live |
| About | about.html | Project description, L1Techs connection, contribution info | ✅ Live |

### Design System
- All styling in `css/style.css` (CSS custom properties / design tokens)
- All interactivity in `js/main.js` (vanilla JS, no dependencies)
- Dark mode by default
- Mobile responsive (hamburger nav, stacked cards)
- Open Graph tags on every page (for forum onebox cards)

### Key Design Decisions
- Static HTML (no SPA, no framework, no build step)
- Python generates the HTML (Jinja2-style string formatting)
- GitHub Pages hosts it (free, CDN, custom domain capable)
- Data is injected at build time (no runtime API calls, no CORS issues)
- Each page is self-contained (works without any server logic)

## The Forum Posts

### Post #1 (The Hub)
- File: `forum/Post1.md`
- Purpose: Front door. Orientation, dashboard link, quick GPU lookup, use-case finder, full matrix (6 tiers, 27 models), community highlights, CTA to contribute
- Format: Discourse markdown + HTML (details/summary, tables)
- Current version: v2.1

### Post #2 (The Reference)
- File: `forum/Post2.md`
- Purpose: Deep reference. Submission templates, backend guide, hardware notes, non-GGUF guide, KV cache rule, constraints, data viewport, changelog, integration process
- Format: Discourse markdown + HTML
- Current version: v2.1

### Bump Post
- File: `forum/bump.md`
- Purpose: Announces updates, drives traffic back to the thread
- Current: v2.1 bump

### Change Log
- File: `forum/Post_Change_Log.md`
- Purpose: Version history for all forum posts (v1.0 → v2.0 → v2.1)

### Key Forum Integration Points
- **Featured Link**: Set the topic's featured link to `https://madgoathaz.github.io/llm-matrix/` — this shows a onebox preview card at the top of the thread (requires OG tags, which are in place)
- **Onebox**: Pasting the dashboard URL in any post auto-generates a preview card
- **No iframes**: Discourse blocks iframes from non-allowlisted domains. The relationship is link-based, not embed-based.

## Monitored Threads

Defined in `tools/schema.json` under `monitored_threads`:

| ID | Thread | Type | Data Extracted |
|----|--------|------|----------------|
| main | The Local AI Stack (#256443) | submissions | [COMMUNITY-SUBMISSION] blocks → submissions.json |
| crucible | Crucible: LLM Bench (#257531) | benchmarks | Performance data (TTFT, throughput) → benchmarks.json |
| rigs | Show Off Your AI Rig (#255709) | hardware | GPU configs, builds → hardware.json |
| category | ML, LLMs & AI Category (#155) | general | New thread titles/URLs → category_threads.json |

To add a new thread: add an entry to `monitored_threads` in schema.json with id, url (with .json), name, type, description. Then add a parser function in `parse_thread.py`.

## Configuration Files

### tools/schema.json
The editable definition of all valid values:
- `tiers`: 6 VRAM tiers with ID, label, range
- `hardware_vendors`: NVIDIA, AMD, Apple, Intel, Mixed
- `backends`: All known inference backends (vLLM, llama.cpp, llama-swap, Ollama, LM Studio, Unsloth Desktop, Strata, Radiance, Colibri, TensorRT-LLM, MLX, Other)
- `os_drivers`: OS + driver combinations
- `quant_formats`: All known quantization formats (W4A16, FP8, NVFP4, MXFP4, Q4_K_M, I-Nano, etc.)
- `kv_cache_types`: KV cache precision options
- `use_cases`: Categorized use cases
- `engine_modes`: VRAM-only, Hybrid variants, CPU+GPU
- `confidence_levels`: op-verified, community-verified, community-reported, unverified
- `lifecycle_statuses`: current, watch, superseded, discontinued
- `monitored_threads`: The 4 threads being tracked

**When the field changes** (new backend, new quant format, new tier): edit this file, then re-run parse + generate.

### tools/tags.json
Manual curation layer:
- `submissions`: Per-submission overrides (confidence, lifecycle, highlight, tags)
- `forum_feedback`: Tracking of community suggestions and their resolution status

**When to edit**: When you want to highlight a particular submission, change its confidence level, or track a community suggestion.

## The Guides (All Live)

8 guides, rendered from authored markdown in `content/guides/`:

| # | Guide | Slug | Status |
|---|-------|------|--------|
| 1 | Quantization Basics | `quantization` | ✅ Live |
| 2 | File Formats | `file-formats` | ✅ Live |
| 3 | Quantization Methods | `quantization-methods` | ✅ Live |
| 4 | Model Architectures | `model-architectures` | ✅ Live |
| 5 | KV Cache | `kv-cache` | ✅ Live |
| 6 | Context Extension | `context-extension` | ✅ Live |
| 7 | Backends Deep Dive | `backends` | ✅ Live |
| 8 | Multi-GPU & Hybrid | `multi-gpu` | ✅ Live |

**To add or update a guide:**
1. Author the content as `content/guides/<slug>.md` (front matter + markdown; the guide renderer handles the rest)
2. Dataset figures in the prose use `{{data tokens}}` (e.g. `{{submission_count}}`, `{{backend_count}}`, `{{last_updated}}`) — the renderer fills them from the live dataset at build time, so the numbers never go stale
3. Re-run `python -m tools.site`
4. Push

## Research Notes

The one-off research notes that informed the original build were pruned
during the final cleanup: their findings were folded into the guides and the
built site. The originals remain recoverable from git history if ever needed.

## Git History

Run `git log --oneline` to see full history. Key milestones:
- `8388c08` — Initial commit: tools + schema + forum posts
- `504f156` — L1Techs community branding
- `86e2537` — Dashboard output to repo root for GitHub Pages
- `c8d55a6` — First full pipeline run: dashboard live with community data
- `234ebea` — Restructure: Post #1 = Hub, Post #2 = Reference. Add community insights
- `0e3a85b` — Fix dashboard: filter templates, fix tier sort/filter, add columns, HTML escape, CSS ellipsis
- `e1dc02a` — Clean up forum/: Post1.md, Post2.md, bump.md, Post_Change_Log.md
- `c6d87f5` — Rebuild as multi-page website: homepage, matrix, community, guides, about. Full design system. OG tags
- `2dcc2c7` — Multi-thread monitoring: pull + parse Crucible, AI Rigs, and ML/AI category
- `47d14b6` — Homepage: remove Find Your Setup, enhance Community Highlights, add Related Resources

## Historical: Known Issues (All Resolved)

The original handover listed these as open work. **Every one is done** —
they are kept here only so a future reader can see the arc:

- ~~og-image.png missing~~ — created (1200×630, `og-image.svg` is the editable source)
- ~~Forum posts not updated to match the website~~ — Post #1 (Hub) and Post #2 (Reference) are live in the thread
- ~~Featured Link not set~~ — set on the forum topic
- ~~8 guide pages empty~~ — all 8 guides are written and live
- ~~No automated CI/CD~~ — `ci.yml` (test + lint + build + auto-deploy) and `weekly-pull.yml` (scheduled data rollup) are live
- ~~Comparison view / recommendation engine / launch commands / submission form~~ — all built (compare/, recommend/, the 🚀 command buttons, submit/)
- ~~Charts~~ — VRAM distribution + backend donut on the homepage and matrix
- ~~Data-quality gaps~~ — the parser now handles unmarked blocks, prose attribution, cross-block inheritance, sentinel cleanup, and a wipe guard; `validate.py` gates every push

## Remaining Gaps (Current)

1. **No Apple/MLX submissions** — the biggest demographic gap in the data (the MLX guide section documents this openly)
2. **Some parsed fields are incomplete** — non-standard user formatting can still lose data; the `candidates.json` review queue catches prose-only submissions for human review
3. **Custom domain** — the site deliberately stays at `madgoathaz.github.io/llm-matrix` (linked from the forum; changing it breaks bookmarks). Migrating to a custom domain is a maintainer task and needs care with the `CNAME`
4. **The forum thread's title** is still the original "Local LLM Matrix" name — fine for now (it's the thread's identity), but worth revisiting if the project outgrows it

## First Things to Do When Inheriting

1. **Read this document** (you're doing this now) and [`README.md`](README.md)
2. **Browse the live site**: <https://madgoathaz.github.io/llm-matrix/>
3. **Read the forum thread**: <https://forum.level1techs.com/t/256443>
4. **Run `make check`** — lint + data validation + the full test suite (the same gates CI enforces)
5. **Run the pipeline once** (`./pull.sh --dry-run`) to verify it works end-to-end
6. **Watch the weekly workflow** in GitHub Actions for a green run

## Philosophy & Principles

- **Community-first**: The data belongs to the people who submitted it. Credit them. Show their names. Make them feel seen.
- **Forum is the source, website is the view**: Discussion happens in the forum. The website organizes and displays. They complement each other.
- **The OP is a maintainer, not an author**: The content is community-generated. The maintainer's job is to organize, validate, and present.
- **Respect the L1Techs community**: This is their forum. We represent them. Professional, credit given, no overstepping.
- **The field moves fast**: New models, new quant formats, new backends appear weekly. The system must be easy to extend (edit schema.json, re-run pipeline).
- **Static over dynamic**: No server, no database, no API keys. Python scripts + GitHub Pages. Boring technology that just works.
