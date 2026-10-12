#!/usr/bin/env python3
"""Structural verification for the multi-page site."""
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path("/home/madgoat/Documents/Local LLM Matrix")
PAGES = ["index.html", "matrix.html", "community.html", "guides.html", "about.html"]
ASSETS = ["css/style.css", "js/main.js", "data.json"]

checks = []
def check(name, ok, detail=""):
    checks.append((name, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  [{detail}]" if detail and not ok else ""))

# --- 1. Files exist ---
for p in PAGES + ASSETS:
    check(f"exists: {p}", (ROOT / p).exists())

# --- 2. Per-page structural checks ---
OG = [
    'og:title" content="The Local AI Stack — Models, Hardware, Backends &amp; Community Data"',
    'og:description" content="A community-driven guide to running AI models on your own hardware.',
    'og:url" content="https://madgoathaz.github.io/llm-matrix/"',
    'og:type" content="website"',
    'og:image" content="https://madgoathaz.github.io/llm-matrix/og-image.png"',
]
NAV_LINKS = ["index.html", "matrix.html", "community.html", "guides.html", "about.html"]

for p in PAGES:
    html = (ROOT / p).read_text()
    check(f"{p}: doctype", html.startswith("<!DOCTYPE html>"))
    check(f"{p}: nav present", '<nav class="nav">' in html)
    check(f"{p}: footer present", '<footer class="footer">' in html)
    check(f"{p}: css linked", 'href="css/style.css"' in html)
    check(f"{p}: js linked", 'src="js/main.js"' in html)
    check(f"{p}: viewport meta", 'name="viewport"' in html)
    check(f"{p}: all 5 nav links", all(f'href="{l}"' in html for l in NAV_LINKS))
    check(f"{p}: OG tags (5)", all(o in html for o in OG))
    check(f"{p}: no {{ leaks", "{{" not in html and "}}" not in html)
    check(f"{p}: no unrendered python", "None" not in re.findall(r'<td[^>]*>None<', html))

# --- 3. Homepage specifics ---
h = (ROOT / "index.html").read_text()
check("index: hero title", "The <span>Local AI Stack</span>" in h)
check("index: hero tagline", "Your community-driven guide to running AI models on your own hardware" in h)
check("index: CTA matrix", 'href="matrix.html" class="btn-large btn-large-primary">Browse the Matrix →' in h)
check("index: CTA guides", 'href="guides.html" class="btn-large btn-large-secondary">Explore Guides →' in h)
check("index: stats row (4 cards)", h.count('class="stat-card"') == 4)
check("index: find-your-setup section", "Find Your Setup" in h)
check("index: gpu table 6 tier rows", len(re.findall(r'badge badge-blue">[≤0-9]', h)) >= 6)
check("index: use-case table 6 rows", all(uc in h for uc in ["Agentic Coding", "Deep Reasoning", "RAG / Document Ingestion", "Creative Writing / Roleplay", "General Chat", "Production Serving"]))
check("index: community highlights section", "Community Highlights" in h)
check("index: highlight cards 3-4", 3 <= h.count("⚡ ") <= 4)
check("index: how it works 3 cards", all(x in h for x in ["1. 📝 Submit", "2. ⚙️ We Parse", "3. 📊 You Browse"]))
check("index: forum credit + CTA", "Join the discussion →" in h and "forum.level1techs.com/t/256443" in h)

# --- 4. Matrix specifics ---
m = (ROOT / "matrix.html").read_text()
check("matrix: header", "<h1>The Matrix</h1>" in m)
check("matrix: subtitle", "All community submissions, filterable and sortable" in m)
check("matrix: search input", 'id="filter-search"' in m)
check("matrix: tier select", 'data-filter="tier"' in m)
check("matrix: vendor select", 'data-filter="vendor"' in m)
check("matrix: backend select", 'data-filter="backend"' in m)
check("matrix: reset button", 'id="filter-reset"' in m)
check("matrix: table id", 'id="data-table"' in m)
data_rows = re.findall(r'<tr class="t\d[^"]*" data-tier=', m)
check("matrix: 12 data rows", len(data_rows) == 12, f"got {len(data_rows)}")
tier_headers = re.findall(r'<tr class="tier-header" data-tier="(t\d)">' , m)
check("matrix: tier headers (t1,t2,t3,t4)", tier_headers == ["t1", "t2", "t3", "t4"], str(tier_headers))
check("matrix: 12 columns in header", len(re.findall(r"<th>[A-Z]", m)) == 12)
cols = re.findall(r"<th>([^<]+)</th>", m)
check("matrix: column names", cols == ["Contributor", "Hardware", "Vendor", "Backend", "Model", "Quant", "Use Case", "Speed", "Context", "KV", "Power", "Mode"], str(cols))
check("matrix: rows have data-vendor", m.count('data-vendor="') >= 12)
check("matrix: rows have data-backend", m.count('data-backend="') >= 12)
check("matrix: normalized backends in attrs", 'data-backend="llama.cpp"' in m and 'data-backend="vLLM"' in m and 'data-backend="llama-swap"' in m and 'data-backend="Strata"' in m and 'data-backend="Ollama"' in m)
check("matrix: colspan 12 on tier headers", m.count('colspan="12"') == len(tier_headers))
check("matrix: all cells have title attr", m.count("<td title=") == 12 * 12, f"got {m.count('<td title=')}")

# --- 5. Community specifics ---
c = (ROOT / "community.html").read_text()
check("community: header", "<h1>The Community</h1>" in c)
check("community: 5 contributor cards", c.count('class="contributor-card"') == 5, str(c.count('class="contributor-card"')))
for u in ["MadGoat", "digitalscream", "Burhan", "s1ugh34d", "PawingUnplug"]:
    check(f"community: has {u}", u in c)
check("community: avatars (5)", c.count('class="avatar"') == 5)
check("community: submissions count labels", "3 submissions" in c and "5 submissions" in c and "2 submissions" in c)
check("community: want-to-be-here CTA", "Want to be here?" in c and "forum.level1techs.com/t/256443" in c)

# --- 6. Guides specifics ---
g = (ROOT / "guides.html").read_text()
check("guides: header", "<h1>Guides</h1>" in g)
check("guides: 8 guide cards", g.count('class="guide-card"') == 8, str(g.count('class="guide-card"')))
for title in ["Quantization Basics", "File Formats", "Quantization Methods", "Model Architectures", "KV Cache", "Context Extension", "Backends Deep Dive", "Multi-GPU &amp; Hybrid"]:
    check(f"guides: has {title}", title in g)
check("guides: 8 coming-soon badges", g.count("badge-amber\">Coming Soon") == 8)
check("guides: forum note", "Guides are being written" in g and "forum.level1techs.com/t/256443" in g)

# --- 7. About specifics ---
a = (ROOT / "about.html").read_text()
check("about: header", "<h1>About The Local AI Stack</h1>" in a)
for s in ["What It Is", "How It Works", "Connection to L1Techs", "How to Contribute", "Credits"]:
    check(f"about: has {s}", s in a)
check("about: L1Techs category link", "forum.level1techs.com/c/high-performance-computing" in a)
check("about: MadGoat credit", "forum.level1techs.com/u/MadGoat" in a)
check("about: github link", "github.com/MadGoatHaz/llm-matrix" in a)

# --- 8. data.json valid + matches ---
d = json.loads((ROOT / "data.json").read_text())
check("data.json: valid json w/ submissions", len(d["submissions"]) == 12)

# --- 9. Tag balance (HTMLParser) ---
class TagChecker(HTMLParser):
    VOID = {"meta", "link", "br", "hr", "img", "input"}
    def __init__(self):
        super().__init__()
        self.stack = []
        self.errors = []
    def handle_starttag(self, tag, attrs):
        if tag not in self.VOID:
            self.stack.append(tag)
    def handle_endtag(self, tag):
        if tag in self.VOID:
            return
        if not self.stack:
            self.errors.append(f"unexpected </{tag}>")
        elif self.stack[-1] == tag:
            self.stack.pop()
        else:
            self.errors.append(f"mismatch: open <{self.stack[-1]}> closed by </{tag}>")
            if tag in self.stack:
                while self.stack and self.stack[-1] != tag:
                    self.stack.pop()
                if self.stack:
                    self.stack.pop()

for p in PAGES:
    tc = TagChecker()
    tc.feed((ROOT / p).read_text())
    check(f"{p}: tags balanced", not tc.errors and not tc.stack, f"errors={tc.errors[:3]} open={tc.stack[:5]}")

# --- 10. CSS + JS sanity ---
css = (ROOT / "css/style.css").read_text()
check("css: design tokens (:root)", ":root {" in css and "--accent: #3b82f6;" in css)
for token in ["--bg: #0a0e17;", "--surface: #131a2b;", "--border: #1e2d3f;", "--text: #e2e8f0;",
              "--success: #10b981;", "--warning: #f59e0b;", "--danger: #ef4444;",
              "--purple: #8b5cf6;", "--cyan: #06b6d4;", "--radius: 8px;", "--nav-height: 60px;"]:
    check(f"css: {token}", token in css)
for selector in [".nav {", ".container {", ".card {", ".stats-row {", ".table-wrapper {",
                 ".filter-bar {", ".badge {", ".hero {", ".footer {", ".guide-card {",
                 ".contributor-card {", ".avatar {", "@media (max-width: 768px) {"]:
    check(f"css: {selector}", selector in css)
check("css: braces balanced", css.count("{") == css.count("}"), f"{css.count('{')} vs {css.count('}')}")

js = (ROOT / "js/main.js").read_text()
for fn in ["initSorting", "sortTable", "initFilters", "nav-toggle", "filter-search", "filter-reset"]:
    check(f"js: has {fn}", fn in js)
check("js: braces balanced", js.count("{") == js.count("}"), f"{js.count('{')} vs {js.count('}')}")
check("js: parens balanced", js.count("(") == js.count(")"), f"{js.count('(')} vs {js.count(')')}")

# --- Summary ---
fails = [c for c in checks if not c[1]]
print(f"\n{'='*50}\nTOTAL: {len(checks)} checks, {len(checks)-len(fails)} pass, {len(fails)} fail")
if fails:
    print("FAILURES:")
    for n, _, det in fails:
        print(f"  - {n} {det}")
    sys.exit(1)
print("ALL CHECKS PASS")
