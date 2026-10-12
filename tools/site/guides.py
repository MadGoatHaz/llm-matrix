"""Generic guide renderer.

Reads an authored markdown guide from ``content/guides/<slug>.md``, parses its
front-matter, renders the body to HTML, wraps it in the page shell at depth 2
(guides live at ``guides/<slug>/index.html``), and writes the result. Related
guides are linked from the front-matter.

This module is the foundation the eight P1-1…P1-8 guides build on.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import markdown as md
from . import utils
from .template import page_shell

#: Guides live two levels below the repo root: ``guides/<slug>/index.html``.
GUIDE_DEPTH = 2

#: Human-readable display names for the known guide slugs, used in the
#: auto-generated "Related guides" section. The naive fallback
#: (``slug.replace("-", " ").title()``) mangles acronyms — ``kv-cache`` ->
#: "Kv Cache", ``multi-gpu`` -> "Multi Gpu" — so the eight known guides carry
#: explicit labels. Any slug not listed here (future guides) uses the
#: title-cased fallback.
GUIDE_LABELS = {
    "quantization": "Quantization Basics",
    "file-formats": "File Formats",
    "quantization-methods": "Quantization Methods",
    "model-architectures": "Model Architectures",
    "kv-cache": "KV Cache",
    "context-extension": "Context Extension",
    "backends": "Backends",
    "multi-gpu": "Multi-GPU & Hybrid",
}


def _label_for(slug: str) -> str:
    """Display name for a guide slug (known label, else title-cased slug)."""
    return GUIDE_LABELS.get(slug, slug.replace("-", " ").title())


def _parse_extra_scripts(value: Any) -> list[str] | None:
    """Front-matter ``extra_scripts`` -> a list of script paths (or ``None``).

    A guide can opt in to a client-side tool (e.g. the launch-command
    generator) by declaring ``extra_scripts: js/commands.js``. Comma-separated
    values are split into a list.
    """
    if not value:
        return None
    if isinstance(value, str):
        items = [v.strip() for v in value.split(",") if v.strip()]
        return items or None
    return [str(v) for v in value]


def _related_links(meta: dict[str, Any]) -> str:
    """Build the "Related guides" section from the front-matter.

    ``related`` is a comma-separated list of guide slugs. Each becomes a link
    to the sibling guide's directory URL, labelled from :data:`GUIDE_LABELS`.
    Returns ``""`` when none are given.
    """
    related = meta.get("related")
    if not related:
        return ""
    if isinstance(related, str):
        slugs = [s.strip() for s in related.split(",") if s.strip()]
    else:
        slugs = [str(s) for s in related]
    if not slugs:
        return ""
    items = "\n".join(
        f'      <li><a href="{slug}/">{utils.html_escape(_label_for(slug))}</a></li>'
        for slug in slugs
    )
    return f'''
  <section class="guide-related">
    <h2>Related guides</h2>
    <ul>
{items}
    </ul>
  </section>'''


def render_guide(md_path: Path, title_override: str | None = None,
                guides_menu: list[tuple[str, str]] | None = None,
                subs: list[dict] | None = None,
                schema: dict | None = None) -> str:
    """Render a single guide markdown file to a full HTML document.

    Args:
        md_path: Path to the ``.md`` guide (e.g. ``content/guides/kv-cache.md``).
        title_override: Optional ``<title>``; defaults to the front-matter
            ``title``, then the file stem.
        guides_menu: Optional ``(label, url)`` list for the nav dropdown.
        subs: Real submissions; used to bake the ``#commands-config`` island
            when the guide opts into a client tool via ``extra_scripts``.
        schema: The parsed ``schema.json`` (backends, tiers) for the island.

    Returns:
        The full ``guides/<slug>/index.html`` document (depth-2 shell).
    """
    text = md_path.read_text(encoding="utf-8")
    meta, body = md.split_front_matter(text)

    title = title_override or meta.get("title") or md_path.stem
    description = meta.get("description", "")

    body_html = md.render_markdown(body)
    related_html = _related_links(meta)

    # Wrap in the long-form ``.guide`` container: all guide typography,
    # table, code-block, and TOC styles in css/style.css are scoped under
    # ``.guide`` (see the GUIDE PAGE LAYER section). Diagram and callout
    # styles are top-level, so they render inside it unchanged.
    wrapped = f'\n<div class="guide">\n{body_html}\n{related_html}\n</div>'

    extra_scripts = _parse_extra_scripts(meta.get("extra_scripts"))
    if extra_scripts and subs is not None and schema is not None:
        # A guide that opts into a client tool (e.g. the launch-command
        # generator) also gets the #commands-config island so the tool runs
        # with no network request.
        wrapped += "\n" + utils.commands_config_island(subs, schema)

    return page_shell(title, description, wrapped, depth=GUIDE_DEPTH,
                      guides_menu=guides_menu,
                      extra_scripts=extra_scripts)


def generate_guides(content_dir: Path, out_dir: Path,
                   guides_menu: list[tuple[str, str]] | None = None,
                   subs: list[dict] | None = None,
                   schema: dict | None = None) -> list[str]:
    """Render every authored guide in ``content_dir`` into ``out_dir``.

    Each ``content_dir/<slug>.md`` becomes ``out_dir/guides/<slug>/index.html``.
    Files whose name starts with ``_`` are treated as drafts/samples and are
    skipped, so a proof-of-concept never ships. The ``index.md`` file is also
    skipped here — it is rendered separately by ``guides_index.render_index()``.

    Args:
        content_dir: The authored-content directory (``content/guides``).
        out_dir: Where generated pages are written (the repo root).
        guides_menu: Optional ``(label, url)`` list for the nav dropdown.
        subs: Real submissions (baked into the island for guides that opt
            into a client tool).
        schema: The parsed ``schema.json`` for the island.

    Returns:
        The list of guide slugs written (empty if there is no content).
    """
    written: list[str] = []
    if not content_dir.is_dir():
        return written
    for md_path in sorted(content_dir.glob("*.md")):
        if md_path.name.startswith("_"):
            continue
        if md_path.stem == "index":
            continue  # rendered by guides_index.render_index()
        html = render_guide(md_path, guides_menu=guides_menu,
                           subs=subs, schema=schema)
        dest = out_dir / "guides" / md_path.stem / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(html, encoding="utf-8")
        written.append(md_path.stem)
    return written
