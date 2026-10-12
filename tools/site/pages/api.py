"""``api/index.html`` — the data API documentation page (P4-4).

The site's dataset is published as stable, versioned JSON. This page is the
human-readable front door to that contract: what the endpoints are, the
shape of a record, the versioning policy, and how to consume the data from
your own site (GitHub Pages serves it with permissive CORS).

The explainer copy lives in ``content/api.md`` (markdown, rendered by the
shared ``tools.site.markdown`` layer); the page itself is static. No client
script is needed — the JSON lives at ``data/api/v1/`` and ``data.json``.

The page lives at ``api/index.html`` (depth 1).
"""

from __future__ import annotations

from pathlib import Path

from .. import markdown as md
from .. import utils
from ..template import page_shell

#: The API docs page is one level below the repo root.
API_DEPTH = 1


def render(content_dir: Path,
          guides_menu: list[tuple[str, str]] | None = None) -> str:
    """Render the API documentation page.

    Args:
        content_dir: The authored-content directory (``content/``); the
            explainer is read from ``content_dir/api.md``.
        guides_menu: Optional ``(label, url)`` list for the nav dropdown.

    Returns:
        The full ``api/index.html`` document (depth 1).

    Raises:
        FileNotFoundError: if ``content/api.md`` does not exist.
        ImportError: if the ``markdown`` content dependency is not installed.
    """
    md_path = content_dir / "api.md"
    meta, body_md = md.split_front_matter(md_path.read_text(encoding="utf-8"))
    intro_html = md.render_markdown(body_md)

    body = f'''
  <div class="page-header">
    <h1>The Data API</h1>
    <p class="subtitle">Stable, versioned JSON for the community dataset — no server, no auth</p>
  </div>

{intro_html}

  <section aria-labelledby="api-next-title">
    <h2 id="api-next-title" class="section-title">Next steps</h2>
    <div class="card">
      <p><strong>Read the full contract.</strong> Every field, the versioning policy, and the changelog live in the <a href="{utils.GITHUB_REPO}/blob/main/data/api/README.md" target="_blank" rel="noopener">API README</a> in the repo.</p>
      <p><strong>Validate against the schema.</strong> The formal JSON Schema (draft 2020-12) is served at <a href="../data/api/v1/schema.json">data/api/v1/schema.json</a> — point your validator at it.</p>
      <p><strong>Fetch the data.</strong> <a href="../data.json">data.json</a> (site root) or <a href="../data/api/v1/submissions.json">data/api/v1/submissions.json</a> — same payload, the versioned path is the one to code against.</p>
    </div>
  </section>'''

    title = f'{meta.get("title", "The Data API")} — The Local AI Stack'
    desc = meta.get("description", "")
    return page_shell(title, desc, body, depth=API_DEPTH,
                      guides_menu=guides_menu)
