# LLM Matrix Tools

Local tooling for maintaining the [Local LLM Matrix](https://forum.level1techs.com/t/256443) forum thread and its companion website, [The Local AI Stack](https://madgoathaz.github.io/llm-matrix/).

**Python 3.14, stdlib only** — there is nothing to install to run these tools.

## Quick Start (Weekly Cycle)

```bash
# 1. Pull all monitored threads (main + 3 secondary)
python tools/pull.py

# 2. See what's new since last pull
python tools/diff.py

# 3. (Optional) Edit tools/schema.json or tools/tags.json
#    - Add new backends, quants, tiers as the field evolves
#    - Tag highlighted submissions, set confidence levels

# 4. Parse the main thread → canonical submission dataset
python tools/parse.py

# 5. Parse the secondary threads → benchmarks / hardware / category lists
python tools/parse_thread.py

# 6. Regenerate the site (all pages + data.json + the versioned data API)
python tools/generate_site.py

# 7. Deploy
git add . && git commit -m "Weekly rollup $(date +%Y-%m-%d)" && git push
#    → GitHub Pages auto-deploys from the repo root
```

## Files

| File | Purpose |
|------|---------|
| `tools/pull.py` | Fetch monitored thread JSON from the Discourse API (browser User-Agent with curl fallback) |
| `tools/diff.py` | Show new/edited/removed posts vs `data/last_seen.json`; updates the baseline |
| `tools/parse.py` | Extract + normalize main-thread submissions → `data/submissions.json` (tier normalization, template filtering, backend normalization, tag overrides) |
| `tools/parse_thread.py` | Parse secondary monitored threads → `data/benchmarks.json`, `data/hardware.json`, `data/category_threads.json` |
| `tools/generate_site.py` | Thin entry point for the site generator — delegates to the `tools/site/` package (see below) |
| `tools/site/` | **The site generator package** (P1-0): `template.py` (shared page shell — OG tags, nav, footer), `utils.py` (data loading, normalization, aggregation), `markdown.py` (the single `markdown` dep + front-matter), `guides.py` (guide renderer), `api.py` (the versioned data API writer), `pages/` (one pure renderer per page: homepage, matrix, community, guides index, about, recommend, compare, submit, api) |
| `tools/validate.py` | Data-quality gate: checks `submissions.json` against `schema.json` (required fields, enum conformance, known gaps) — runs in CI, exits non-zero on hard errors |
| `tools/generate.py` | **Legacy** — the original single-page dashboard + Post #3 viewport generator. Superseded by `generate_site.py`; kept for reference only, do not use |
| `tools/schema.json` | **You edit this.** Valid tiers, vendors, backends, quants, use cases, engine modes, monitored threads (v2.1) |
| `tools/tags.json` | **You edit this.** Manual curation: highlights, confidence overrides, forum feedback |

## Data Flow

```
Discourse API
    │
    ▼
pull.py ──► data/raw/{main,crucible,rigs,category}_latest.json
    │        (data/raw/latest.json = copy of main, backward compat)
    │
    ├──► diff.py          (shows what's new; updates data/last_seen.json)
    │
    ├──► parse.py         ──► data/submissions.json      (the main dataset)
    │
    └──► parse_thread.py  ──► data/benchmarks.json
                              data/hardware.json
                              data/category_threads.json

submissions.json + schema.json
    │
    ▼
generate_site.py (tools/site/) ──► all site pages (root + recommend/ +
                      compare/ + submit/ + api/ + guides/),
                      data.json,
                      data/api/v1/{submissions,benchmarks,hardware}.json
                      (the versioned data API — the authored
                      data/api/v1/schema.json is never overwritten)
                      (all committed at repo root → GitHub Pages)
```

## Monitored Threads

`schema.json → monitored_threads` defines what `pull.py` fetches and which parser owns each thread:

| id | Thread | Parsed by | Output |
|----|--------|-----------|--------|
| `main` | The Local LLM Matrix (submissions) | `parse.py` | `data/submissions.json` |
| `crucible` | Crucible LLM Bench | `parse_thread.py` | `data/benchmarks.json` |
| `rigs` | Show Off Your AI Rig | `parse_thread.py` | `data/hardware.json` |
| `category` | ML, LLMs & AI category | `parse_thread.py` | `data/category_threads.json` |

**To add a new thread:** add an entry to `monitored_threads` (`id`, `url`, `name`, `type`, `description`), then add a parser for it in `parse_thread.py` (or `parse.py` if it's a submissions thread). `pull.py` picks up new entries automatically.

## Extending

**When the field changes** (new engine, new quant, new hardware):

1. Add it to `tools/schema.json` (e.g., a new backend name)
2. If it needs special handling, update `parse.py`
3. Re-run the pipeline
4. Done — no frontend changes needed for new data values.

**When you want a new site feature:**

1. Add a renderer module in `tools/site/pages/` (one pure function per page) and wire it into `tools/site/__init__.py::main()`; page copy lives in `content/*.md`
2. Re-run `python tools/generate_site.py`
3. If the change intentionally alters generated output, re-baseline with `make golden` and include the golden diff in your PR
4. The generator is the single writer of HTML — never hand-edit the generated `*.html` files; content changes go through `content/` and `tools/site/`.

## Tests

```bash
python -m unittest discover -s tests -v
```

The suite in [`tests/`](../tests/) validates `schema.json` structure, `submissions.json` invariants, the data-quality gate, the versioned data API (including `data.json` conformance to `data/api/v1/schema.json` via a stdlib validator), and the generator output (all pages, golden-file regression, tag balance, no template leaks, WCAG 2.1 AA + performance budgets) using stdlib `unittest` — no test dependencies.
