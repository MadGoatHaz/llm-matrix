# Contributing to The Local AI Stack

The Local AI Stack is a community-driven reference that answers one question
for anyone running AI on their own hardware:

> **"What should I run, on what I have, for what I need?"**

Every row in the [Matrix](https://madgoathaz.github.io/llm-matrix/matrix.html)
is a real setup someone is actually running. This repo has two kinds of
contributors: **the community** (you, with a GPU) and **builders** (you, with
a keyboard and Python 3.14). Both are welcome — here's how each works.

---

## Adding your setup (the 90% case)

Three paths, all free, all ending in the same place. Pick your favorite:

### 1. The web form — fastest (30 seconds, no account)

Open <https://madgoathaz.github.io/llm-matrix/submit/> and fill in the form.
It assembles a ready-to-post `[COMMUNITY-SUBMISSION]` block in your browser —
you can **copy it for the forum thread** or **open a pre-filled GitHub
issue**. Nothing is stored; it all happens on your machine.

### 2. A GitHub issue

Click **New issue** in this repo and pick the **"📥 Submit a Setup"** form.
The same fields as the web form, tracked right here in the repo.

### 3. The forum thread (the original source)

Post in the [L1Techs matrix thread](https://forum.level1techs.com/t/256443)
using the submission template in **Post #2**. This is where the data has
always lived — the site is the reference, the thread is the conversation.

**What happens next (all three paths):** submissions are reviewed on the
**weekly automated cycle** (Mondays), parsed into the dataset, validated, and
published — your entry appears in the Matrix and the data API, **credited to
you**. When a number looks off, the maintainer asks in-thread; a quick reply
keeps the data honest.

### What makes a good submission

- **Be specific.** "2x RX 7900 XTX 24GB, 128GB DDR5, Linux/ROCm" beats "big
  AMD card". The hardware description is the field people copy.
- **Name the model exactly as you run it** (repo/model), and link it if it's
  on HuggingFace.
- **Report the quant and precision** ("GGUF Q4_K_M", "FP8 native",
  "I-Nano ~2.5bpw") — this is the whole point of the matrix.
- **Numbers over adjectives.** "54.4 decode / 215 prefill / 19.3s cold TTFT /
  150W peak" is worth a thousand "runs great".
- **Say what it's for.** "LLM-assisted coding", "long-context RAG" — use
  cases are what the recommendation engine ranks on.
- **Include the launch flags** in the notes. The next person with your card
  will be grateful.
- **It's fine to be rough.** A quick report with GPU + model + "it works" is
  genuinely valuable — it corroborates other submissions. Full precision can
  come later in a follow-up post.
- **Honesty is the contract.** If a number is a guess, say so. If a setup
  doesn't fit, report what you tried. The `confidence` field exists for a
  reason.

---

## Running the pipeline locally

The whole thing is **Python 3.14, stdlib-only** for the data tools — there is
nothing to install to run them.

```bash
git clone https://github.com/MadGoatHaz/llm-matrix.git
cd llm-matrix

# The weekly cycle (the exact steps the automated Monday run performs):
python tools/pull.py          # 1. Fetch all monitored forum threads (JSON)
python tools/diff.py          # 2. See what's new/changed since last time
python tools/parse.py         # 3. Normalize the main thread → data/submissions.json
python tools/parse_thread.py  # 4. Parse secondary threads → benchmarks / hardware / category
python tools/validate.py      # 5. Data-quality gate (enum conformance, gaps)
python tools/generate_site.py # 6. Regenerate all pages + data.json + data/api/v1/
```

Prefer `make`? The [Makefile](Makefile) wraps the common tasks:

```bash
make build      # regenerate the site (all pages + data.json + API files)
make test       # the full unittest suite (the CI quality gate)
make lint       # byte-compile every .py + validate every JSON
make validate   # the data-quality validator
make check      # lint + validate + test — the gates CI enforces
make golden     # re-baseline tests/golden/ (only after an intentional output change!)
```

The only non-stdlib dependency is `markdown` (the single content-layer dep,
pinned in [pyproject.toml](pyproject.toml)) — needed to render the guide
pages. In a clean environment: `python -m venv .venv && .venv/bin/pip install -e .`.
The data tools (`pull`/`diff`/`parse`/`parse_thread`/`validate`) never need it.

**No network access?** `tools/pull.py --file <downloaded.json>` imports a
locally saved thread export, so the full cycle works offline.

---

## Code style

The project has strict, deliberate conventions — they're what keep a
single-maintainer project readable by anyone:

- **PEP 8** for all Python. Type hints + docstrings on every public function.
  `python -m py_compile` (and `make lint`) must stay clean.
- **The data pipeline stays stdlib-only.** `pull.py`, `diff.py`, `parse.py`,
  `parse_thread.py`, `validate.py` — no third-party imports, ever. This
  preserves the project's core strength: the weekly cycle runs anywhere
  Python 3.14 does.
- **One content dependency, used sparingly.** `markdown` (tables,
  fenced_code, sane_lists, toc) is the *only* non-stdlib dep, and it's
  imported lazily in `tools/site/markdown.py` so the core pages stay
  stdlib-only.
- **The generator is the single writer of HTML.** Never hand-edit a
  generated `*.html`. Content changes go through `content/**` +
  `tools/site/`; style changes go through `css/style.css`.
- **One design system.** All styling lives in `css/style.css` (tokens +
  named component classes). No inline styles, no per-page CSS blobs. All
  shared client behavior lives in `js/main.js` — vanilla JS, zero
  dependencies, no frameworks.
- **Escape everything.** `html.escape()` on every interpolated data value
  (XSS-safe by construction).
- **Fail loudly, report honestly.** A page that can't render is *reported*
  (a warning names the cause), never silently skipped.
- **No dead code.** Superseded files are deleted, not left to rot.
- **Boring, reliable technology.** Static files, GitHub Pages, Python. No
  build step, no server, no database — that constraint is a feature.

---

## The PR process

1. **Fork + branch.** Branch from `main`: `git checkout -b <area>/<short-description>`
   (the maintainer's own chunks use `branch/chunk-<ids>`).
2. **Make the change small.** One concern per PR. If your diff touches
   files you can't explain in a sentence, split it.
3. **Run the gates locally before pushing:**
   ```bash
   make check   # lint + validate + test — all must be green
   ```
   If you changed something the *generator* emits (a template, a page, the
   data contract), also run `make build` and review the resulting HTML diff.
4. **Golden files.** `tests/golden/` locks the generated output
   byte-for-byte. If your change *intentionally* changes a page, re-baseline
   with `make golden` and **include the golden diff in your PR** — a reviewer
   must be able to see exactly what changed and why. An *unintentional*
   golden diff is a bug; don't paper over it.
5. **Commit messages** follow the repo's style — short, scoped, factual:
   `feat(<area>): …`, `fix(<area>): …`, `docs: …`, `chore(data): …`.
6. **Open the PR** with a note on *what* changed and *why* (link the issue
   if there is one). CI runs the full suite (test + lint + build) on every
   PR; a red build can't merge.
7. **Review is human, not heroic.** The maintainer reviews every PR — the
   goal is that any contributor can pick up a chunk and ship it, so keep PRs
   reviewable in one sitting.

### What gets reviewed carefully

- Anything touching `data/submissions.json`'s shape (the contract — see
  below) or `tools/schema.json` (the curation vocabulary).
- Changes to `tools/site/template.py` (the shared shell — every page).
- Guide content (accuracy: every number must trace to a real submission or
  the research; fast-moving topics get "new/evolving" flags).

### The data contract (versioning)

The published data API is **versioned** (see
[data/api/README.md](data/api/README.md)): additive changes bump the minor
in place; breaking changes bump the major under a new `data/api/vN/` path
and freeze the old one. If your PR changes the shape of
`data/submissions.json`, say so in the PR description — the schema
(`data/api/v1/schema.json`), the validator (`tools/validate.py`), and the
tests all encode the contract and must move together.

---

## Where to talk

- **Data questions, submissions, show-and-tell:** the
  [forum thread](https://forum.level1techs.com/t/256443) — the community's
  home.
- **Repo issues (bugs, features, submissions):** [GitHub issues](https://github.com/MadGoatHaz/llm-matrix/issues)
  — the structured forms make reporting easy.
- **The project's philosophy:** [VISION.md](VISION.md) · **Current state:**
  [HANDOVER.md](HANDOVER.md)

*Not an official Level1Techs project. All performance data is
community-reported, not lab-benchmarked — and that's by design.*
