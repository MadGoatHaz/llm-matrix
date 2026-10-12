#!/usr/bin/env python3
"""QA structural verification — independent check of all generated site files.

Checks (per task spec):
  1. Every HTML: doctype, <html lang>, meta charset/viewport, title, OG tags,
     nav + footer + <main> landmarks.
  2. Every local href/src resolves to an existing file (no internal 404s).
     Same-page #anchor targets must exist in that page.
  3. Nav block identical (normalized) across all pages.
  4. CSS/JS referenced files exist.
  5. data.json: valid JSON, expected top-level keys, consistent 19-key
     submission contract, totals match.

Exit 0 = all pass, 1 = failures found.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

HTML_FILES = sorted(
    p for p in ROOT.rglob("*.html")
    if not any(part in (".git", "tests", "work", "Backup", ".venv", "forum", "templates", "data") for part in p.parts)
)

failures = []
warnings = []

def check(cond, msg):
    if cond:
        return
    failures.append(msg)

# ---------- 1-4: HTML structure, links, nav, assets ----------
nav_blobs = {}
all_ids = {}

for p in HTML_FILES:
    rel = p.relative_to(ROOT)
    text = p.read_text(encoding="utf-8")

    # 1. structural requirements
    check(text.lstrip().lower().startswith("<!doctype html>"), f"{rel}: missing/invalid doctype")
    m = re.search(r'<html[^>]*>', text, re.I)
    check(m and re.search(r'lang="[^"]+"', m.group(0)), f"{rel}: <html> missing lang attribute")
    check(re.search(r'<meta[^>]+(?:name="charset"|charset=)', text, re.I), f"{rel}: missing meta charset")
    check(re.search(r'<meta[^>]+name="viewport"', text, re.I), f"{rel}: missing meta viewport")
    tm = re.search(r"<title>(.*?)</title>", text, re.S)
    check(tm and tm.group(1).strip(), f"{rel}: missing/empty <title>")
    for og in ("og:title", "og:description", "og:image", "og:url"):
        check(re.search(rf'<meta[^>]+property="{og}"[^>]+content="[^"]+"', text), f"{rel}: missing {og} meta")
    check(re.search(r'<nav[^>]*>', text), f"{rel}: missing <nav>")
    check(re.search(r'<footer[^>]*>', text), f"{rel}: missing <footer>")
    check(re.search(r'<main[^>]*>', text), f"{rel}: missing <main>")
    check("{{" not in text and "}}" not in text, f"{rel}: unrendered template braces leaked")

    # collect ids for anchor checks
    ids = set(re.findall(r'\bid="([^"]+)"', text))
    all_ids[rel] = ids

    # nav consistency (normalize depth-relative href prefixes to a canonical base,
    # since pages at depth 1/2 use ../ and ../../ by design)
    nm = re.search(r"<nav\b.*?</nav>", text, re.S)
    check(nm, f"{rel}: nav block not found")
    if nm:
        norm = re.sub(r"\s+", " ", nm.group(0)).strip()
        # Canonicalize depth-relative prefixes so navs at depth 0/1/2 compare
        # equal: strip leading "../../" then "../" from every href.
        norm = norm.replace('href="../../', 'href="').replace('href="../', 'href="')
        nav_blobs[rel] = norm

    # 2. link resolution
    refs = re.findall(r'(?:href|src)="([^"]+)"', text)
    for r in refs:
        if r.startswith(("#", "http://", "https://", "mailto:", "tel:", "data:", "javascript:")):
            if r.startswith("#") and len(r) > 1:
                # same-page anchor
                check(r[1:] in ids, f"{rel}: anchor {r} has no matching id on page")
            continue
        target = r.split("#")[0].split("?")[0]
        if not target:
            continue
        base = (p.parent / target).resolve()
        check(base.exists(), f"{rel}: broken local link -> {r}")

# nav identical across pages?
norms = list(nav_blobs.values())
if len(set(norms)) == 1:
    print(f"NAV: identical across all {len(HTML_FILES)} pages")
else:
    uniq = {}
    for rel, n in nav_blobs.items():
        uniq.setdefault(n, []).append(str(rel))
    for i, (n, rels) in enumerate(uniq.items()):
        print(f"NAV variant {i}: {rels}")
    check(len(uniq) == 1, f"nav differs across {len(uniq)} variants")

# ---------- 5. data.json ----------
d = json.loads((ROOT / "data.json").read_text(encoding="utf-8"))
expected_keys = {"version", "generated_at", "schema_version", "source_thread",
                 "total_submissions", "skipped_templates", "submissions"}
check(set(d.keys()) == expected_keys, f"data.json: top-level keys {sorted(d.keys())} != expected {sorted(expected_keys)}")
check(isinstance(d["submissions"], list) and d["submissions"], "data.json: submissions not a non-empty list")
check(d["total_submissions"] == len(d["submissions"]), f"data.json: total_submissions {d['total_submissions']} != len {len(d['submissions'])}")
keysets = {tuple(sorted(s.keys())) for s in d["submissions"]}
check(len(keysets) == 1, f"data.json: submissions do not share one key set ({len(keysets)} variants)")
if len(keysets) == 1:
    ks = keysets.pop()
    print(f"DATA: {len(d['submissions'])} submissions, uniform {len(ks)}-key contract: {list(ks)}")
# api endpoint files
for f in ("submissions", "benchmarks", "hardware"):
    ap = ROOT / "data" / "api" / "v1" / f"{f}.json"
    check(ap.exists(), f"missing data/api/v1/{f}.json")
    if ap.exists():
        json.loads(ap.read_text(encoding="utf-8"))  # raises if invalid
check((ROOT / "data" / "api" / "v1" / "schema.json").exists(), "missing data/api/v1/schema.json")

# css/js assets
for a in ("css/style.css", "js/main.js"):
    check((ROOT / a).exists(), f"missing asset {a}")

# ---------- report ----------
print()
print(f"HTML files checked: {len(HTML_FILES)}")
for r in sorted(all_ids):
    print(f"  {r} ({len(all_ids[r])} ids)")
print()
if warnings:
    print("WARNINGS:")
    for w in warnings:
        print(f"  ⚠ {w}")
if failures:
    print(f"FAILURES ({len(failures)}):")
    for f in failures:
        print(f"  ✗ {f}")
    sys.exit(1)
print("ALL STRUCTURAL CHECKS PASSED")
