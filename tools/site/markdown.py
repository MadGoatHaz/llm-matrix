"""Markdown → HTML for the guide layer.

Wraps the single third-party dependency (``markdown``) with the extensions the
guides need (tables, fenced code, sane lists, TOC) plus a small front-matter
parser. Raw ``<div class="diagram">`` blocks pass through untouched, which is
how the CSS-only diagrams are authored inline in the markdown.

The ``markdown`` import is deferred to first use (:func:`render_markdown`) so
the rest of the ``tools.site`` package — the five core pages — stays
stdlib-only and importable even when the dependency is not installed.
"""

from __future__ import annotations

import re
from typing import Any

#: Extensions enabled for guide bodies (see PLAN.md §5.1).
MARKDOWN_EXTENSIONS = ("tables", "fenced_code", "sane_lists", "toc")

#: A leading ``--- ... ---`` front-matter block at the very start of the file.
_FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


def _parse_front_matter_block(block: str) -> dict[str, str]:
    """Parse ``key: value`` lines from a front-matter block.

    Blank lines and ``#`` comments are ignored. Values are stripped of
    surrounding quotes. List-like values (e.g. ``related: a, b, c``) are kept
    as the raw string and split by the caller.
    """
    meta: dict[str, str] = {}
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            meta[key] = value
    return meta


def split_front_matter(text: str) -> tuple[dict[str, str], str]:
    """Split a guide document into ``(front-matter, body)``.

    The front-matter is an optional leading ``--- ... ---`` block of
    ``key: value`` pairs (``title``, ``description``, ``nav``, ``icon``,
    ``related``, ``og_image``). If absent, an empty dict and the whole text
    are returned unchanged.
    """
    m = _FRONT_MATTER_RE.match(text)
    if not m:
        return {}, text
    return _parse_front_matter_block(m.group(1)), text[m.end():]


#: A decorative guide-icon div (raw HTML in the content markdown) — hidden
#: from the accessibility tree; the card's heading is the accessible name.
_GUIDE_ICON_RE = re.compile(r'<div class="guide-icon">([^<]*)</div>')


def render_markdown(body: str) -> str:
    """Convert a markdown body to HTML.

    Raw HTML (e.g. ``<div class="diagram">...</div>``) passes through
    unchanged, so CSS-only diagrams authored in the markdown survive the
    conversion.

    Two a11y post-passes (P2-6) run on the rendered fragment:

    * ``<th>`` → ``<th scope="col">`` so screen readers associate each
      column with its header (WCAG 1.3.1 / the Lighthouse table-scope
      audit); guide tables use no row headers, so the blanket replace is
      safe;
    * decorative ``<div class="guide-icon">`` cards get ``aria-hidden``.

    Args:
        body: The markdown source (front-matter already removed).

    Returns:
        The rendered HTML fragment.

    Raises:
        ImportError: if the ``markdown`` package is not installed.
    """
    import markdown  # deferred: keeps the five core pages stdlib-only

    html = markdown.markdown(
        body,
        extensions=list(MARKDOWN_EXTENSIONS),
        output_format="html",
    )
    html = re.sub(r"<th>", '<th scope="col">', html)
    html = _GUIDE_ICON_RE.sub(
        r'<div class="guide-icon" aria-hidden="true">\1</div>', html)
    return html
