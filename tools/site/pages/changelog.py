"""``changelog/index.html`` — the project changelog (C5).

"Nothing goes stale silently." This page makes the project's evolution
visible to users: a clean, scannable list of releases with dates and the
key changes in each.

The content is authored once in ``content/changelog.md`` (markdown, rendered
by the shared ``tools.site.markdown`` layer) and maintained manually — each
new release gets a new ``## vX.Y — <Month Year>`` section at the top. The
page itself is static: no client script, no data tokens.

The page lives at ``changelog/index.html`` (depth 1).
"""

from __future__ import annotations

from pathlib import Path

from .. import markdown as md
from .. import utils
from ..template import page_shell

#: The changelog page is one level below the repo root.
CHANGELOG_DEPTH = 1


def render(content_dir: Path,
           guides_menu: list[tuple[str, str]] | None = None) -> str:
    """Render the changelog page document.

    Args:
        content_dir: The authored-content directory (``content/``); the
            changelog is read from ``content_dir/changelog.md``.
        guides_menu: Optional ``(label, url)`` list for the nav dropdown.

    Returns:
        The full ``changelog/index.html`` document (depth 1).

    Raises:
        FileNotFoundError: if ``content/changelog.md`` does not exist.
        ImportError: if the ``markdown`` content dependency is not installed.
    """
    md_path = content_dir / "changelog.md"
    meta, body_md = md.split_front_matter(md_path.read_text(encoding="utf-8"))
    body_html = md.render_markdown(body_md)

    title = utils.html_escape(meta.get("title", "Changelog"))
    desc = meta.get("description", "")

    body = f'''
  <div class="page-header">
    <h1>{title}</h1>
    <p class="subtitle">{utils.html_escape(desc)}</p>
  </div>

  <section class="changelog" aria-label="Release history">
{body_html}
  </section>'''

    full_title = f'{title} — The Local AI Stack'
    return page_shell(full_title, desc, body, depth=CHANGELOG_DEPTH,
                      guides_menu=guides_menu)
