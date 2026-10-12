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


def _related_links(meta: dict[str, Any]) -> str:
    """Build the "Related guides" section from the front-matter.

    ``related`` is a comma-separated list of guide slugs. Each becomes a link
    to the sibling guide's directory URL. Returns ``""`` when none are given.
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
        f'      <li><a href="{slug}/">{utils.html_escape(slug.replace("-", " ").title())}</a></li>'
        for slug in slugs
    )
    return f'''
  <section class="guide-related">
    <h2>Related guides</h2>
    <ul>
{items}
    </ul>
  </section>'''


def render_guide(md_path: Path, title_override: str | None = None) -> str:
    """Render a single guide markdown file to a full HTML document.

    Args:
        md_path: Path to the ``.md`` guide (e.g. ``content/guides/kv-cache.md``).
        title_override: Optional ``<title>``; defaults to the front-matter
            ``title``, then the file stem.

    Returns:
        The full ``guides/<slug>/index.html`` document (depth-2 shell).
    """
    text = md_path.read_text(encoding="utf-8")
    meta, body = md.split_front_matter(text)

    title = title_override or meta.get("title") or md_path.stem
    description = meta.get("description", "")

    body_html = md.render_markdown(body)
    related_html = _related_links(meta)

    return page_shell(title, description, f"\n{body_html}\n{related_html}", depth=GUIDE_DEPTH)


def generate_guides(content_dir: Path, out_dir: Path) -> list[str]:
    """Render every authored guide in ``content_dir`` into ``out_dir``.

    Each ``content_dir/<slug>.md`` becomes ``out_dir/guides/<slug>/index.html``.
    Files whose name starts with ``_`` are treated as drafts/samples and are
    skipped, so a proof-of-concept never ships.

    Args:
        content_dir: The authored-content directory (``content/guides``).
        out_dir: Where generated pages are written (the repo root).

    Returns:
        The list of guide slugs written (empty if there is no content).
    """
    written: list[str] = []
    if not content_dir.is_dir():
        return written
    for md_path in sorted(content_dir.glob("*.md")):
        if md_path.name.startswith("_"):
            continue
        html = render_guide(md_path)
        dest = out_dir / "guides" / md_path.stem / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(html, encoding="utf-8")
        written.append(md_path.stem)
    return written
