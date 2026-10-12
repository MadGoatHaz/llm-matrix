#!/usr/bin/env python3
"""
generate_site.py — Generate the full multi-page static site.

Usage:
    python tools/generate_site.py

Reads:
    data/submissions.json
    tools/schema.json

Writes (all at repo root):
     index.html        (homepage: hero, stats, community highlights,
                       how-it-works, related resources)
    matrix.html       (the data table: filters + sortable, tier-grouped)
    community.html    (contributor showcase)
    guides.html       (guides hub, "Coming Soon" cards)
    about.html        (about the project)
    data.json         (raw data for client-side use)

Shared assets (authored once, referenced by every page):
    css/style.css     (design system)
    js/main.js        (navigation, filters, theme)

This is the "one command to produce all pages" script. Re-run it any time
the data changes (new submissions) and every page updates. The matrix and
community pages are data-driven; guides/about are static content baked
into this generator.

Notes:
    - All values interpolated into HTML are escaped via html_escape().
    - Unfilled template submissions (empty or all-placeholder fields) are
      excluded from stats, tables, and the community page so counts match
      the rows actually displayed.
    - Cells render the FULL value and rely on CSS ellipsis + a title
      tooltip for overflow (no Python-side string slicing in the table).
"""

import html as html_module
import json
import re
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
DATA_DIR = WORKSPACE / "data"
SUBMISSIONS = DATA_DIR / "submissions.json"
SCHEMA = WORKSPACE / "tools" / "schema.json"

# Canonical URLs
SITE_URL = "https://madgoathaz.github.io/llm-matrix"
FORUM_THREAD = "https://forum.level1techs.com/t/256443"
FORUM_CATEGORY = ("https://forum.level1techs.com/"
                  "c/high-performance-computing/deep-machine-learning-ai/155")
GITHUB_REPO = "https://github.com/MadGoatHaz/llm-matrix"

# ---------------------------------------------------------------------------
# Data loading + template / placeholder detection
# ---------------------------------------------------------------------------

def load_json(path):
    with open(path) as f:
        return json.load(f)


def html_escape(s):
    if not s:
        return ""
    return html_module.escape(str(s))


# Unfilled template values look like "[e.g., ...]" — i.e. the whole value is
# wrapped in brackets.
PLACEHOLDER_RE = re.compile(r"^\[.*\]$", re.DOTALL)


def is_placeholder(value):
    """True if value is empty/None or an unfilled template placeholder."""
    if value is None:
        return True
    s = str(value).strip()
    if not s:
        return True
    return bool(PLACEHOLDER_RE.match(s))


def clean_value(value):
    """Display string for a field: '' if placeholder, else the stripped value."""
    if is_placeholder(value):
        return ""
    return str(value).strip()


def is_template_submission(s):
    """True if a submission carries no real data (unfilled/empty template)."""
    key_fields = [
        (s.get("hardware") or {}).get("description"),
        (s.get("model") or {}).get("name"),
        s.get("backend"),
        s.get("quant"),
        (s.get("performance") or {}).get("decode_tps"),
        (s.get("context") or {}).get("stable"),
        s.get("use_cases"),
    ]
    return all(is_placeholder(v) for v in key_fields)


def real_submissions(data):
    """Submissions with real data (templates filtered out)."""
    return [s for s in data.get("submissions", []) if not is_template_submission(s)]


# ---------------------------------------------------------------------------
# Field accessors + display helpers
# ---------------------------------------------------------------------------

def hw(s):
    return s.get("hardware") or {}


def model_name(s):
    return (s.get("model") or {}).get("name", "")


def perf(s):
    return s.get("performance") or {}


def ctx(s):
    return s.get("context") or {}


def short_model(name):
    """Compact model label for cards: first model only, no repo prefix."""
    if not name:
        return ""
    s = str(name).strip()
    s = s.split(",")[0].strip()
    if "/" in s and not s.lower().startswith(("http", "www")):
        s = s.split("/", 1)[1]
    s = re.sub(r"\s*\([^)]*\)\s*$", "", s).strip(" ,")
    if len(s) > 55:
        s = s[:52] + "…"
    return s


BACKEND_ALIASES = {
    "llamacpp": "llama.cpp",
    "llama-cpp": "llama.cpp",
    "llama cpp": "llama.cpp",
}


def normalize_backend(raw, schema):
    """Canonical backend name for filter attributes.

    'vLLM (magiccodingman/vllm-radiance, adaptive MTP=8)' -> 'vLLM'
    'Strata 0.1.42' -> 'Strata'
    'llamacpp' -> 'llama.cpp'
    """
    if not raw:
        return ""
    s = str(raw).strip()
    s = re.sub(r"\(.*$", "", s).strip()              # drop trailing parenthetical
    s = re.sub(r"\s+\d[\w.]*$", "", s).strip()       # drop trailing version
    if not s:
        return ""
    alias = BACKEND_ALIASES.get(s.lower())
    if alias:
        return alias
    for sb in schema.get("backends", []):
        if sb.lower() == s.lower():
            return sb
    return s


def compute_stats(subs, schema):
    vendor_set = set()
    backend_set = set()
    for s in subs:
        v = hw(s).get("vendor", "")
        if v and not is_placeholder(v):
            # Exclude "Mixed" when it comes only from empty/template entries
            if v == "Mixed" and is_placeholder(hw(s).get("description")):
                continue
            vendor_set.add(v)
        b = normalize_backend(s.get("backend", ""), schema)
        if b:
            backend_set.add(b)
    contributors = {s["source"]["username"] for s in subs}
    return {
        "submissions": len(subs),
        "contributors": len(contributors),
        "vendors": len(vendor_set),
        "backends": len(backend_set),
    }


def group_by_tier(subs, tiers):
    """Ordered [(tier_id, tier_label, [subs...])] for tiers that have rows."""
    labels = {t["id"]: t["label"] for t in tiers}
    out = []
    for t in tiers:
        tier_subs = [s for s in subs if s.get("tier") == t["id"]]
        if tier_subs:
            out.append((t["id"], labels[t["id"]], tier_subs))
    return out


def group_by_contributor(subs):
    """[(username, [subs...])] sorted by submission count desc, then name."""
    by_user = {}
    for s in subs:
        by_user.setdefault(s["source"]["username"], []).append(s)
    return sorted(by_user.items(), key=lambda kv: (-len(kv[1]), kv[0].lower()))


# Quant/format/author tokens used to reduce a raw (messy, repo-prefixed,
# comma-separated) model name down to a clean "family" label for trend
# grouping — e.g. "Swift-Qwen3.8-27B-Uncensored-FP8" -> "Qwen3.8-27B".
FAMILY_AUTHOR_PREFIX = re.compile(
    r"^(?:swift|carnice|unsloth|bartowski|deadbydawn101|d0xin|"
    r"maziyarpanahi|samuelcardillo|kwaipilot)[-_]?", re.I)
FAMILY_TAIL_TOKEN = re.compile(
    r"[-_](?:gguf|sft|fp16|fp8|bf16|nvfp4|mxfp4|iq\d[\w.]*|q\d[\w.]*|"
    r"i-nano|uncensored|w\d+a\d+|exl2[\w.]*|the-defiant[\w-]*|"
    r"heretic[\w-]*|neo-max[\w-]*|mtp[\w-]*|agentic[\w-]*|opus[\w-]*|"
    r"reasoning[\w-]*|gemini-?cli[\w-]*|dev)\b[\w.-]*$", re.I)


def model_family(name):
    """Reduce a raw model name to a clean family label (first model only)."""
    if not name:
        return ""
    s = str(name).split(",")[0].strip()
    if "/" in s and not s.lower().startswith(("http", "www")):
        s = s.split("/", 1)[1].strip()
    s = re.sub(r"\s*\([^)]*\)\s*$", "", s).strip()   # drop trailing parenthetical
    s = FAMILY_AUTHOR_PREFIX.sub("", s).strip()
    for _ in range(6):  # peel trailing quant/format tokens one at a time
        new = FAMILY_TAIL_TOKEN.sub("", s).strip(" -_")
        if new == s:
            break
        s = new
    return s


def parse_speed(value):
    """First numeric token in a decode_tps string, as float (or None)."""
    m = re.search(r"(\d+(?:\.\d+)?)", clean_value(value))
    return float(m.group(1)) if m else None


def trending_models(subs, n=3):
    """Top-n model families by submission count: [(family, count, note)]."""
    counts = {}
    best_speed = {}
    for s in subs:
        fam = model_family(model_name(s))
        if not fam:
            continue
        counts[fam] = counts.get(fam, 0) + 1
        sp = parse_speed(perf(s).get("decode_tps"))
        if sp is not None:
            best_speed[fam] = max(best_speed.get(fam, 0.0), sp)
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0].lower()))[:n]
    out = []
    for fam, c in ranked:
        sp = best_speed.get(fam)
        note = f"Up to {sp:g} t/s decode" if sp else "Community favorite"
        out.append((fam, c, note))
    return out


def popular_backends(subs, schema, n=3):
    """Top-n backends by usage: [(backend, count)]."""
    counts = {}
    for s in subs:
        b = normalize_backend(s.get("backend", ""), schema)
        if b:
            counts[b] = counts.get(b, 0) + 1
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0].lower()))[:n]


def fastest_setups(subs, n=3):
    """Top-n submissions by decode speed: [(username, model, speed, hardware)]."""
    rows = []
    for s in subs:
        sp = parse_speed(perf(s).get("decode_tps"))
        if sp is None:
            continue
        rows.append((sp, s["source"]["username"], model_name(s),
                     hw(s).get("description")))
    rows.sort(key=lambda r: -r[0])
    return [(u, m, sp, h) for sp, u, m, h in rows[:n]]


# ---------------------------------------------------------------------------
# Page shell (nav + footer + OG tags, shared by every page)
# ---------------------------------------------------------------------------

OG_TAGS = '''    <meta property="og:title" content="The Local AI Stack — Models, Hardware, Backends &amp; Community Data">
    <meta property="og:description" content="A community-driven guide to running AI models on your own hardware. Browse the matrix, explore guides, and see what the community is running.">
    <meta property="og:url" content="https://madgoathaz.github.io/llm-matrix/">
    <meta property="og:type" content="website">
    <meta property="og:image" content="https://madgoathaz.github.io/llm-matrix/og-image.png">'''

NAV = '''  <nav class="nav">
    <div class="nav-inner">
      <a href="index.html" class="nav-logo">📊 Local AI <span>Stack</span></a>
      <button class="nav-toggle" aria-label="Toggle navigation">☰</button>
      <ul class="nav-links">
        <li><a href="index.html">Home</a></li>
        <li><a href="matrix.html">Matrix</a></li>
        <li><a href="community.html">Community</a></li>
        <li><a href="guides.html">Guides</a></li>
        <li><a href="about.html">About</a></li>
      </ul>
    </div>
  </nav>'''

FOOTER = f'''  <footer class="footer">
    <div>The Local AI Stack — data from the <a href="{FORUM_THREAD}">Local LLM Matrix thread</a> on Level1Techs · <a href="{GITHUB_REPO}">GitHub</a></div>
    <div class="forum-credit">Not an official Level1Techs project. All data is community-reported — check the thread for context.</div>
  </footer>'''


def page_shell(title, description, body):
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html_escape(title)}</title>
    <meta name="description" content="{html_escape(description)}">
{OG_TAGS}
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
{NAV}
<main class="container">
{body}
</main>
{FOOTER}
<script src="js/main.js"></script>
</body>
</html>
'''


# ---------------------------------------------------------------------------
# index.html — Homepage
# ---------------------------------------------------------------------------

def render_homepage(subs, schema, stats):
    # --- Stats row ---
    stats_html = '''
  <div class="stats-row">
    <div class="stat-card"><div class="value">{submissions}</div><div class="label">Submissions</div></div>
    <div class="stat-card"><div class="value">{contributors}</div><div class="label">Contributors</div></div>
    <div class="stat-card"><div class="value">{vendors}</div><div class="label">Hardware Vendors</div></div>
    <div class="stat-card"><div class="value">{backends}</div><div class="label">Backends</div></div>
  </div>'''.format(**stats)

    # --- Community Highlights (all data-driven, from submissions.json) ---

    # Trending Models: top 3 model families by submission count.
    trend_cards = []
    for fam, count, note in trending_models(subs, n=3):
        trend_cards.append(f'''
    <div class="card">
      <h3>🔥 {html_escape(fam)}</h3>
      <p><span class="badge badge-blue">{count} submission{'s' if count != 1 else ''}</span></p>
      <p class="mono">{html_escape(note)}</p>
    </div>''')
    trend_html = (
        f'\n  <div class="card-grid">\n{chr(10).join(trend_cards)}\n  </div>'
        if trend_cards else "")

    # Popular Backends: top 3 backends by usage.
    backend_items = []
    for backend, count in popular_backends(subs, schema, n=3):
        backend_items.append(
            f'    <div class="stat-card"><div class="value">{count}</div>'
            f'<div class="label">{html_escape(backend)}</div></div>')
    backend_html = (
        f'\n  <div class="stats-row">\n{chr(10).join(backend_items)}\n  </div>'
        if backend_items else "")

    # Fastest Setups: top 3 submissions by decode speed.
    fast_cards = []
    for username, model, speed, hardware in fastest_setups(subs, n=3):
        fast_cards.append(f'''
    <div class="card">
      <h3>⚡ {speed:g} t/s</h3>
      <p>{html_escape(short_model(model))}</p>
      <p class="mono">{html_escape(clean_value(hardware))}</p>
      <p>by <strong>{html_escape(username)}</strong> · <a href="matrix.html">See in the matrix →</a></p>
    </div>''')
    fast_html = (
        f'\n  <div class="card-grid">\n{chr(10).join(fast_cards)}\n  </div>'
        if fast_cards else "")

    highlights_html = f'''
  <section>
    <h2 class="section-title">🏆 Community Highlights</h2>

    <h3 style="margin: 1rem 0 0.5rem; color: var(--text-secondary); font-size: 0.9rem; text-transform: uppercase;">Trending Models</h3>
{trend_html}

    <h3 style="margin: 1.5rem 0 0.5rem; color: var(--text-secondary); font-size: 0.9rem; text-transform: uppercase;">Popular Backends</h3>
{backend_html}

    <h3 style="margin: 1.5rem 0 0.5rem; color: var(--text-secondary); font-size: 0.9rem; text-transform: uppercase;">Fastest Setups</h3>
{fast_html}
  </section>'''

    # --- How It Works (kept as-is) ---
    how_html = '''
  <h2 class="section-title">🔄 How It Works</h2>
  <div class="card-grid">
    <div class="card">
      <h3>1. 📝 Submit</h3>
      <p>Head to the <a href="''' + FORUM_THREAD + '''">forum thread</a> and use the Quick Submit template in Post #2. 30 seconds: tier, hardware, model, speed.</p>
    </div>
    <div class="card">
      <h3>2. ⚙️ We Parse</h3>
      <p>The pipeline pulls the thread, parses every submission, and organizes it by VRAM tier, hardware vendor, backend, and model.</p>
    </div>
    <div class="card">
      <h3>3. 📊 You Browse</h3>
      <p>Filter the matrix by your hardware. See exactly what the community runs, at what speed, in what context.</p>
    </div>
  </div>'''

    # --- Related Resources (curated community links) ---
    related_html = '''
  <section>
    <h2 class="section-title">🔗 Related Resources</h2>
    <div class="card-grid">
      <a class="guide-card" href="https://forum.level1techs.com/t/crucible-llm-bench-your-llm-and-server-is-it-fast-enough-for-everyone/257531">
        <div class="guide-icon">⚗️</div>
        <h3>Crucible: LLM Bench</h3>
        <p>Benchmark your LLM server. Is it fast enough for everyone? Community-driven performance testing.</p>
        <div class="guide-meta">L1Techs Thread</div>
      </a>
      <a class="guide-card" href="https://forum.level1techs.com/t/post-show-off-your-ai-rig-whatchya-got-in-there/255709">
        <div class="guide-icon">🖥️</div>
        <h3>Show Off Your AI Rig</h3>
        <p>The community hardware showcase. What are people building? 40+ rigs and counting.</p>
        <div class="guide-meta">L1Techs Thread</div>
      </a>
      <a class="guide-card" href="https://forum.level1techs.com/c/high-performance-computing/deep-machine-learning-ai/155">
        <div class="guide-icon">🤖</div>
        <h3>ML, LLMs &amp; AI Category</h3>
        <p>The full L1Techs AI category. Benchmarks, guides, discussions, and results.</p>
        <div class="guide-meta">L1Techs Forum</div>
      </a>
      <a class="guide-card" href="https://forum.level1techs.com/t/256443">
        <div class="guide-icon">💬</div>
        <h3>This Project's Thread</h3>
        <p>The Local AI Stack — where the community submits data and discusses models.</p>
        <div class="guide-meta">L1Techs Thread</div>
      </a>
    </div>
  </section>'''

    body = f'''
  <section class="hero">
    <h1>The <span>Local AI Stack</span></h1>
    <p class="tagline">Your community-driven guide to running AI models on your own hardware</p>
    <div class="actions">
      <a href="matrix.html" class="btn-large btn-large-primary">Browse the Matrix →</a>
      <a href="guides.html" class="btn-large btn-large-secondary">Explore Guides →</a>
    </div>
  </section>

{stats_html}
{highlights_html}
{how_html}
{related_html}'''

    title = "The Local AI Stack — Community-Driven Local LLM Reference"
    desc = ("Your community-driven guide to running AI models on your own hardware. "
            "Browse the matrix, explore guides, and see what the community is running.")
    return page_shell(title, desc, body)


# ---------------------------------------------------------------------------
# matrix.html — The data table
# ---------------------------------------------------------------------------

MATRIX_COLUMNS = [
    "Contributor", "Hardware", "Vendor", "Backend", "Model", "Quant",
    "Use Case", "Speed", "Context", "KV", "Power", "Mode",
]


def td(value):
    v = html_escape(clean_value(value))
    return f'<td title="{v}">{v}</td>'


def render_matrix(subs, schema, stats):
    tiers = schema.get("tiers", [])
    labels = {t["id"]: t["label"] for t in tiers}

    # --- Filter options ---
    vendor_set = set()
    backend_set = set()
    for s in subs:
        v = hw(s).get("vendor", "")
        if v and not is_placeholder(v):
            vendor_set.add(v)
        b = normalize_backend(s.get("backend", ""), schema)
        if b:
            backend_set.add(b)

    tier_opts = "".join(
        f'<option value="{html_escape(t["id"])}">{html_escape(t["label"])}</option>'
        for t in tiers)
    vendor_opts = "".join(
        f'<option value="{html_escape(v)}">{html_escape(v)}</option>'
        for v in sorted(vendor_set))
    backend_opts = "".join(
        f'<option value="{html_escape(b)}">{html_escape(b)}</option>'
        for b in sorted(backend_set))

    # --- Table body: tier groups ---
    body_rows = []
    for tier_id, _label, tier_subs in group_by_tier(subs, tiers):
        body_rows.append(
            f'        <tr class="tier-header" data-tier="{html_escape(tier_id)}">'
            f'<td colspan="{len(MATRIX_COLUMNS)}">{html_escape(labels.get(tier_id, tier_id))}</td></tr>'
        )
        for s in tier_subs:
            highlight = ' highlighted' if s.get("highlight") else ''
            vendor = clean_value(hw(s).get("vendor"))
            backend = normalize_backend(s.get("backend", ""), schema)
            body_rows.append(f'''        <tr class="{html_escape(tier_id)}{highlight}" data-tier="{html_escape(tier_id)}" data-vendor="{html_escape(vendor)}" data-backend="{html_escape(backend)}">
          {td(s["source"]["username"])}
          {td(hw(s).get("description"))}
          {td(hw(s).get("vendor"))}
          {td(s.get("backend"))}
          {td(model_name(s))}
          {td(s.get("quant"))}
          {td(s.get("use_cases"))}
          {td(perf(s).get("decode_tps"))}
          {td(ctx(s).get("stable"))}
          {td(ctx(s).get("kv_cache"))}
          {td(perf(s).get("power_w"))}
          {td(s.get("engine_mode"))}
        </tr>''')

    header_cells = "".join(f"<th>{c}</th>" for c in MATRIX_COLUMNS)

    updated = schema.get("last_updated", "")
    body = f'''
  <div class="page-header">
    <h1>The Matrix</h1>
    <p class="subtitle">All community submissions, filterable and sortable</p>
    <p class="meta">{stats["submissions"]} submissions · {stats["contributors"]} contributors · {stats["vendors"]} vendors · {stats["backends"]} backends · updated {html_escape(updated)}</p>
  </div>

  <div class="filter-bar">
    <input type="text" id="filter-search" placeholder="Search models, hardware, backends...">
    <select class="filter-select" data-filter="tier">
      <option value="">All Tiers</option>
      {tier_opts}
    </select>
    <select class="filter-select" data-filter="vendor">
      <option value="">All Vendors</option>
      {vendor_opts}
    </select>
    <select class="filter-select" data-filter="backend">
      <option value="">All Backends</option>
      {backend_opts}
    </select>
    <button id="filter-reset" class="btn">Reset</button>
  </div>

  <div class="table-wrapper">
    <table id="data-table">
      <thead>
        <tr>{header_cells}</tr>
      </thead>
      <tbody>
{chr(10).join(body_rows)}
      </tbody>
    </table>
  </div>

  <div class="card">
    <h3>ℹ️ Reading the matrix</h3>
    <p>Click any column header to sort (within each tier). Cells show the full value on hover.
       <strong>Speed</strong> is community-reported decode throughput; <strong>Context</strong> is the
       stable context tested; <strong>KV</strong> is the KV-cache precision; <strong>Mode</strong> is how the
       engine splits weights across VRAM/RAM/SSD. All data is community-reported — treat numbers as
       user-experienced, not lab-tested. <a href="{FORUM_THREAD}">Discussion lives in the forum thread →</a></p>
  </div>'''

    title = "The Matrix — The Local AI Stack"
    desc = ("All community submissions, filterable and sortable: VRAM tier, hardware, vendor, "
            "backend, model, quant, use case, speed, context, KV cache, power, engine mode.")
    return page_shell(title, desc, body)


# ---------------------------------------------------------------------------
# community.html — Contributor showcase
# ---------------------------------------------------------------------------

def render_community(subs, schema, stats):
    cards = []
    for username, user_subs in group_by_contributor(subs):
        initial = (username[:1] or "?").upper()
        n = len(user_subs)
        role = f"{n} submission{'s' if n != 1 else ''}"

        items = []
        for s in user_subs:
            parts = [f'<strong>{html_escape(short_model(model_name(s)))}</strong>']
            hw_desc = clean_value(hw(s).get("description"))
            speed = clean_value(perf(s).get("decode_tps"))
            if hw_desc:
                parts.append(f" — {html_escape(hw_desc)}")
            if speed:
                parts.append(f" · {html_escape(speed)}")
            items.append("          <li>" + "".join(parts) + "</li>")
        setup_list = (
            '          <ul class="setup-list">\n' + "\n".join(items) + "\n          </ul>"
            if items else '          <ul class="setup-list"><li>See the matrix</li></ul>')

        cards.append(f'''
    <div class="contributor-card">
      <div class="contributor-header">
        <div class="avatar">{html_escape(initial)}</div>
        <div>
          <div class="contributor-name">{html_escape(username)}</div>
          <div class="contributor-role">{html_escape(role)}</div>
        </div>
      </div>
{setup_list}
    </div>''')

    body = f'''
  <div class="page-header">
    <h1>The Community</h1>
    <p class="subtitle">The people behind the data</p>
    <p class="meta">{stats["contributors"]} contributors · {stats["submissions"]} submissions</p>
  </div>

  <div class="card-grid">
{chr(10).join(cards)}
  </div>

  <div class="card">
    <h3>🙌 Want to be here?</h3>
    <p>Submit your setup in the <a href="{FORUM_THREAD}">forum thread</a> using the Quick Submit
       template in Post #2. It takes 30 seconds, and your data appears in the matrix on the next
       update. Every row in <a href="matrix.html">the matrix</a> started exactly this way.</p>
    <p><a href="{FORUM_THREAD}" class="btn btn-primary">Submit your setup →</a></p>
  </div>'''

    title = "Community — The Local AI Stack"
    desc = ("The people behind the data. A showcase of every contributor to the Local AI Stack "
            "and the setups they run.")
    return page_shell(title, desc, body)


# ---------------------------------------------------------------------------
# guides.html — Guides hub
# ---------------------------------------------------------------------------

GUIDES = [
    ("🔢", "Quantization Basics",
     "What are W4A16, FP8, Q4_K_M? How precision affects quality and speed."),
    ("📦", "File Formats",
     "GGUF vs safetensors vs MLX. What's inside a model file and when to use which."),
    ("⚙️", "Quantization Methods",
     "AutoRound, AWQ, GPTQ, RTN, SmoothQuant. How quants are made and their tradeoffs."),
    ("🧠", "Model Architectures",
     "Dense vs MoE. What A3B means. How 125B models run on 24GB."),
    ("💾", "KV Cache",
     "The memory eater. Why context length costs VRAM and when to quantize it."),
    ("📏", "Context Extension",
     "RoPE, YaRN, NTK. Pushing models beyond their native context window."),
    ("⚡", "Backends Deep Dive",
     "vLLM, llama.cpp, Strata, Radiance, Ollama. When to use which."),
    ("🖥️", "Multi-GPU & Hybrid",
     "Tensor parallel, layer offload, VRAM+RAM+SSD. Making big models fit."),
]


def render_guides():
    cards = []
    for icon, name, desc in GUIDES:
        cards.append(f'''
    <div class="guide-card">
      <div class="guide-icon">{icon}</div>
      <h3>{html_escape(name)}</h3>
      <p>{html_escape(desc)}</p>
      <div class="guide-meta"><span class="badge badge-amber">Coming Soon</span></div>
    </div>''')

    body = f'''
  <div class="page-header">
    <h1>Guides</h1>
    <p class="subtitle">Understand the technology behind your setup</p>
  </div>

  <div class="card-grid">
{chr(10).join(cards)}
  </div>

  <div class="card">
    <h3>🚧 Guides are being written</h3>
    <p>Check back soon. In the meantime, the <a href="{FORUM_THREAD}">forum thread</a> has the discussion.</p>
  </div>'''

    title = "Guides — The Local AI Stack"
    desc = ("Understand the technology behind your setup: quantization, file formats, KV cache, "
            "model architectures, context extension, backends, and multi-GPU.")
    return page_shell(title, desc, body)


# ---------------------------------------------------------------------------
# about.html — About the project
# ---------------------------------------------------------------------------

def render_about():
    body = f'''
  <div class="page-header">
    <h1>About The Local AI Stack</h1>
    <p class="subtitle">A community-driven resource for running AI models on your own hardware</p>
  </div>

  <div class="card">
    <h3>📖 What It Is</h3>
    <p>A community-driven resource for running AI models on your own hardware. Born from the
       Level1Techs forum, built for the broader local AI community.</p>
  </div>

  <div class="card">
    <h3>🔄 How It Works</h3>
    <p>Community members submit their setups. We parse, organize, and display the data. The more
       submissions, the better the resource.</p>
  </div>

  <div class="card">
    <h3>🤝 Connection to L1Techs</h3>
    <p>This project originated in the <a href="{FORUM_CATEGORY}">Machine Learning, LLMs &amp; AI category</a>
       on <a href="https://forum.level1techs.com">Level1Techs</a>. The forum thread is where the
       discussion happens — this site is where the reference lives.</p>
  </div>

  <div class="card">
    <h3>✍️ How to Contribute</h3>
    <p>Head to the <a href="{FORUM_THREAD}">forum thread</a> and use the submission template in
       Post #2. Quick Submit takes 30 seconds.</p>
  </div>

  <div class="card">
    <h3>👤 Credits</h3>
    <p>Built and maintained by <a href="https://forum.level1techs.com/u/MadGoat">MadGoat</a> with
       data from the L1Techs community.</p>
    <p><a href="{GITHUB_REPO}">GitHub →</a></p>
  </div>'''

    title = "About — The Local AI Stack"
    desc = ("About The Local AI Stack — a community-driven resource for running AI models on your "
            "own hardware, born from the Level1Techs forum.")
    return page_shell(title, desc, body)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # --- Load inputs ---
    if not SUBMISSIONS.exists():
        print(f"ERROR: {SUBMISSIONS} not found. Run pull.py -> parse.py first.",
              file=sys.stderr)
        sys.exit(1)
    if not SCHEMA.exists():
        print(f"ERROR: {SCHEMA} not found.", file=sys.stderr)
        sys.exit(1)

    data = load_json(SUBMISSIONS)
    schema = load_json(SCHEMA)

    # --- Shared assets must exist (authored files, not generated) ---
    for asset in ("css/style.css", "js/main.js"):
        p = WORKSPACE / asset
        if not p.exists():
            print(f"ERROR: shared asset {asset} is missing.", file=sys.stderr)
            sys.exit(1)

    subs = real_submissions(data)
    stats = compute_stats(subs, schema)

    # --- Write outputs ---
    pages = {
        "index.html": render_homepage(subs, schema, stats),
        "matrix.html": render_matrix(subs, schema, stats),
        "community.html": render_community(subs, schema, stats),
        "guides.html": render_guides(),
        "about.html": render_about(),
    }
    for name, html in pages.items():
        path = WORKSPACE / name
        path.write_text(html, encoding="utf-8")
        print(f"  wrote {name} ({len(html)} bytes)")

    data_json = WORKSPACE / "data.json"
    with open(data_json, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"  wrote data.json ({data_json.stat().st_size} bytes)")

    print(f"\nSite generated: {stats['submissions']} submissions, "
          f"{stats['contributors']} contributors, {stats['vendors']} vendors, "
          f"{stats['backends']} backends.")


if __name__ == "__main__":
    main()
