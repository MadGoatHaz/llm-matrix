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
``data.json``, and renders the individual guides. Run it directly
(``python -m tools.site``) or via the thin ``tools/generate_site.py`` entry
point.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from . import guides
from . import utils
from .pages import about, community, guides_index, homepage, matrix

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
        "guides.html": guides_index.render(),
        "about.html": about.render(guides_menu),
    }
    for name, html in pages.items():
        path = ws / name
        path.write_text(html, encoding="utf-8")
        print(f"  wrote {name} ({len(html)} bytes)")

    # --- data.json (raw dataset for client-side use) ---
    data_json = ws / "data.json"
    with open(data_json, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"  wrote data.json ({data_json.stat().st_size} bytes)")

    # --- Guides index (guides/index.html, depth 1) ---
    content_guides = ws / "content" / "guides"
    try:
        index_html = guides_index.render_index(content_guides, guides_menu)
        index_path = ws / "guides" / "index.html"
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(index_html, encoding="utf-8")
        print(f"  wrote guides/index.html ({len(index_html)} bytes)")
    except FileNotFoundError as e:
        print(f"WARNING: {e}", file=sys.stderr)

    # --- Individual guides (guides/<slug>/index.html, depth 2) ---
    for slug in guides.generate_guides(content_guides, ws, guides_menu):
        print(f"  wrote guides/{slug}/index.html")

    print(f"\nSite generated: {stats['submissions']} submissions, "
          f"{stats['contributors']} contributors, {stats['vendors']} vendors, "
          f"{stats['backends']} backends.")
