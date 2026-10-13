"""The Local AI Stack site generator.

A modular replacement for the legacy 826-line ``tools/generate_site.py``
monolith. The package splits the work into focused modules:

* :mod:`tools.site.utils`     — data loading, placeholder detection, formatting,
  and the aggregation helpers the pages build on (stdlib-only).
* :mod:`tools.site.template`  — the shared page shell (head/OG tags, nav,
  footer) with depth-relative asset paths.
* :mod:`tools.site.pages`     — one pure renderer per site page.
* :mod:`tools.site.markdown`  — markdown → HTML + front-matter (guide layer).
* :mod:`tools.site.guides`    — the generic ``guides/<slug>/index.html`` renderer.

:func:`main` is the single orchestration point: it loads the data, builds the
guides nav dropdown, renders the five core pages + the guides index, writes
the versioned data API (``data.json`` + ``data/api/v1/*.json``) and the
``/api/`` documentation page, and renders the individual guides. Run it
directly (``python -m tools.site``) or via the thin
``tools/generate_site.py`` entry point.
"""

from __future__ import annotations

import sys
from pathlib import Path

from . import api
from . import guides
from . import utils
from .pages import (about, api as api_page, changelog, community, compare,
                    guides_index, homepage, matrix, recommend, submit)

__all__ = ["main"]


def _build_guides_menu() -> list[tuple[str, str]]:
    """Build the ``(label, url)`` list for the Guides nav dropdown.

    The URLs are relative to the repo root (the nav is rendered at depth 0
    for the core pages; ``template.nav()`` computes the correct prefix).
    Each guide lives at ``guides/<slug>/``.
    """
    return [
        (label, f"guides/{slug}/")
        for slug, label in guides.GUIDE_LABELS.items()
    ]


def main(workspace: str | Path | None = None,
         data_dir: str | Path | None = None,
         submissions: str | Path | None = None,
         schema: str | Path | None = None) -> None:
    """Generate the full site (core pages + guides index + guides + data.json).

    All paths default to the real repo root, but each can be overridden — the
    test suite points them at a temp workspace so the committed site is never
    touched.

    Args:
        workspace: Repo root / output directory.
        data_dir: Directory holding ``submissions.json``.
        submissions: Path to ``submissions.json``.
        schema: Path to ``schema.json``.

    Exits with status 1 (and a stderr message) if a required input or shared
    asset is missing — a failure is reported, never silently skipped.
    """
    ws = Path(workspace) if workspace else utils.WORKSPACE
    data_dir = Path(data_dir) if data_dir else ws / "data"
    subs_path = Path(submissions) if submissions else data_dir / "submissions.json"
    schema_path = Path(schema) if schema else ws / "tools" / "schema.json"

    # --- Load inputs ---
    if not subs_path.exists():
        print(f"ERROR: {subs_path} not found. Run pull.py -> parse.py first.",
              file=sys.stderr)
        sys.exit(1)
    if not schema_path.exists():
        print(f"ERROR: {schema_path} not found.", file=sys.stderr)
        sys.exit(1)

    data = utils.load_json(subs_path)
    schema = utils.load_json(schema_path)

    # --- Shared assets must exist (authored files, not generated) ---
    for asset in ("css/style.css", "js/main.js"):
        p = ws / asset
        if not p.exists():
            print(f"ERROR: shared asset {asset} is missing.", file=sys.stderr)
            sys.exit(1)

    subs = utils.real_submissions(data)
    stats = utils.compute_stats(subs, schema)

    # --- Build the Guides nav dropdown (shared by every page) ---
    guides_menu = _build_guides_menu()

    # --- Write the core pages (all get the Guides dropdown) ---
    pages = {
        "index.html": homepage.render(subs, schema, stats, guides_menu),
        "matrix.html": matrix.render(subs, schema, stats, guides_menu),
        "community.html": community.render(subs, schema, stats, guides_menu),
        "guides.html": guides_index.render(guides_menu),
        "about.html": about.render(guides_menu),
    }
    for name, html in pages.items():
        path = ws / name
        path.write_text(html, encoding="utf-8")
        print(f"  wrote {name} ({len(html)} bytes)")

    # --- Recommend page (recommend/index.html, depth 1; P2-1) ---
    # ImportError = the optional `markdown` dep is not installed; the five
    # core pages are stdlib-only by design, so the content layer degrades
    # with a reported warning (never silently).
    content_dir = ws / "content"
    try:
        rec_html = recommend.render(subs, schema, content_dir, guides_menu)
        rec_path = ws / "recommend" / "index.html"
        rec_path.parent.mkdir(parents=True, exist_ok=True)
        rec_path.write_text(rec_html, encoding="utf-8")
        print(f"  wrote recommend/index.html ({len(rec_html)} bytes)")
    except (FileNotFoundError, ImportError) as e:
        print(f"WARNING: recommend page skipped: {e}", file=sys.stderr)

    # --- Compare page (compare/index.html, depth 1; P2-2) ---
    try:
        cmp_html = compare.render(subs, schema, guides_menu)
        cmp_path = ws / "compare" / "index.html"
        cmp_path.parent.mkdir(parents=True, exist_ok=True)
        cmp_path.write_text(cmp_html, encoding="utf-8")
        print(f"  wrote compare/index.html ({len(cmp_html)} bytes)")
    except FileNotFoundError as e:
        print(f"WARNING: {e}", file=sys.stderr)

    # --- Submit page (submit/index.html, depth 1; P3-4) ---
    # Static community submission form. Uses the same content dir as the
    # recommend page; degrades with a reported warning if content/submit.md
    # or the `markdown` dep is missing (never silently).
    try:
        submit_html = submit.render(schema, content_dir, guides_menu)
        submit_path = ws / "submit" / "index.html"
        submit_path.parent.mkdir(parents=True, exist_ok=True)
        submit_path.write_text(submit_html, encoding="utf-8")
        print(f"  wrote submit/index.html ({len(submit_html)} bytes)")
    except (FileNotFoundError, ImportError) as e:
        print(f"WARNING: submit page skipped: {e}", file=sys.stderr)

    # --- Versioned data API (P4-4): data.json + data/api/v1/*.json ---
    # data.json gains the API `version` field; v1/submissions.json is the
    # same payload at its stable versioned path; the secondary datasets get
    # versioned copies when present. The authored v1/schema.json is untouched.
    api.write_api(ws, data)

    # --- API documentation page (api/index.html, depth 1; P4-4) ---
    # The dataset + schema feed the {{data tokens}} (C8) in content/api.md,
    # so the example payload's version stamps and counts track the live data.
    try:
        api_html = api_page.render(content_dir, guides_menu, data=data,
                                   schema=schema)
        api_page_path = ws / "api" / "index.html"
        api_page_path.parent.mkdir(parents=True, exist_ok=True)
        api_page_path.write_text(api_html, encoding="utf-8")
        print(f"  wrote api/index.html ({len(api_html)} bytes)")
    except (FileNotFoundError, ImportError) as e:
        print(f"WARNING: api page skipped: {e}", file=sys.stderr)

    # --- Changelog page (changelog/index.html, depth 1; C5) ---
    # Static, authored markdown (content/changelog.md). Degrades with a
    # reported warning if the content file or the `markdown` dep is missing
    # (never silently).
    try:
        changelog_html = changelog.render(content_dir, guides_menu)
        changelog_path = ws / "changelog" / "index.html"
        changelog_path.parent.mkdir(parents=True, exist_ok=True)
        changelog_path.write_text(changelog_html, encoding="utf-8")
        print(f"  wrote changelog/index.html ({len(changelog_html)} bytes)")
    except (FileNotFoundError, ImportError) as e:
        print(f"WARNING: changelog page skipped: {e}", file=sys.stderr)

    # --- Guides index (guides/index.html, depth 1) ---
    content_guides = ws / "content" / "guides"
    try:
        index_html = guides_index.render_index(content_guides, guides_menu,
                                              subs, schema)
        index_path = ws / "guides" / "index.html"
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(index_html, encoding="utf-8")
        print(f"  wrote guides/index.html ({len(index_html)} bytes)")
    except (FileNotFoundError, ImportError) as e:
        print(f"WARNING: guides index skipped: {e}", file=sys.stderr)

    # --- Individual guides (guides/<slug>/index.html, depth 2) ---
    try:
        for slug in guides.generate_guides(content_guides, ws, guides_menu, subs, schema):
            print(f"  wrote guides/{slug}/index.html")
    except ImportError as e:
        print(f"WARNING: guides skipped (the `markdown` content dep is not "
              f"installed): {e}", file=sys.stderr)

    print(f"\nSite generated: {stats['submissions']} submissions, "
          f"{stats['contributors']} contributors, {stats['vendors']} vendors, "
          f"{stats['backends']} backends.")
