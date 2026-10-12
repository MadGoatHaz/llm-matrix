#!/usr/bin/env python3
"""
generate.py — Generate dashboard HTML and forum Post #3 viewport.

Usage:
    python tools/generate.py

Reads:
    data/submissions.json
    tools/schema.json

Writes:
    dashboard/index.html      (GitHub Pages dashboard)
    dashboard/data.json       (raw data for client-side JS)
    forum/post3_viewport.md   (in-forum data viewport post)
    forum/bump_changelog.md   (what changed this cycle)

This is the "one command to produce all outputs" script.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent
DATA_DIR = WORKSPACE / "data"
SUBMISSIONS = DATA_DIR / "submissions.json"
SCHEMA = WORKSPACE / "tools" / "schema.json"
DASHBOARD_DIR = WORKSPACE / "dashboard"
FORUM_DIR = WORKSPACE / "forum"

def load_json(path):
    with open(path) as f:
        return json.load(f)

def generate_dashboard(data, schema):
    """Generate the static dashboard HTML."""
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)

    # Write data.json for client-side use
    with open(DASHBOARD_DIR / "data.json", 'w') as f:
        json.dump(data, f)

    # Generate index.html
    tiers = schema.get("tiers", [])
    tier_labels = {t["id"]: t["label"] for t in tiers}

    # Build table rows grouped by tier
    html_rows = ""
    for tier_id in [t["id"] for t in tiers]:
        tier_subs = [s for s in data["submissions"] if s.get("tier") == tier_id]
        if not tier_subs:
            continue
        html_rows += f'\n      <tr class="tier-header"><td colspan="8">{tier_labels.get(tier_id, tier_id)}</td></tr>\n'
        for s in tier_subs:
            highlight = ' class="highlighted"' if s.get("highlight") else ''
            html_rows += f'''
      <tr{highlight}>
        <td>{s["source"]["username"]}</td>
        <td>{s["hardware"]["description"][:60]}</td>
        <td>{s["hardware"]["vendor"]}</td>
        <td>{s["backend"]}</td>
        <td>{s["model"]["name"][:40]}</td>
        <td>{s["quant"][:30]}</td>
        <td>{s["performance"]["decode_tps"]}</td>
        <td>{s["context"]["stable"][:20]}</td>
      </tr>'''

    html = f'''<!DOCTYPE html>
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
        td {{
            padding: 0.6rem 0.75rem;
            border-bottom: 1px solid var(--border);
        }}
        tr.tier-header td {{
            background: var(--surface);
            font-weight: 700;
            color: var(--accent);
            padding: 0.5rem 0.75rem;
            font-size: 0.8rem;
        }}
        tr.highlighted {{ border-left: 3px solid var(--highlight); }}
        tr:hover {{ background: rgba(59, 130, 246, 0.05); }}
        .footer {{
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border);
            text-align: center;
            color: var(--text-muted);
            font-size: 0.8rem;
        }}
        .footer a {{ color: var(--accent); text-decoration: none; }}
        @media (max-width: 768px) {{
            body {{ padding: 1rem; }}
            .filters {{ flex-direction: column; }}
            table {{ font-size: 0.75rem; }}
            td, th {{ padding: 0.4rem; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 The Local LLM Matrix</h1>
            <p>Community-verified setups for running local models on real silicon</p>
            <div class="stats">
                <div class="stat"><div class="num">{data["total_submissions"]}</div><div class="label">Submissions</div></div>
                <div class="stat"><div class="num">{len(set(s["hardware"]["vendor"] for s in data["submissions"]))}</div><div class="label">Vendors</div></div>
                <div class="stat"><div class="num">{len(set(s["backend"] for s in data["submissions"] if s["backend"]))}</div><div class="label">Backends</div></div>
                <div class="stat"><div class="num">{len(set(s["tier"] for s in data["submissions"] if s["tier"]))}</div><div class="label">Tiers</div></div>
            </div>
        </header>

        <div class="filters">
            <input type="text" id="search" placeholder="Search models, hardware, notes...">
            <select id="filter-tier">
                <option value="">All Tiers</option>
                {''.join(f'<option value="{t["id"]}">{t["label"]}</option>' for t in tiers)}
            </select>
            <select id="filter-vendor">
                <option value="">All Vendors</option>
                {''.join(f'<option>{v}</option>' for v in sorted(set(s["hardware"]["vendor"] for s in data["submissions"])))}
            </select>
            <select id="filter-backend">
                <option value="">All Backends</option>
                {''.join(f'<option>{b}</option>' for b in sorted(set(s["backend"] for s in data["submissions"] if s["backend"])))}
            </select>
        </div>

        <table id="main-table">
            <thead>
                <tr>
                    <th onclick="sortTable(0)">User</th>
                    <th onclick="sortTable(1)">Hardware</th>
                    <th onclick="sortTable(2)">Vendor</th>
                    <th onclick="sortTable(3)">Backend</th>
                    <th onclick="sortTable(4)">Model</th>
                    <th onclick="sortTable(5)">Quant</th>
                    <th onclick="sortTable(6)">Speed</th>
                    <th onclick="sortTable(7)">Context</th>
                </tr>
            </thead>
            <tbody>
                {html_rows}
            </tbody>
        </table>

        <div class="footer">
            <p>Data source: <a href="https://forum.level1techs.com/t/256443">L1Techs Forum Thread</a> | Last updated: {data["generated_at"][:10]}</p>
            <p>Community submissions are user-reported. Verify before purchasing hardware.</p>
        </div>
    </div>

    <script>
        // Simple client-side filtering
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
                    row.style.display = '';
                    return;
                }}
                const text = row.textContent.toLowerCase();
                const cells = row.cells;
                let show = true;
                if (q && !text.includes(q)) show = false;
                if (vendor && cells[2] && cells[2].textContent !== vendor) show = false;
                if (backend && cells[3] && cells[3].textContent !== backend) show = false;
                row.style.display = show ? '' : 'none';
            }});
        }}

        search.addEventListener('input', applyFilters);
        tierFilter.addEventListener('change', applyFilters);
        vendorFilter.addEventListener('change', applyFilters);
        backendFilter.addEventListener('change', applyFilters);

        // Simple sort
        let sortDir = 1;
        function sortTable(col) {{
            const tbody = document.querySelector('#main-table tbody');
            const dataRows = Array.from(tbody.querySelectorAll('tr:not(.tier-header)'));
            dataRows.sort((a, b) => {{
                const av = a.cells[col]?.textContent || '';
                const bv = b.cells[col]?.textContent || '';
                return av.localeCompare(bv, undefined, {{numeric: true}}) * sortDir;
            }});
            dataRows.forEach(r => tbody.appendChild(r));
            sortDir *= -1;
        }}
    </script>
</body>
</html>'''

    with open(DASHBOARD_DIR / "index.html", 'w') as f:
        f.write(html)

    print(f"✓ Dashboard: {DASHBOARD_DIR / 'index.html'}")
    print(f"✓ Data: {DASHBOARD_DIR / 'data.json'}")

def generate_post3(data, schema):
    """Generate the in-forum Data Viewport post (Post #3)."""
    FORUM_DIR.mkdir(parents=True, exist_ok=True)

    tiers = schema.get("tiers", [])
    tier_labels = {t["id"]: t["label"] for t in tiers}

    # Group by tier
    by_tier = {}
    for s in data["submissions"]:
        t = s.get("tier") or "unclassified"
        by_tier.setdefault(t, []).append(s)

    # Group by vendor
    by_vendor = {}
    for s in data["submissions"]:
        v = s["hardware"]["vendor"]
        by_vendor.setdefault(v, []).append(s)

    # Group by backend
    by_backend = {}
    for s in data["submissions"]:
        b = s.get("backend", "Unknown")
        by_backend.setdefault(b, []).append(s)

    def make_table(subs, show_vendor=False):
        rows = ""
        for s in subs:
            h = ' style="border-left:3px solid #f59e0b"' if s.get("highlight") else ""
            rows += f"""<tr{h}>
<td>{s['source']['username']}</td>
<td>{s['hardware']['description'][:50]}</td>
{'<td>' + s['hardware']['vendor'] + '</td>' if show_vendor else ''}
<td>{s['backend']}</td>
<td>{s['model']['name'][:35]}</td>
<td>{s['quant'][:25]}</td>
<td>{s['performance']['decode_tps'][:15]}</td>
<td>{s['context']['stable'][:15]}</td>
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

*Auto-generated index of all community submissions. Last updated: {data['generated_at'][:10]} | {data['total_submissions']} submissions*

**🌐 Full Interactive Dashboard:** [llm-matrix dashboard](https://YOUR-GITHUB-USERNAME.github.io/llm-matrix-dashboard/)

---

<details>
<summary>📊 View by Tier</summary>

"""
    for tier in tiers:
        tid = tier["id"]
        subs = by_tier.get(tid, [])
        if subs:
            content += f"""<details>
<summary>{tier['label']} ({len(subs)} entries)</summary>
{make_table(subs)}
</details>
"""
    content += "</details>\n"

    content += f"""
<details>
<summary>🖥️ View by Hardware Vendor</summary>

"""
    for vendor in sorted(by_vendor.keys()):
        subs = by_vendor[vendor]
        content += f"""<details>
<summary>{vendor} ({len(subs)} entries)</summary>
{make_table(subs)}
</details>
"""
    content += "</details>\n"

    content += f"""
<details>
<summary>⚙️ View by Backend</summary>

"""
    for backend in sorted(by_backend.keys()):
        subs = by_backend[backend]
        content += f"""<details>
<summary>{backend} ({len(subs)} entries)</summary>
{make_table(subs)}
</details>
"""
    content += "</details>\n"

    content += f"""
<details>
<summary>📋 All Submissions (Chronological)</summary>

{make_table(data['submissions'], show_vendor=True)}
</details>

---
*This post is auto-generated from thread data. If something looks wrong, report it in the thread. The interactive dashboard has full filtering, sorting, and comparison.*
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
    print(f"   Dashboard → push to GitHub Pages")
    print(f"   Post #3   → paste into forum")

if __name__ == "__main__":
    main()
