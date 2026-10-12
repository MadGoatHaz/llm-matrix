#!/usr/bin/env python3
"""Verify all 9 dashboard fixes in generated index.html + post3_viewport.md."""
import re
import sys

ROOT = "/home/madgoat/Documents/Local LLM Matrix"
html = open(f"{ROOT}/index.html").read()
post3 = open(f"{ROOT}/forum/post3_viewport.md").read()

results = []
def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  [{detail}]" if detail and not ok else ""))

# --- Fix 1: no mid-word truncation, full values, CSS ellipsis + title tooltip ---
full_values = [
    "samuelcardillo/Carnice-Qwen3.6-MoE-35B-A3B",
    "65536 tokens (NIAH hit YES at 65k)",
    "1x Radeon VII 16GB HBM2 (gfx906), 32-core EPYC host, 67GB RAM",
    "unsloth/Qwen3.8-27B-GGUF (UD-Q2_K_XL)",
    "MaziyarPanahi/DeepSeek-R1-0528-Qwen3-8B-GGUF",
    "131072 configured;",
    "quantized KV (VRAM 5312MB @4k → 5312MB @65k, +0)",
]
missing = [v for v in full_values if v not in html]
check("F1 full values present (no Python-side slicing)", not missing, f"missing={missing}")

check("F1 CSS ellipsis on td", all(x in html for x in
      ["max-width: 200px;", "overflow: hidden;", "text-overflow: ellipsis;", "white-space: nowrap;"]))
check("F1 CSS td[title]:hover tooltip", "td[title]:hover" in html and "box-shadow: 0 4px 12px rgba(0,0,0,0.3)" in html)

tds = re.findall(r"<td([^>]*)>", html)
tds_data = [a for a in tds if 'colspan' not in a]
no_title = [a for a in tds_data if "title=" not in a]
check("F1 every data <td> has title attr", not no_title, f"no_title={len(no_title)}")

# --- Fix 2: HTML escaping ---
check("F2 > escaped in data (>=106,493)", "&gt;=106,493" in html)
check("F2 no unescaped raw data angle brackets", not re.search(r"<td[^>]*>[^<]*[<>][^<]*</td>", html))
# & in data: check '9B active params ≈ 9B compute' (no &), check forum credit uses &amp;
check("F2 static &amp; in forum-credit intact", "Machine Learning, LLMs &amp; AI" in html)

# --- Fix 3: tier filter live ---
check("F3 applyFilters uses dataset.tier", "row.dataset.tier !== tier" in html)
check("F3 tier-header hiding logic", "Hide tier headers that have no visible rows" in html)
hdr_tiers = re.findall(r'<tr class="tier-header" data-tier="([^"]+)">', html)
check("F3 data-tier on tier-header rows", len(hdr_tiers) == 4, f"headers={hdr_tiers}")

# --- Fix 4: sort within tier groups ---
check("F4 sortState + group sort", "let sortState = {}" in html and "currentGroup = { header: row, rows: [] }" in html)
check("F4 numeric + localeCompare sort", "parseFloat(av.replace" in html and "localeCompare(bv, undefined, {numeric: true})" in html)
check("F4 sort indicator CSS", "th.sort-asc::after" in html and "th.sort-desc::after" in html)

# --- Fix 5: 12 columns ---
th = re.findall(r"<th[^>]*>([^<]*)</th>", html)
expected_th = ["Contributor", "Hardware", "Vendor", "Backend", "Model", "Quant",
               "Use Case", "Speed", "Context", "KV", "Power", "Mode"]
check("F5 thead has 12 expected columns", th == expected_th, f"got={th}")
rowblocks = re.findall(r"<tr (?:class=\"highlighted\" )?data-tier=\"[^\"]+\">(.*?)</tr>", html, re.DOTALL)
badrows = [r for r in rowblocks if len(re.findall(r"<td", r)) != 12]
check("F5 every data row has 12 tds", not badrows, f"badrows={len(badrows)}")
check("F5 tier-header colspan=12", 'colspan="12"' in html)
check("F5 hide-mobile on Use Case/KV/Power/Mode", html.count('class="hide-mobile"') >= 4 * (len(rowblocks) + 1))
check("F5 media query hides .hide-mobile", ".hide-mobile { display: none; }" in html)

# --- Fix 6: stats = real submissions only (computed independently from data) ---
import json as _json
_d = _json.load(open(f"{ROOT}/data/submissions.json"))
_ph = lambda v: (not str(v or "").strip()) or bool(re.match(r"^\[.*\]$", str(v).strip(), re.DOTALL))
# replicate generate.py: template = all key fields placeholder
_real = [s for s in _d["submissions"]
         if not all([
             _ph(s.get("hardware", {}).get("description")),
             _ph(s.get("model", {}).get("name")),
             _ph(s.get("backend")),
             _ph(s.get("quant")),
             _ph(s.get("performance", {}).get("decode_tps")),
             _ph(s.get("context", {}).get("stable")),
             _ph(s.get("use_cases")),
         ])]
_disp = [s for s in _real if s.get("tier")]
_vendors = set()
for s in _disp:
    v = s["hardware"].get("vendor", "")
    if v and not (v == "Mixed" and _ph(s["hardware"].get("description"))):
        _vendors.add(v)
_backends = {s["backend"] for s in _disp if s.get("backend") and not _ph(s["backend"])}
_tiers = {s["tier"] for s in _disp if s.get("tier")}
expected_stats = {"Submissions": str(len(_disp)), "Vendors": str(len(_vendors)),
                  "Backends": str(len(_backends)), "Tiers": str(len(_tiers))}
stats = dict((label, num) for num, label in re.findall(r'<div class="num">(\d+)</div><div class="label">(\w+)</div>', html))
check("F6 stats match real-data computation", stats == expected_stats,
      f"html={stats} expected={expected_stats}")
check("F6 stats use real count not total_submissions", stats["Submissions"] == "12" and _d["total_submissions"] == 12)
check("F6 no Mixed vendor option", '>Mixed<' not in html)
check("F6 vendor options are AMD/NVIDIA", re.findall(r'<select id="filter-vendor">(.*?)</select>', html, re.DOTALL)[0].count("<option value=") == 3)

# --- Fix 7: reset button ---
check("F7 reset button in filters", '<button onclick="resetFilters()" class="btn-reset">Reset</button>' in html)
check("F7 resetFilters JS", "function resetFilters()" in html and "location.reload()" in html)
check("F7 btn-reset CSS", ".btn-reset:hover" in html)

# --- Fix 8: post3 URL ---
check("F8 post3 dashboard URL", "https://madgoathaz.github.io/llm-matrix" in post3)
check("F8 no YOUR-USERNAME left", "YOUR-USERNAME" not in post3 and "llm-matrix-dashboard" not in post3)
check("F8 post3 count = 12", "12 submissions" in post3)

# --- Fix 9: data-tier on all data rows ---
drows = re.findall(r'<tr (?:class="highlighted" )?data-tier="(t\d+)">', html)
from collections import Counter
c = Counter(drows)
check("F9 data-tier on 12 data rows", len(drows) == 12 and c == {"t1": 6, "t2": 1, "t3": 1, "t4": 4}, f"dist={dict(c)}")

# --- JS sanity: brace/quote balance of the inline script ---
script = re.search(r"<script>(.*?)</script>", html, re.DOTALL).group(1)
ok_balance = (script.count("{") == script.count("}")) and (script.count("(") == script.count(")"))
check("JS brace+paren balance", ok_balance, f"{{={script.count('{')} }}={script.count('}')} (={script.count('(')} )={script.count(')')}")
# no doubled braces leaked from f-string
check("no leaked {{ in JS/CSS output", "{{" not in html and "}}" not in html)

# --- JS syntax check via node (if available) ---
import shutil, tempfile, os
if shutil.which("node"):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as tf:
        tf.write(script)
        js_path = tf.name
    r = os.system(f"node --check {js_path} >/dev/null 2>&1")
    os.unlink(js_path)
    check("node --check inline script", r == 0, f"exit={r}")
else:
    print("SKIP  node not available for JS syntax check")

fails = [n for n, ok, _ in results if not ok]
print(f"\n{len(results) - len(fails)}/{len(results)} checks passed")
if fails:
    print("FAILURES:", fails)
    sys.exit(1)
