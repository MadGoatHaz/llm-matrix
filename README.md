# The Local AI Stack

A community-driven reference for running LLMs on personal hardware: **12+ pages, 8 educational guides, a recommendation engine, a comparison tool, and a launch-command generator.**

> **"What should I run, on what I have, for what I need?"**

Every data point is community-sourced — real people running real models on real hardware, reported in the [L1Techs Local LLM Matrix thread](https://forum.level1techs.com/t/256443) and organized by your GPU's VRAM tier.

**Live site:** <https://madgoathaz.github.io/llm-matrix/>

## What's included

- **The Matrix** — every submission grouped by VRAM tier, with filters, search, sorting, detail panels, and verification badges
- **Recommend** — the core tool: a 3-step "Start Here" wizard, then community setups ranked for your hardware and use case, with honest tradeoffs
- **Compare** — any 2–4 setups side by side, with directional tradeoff readings from a shareable URL
- **Launch commands** — copy-paste start commands for every backend, tailored to each submission
- **8 guides** — quantization, file formats, quantization methods, model architectures, KV cache, context extension, backends, multi-GPU
- **Community & submit** — contributor credits, plus a 30-second form that builds your ready-to-post submission block
- **Data API** — the whole dataset as stable, versioned JSON (`data.json`, `data/api/v1/`)

## The Site

A static site on GitHub Pages — no build step, no server, no client-side dependencies. Every page is **generated** by the `tools/site/` package — never hand-edit the HTML.

| Page | URL | What it shows |
|------|-----|---------------|
| Homepage | `/` | Hero, live stats, charts, community highlights, how it works |
| Matrix | `/matrix.html` | The full data table: filters, search, sorting, detail panels, launch commands |
| Compare | `/compare/` | Side-by-side 2–4 setups with a tradeoff read |
| Recommend | `/recommend/` | "What should I run?" — ranked community setups |
| Community | `/community.html` | Contributor cards — who submitted what |
| Submit | `/submit/` | The static form that builds a ready-to-post `[COMMUNITY-SUBMISSION]` block |
| Guides | `/guides/` | The 8 deep-dive guides |
| Data API | `/api/` | Documentation for the versioned JSON data contract |
| Changelog | `/changelog/` | What's new and what changed, release by release |
| About | `/about.html` | What the project is, how data is sourced, how to contribute |

## The Weekly Cycle

```bash
python tools/pull.py          # 1. Fetch all monitored threads (forum JSON)
python tools/diff.py          # 2. See what's new/changed since last time
python tools/parse.py         # 3. Normalize the main thread → data/submissions.json
python tools/parse_thread.py  # 4. Parse secondary threads → benchmarks / hardware / category
python -m tools.site          # 5. Regenerate all pages + data.json + versioned data API
git add . && git commit -m "Weekly rollup $(date +%Y-%m-%d)" && git push
```

…or just `./pull.sh` — one command for the whole cycle (`--dry-run` stages without committing). The pipeline is **Python 3.14, stdlib only**; the single content-layer dependency (`markdown`) is declared in [`pyproject.toml`](pyproject.toml). GitHub Pages auto-deploys from the repo root.

## The Data API

The dataset is published as a **stable, versioned JSON API** — the same files GitHub Pages serves: [`data.json`](https://madgoathaz.github.io/llm-matrix/data.json) (the canonical payload) and [`data/api/v1/`](https://madgoathaz.github.io/llm-matrix/data/api/v1/) (versioned copies + the JSON Schema). Any site can `fetch()` it — the full contract, changelog, and examples live in [`data/api/README.md`](data/api/README.md).

## Contributing

Three free paths, all covered in [`CONTRIBUTING.md`](CONTRIBUTING.md):

1. **The web form** — [`/submit/`](https://madgoathaz.github.io/llm-matrix/submit/) builds a ready-to-post block in your browser (30 seconds, no account)
2. **A GitHub issue** — the structured "📥 Submit a Setup" form
3. **The forum** — post in the [matrix thread](https://forum.level1techs.com/t/256443) using the [Post #2 submission template](forum/Post2.md)

## Project Docs

- [`VISION.md`](VISION.md) — what we're building and why
- [`HANDOVER.md`](HANDOVER.md) — current state, directory map, onboarding checklist

## Tests

```bash
python -m unittest discover -s tests -v
```

The suite in [`tests/`](tests/) validates the schema, the dataset, and the generator output using stdlib `unittest` (no test dependencies).

---

*Not an official Level1Techs project. All performance data is community-reported, not lab-benchmarked.*
