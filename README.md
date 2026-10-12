# The Local AI Stack

A community-driven reference that answers one question for anyone running AI on their own hardware:

**"What should I run, on what I have, for what I need?"**

Every data point is community-sourced — real people running real models on real hardware, reported in the [L1Techs Local LLM Matrix thread](https://forum.level1techs.com/t/256443) and organized by your GPU's VRAM tier.

**Live site:** <https://madgoathaz.github.io/llm-matrix/>

---

## The Site

A static site on GitHub Pages — no build step, no server, no client-side dependencies:

| Page | URL | What it shows |
|------|-----|---------------|
| Homepage | `/` | Hero, live stats, charts, community highlights (trending models, popular backends, fastest setups), how it works, related resources |
| Matrix | `/matrix.html` | The full data table: every submission grouped by VRAM tier, with multi-select filters, search, sorting, removable filter chips, row detail panels, and launch commands |
| Compare | `/compare/` | Side-by-side 2–4 setups with differences highlighted, from a shareable URL |
| Recommend | `/recommend/` | The core tool: "what should I run, on what I have, for what I need?" — ranked community setups with honest tradeoffs |
| Community | `/community.html` | Contributor cards — who submitted what |
| Submit | `/submit/` | The static submission form — builds a ready-to-post `[COMMUNITY-SUBMISSION]` block in your browser |
| Guides | `/guides/` | The 8 deep-dive guides (quantization, file formats, model architectures, KV cache, context, backends, multi-GPU) |
| Data API | `/api/` | Documentation for the versioned JSON data contract |
| About | `/about.html` | What the project is, how data is sourced, how to contribute |

Every page is **generated** by `tools/generate_site.py` (the `tools/site/` package) — never hand-edit them. The generator is the single writer of HTML.

## What's Here

| Path | Contents |
|------|----------|
| `*.html`, `data.json` | The generated site (committed so GitHub Pages can serve it) |
| `CNAME` | The custom domain (`localaistack.com` — placeholder until purchased; see [`work/docs/custom-domain.md`](work/docs/custom-domain.md)) |
| `CONTRIBUTING.md` | The contribution guide: submitting data, running the pipeline, code style, PR process |
| `css/style.css` | The design system: CSS tokens + components (authored) |
| `js/` | Client behavior: `main.js` (nav, filters, sorting, detail panel), `recommend.js`, `compare.js`, `commands.js`, `submit.js` — all vanilla, zero dependencies |
| `og-image.svg` / `og-image.png` | Open Graph image (1200×630) for forum onebox cards — the SVG is the editable source |
| `tools/` | The pipeline scripts + the `tools/site/` generator package + config (`schema.json`, `tags.json`) — see [`tools/README.md`](tools/README.md) |
| `data/` | Raw thread snapshots (`raw/`) + parsed datasets (`submissions.json`, `benchmarks.json`, `hardware.json`, `category_threads.json`) + the versioned **data API** (`data/api/`) |
| `content/` | Authored page copy (markdown): the 8 guides, recommend, submit, api |
| `.github/` | CI/CD workflows (`ci.yml`, `weekly-pull.yml`) + structured issue templates (submission, bug, feature) |
| `forum/` | Forum post sources (Post #1 matrix, Post #2 submissions, bump, changelog) |
| `work/` | Development plans, handover docs, research notes, docs, scratch space |
| `templates/` | Reserved for future use |

## The Weekly Cycle

```bash
python tools/pull.py          # 1. Fetch all monitored threads (forum JSON)
python tools/diff.py          # 2. See what's new/changed since last time
#        review; edit tools/schema.json or tools/tags.json if the field moved
python tools/parse.py         # 3. Normalize the main thread → data/submissions.json
python tools/parse_thread.py  # 4. Parse secondary threads → benchmarks / hardware / category
python tools/generate_site.py # 5. Regenerate all 5 pages + data.json
git add . && git commit -m "Weekly rollup $(date +%Y-%m-%d)" && git push
                              # 6. GitHub Pages auto-deploys from the repo root
```

The pipeline is **Python 3.14, stdlib only** — there is nothing to install to run the data tools. The project manifest (with the single content-layer dependency, `markdown`) is declared in [`pyproject.toml`](pyproject.toml).

## The Data API

The dataset behind the site is published as a **stable, versioned JSON API** — the same files GitHub Pages serves:

| Path | What it is |
|------|------------|
| [`/api/`](https://madgoathaz.github.io/llm-matrix/api/) | The human-readable API documentation page |
| `data.json` | The canonical submissions dataset (carries the `version` field) |
| `data/api/v1/submissions.json` | The same payload at its versioned path |
| `data/api/v1/schema.json` | The **JSON Schema** (draft 2020-12) formally defining the shape |
| `data/api/v1/benchmarks.json`, `data/api/v1/hardware.json` | The secondary community datasets |

GitHub Pages serves every file with `Access-Control-Allow-Origin: *`, so any site can `fetch()` the data directly. Versioning: additive changes bump the minor in place; breaking changes bump the major under a new `vN/` path. The full contract, changelog, and examples live in [`data/api/README.md`](data/api/README.md).

## Custom Domain

The site runs on GitHub Pages at [`madgoathaz.github.io/llm-matrix`](https://madgoathaz.github.io/llm-matrix/). A `CNAME` file at the repo root carries the (placeholder) custom domain `localaistack.com` — purchasing the domain and pointing DNS at GitHub Pages is a maintainer task, fully documented step-by-step in [`work/docs/custom-domain.md`](work/docs/custom-domain.md).

## Contributing

Three free paths, all covered in [`CONTRIBUTING.md`](CONTRIBUTING.md):

1. **The web form** — [`/submit/`](https://madgoathaz.github.io/llm-matrix/submit/) builds a ready-to-post block in your browser (30 seconds, no account)
2. **A GitHub issue** — the structured "📥 Submit a Setup" form
3. **The forum** — post in the [matrix thread](https://forum.level1techs.com/t/256443) using the [Post #2 submission template](forum/Post2.md)

All three are reviewed on the weekly cycle and appear on the site — with your name on it. Builders: the same guide covers running the pipeline locally, code style, and the PR process.

## Project Docs

- [`VISION.md`](VISION.md) — what we're building and why
- [`HANDOVER.md`](HANDOVER.md) — current state, directory map, known issues, onboarding checklist
- [`work/plans/PLAN.md`](work/plans/PLAN.md) — the development plan: phased chunks covering the 8 guides, decision tools (recommend/compare/launch commands), and automation (CI, tests, weekly pull)

## Tests

```bash
python -m unittest discover -s tests -v
```

The suite in [`tests/`](tests/) validates the schema, the submission dataset, and the generator output using stdlib `unittest` (no test dependencies).

---

*Not an official Level1Techs project. All performance data is community-reported, not lab-benchmarked.*
