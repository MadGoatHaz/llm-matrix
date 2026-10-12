"""Guides index and redirect stub.

Two documents are produced:

* ``guides/index.html`` — the real guides hub, rendered from
  ``content/guides/index.md`` at depth 1. This is the landing point
  for the educational section.
* ``guides.html`` — a thin redirect stub (meta refresh + canonical)
  that preserves back-compat with any existing links to the old
  flat-page URL.
"""

from __future__ import annotations

from pathlib import Path

from .. import markdown as md
from .. import utils
from ..template import page_shell


def render() -> str:
    """Render the ``guides.html`` redirect stub.

    A minimal page that meta-refreshes to ``guides/`` and carries a
    canonical link so search engines follow the move.

    Returns:
        The full ``guides.html`` document (depth 0).
    """
    body = (
        '  <div class="page-header">\n'
        '    <h1>Guides</h1>\n'
        '    <p class="subtitle">Redirecting to the guides index&hellip;</p>\n'
        '  </div>\n'
        '  <p><a href="guides/">Continue to the Guides index →</a></p>'
    )
    title = "Guides — The Local AI Stack"
    desc = ("Understand the technology behind your setup: quantization, file formats, "
            "KV cache, model architectures, context extension, backends, and multi-GPU.")
    html = page_shell(title, desc, body)
    # Inject the meta refresh + canonical right after the <title> tag.
    meta_refresh = ('    <meta http-equiv="refresh" content="0; url=guides/">\n'
                    '    <link rel="canonical" href="guides/">')
    html = html.replace("</title>", f"</title>\n{meta_refresh}", 1)
    return html


def render_index(content_dir: Path,
                 guides_menu: list[tuple[str, str]] | None = None) -> str:
    """Render the guides index from ``content/guides/index.md``.

    The index lives at ``guides/index.html`` (depth 1). It is rendered
    through the same markdown pipeline as the individual guides, but
    without the ``.guide`` wrapper (the index uses the normal page layout
    with card grids).

    Args:
        content_dir: The authored-content directory (``content/guides``).
        guides_menu: Optional ``(label, url)`` list for the nav dropdown.

    Returns:
        The full ``guides/index.html`` document.

    Raises:
        FileNotFoundError: if ``content/guides/index.md`` does not exist.
    """
    index_path = content_dir / "index.md"
    if not index_path.exists():
        raise FileNotFoundError(f"Guides index not found: {index_path}")

    text = index_path.read_text(encoding="utf-8")
    meta, body = md.split_front_matter(text)

    title = meta.get("title", "Guides")
    description = meta.get(
        "description",
        "The complete educational series for local LLMs.")

    body_html = md.render_markdown(body)
    # The index page uses the normal page layout (not the .guide long-form
    # wrapper), so the card-grid and guide-card styles apply directly.
    wrapped = f'\n{body_html}'

    return page_shell(title, description, wrapped, depth=1,
                      guides_menu=guides_menu)
