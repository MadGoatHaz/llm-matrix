# The Local LLM Matrix — Interactive Dashboard Project Plan

## 1. Vision & Goals

**One-liner:** A free, interactive web dashboard that turns the community submissions from the L1Techs "Local LLM Matrix" thread into a queryable, filterable, comparable resource — the "spec sheet browser" for local AI hardware.

**Primary Goals:**
- Answer "What should I run on [my hardware] for [my use case]?" in under 10 seconds
- Make 50+ community submissions mentally organizable (s1ugh34d's request)
- Become the canonical "go-to" reference that the forum post links to
- Zero cost to run (GitHub Pages + GitHub Actions)
- Update automatically when new data hits the thread

**Secondary Goals:**
- Generate the in-forum "Data Viewport" Post #3 from the same data pipeline
- Provide shareable deep-links (e.g., "show me all AMD setups doing coding")
- Serve as a data source for future tools (API, CLI, desktop app)
- SEO: rank for "best local LLM for [use case]" queries

**Non-Goals (v1):**
- User accounts / login
- Writing data back to the forum
- Real-time updates (build-time is fine, weekly cadence)
- Mobile app

---

## 2. Data Architecture

### 2.1 Source of Truth

The Discourse thread JSON API:
```
https://forum.level1techs.com/t/256443.json
```

This returns all posts with their `cooked` (HTML) content. We parse `[COMMUNITY-SUBMISSION]` and `[QUICK-SUBMIT]` blocks from the `cooked` field.

### 2.2 Canonical Data Schema

Every submission is normalized into this structure:

```json
{
  "id": "unique-uuid",
  "source": {
    "post_number": 28,
    "post_id": 4128376,
    "username": "digitalscream",
    "submitted_at": "2026-10-12T11:17:02Z"
  },
  "tier": "48-64GB",
  "hardware": {
    "description": "2x R9700 32GB, Threadripper 3960X, 128GB DDR4",
    "vendor": "AMD",
    "gpus": [{"model": "R9700", "vram_gb": 32, "count": 2}],
    "cpu": "Threadripper 3960X",
    "ram_gb": 128,
    "storage": null
  },
  "backend": {
    "name": "Radiance",
    "version": "1.3.0",
    "os": "Linux",
    "driver": "amdgpu"
  },
  "model": {
    "name": "Swift 1.5 Flash Next",
    "family": "Qwen3.8-Flash-Next",
    "params": "125B",
    "architecture": "MoE",
    "quant": "IQ4 weights, FP8 PLE",
    "weight_precision": "4-bit/8-bit",
    "url": "https://huggingface.co/StillDeadcode/swift1.5-qwen3.8-next-flash-fp8-iq4r-moe"
  },
  "performance": {
    "decode_tps": 200,
    "prefill_tps": 6200,
    "ttft_cold_s": null,
    "power_w": 600,
    "gpu_util_pct": null
  },
  "context": {
    "configured_tokens": 262144,
    "stable_tokens": 200000,
    "kv_cache": "FP8",
    "max_native": "256k",
    "max_yarn": "1m"
  },
  "use_cases": ["agentic coding", "general purpose"],
  "engine_mode": "VRAM+RAM",
  "notes": "Everything running in VRAM and system RAM, no disk tier",
  "user_quote": "This thing is nuts...",
  "confidence": "community-reported",
  "status": "current"
}
```

### 2.3 Parsing Strategy

**Python script** (`parser/parse_submissions.py`):
1. Fetch thread JSON via `requests`
2. For each post, extract `cooked` HTML
3. Find all `<pre><code>` blocks containing `[COMMUNITY-SUBMISSION]` or `[QUICK-SUBMIT]`
4. Parse key-value pairs with regex (handle multi-line values, lists in brackets)
5. Normalize into the canonical schema
6. Infer missing fields (e.g., vendor from GPU model name)
7. Output: `data/submissions.json`

**Edge cases to handle:**
- Inconsistent tier naming ("48-96GB" vs "48-64GB")
- Multi-model submissions (one post, 3 models)
- Missing fields (Quick Submit has only 4 fields)
- HTML entities in cooked content (`&amp;`, `&lt;`)
- Posts edited after initial submission

### 2.4 Data Enrichment

Beyond raw parsing, the pipeline adds:
- **GPU database lookup**: Map GPU model names to specs (VRAM, vendor, architecture, TDP)
- **Model database lookup**: Map model names to params, architecture, native context
- **Tier validation**: Flag submissions where stated tier doesn't match hardware VRAM
- **Deduplication**: Same user + same model + same hardware = update, not new entry
- **Confidence scoring**: 1 source = "community", 2+ sources = "verified", OP-tested = "confirmed"

---

## 3. Technical Architecture

### 3.1 Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Frontend | **Svelte 4** + **Vite** | Small bundle, reactive by default, perfect for data-heavy UIs. No React overhead. |
| Styling | **Tailwind CSS** | Rapid responsive development, dark mode built-in, consistent design |
| State | **URL params** + **localStorage** | Filters in URL = shareable. Prefs in localStorage = persistent. No Redux needed. |
| Charts | **Chart.js** | Lightweight, responsive, good for scatter/bar. No D3 learning curve. |
| Data | **Build-time JSON injection** | `submissions.json` bundled with the site. No CORS issues. Instant load. |
| Parser | **Python 3.11** + `requests` + `re` | Simple, readable, runs in GitHub Actions |
| CI/CD | **GitHub Actions** | Free for public repos. Cron + manual trigger. |
| Hosting | **GitHub Pages** | Free, CDN-backed, custom domain optional. |
| Domain | `llm-matrix.dev` (or similar) | Professional branding. GitHub Pages supports custom domains. |

### 3.2 Why NOT client-side API fetch?

Discourse's JSON API likely doesn't send `Access-Control-Allow-Origin` headers for arbitrary domains. Even if it did, hitting the API on every page load is wasteful. **Build-time injection** means:
- Zero runtime API dependency
- Instant page load (data is local)
- Works offline (PWA-ready)
- No rate limit concerns
- GitHub Pages is purely static

### 3.3 Project Structure

```
llm-matrix-dashboard/
├── .github/
│   └── workflows/
│       └── build.yml          # GitHub Actions: parse → build → deploy
├── parser/
│   ├── parse_submissions.py   # Main parsing script
│   ├── gpu_database.json      # GPU specs lookup
│   ├── model_database.json    # Model specs lookup
│   └── generate_post3.py     # Generates the in-forum Data Viewport HTML
├── data/
│   └── submissions.json       # Build output (committed for Pages)
├── src/
│   ├── main.js
│   ├── App.svelte
│   ├── components/
│   │   ├── FilterSidebar.svelte
│   │   ├── SubmissionTable.svelte
│   │   ├── SubmissionCard.svelte
│   │   ├── ComparisonView.svelte
│   │   ├── RecommendationEngine.svelte
│   │   ├── VRAMCalculator.svelte
│   │   ├── LaunchCommandGen.svelte
│   │   ├── SubmissionForm.svelte
│   │   ├── SpeedChart.svelte
│   │   ├── HardwareHeatmap.svelte
│   │   ├── TierDistribution.svelte
│   │   └── ChangeIndicator.svelte
│   ├── lib/
│   │   ├── filters.js
│   │   ├── sorters.js
│   │   ├── recommend.js
│   │   ├── commands.js
│   │   └── share.js
│   └── styles/
│       └── tailwind.css
├── public/
│   ├── favicon.ico
│   ├── robots.txt
│   └── sitemap.xml
├── index.html
├── svelte.config.js
├── tailwind.config.js
├── vite.config.js
├── package.json
└── README.md
```

### 3.4 GitHub Actions Workflow

```yaml
# .github/workflows/build.yml
name: Build & Deploy Dashboard

on:
  schedule:
    - cron: '0 12 * * 6'  # Every Saturday at noon UTC (weekly rollup)
  workflow_dispatch: {}     # Manual trigger
  # Future: webhook from Discourse (when new post in thread)

jobs:
  parse-and-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Parse submissions
        run: |
          pip install requests
          python parser/parse_submissions.py

      - name: Generate Post #3 HTML
        run: python parser/generate_post3.py

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Build frontend
        run: |
          npm ci
          npm run build

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./dist
          publish_branch: main
          path: dashboard/
```

**Output:**
- `dashboard/` branch/path: Static site (HTML+JS+CSS+JSON)
- `data/post3_viewport.html`: Ready-to-paste Discourse post content
- Notification: Discord webhook (optional) when new data is integrated

---

## 4. UI/UX Design

### 4.1 Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  🏠 The Local LLM Matrix          [Search]  [Theme]  [GitHub]     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐  ┌──────────────────────────────────────────────┐ │
│  │              │  │                                              │ │
│  │  FILTERS     │  │  MAIN CONTENT AREA                          │ │
│  │              │  │  (Table / Cards / Comparison / Chart)        │ │
│  │  ▸ Tier     │  │                                              │ │
│  │  ▸ Vendor   │  │                                              │ │
│  │  ▸ Backend  │  │                                              │ │
│  │  ▸ Use Case │  │                                              │ │
│  │  ▸ Precision│  │                                              │ │
│  │  ▸ Speed    │  │                                              │ │
│  │  ▸ Context  │  │                                              │ │
│  │              │  │                                              │ │
│  │  [Compare]  │  │                                              │ │
│  │  [Export]   │  │                                              │ │
│  └──────────────┘  └──────────────────────────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Views (User-Selectable)

| View | Description |
|------|-------------|
| **Table** (default) | Sortable, filterable data table. All columns visible. Row click → detail panel. |
| **Cards** | Grid of submission cards. Good for scanning. Each card shows key stats. |
| **Compare** | Select 2-4 submissions. Side-by-side column comparison. Highlights differences. |
| **Chart** | Scatter plot (VRAM vs Speed), bar chart (context lengths), heat map (hardware compatibility) |
| **Recommend** | "I have [GPU] + [RAM] and want to do [use case]" → ranked recommendations |

### 4.3 Filter Dimensions

- **Tier:** ≤16, 16-24, 24-32, 48-64, 96-128, 196-256+
- **Hardware Vendor:** NVIDIA, AMD, Apple, Mixed
- **Specific GPU:** (populated from data)
- **Backend:** vLLM, llama.cpp, Strata, Radiance, Ollama, LM Studio, Colibri
- **Use Case:** Coding, Creative, RAG, Translation, General, Security, Multimodal
- **Weight Precision:** W4A16, FP8, NVFP4, Q4_K_M, Q8_0, IQ3_S, BF16
- **Engine Mode:** VRAM-only, Hybrid (VRAM+RAM), Hybrid (VRAM+RAM+SSD), CPU+GPU
- **Min Decode Speed:** slider (0-500 tok/s)
- **Min Context:** slider (0-1M tokens)
- **KV Cache:** FP16, FP8, INT8, INT4
- **Data Confidence:** OP-verified, Community (2+), Community (1)

### 4.4 Key Interactions

- **Row click** → Slides out a detail panel with full submission notes, user quote, setup commands
- **Checkbox select** → Enables "Compare" button (2-4 items)
- **Column header click** → Sort asc/desc
- **URL reflects state** → `?tier=48-64&vendor=AMD&backend=Radiance&sort=decode_tps&desc=true`
- **Share button** → Copies current URL with all filters applied
- **"Copy Launch Command"** → Generates the exact CLI command for this model+backend combo
- **"Generate Submission"** → Pre-fills the forum template with this user's data format

### 4.5 Dark Mode

Default to dark (it's a tech audience). Toggle to light. Persist in localStorage. Tailwind's `dark:` classes handle this.

### 4.6 Mobile

- Filters collapse into a hamburger/drawer
- Table becomes cards on small screens
- Comparison view stacks vertically
- All touch targets ≥ 44px

---

## 5. Feature Roadmap

### Phase 1: MVP (Week 1)

**Goal:** Filterable, sortable table of all submissions. Deployed and live.

- [ ] Parser script (Python) — extracts all submissions from thread JSON
- [ ] GPU + Model databases (JSON lookup files)
- [ ] Svelte + Vite + Tailwind project scaffold
- [ ] Main table view with column sorting
- [ ] Filter sidebar (tier, vendor, backend, use case)
- [ ] Dark/light theme toggle
- [ ] Mobile responsive
- [ ] GitHub Actions workflow (weekly cron + manual)
- [ ] Deploy to GitHub Pages
- [ ] Link from forum Post #1

**Deliverable:** Working dashboard at `llm-matrix-dashboard.github.io` with all current data, filterable and sortable.

### Phase 2: Power Features (Week 2)

**Goal:** Make it a decision tool, not just a data browser.

- [ ] **Comparison View** — Select 2-4 submissions, side-by-side with diff highlighting
- [ ] **Recommendation Engine** — "I have [hardware] + want [use case]" → ranked matches with explanation
- [ ] **Launch Command Generator** — Click any submission → get the exact `vllm serve` / `llama-server` / `strata` command
- [ ] **Submission Form** — Web form that generates the `[COMMUNITY-SUBMISSION]` text block for easy copy-paste to the forum
- [ ] **Chart View** — Scatter (VRAM vs speed), Bar (context by model), Heatmap (hardware × use case)
- [ ] **Shareable URLs** — Deep links with all filter state encoded
- [ ] **Export** — CSV / JSON download of current filtered view
- [ ] **Post #3 Generator** — Same data → static HTML for the in-forum Data Viewport post

**Deliverable:** Full decision-making tool. User can go from "I have a 4090 and want to code" to "here's your exact launch command" in 3 clicks.

### Phase 3: Polish & Growth (Month 1)

**Goal:** Make it the definitive resource. SEO, engagement, data richness.

- [ ] **Change Detection** — "New since your last visit" badge (localStorage timestamp)
- [ ] **SEO Pages** — Static pages: "Best Local LLM for Coding", "Best 16GB GPU for AI", etc. Auto-generated from data.
- [ ] **Custom Domain** — `llm-matrix.dev` or similar
- [ ] **PWA** — Installable, works offline (data is already local)
- [ ] **Contributor Leaderboard** — Who's submitted the most data
- [ ] **Data Quality Flags** — Visual indicators for unverified, inconsistent, or outdated entries
- [ ] **Timeline View** — When models entered the matrix, showing evolution
- [ ] **API Endpoint** — `GET /api/submissions?tier=48-64&vendor=AMD` for other tools
- [ ] **Discord Webhook** — Notify when new data is parsed and deployed
- [ ] **Sitemap + Robots.txt** — For Google indexing

**Deliverable:** SEO-discoverable, PWA-installable, API-accessible dashboard that ranks for "best local LLM" queries.

### Phase 4: Community & Ecosystem (Ongoing)

- [ ] **User Notes** (if we add a backend): "This setup works for me" confirmations
- [ ] **Cost Calculator**: $/month estimate based on power draw × local electricity rate
- [ ] **Noise Estimation**: RGB scale for expected fan noise (community-reported)
- [ ] **Integration with other tools**: Home Assistant card, macOS menu bar app
- [ ] **Weekly Digest**: Auto-generated summary of new submissions, posted to Discord/forum
- [ ] **Model Lifecycle Tracking**: Visual indication when a model gets superseded

---

## 6. The In-Forum "Data Viewport" (Post #3)

Generated by the SAME parsing pipeline. Static HTML, no JS. Serves as the "low-tech" fallback for users who don't want to leave the forum.

**Structure:**
```
📊 Community Data Viewport
Last updated: [date] | [N] submissions | [N] unique GPUs | [N] backends

<details> 📊 All Submissions (Table) </details>
<details> 🎯 By Use Case </details>
<details> 🖥️ By Hardware Vendor </details>
<details> ⚙️ By Backend </details>
<details> 📈 By Speed </details>
<details> 🔀 Hybrid / Offload Setups </details>
<details> 📋 Raw (Chronological) </details>

🌐 Full Interactive Dashboard → [link]
```

**Maintenance:** OP runs `python parser/generate_post3.py` weekly (or the GitHub Action outputs it), copies the HTML into Post #3.

---

## 7. Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Discourse API changes/breaks | Parser fails | Pin API version, add error handling, alert on parse failure |
| Thread deleted/moved | Data source gone | Cache last successful parse. Mirror data in repo. |
| Too many submissions (100+) | Table performance | Virtualized rendering (svelte-virtual-list). Paginate. |
| GitHub Actions rate limit | Build fails | Weekly cadence is well within limits. Manual trigger as backup. |
| CORS (if we ever go client-side) | Can't fetch data | We're build-time. Not an issue. |
| Custom domain DNS | Setup friction | GitHub Pages works fine on `username.github.io` initially. Domain is optional. |
| Data quality (bad submissions) | Misleading info | Confidence flags. "Unverified" badge. OP curation in weekly rollup. |

---

## 8. Success Metrics

- **Time to answer:** User goes from landing page to "here's my model + command" in <30 seconds
- **Weekly unique visitors:** Track via GitHub Pages analytics (or Plausible.io)
- **Forum engagement:** Does the dashboard link drive more submissions to the thread?
- **SEO:** Rankings for "best local LLM [use case]" within 3 months
- **Data completeness:** % of submissions with all key fields filled

---

## 9. Immediate Next Steps

1. **Today:** Create GitHub repo `llm-matrix-dashboard`. Scaffold Svelte + Vite + Tailwind.
2. **This week:** Write the Python parser. Run it against the live thread JSON. Validate output.
3. **This week:** Build the MVP table view with filters. Deploy to GitHub Pages.
4. **Next week:** Add comparison, recommendation, launch command features.
5. **Ongoing:** Weekly cron updates. New features per roadmap.

---

## 10. What We're NOT Doing (and Why)

- **No backend server.** GitHub Pages is static. If we need user-generated data (notes, upvotes), we'd add a Firebase/Supabase layer later. Not v1.
- **No real-time updates.** Weekly is fine. The forum thread IS the real-time source. The dashboard is the curated view.
- **No AI-powered recommendations.** The recommendation engine is rule-based (hardware match + use case match + speed ranking). Adding an LLM to recommend models would be ironic and over-engineered.
- **No mobile app.** PWA covers this. Native app is scope creep.
