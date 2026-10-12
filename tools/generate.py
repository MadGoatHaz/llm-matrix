#!/usr/bin/env python3
"""
generate.py — Generate dashboard HTML and forum Post #3 viewport.

Usage:
    python tools/generate.py

Reads:
    data/submissions.json
    tools/schema.json

Writes:
    index.html               (GitHub Pages dashboard, at repo root)
    data.json                (raw data for client-side JS, at repo root)
    forum/post3_viewport.md  (in-forum data viewport post)

This is the "one command to produce all outputs" script.

Notes:
    - All values interpolated into HTML are escaped via html_escape().
    - Unfilled template submissions (empty or all-placeholder fields) are
      excluded from stats, table rows, and the Post #3 viewport so counts
      match the data rows actually displayed.
    - The dashboard table shows 12 columns; Use Case / KV / Power / Mode are
      hidden on narrow viewports via CSS (.hide-mobile).
    - Cells render the FULL value and rely on CSS ellipsis + a title tooltip
      for overflow (no Python-side string slicing in the dashboard).
"""

import html as html_module
import json
import re
import sys
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent
DATA_DIR = WORKSPACE / "data"
SUBMISSIONS = DATA_DIR / "submissions.json"
SCHEMA = WORKSPACE / "tools" / "schema.json"
DASHBOARD_DIR = WORKSPACE
FORUM_DIR = WORKSPACE / "forum"

# Canonical live dashboard URL (GitHub Pages)
DASHBOARD_URL = "https://madgoathaz.github.io/llm-matrix"

def load_json(path):
    with open(path) as f:
        return json.load(f)

def html_escape(s):
    if not s:
        return ""
    return html_module.escape(str(s))

# ---------------------------------------------------------------------------
# Template / placeholder detection
# ---------------------------------------------------------------------------

# Unfilled template values look like "[e.g., ...]" or "[Full model repository
# or exact filename]" — i.e. the whole value is wrapped in brackets.
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
        s.get("hardware", {}).get("description"),
        s.get("model", {}).get("name"),
        s.get("backend"),
        s.get("quant"),
        s.get("performance", {}).get("decode_tps"),
        s.get("context", {}).get("stable"),
        s.get("use_cases"),
    ]
    return all(is_placeholder(v) for v in key_fields)

def real_submissions(data):
    """Submissions with real data (templates filtered out)."""
    return [s for s in data["submissions"] if not is_template_submission(s)]

# ---------------------------------------------------------------------------
# Dashboard (index.html + data.json)
# ---------------------------------------------------------------------------

def generate_dashboard(data, schema):
    """Generate the static dashboard HTML."""
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)

    # Write data.json for client-side use
    with open(DASHBOARD_DIR / "data.json", 'w') as f:
        json.dump(data, f)

    tiers = schema.get("tiers", [])
    tier_labels = {t["id"]: t["label"] for t in tiers}

    # Only real submissions (templates excluded) feed stats + rows.
    subs = real_submissions(data)
    # Rows actually displayed in the table: grouped by tier, so tiered only.
    displayed = [s for s in subs if s.get("tier")]

    # --- Stats (must match displayed rows) ---
    vendor_set = set()
    for s in displayed:
        v = s["hardware"].get("vendor", "")
        if not v:
            continue
        # Exclude "Mixed" when it comes only from empty/template entries
        if v == "Mixed" and is_placeholder(s["hardware"].get("description")):
            continue
        vendor_set.add(v)

    backend_set = set()
    for s in displayed:
        b = s.get("backend", "")
        if b and not is_placeholder(b):
            backend_set.add(b)

    tier_set = set(s["tier"] for s in displayed if s.get("tier"))

    # --- Table rows grouped by tier (12 columns) ---
    # Columns: Contributor | Hardware | Vendor | Backend | Model | Quant |
    #          Use Case | Speed | Context | KV | Power | Mode
    def td(value, hide=False):
        v = html_escape(clean_value(value))
        cls = ' class="hide-mobile"' if hide else ''
        return f'<td{cls} title="{v}">{v}</td>'

    html_rows = ""
    for tier_id in [t["id"] for t in tiers]:
        tier_subs = [s for s in displayed if s.get("tier") == tier_id]
        if not tier_subs:
            continue
        html_rows += (
            f'\n      <tr class="tier-header" data-tier="{html_escape(tier_id)}">'
            f'<td colspan="12">{html_escape(tier_labels.get(tier_id, tier_id))}</td></tr>\n'
        )
        for s in tier_subs:
            highlight = ' class="highlighted"' if s.get("highlight") else ''
            html_rows += f'''
      <tr{highlight} data-tier="{html_escape(tier_id)}">
        {td(s["source"]["username"])}
        {td(s["hardware"]["description"])}
        {td(s["hardware"]["vendor"])}
        {td(s["backend"])}
        {td(s["model"]["name"])}
        {td(s["quant"])}
        {td(s.get("use_cases"), hide=True)}
        {td(s["performance"]["decode_tps"])}
        {td(s["context"]["stable"])}
        {td(s["context"]["kv_cache"], hide=True)}
        {td(s["performance"]["power_w"], hide=True)}
        {td(s.get("engine_mode"), hide=True)}
      </tr>'''

    # Raw f-string: the embedded JS contains a `\d` regex escape that must
    # reach the browser verbatim (avoids Python SyntaxWarning).
    html = rf'''<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Local LLM Matrix — Dashboard</title>
    <meta name="description" content="Interactive dashboard of community-submitted local LLM setups, organized by VRAM tier, hardware, backend, and use case.">
    <style>
        :root {{
            --bg: #0f1117;
            --surface: #1a1d2e;
            --border: #2a2d3e;
            --text: #e2e8f0;
            --text-muted: #94a3b8;
            --accent: #3b82f6;
            --highlight: #f59e0b;
            --green: #10b981;
            --red: #ef4444;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            padding: 2rem;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        header {{
            text-align: center;
            margin-bottom: 2rem;
            padding-bottom: 1.5rem;
            border-bottom: 1px solid var(--border);
        }}
        header h1 {{ font-size: 1.8rem; margin-bottom: 0.5rem; }}
        header p {{ color: var(--text-muted); font-size: 0.9rem; }}
        .branding {{ text-align: center; margin-bottom: 1rem; }}
        .tagline {{ color: var(--text-muted); font-size: 1rem; margin-top: 0.25rem; }}
        .forum-credit {{
            color: var(--text-muted);
            font-size: 0.85rem;
            margin-top: 0.75rem;
            padding-top: 0.75rem;
            border-top: 1px solid var(--border);
        }}
        .forum-link {{
            color: var(--accent);
            text-decoration: none;
            border-bottom: 1px dotted var(--accent);
        }}
        .forum-link:hover {{ border-bottom-style: solid; }}
        .stats {{
            display: flex;
            gap: 1.5rem;
            justify-content: center;
            margin: 1rem 0;
            flex-wrap: wrap;
        }}
        .stat {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 0.75rem 1.25rem;
            text-align: center;
        }}
        .stat .num {{ font-size: 1.5rem; font-weight: 700; color: var(--accent); }}
        .stat .label {{ font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; }}
        .filters {{
            display: flex;
            gap: 0.75rem;
            margin-bottom: 1.5rem;
            flex-wrap: wrap;
        }}
        .filters select, .filters input {{
            background: var(--surface);
            border: 1px solid var(--border);
            color: var(--text);
            padding: 0.5rem 1rem;
            border-radius: 6px;
            font-size: 0.85rem;
        }}
        .filters input {{ flex: 1; min-width: 200px; }}
        .btn-reset {{
            background: var(--surface);
            border: 1px solid var(--border);
            color: var(--text-muted);
            padding: 0.5rem 1rem;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.85rem;
        }}
        .btn-reset:hover {{ color: var(--text); border-color: var(--accent); }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85rem;
        }}
        th {{
            text-align: left;
            padding: 0.75rem;
            border-bottom: 2px solid var(--border);
            color: var(--text-muted);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.75rem;
            cursor: pointer;
        }}
        th:hover {{ color: var(--accent); }}
        th.sort-asc::after {{ content: ' ↑'; color: var(--accent); }}
        th.sort-desc::after {{ content: ' ↓'; color: var(--accent); }}
        td {{
            padding: 0.6rem 0.75rem;
            border-bottom: 1px solid var(--border);
            max-width: 200px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        td[title]:hover {{
            white-space: normal;
            overflow: visible;
            position: relative;
            z-index: 10;
            background: var(--surface);
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }}
        td:first-child {{ font-weight: 600; color: var(--text); }}
        tr.tier-header td {{
            background: var(--surface);
            font-weight: 700;
            color: var(--accent);
            padding: 0.5rem 0.75rem;
            font-size: 0.8rem;
            max-width: none;
            overflow: visible;
            white-space: normal;
        }}
        tr.highlighted {{ border-left: 3px solid var(--highlight); }}
        tr:hover {{ background: rgba(59, 130, 246, 0.05); }}
        .how-it-works {{
            max-width: 800px;
            margin: 0 auto 1.5rem;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 0;
        }}
        .how-it-works summary {{
            padding: 0.75rem 1rem;
            cursor: pointer;
            font-weight: 600;
            color: var(--text-muted);
        }}
        .how-it-works[open] summary {{
            border-bottom: 1px solid var(--border);
        }}
        .how-content {{
            padding: 1rem;
            font-size: 0.9rem;
            line-height: 1.7;
        }}
        .how-content a {{ color: var(--accent); }}
        .how-content p {{ margin-bottom: 0.5rem; }}
        .footer {{
            margin-top: 3rem;
            padding-top: 1.5rem;
            border-top: 1px solid var(--border);
            text-align: center;
            color: var(--text-muted);
            font-size: 0.8rem;
        }}
        .footer a {{ color: var(--accent); text-decoration: none; }}
        .footer-main {{ margin-bottom: 1rem; font-size: 0.85rem; }}
        .footer-cta {{ margin-bottom: 1rem; }}
        .btn-forum {{
            display: inline-block;
            background: var(--accent);
            color: white;
            padding: 0.6rem 1.5rem;
            border-radius: 6px;
            text-decoration: none;
            font-weight: 600;
            font-size: 0.9rem;
            transition: opacity 0.2s;
        }}
        .btn-forum:hover {{ opacity: 0.85; }}
        .footer-meta {{ font-size: 0.75rem; opacity: 0.7; }}
        .footer-meta a {{ color: var(--text-muted); }}
        @media (max-width: 768px) {{
            body {{ padding: 1rem; }}
            .filters {{ flex-direction: column; }}
            table {{ font-size: 0.75rem; }}
            td, th {{ padding: 0.4rem; }}
            .hide-mobile {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="branding">
                <h1>📊 The Local LLM Matrix</h1>
                <p class="tagline">A community-driven reference for running local AI models on real silicon</p>
                <p class="forum-credit">
                    From the <a href="https://forum.level1techs.com/t/256443" class="forum-link">Machine Learning, LLMs &amp; AI</a> community at
                    <a href="https://forum.level1techs.com" class="forum-link"><strong>Level1Techs</strong></a>
                </p>
            </div>
            <div class="stats">
                <div class="stat"><div class="num">{len(displayed)}</div><div class="label">Submissions</div></div>
                <div class="stat"><div class="num">{len(vendor_set)}</div><div class="label">Vendors</div></div>
                <div class="stat"><div class="num">{len(backend_set)}</div><div class="label">Backends</div></div>
                <div class="stat"><div class="num">{len(tier_set)}</div><div class="label">Tiers</div></div>
            </div>
        </header>

        <details class="how-it-works">
        <summary>ℹ️ How This Dashboard Works</summary>
        <div class="how-content">
            <p>This is a <strong>read-only view</strong> of community submissions from the
            <a href="https://forum.level1techs.com/t/256443">Local LLM Matrix thread on Level1Techs</a>.</p>
            <p><strong>How to contribute:</strong> Head to the
            <a href="https://forum.level1techs.com/t/256443/2">forum thread</a> and use the submission template in Post #2.
            Your data will appear here within the next weekly update.</p>
            <p><strong>Data is community-reported.</strong> We don't independently verify benchmarks.
            Treat numbers as user-experienced, not lab-tested. Hardware, drivers, and setup all affect results.</p>
            <p><strong>Respect the contributors.</strong> The data here is people sharing their time and experience.
            Link back to the forum, credit usernames, and keep the discussion constructive.</p>
        </div>
        </details>

        <div class="filters">
            <input type="text" id="search" placeholder="Search models, hardware, notes...">
            <select id="filter-tier">
                <option value="">All Tiers</option>
                {''.join(f'<option value="{html_escape(t["id"])}">{html_escape(t["label"])}</option>' for t in tiers)}
            </select>
            <select id="filter-vendor">
                <option value="">All Vendors</option>
                {''.join(f'<option value="{html_escape(v)}">{html_escape(v)}</option>' for v in sorted(vendor_set))}
            </select>
            <select id="filter-backend">
                <option value="">All Backends</option>
                {''.join(f'<option value="{html_escape(b)}">{html_escape(b)}</option>' for b in sorted(backend_set))}
            </select>
            <button onclick="resetFilters()" class="btn-reset">Reset</button>
        </div>

        <table id="main-table">
            <thead>
                <tr>
                    <th onclick="sortTable(0)">Contributor</th>
                    <th onclick="sortTable(1)">Hardware</th>
                    <th onclick="sortTable(2)">Vendor</th>
                    <th onclick="sortTable(3)">Backend</th>
                    <th onclick="sortTable(4)">Model</th>
                    <th onclick="sortTable(5)">Quant</th>
                    <th class="hide-mobile" onclick="sortTable(6)">Use Case</th>
                    <th onclick="sortTable(7)">Speed</th>
                    <th onclick="sortTable(8)">Context</th>
                    <th class="hide-mobile" onclick="sortTable(9)">KV</th>
                    <th class="hide-mobile" onclick="sortTable(10)">Power</th>
                    <th class="hide-mobile" onclick="sortTable(11)">Mode</th>
                </tr>
            </thead>
            <tbody>
                {html_rows}
            </tbody>
        </table>

        <div class="footer">
            <p class="footer-main">
                <strong>The Local LLM Matrix</strong> is a community project originating from
                <a href="https://forum.level1techs.com/t/256443">Level1Techs</a>.
                All data is community-submitted and user-reported.
            </p>
            <p class="footer-cta">
                <a href="https://forum.level1techs.com/t/256443" class="btn-forum">
                    💬 Join the Discussion / Submit Your Setup
                </a>
            </p>
            <p class="footer-meta">
                Last updated: {data["generated_at"][:10]} |
                <a href="https://forum.level1techs.com">forum.level1techs.com</a> |
                Not an official Level1Techs product — a community resource built by forum members.
            </p>
        </div>
    </div>

    <script>
        // Client-side filtering
        const search = document.getElementById('search');
        const tierFilter = document.getElementById('filter-tier');
        const vendorFilter = document.getElementById('filter-vendor');
        const backendFilter = document.getElementById('filter-backend');
        const rows = document.querySelectorAll('#main-table tbody tr');

        function applyFilters() {{
            const q = search.value.toLowerCase();
            const tier = tierFilter.value;
            const vendor = vendorFilter.value;
            const backend = backendFilter.value;

            rows.forEach(row => {{
                if (row.classList.contains('tier-header')) {{
                    // Show tier header only if it has visible children
                    row.style.display = '';
                    return;
                }}
                const text = row.textContent.toLowerCase();
                const cells = row.cells;
                let show = true;
                if (q && !text.includes(q)) show = false;
                if (tier && row.dataset.tier !== tier) show = false;
                if (vendor && cells[2] && cells[2].textContent !== vendor) show = false;
                if (backend && cells[3] && cells[3].textContent !== backend) show = false;
                row.style.display = show ? '' : 'none';
            }});

            // Hide tier headers that have no visible rows
            document.querySelectorAll('.tier-header').forEach(header => {{
                let next = header.nextElementSibling;
                let hasVisible = false;
                while (next && !next.classList.contains('tier-header')) {{
                    if (next.style.display !== 'none') hasVisible = true;
                    next = next.nextElementSibling;
                }}
                header.style.display = hasVisible ? '' : 'none';
            }});
        }}

        search.addEventListener('input', applyFilters);
        tierFilter.addEventListener('change', applyFilters);
        vendorFilter.addEventListener('change', applyFilters);
        backendFilter.addEventListener('change', applyFilters);

        // Sorting WITHIN tier groups (grouping is preserved)
        let sortState = {{}}; // col -> direction

        function sortTable(col) {{
            sortState[col] = -(sortState[col] || -1); // toggle direction, default asc

            // Get all tier groups
            const tbody = document.querySelector('#main-table tbody');
            const groups = [];
            let currentGroup = {{ header: null, rows: [] }};

            tbody.querySelectorAll('tr').forEach(row => {{
                if (row.classList.contains('tier-header')) {{
                    if (currentGroup.header || currentGroup.rows.length) {{
                        groups.push(currentGroup);
                    }}
                    currentGroup = {{ header: row, rows: [] }};
                }} else {{
                    currentGroup.rows.push(row);
                }}
            }});
            if (currentGroup.header || currentGroup.rows.length) groups.push(currentGroup);

            // Sort rows within each group
            groups.forEach(group => {{
                group.rows.sort((a, b) => {{
                    const av = a.cells[col]?.textContent || '';
                    const bv = b.cells[col]?.textContent || '';
                    // Try numeric sort
                    const an = parseFloat(av.replace(/[^\d.-]/g, ''));
                    const bn = parseFloat(bv.replace(/[^\d.-]/g, ''));
                    if (!isNaN(an) && !isNaN(bn)) return (an - bn) * sortState[col];
                    return av.localeCompare(bv, undefined, {{numeric: true}}) * sortState[col];
                }});
            }});

            // Rebuild tbody
            tbody.innerHTML = '';
            groups.forEach(group => {{
                if (group.header) tbody.appendChild(group.header);
                group.rows.forEach(r => tbody.appendChild(r));
            }});

            // Update sort indicators
            document.querySelectorAll('#main-table th').forEach((th, i) => {{
                th.classList.remove('sort-asc', 'sort-desc');
                if (sortState[i]) {{
                    th.classList.add(sortState[i] === 1 ? 'sort-asc' : 'sort-desc');
                }}
            }});
        }}

        function resetFilters() {{
            search.value = '';
            tierFilter.value = '';
            vendorFilter.value = '';
            backendFilter.value = '';
            applyFilters();
            // Reset sort
            sortState = {{}};
            location.reload(); // simplest reset
        }}
    </script>
</body>
</html>'''

    with open(DASHBOARD_DIR / "index.html", 'w') as f:
        f.write(html)

    print(f"✓ Dashboard: {DASHBOARD_DIR / 'index.html'}")
    print(f"✓ Data: {DASHBOARD_DIR / 'data.json'}")
    print(f"  ({len(displayed)} real rows rendered; {len(data['submissions']) - len(subs)} template(s) excluded)")

# ---------------------------------------------------------------------------
# Forum Post #3 viewport
# ---------------------------------------------------------------------------

def generate_post3(data, schema):
    """Generate the in-forum Data Viewport post (Post #3)."""
    FORUM_DIR.mkdir(parents=True, exist_ok=True)

    tiers = schema.get("tiers", [])
    tier_labels = {t["id"]: t["label"] for t in tiers}

    # Only real submissions (templates excluded)
    subs = real_submissions(data)

    # Group by tier
    by_tier = {}
    for s in subs:
        t = s.get("tier") or "unclassified"
        by_tier.setdefault(t, []).append(s)

    # Group by vendor
    by_vendor = {}
    for s in subs:
        v = s["hardware"]["vendor"]
        by_vendor.setdefault(v, []).append(s)

    # Group by backend
    by_backend = {}
    for s in subs:
        b = s.get("backend", "Unknown")
        by_backend.setdefault(b, []).append(s)

    def cell(value, limit):
        """Escape a cleaned value for forum raw HTML, bounded for narrow md-tables."""
        return html_escape(clean_value(value)[:limit])

    def make_table(subs, show_vendor=False):
        rows = ""
        for s in subs:
            h = ' style="border-left:3px solid #f59e0b"' if s.get("highlight") else ""
            rows += f"""<tr{h}>
<td>{html_escape(s['source']['username'])}</td>
<td>{cell(s['hardware']['description'], 50)}</td>
{'<td>' + html_escape(s['hardware']['vendor']) + '</td>' if show_vendor else ''}
<td>{cell(s['backend'], 30)}</td>
<td>{cell(s['model']['name'], 35)}</td>
<td>{cell(s['quant'], 25)}</td>
<td>{cell(s['performance']['decode_tps'], 15)}</td>
<td>{cell(s['context']['stable'], 15)}</td>
</tr>\n"""
        vendor_col = "<th>Vendor</th>" if show_vendor else ""
        return f"""<div class="md-table">
<table>
<thead><tr><th>User</th><th>Hardware</th>{vendor_col}<th>Backend</th><th>Model</th><th>Quant</th><th>Speed</th><th>Context</th></tr></thead>
<tbody>
{rows}</tbody>
</table>
</div>"""

    content = f"""# 📊 Community Data Viewport

*A community index of all submissions from the **Local LLM Matrix** thread. Last updated: {data['generated_at'][:10]} | {len(subs)} submissions*

> 🌐 **Interactive Dashboard:** [Browse, filter, and compare all setups]({DASHBOARD_URL})
> 
> 💬 **The full discussion lives here on the forum.** Submit your own setup using the template in Post #2.

---

<details>
<summary>📊 View by Tier</summary>

"""
    for tier in tiers:
        tid = tier["id"]
        tier_subs = by_tier.get(tid, [])
        if tier_subs:
            content += f"""<details>
<summary>{html_escape(tier['label'])} ({len(tier_subs)} entries)</summary>
{make_table(tier_subs)}
</details>
"""
    content += "</details>\n"

    content += f"""
<details>
<summary>🖥️ View by Hardware Vendor</summary>

"""
    for vendor in sorted(by_vendor.keys()):
        v_subs = by_vendor[vendor]
        content += f"""<details>
<summary>{html_escape(vendor)} ({len(v_subs)} entries)</summary>
{make_table(v_subs)}
</details>
"""
    content += "</details>\n"

    content += f"""
<details>
<summary>⚙️ View by Backend</summary>

"""
    for backend in sorted(by_backend.keys()):
        b_subs = by_backend[backend]
        content += f"""<details>
<summary>{html_escape(backend)} ({len(b_subs)} entries)</summary>
{make_table(b_subs)}
</details>
"""
    content += "</details>\n"

    content += f"""
<details>
<summary>📋 All Submissions (Chronological)</summary>

{make_table(subs, show_vendor=True)}
</details>

---
*This viewport is auto-generated from thread data. The interactive dashboard provides filtering, sorting, and comparison. All data is community-reported — see the [thread](/t/256443) for full context and discussion.*
"""

    out_path = FORUM_DIR / "post3_viewport.md"
    with open(out_path, 'w') as f:
        f.write(content)
    print(f"✓ Post #3 Viewport: {out_path} ({len(content)} chars)")

def main():
    if not SUBMISSIONS.exists():
        print("No parsed data. Run `python tools/parse.py` first.")
        sys.exit(1)

    data = load_json(SUBMISSIONS)
    schema = load_json(SCHEMA)

    generate_dashboard(data, schema)
    generate_post3(data, schema)

    print(f"\n✅ All outputs generated. Ready to deploy.")
    print(f"   Dashboard → push to GitHub Pages ({DASHBOARD_URL})")
    print(f"   Post #3   → paste into forum")

if __name__ == "__main__":
    main()
