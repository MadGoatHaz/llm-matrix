# The Local AI Stack

A community-driven reference that answers one question for anyone running AI on their own hardware:

**"What should I run, on what I have, for what I need?"**

Every data point is community-sourced — real people running real models on real hardware, reported in the [L1Techs Local LLM Matrix thread](https://forum.level1techs.com/t/256443) and organized by your GPU's VRAM tier.

**Live site:** <https://madgoathaz.github.io/llm-matrix/>

---

## The Site

A 5-page static site on GitHub Pages — no build step, no server, no client-side dependencies:

| Page | File | What it shows |
|------|------|---------------|
| Homepage | `index.html` | Hero, live stats, community highlights (trending models, popular backends, fastest setups), how it works, related resources |
| Matrix | `matrix.html` | The full data table: every submission grouped by VRAM tier, with search + tier/vendor/backend filters and sortable columns |
| Community | `community.html` | Contributor cards — who submitted what |
| Guides | `guides.html` | Hub for the 8 deep-dive guides (quantization, file formats, KV cache, backends, …) |
| About | `about.html` | What the project is, how data is sourced, how to contribute |

All five pages are **generated** by `tools/generate_site.py` — never hand-edit them. The generator is the single writer of HTML.

## What's Here

| Path | Contents |
|------|----------|
| `*.html`, `data.json` | The generated site (committed so GitHub Pages can serve it) |
| `css/style.css` | The design system: CSS tokens + components (authored) |
| `js/main.js` | Client behavior: nav toggle, filters, sorting (authored, zero dependencies) |
| `og-image.svg` / `og-image.png` | Open Graph image (1200×630) for forum onebox cards — the SVG is the editable source |
| `tools/` | The 5 pipeline scripts + config (`schema.json`, `tags.json`) — see [`tools/README.md`](tools/README.md) |
| `data/` | Raw thread snapshots (`raw/`) + parsed datasets (`submissions.json`, `benchmarks.json`, `hardware.json`, `category_threads.json`) |
| `forum/` | Forum post sources (Post #1 matrix, Post #2 submissions, bump, changelog) |
| `work/` | Development plans, handover docs, research notes, scratch space |
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

## Contributing Data

The easiest way to add to the matrix is the forum:

1. Post your setup in the [thread](https://forum.level1techs.com/t/256443) using the [Post #2 submission template](forum/Post2.md)
2. It gets pulled and parsed on the next weekly cycle
3. It appears on the site — with your name on it

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
