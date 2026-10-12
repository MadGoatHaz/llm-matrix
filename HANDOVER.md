# The Local AI Stack — Project Handover

> **Currency note:** this document is a point-in-time snapshot. The project
> has since completed Phases 1–4 of
> [`work/plans/PLAN.md`](work/plans/PLAN.md) (all 8 guides live, the
> recommend/compare/submit/API pages, CI + the weekly automated pull, and
> the versioned data API). For the current state, read
> [`README.md`](README.md), [`work/plans/PLAN.md`](work/plans/PLAN.md), and
> the history in [`work/DEV_LOG.md`](work/DEV_LOG.md) — not this file.

## What This Is

The Local AI Stack is a community-driven resource for running AI/LLM models on personal hardware. It originated as a forum thread on Level1Techs (a high-end hardware/tech community) and has grown into a multi-component project:

- **A forum thread** where community members submit their hardware setups, model choices, and performance data
- **A static website** (GitHub Pages) that organizes, filters, and displays all that data interactively
- **A set of Python tools** that automate the data pipeline (pull from forum → parse → generate website)
- **A collection of educational guides** (in development) covering quantization, backends, architectures, and practical local AI knowledge

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
├── data.json                   # Generated: Raw submission data for client-side use
├── guides.html                 # Generated: Guides hub (8 "Coming Soon" guide topic cards)
├── index.html                  # Generated: Homepage (hero, stats, community highlights, how it works, related links)
├── matrix.html                 # Generated: Full data table with filters (tier, vendor, backend, search)
├── og-image.png                # MISSING: 1200×630 OG image for forum onebox cards (see Known Issues #1)
├── README.md                   # Project README (older, references pre-restructure file names)
│
├── css/
│   └── style.css               # Design system: CSS custom properties/tokens, layout, cards, tables, filters, badges, hero, mobile breakpoints
│
├── js/
│   └── main.js                 # Shared interactivity: nav toggle, active-link, table sort, search+filters, reset
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
│   ├── generate.py             # (Legacy) Single-page dashboard generator; superseded by generate_site.py
│   ├── generate_site.py        # Generates the 5-page website (index, matrix, community, guides, about) + data.json
│   ├── parse.py                # Extracts [COMMUNITY-SUBMISSION] blocks from main thread → data/submissions.json
│   ├── parse_thread.py         # Parses secondary threads (crucible→benchmarks, rigs→hardware, category→threads)
│   ├── pull.py                 # Fetches all monitored threads from Discourse API → data/raw/{id}_latest.json
│   ├── schema.json             # Editable config: tiers, vendors, backends, quants, use cases, engine modes, confidence, lifecycle, monitored_threads
│   └── tags.json               # Manual curation layer: per-submission overrides + forum feedback tracking
│
├── work/
│   ├── DEV_LOG.md              # Active lease board, task states, worker history
│   ├── PLAN_dashboard.md       # Original dashboard plan (superseded by website_plan.md)
│   ├── research_prompt.md      # Single comprehensive deep-research prompt (9 topics, 231 lines) — predecessor to research_prompts.md
│   ├── research_prompts.md     # 8 individual self-contained research prompts for guide content (one per guide)
│   │
│   ├── plans/                  # (empty — for future planning docs)
│   │
│   └── scratch/
│       ├── insight_sentiment.md    # Community sentiment analysis: themes, frustrations, enthusiasm, demographics, retention mechanics
│       ├── insight_submissions.md  # Submission data analysis: hardware/backend/model/quant distribution, performance ranges, data quality
│       ├── insight_ux.md           # Dashboard UX opportunities: use cases, information density, trust signals, mobile vs desktop
│       ├── website_plan.md         # Full website architecture plan (15 pages, technical approach, design direction) — 809 lines
│       ├── *.log                   # Execution logs from pipeline runs (pull, parse, generate, diff, verify)
│       ├── *.py                    # Verification scripts (verify_site.py, verify_dashboard_fixes.py, apply_edits.py)
│       └── updated_forum_post.md.bak-v4  # Backup of an older forum post version
│
├── Backup/
│   ├── updated_forum_post.md      # Pre-restructure Post #1 (old name)
│   └── updated_post2_submissions.md  # Pre-restructure Post #2 (old name)
│
├── templates/
│   └── .gitkeep                  # Reserved for future Jinja2 templates
│
└── .gitignore
```

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
- `generate_site.py`: Works. Generates 5-page website (index, matrix, community, guides, about) + data.json. All values HTML-escaped. Template submissions filtered out.

## The Website

### Pages
| Page | File | Purpose | Status |
|------|------|---------|--------|
| Homepage | index.html | Landing, stats, community highlights, how it works, related links | ✅ Live |
| Matrix | matrix.html | Full data table with filters (tier, vendor, backend, search) | ✅ Live |
| Community | community.html | Contributor cards showing each person's submissions | ✅ Live |
| Guides | guides.html | 8 guide topic cards (content "Coming Soon") | 🟡 Structure only |
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

## The Guides (Planned Content)

8 guide topics defined in `guides.html`:

| # | Guide | Status | Content Source |
|---|-------|--------|----------------|
| 1 | Quantization Basics | 🟡 Coming Soon | work/research_prompts.md (Prompt 1) |
| 2 | File Formats | 🟡 Coming Soon | work/research_prompts.md (Prompt 2) |
| 3 | Quantization Methods | 🟡 Coming Soon | work/research_prompts.md (Prompt 3) |
| 4 | Model Architectures | 🟡 Coming Soon | work/research_prompts.md (Prompt 4) |
| 5 | KV Cache | 🟡 Coming Soon | work/research_prompts.md (Prompt 5) |
| 6 | Context Extension | 🟡 Coming Soon | work/research_prompts.md (Prompt 6) |
| 7 | Backends Deep Dive | 🟡 Coming Soon | work/research_prompts.md (Prompt 7) |
| 8 | Multi-GPU & Hybrid | 🟡 Coming Soon | work/research_prompts.md (Prompt 8) |

**To write a guide:**
1. Run the corresponding prompt from `work/research_prompts.md` with a research AI
2. Adapt the output into web-friendly format (headings, paragraphs, tables, code blocks)
3. Add the content to `tools/generate_site.py` (or create a separate template file)
4. Re-run `generate_site.py`
5. Push

## Community Insights (Research Files)

| File | Content |
|------|---------|
| work/scratch/insight_sentiment.md | Community sentiment analysis: themes, frustrations, enthusiasm, demographics, retention mechanics |
| work/scratch/insight_submissions.md | Submission data analysis: hardware/backend/model/quant distribution, performance ranges, data quality |
| work/scratch/insight_ux.md | Dashboard UX opportunities: use cases, information density, trust signals, mobile vs desktop |
| work/website_plan.md | Full website architecture plan (15 pages, technical approach, design direction) |
| work/PLAN_dashboard.md | Original dashboard plan (superseded by website_plan.md) |
| work/research_prompt.md | Single comprehensive deep-research prompt (9 topics) — predecessor to research_prompts.md |

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

## Known Issues & TODOs

### Immediate (affects users)
1. **og-image.png missing** — The OG meta tag references it but the file doesn't exist. Forum onebox card shows title+description but no thumbnail. Create a 1200×630 screenshot of the dashboard and save as `og-image.png` in repo root.
2. **Forum posts not yet updated to match website** — The "Post #1 = Hub, Post #2 = Reference" restructure was done in the files but may not be pasted into the live forum yet.
3. **Featured Link not set** — The forum topic's featured link should be set to the dashboard URL for the onebox card.

### Short-term (content)
4. **8 guide pages are empty** — Need research content (prompts ready in work/research_prompts.md)
5. **Community Data Viewport in Post #2** — The tables are placeholders; need to be populated by generate_site.py output
6. **No automated CI/CD** — The weekly cycle is manual. Could add a GitHub Actions cron job.

### Medium-term (features)
7. **Comparison view** — Select 2-4 submissions, side-by-side
8. **Recommendation engine** — "I have [hardware] + want [use case]" → ranked matches
9. **Launch command generator** — Click a submission → get the exact CLI command
10. **Submission form** — Web form that generates the [COMMUNITY-SUBMISSION] text
11. **Charts** — Speed vs VRAM scatter, context length bars
12. **Custom domain** — llm-matrix.dev or similar

### Data quality
13. **Some parsed fields are incomplete** — Non-standard user formatting causes some data loss (see parse.py known issues)
14. **No Apple submissions** — Biggest demographic gap in the data
15. **Template detection could be more robust** — Edge cases with partially-filled templates

## First Things to Do When Inheriting

1. **Read this document** (you're doing this now)
2. **Browse the live site**: https://madgoathaz.github.io/llm-matrix/
3. **Read the forum thread**: https://forum.level1techs.com/t/256443
4. **Run the pipeline once** to verify it works end-to-end
5. **Set the forum Featured Link** to the dashboard URL (topic settings → featured link)
6. **Create og-image.png** (1200×630 screenshot of the homepage)
7. **Run the research prompts** (work/research_prompts.md) to generate guide content
8. **Start writing Guide #1** (Quantization Basics) as the template for the rest
9. **Paste the updated Post #1 and Post #2** into the forum (from forum/*.md files)
10. **Post the bump** (forum/bump.md) to announce the update

## Philosophy & Principles

- **Community-first**: The data belongs to the people who submitted it. Credit them. Show their names. Make them feel seen.
- **Forum is the source, website is the view**: Discussion happens in the forum. The website organizes and displays. They complement each other.
- **The OP is a maintainer, not an author**: The content is community-generated. The maintainer's job is to organize, validate, and present.
- **Respect the L1Techs community**: This is their forum. We represent them. Professional, credit given, no overstepping.
- **The field moves fast**: New models, new quant formats, new backends appear weekly. The system must be easy to extend (edit schema.json, re-run pipeline).
- **Static over dynamic**: No server, no database, no API keys. Python scripts + GitHub Pages. Boring technology that just works.
