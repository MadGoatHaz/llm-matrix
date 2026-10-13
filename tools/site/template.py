"""The shared page shell: ``<head>`` (title, description, OG tags), nav, footer.

Every generated document is assembled by :func:`page_shell`. The shell is
*depth-aware*: it computes the correct relative prefix (``""`` / ``../`` /
``../../``) for the CSS/JS assets and every nav link, so the exact same shell
works from a root page (``index.html``) and from a nested guide page
(``guides/<slug>/index.html``).

The nav carries a *Guides dropdown slot* (``guides_menu``). In this phase the
slot is unused (``None``), which renders the plain ``Guides`` link — keeping
the five legacy pages byte-identical. Phase P1-9 populates the slot.
"""

from __future__ import annotations

from .utils import FORUM_THREAD, GITHUB_REPO, html_escape

# ---------------------------------------------------------------------------
# OG tags (identical on every page)
# ---------------------------------------------------------------------------

OG_TAGS = '''    <meta property="og:title" content="The Local AI Stack — Models, Hardware, Backends &amp; Community Data">
    <meta property="og:description" content="A community-driven guide to running AI models on your own hardware. Browse the matrix, explore guides, and see what the community is running.">
    <meta property="og:url" content="https://madgoathaz.github.io/llm-matrix/">
    <meta property="og:type" content="website">
    <meta property="og:image" content="https://madgoathaz.github.io/llm-matrix/og-image.png">'''

# ---------------------------------------------------------------------------
# Footer (shared by every page)
# ---------------------------------------------------------------------------

def footer(depth: int = 0) -> str:
    """The shared site footer.

    Depth-aware: the Data API link is relative (``api/``) and needs the
    page's asset prefix; the forum / GitHub / CONTRIBUTING links are
    absolute.
    """
    p = asset_prefix(depth)
    return f'''  <footer class="footer">
    <div>The Local AI Stack — data from the <a href="{FORUM_THREAD}">Local LLM Matrix thread</a> on Level1Techs · <a href="{GITHUB_REPO}">GitHub</a> · <a href="{p}api/">Data API</a> · <a href="{p}changelog/">Changelog</a> · <a href="{GITHUB_REPO}/blob/main/CONTRIBUTING.md" target="_blank" rel="noopener">Contribute</a></div>
    <div class="forum-credit">Not an official Level1Techs project. All data is community-reported — check the thread for context.</div>
  </footer>'''


def asset_prefix(depth: int) -> str:
    """Relative prefix to reach repo-root assets from a page ``depth`` deep.

    >>> asset_prefix(0)   # index.html at the repo root
    ''
    >>> asset_prefix(1)   # guides/index.html
    '../'
    >>> asset_prefix(2)   # guides/quantization/index.html
    '../../'
    """
    return "../" * max(0, int(depth))


def _guides_dropdown(p: str, guides_menu: list[tuple[str, str]]) -> str:
    """Render the Guides nav item as a dropdown (the P1-9 slot).

    Args:
        p: The asset prefix for the current page depth.
        guides_menu: ``(label, url)`` pairs for each guide.

    Returns:
        The ``<li>`` markup for a hover/click dropdown. Only used when a
        ``guides_menu`` is supplied; the P1-0 default nav never calls this.
    """
    items = "\n".join(
        f'            <li><a href="{p}{url}">{html_escape(label)}</a></li>'
        for label, url in guides_menu
    )
    # The toggle is a disclosure: aria-expanded/aria-controls (updated by
    # js/main.js) make the state machine explicit for screen readers. The
    # ▾ glyph is decorative (hidden from the a11y tree).
    return (
        '        <li class="nav-dropdown">\n'
        '          <a href="' + p + 'guides/" class="nav-dropdown-toggle" '
        'aria-expanded="false" aria-controls="guides-menu">'
        'Guides <span class="icon" aria-hidden="true">▾</span></a>\n'
        '          <ul class="nav-dropdown-menu" id="guides-menu">\n'
        + items + '\n          </ul>\n'
        '        </li>'
    )


def nav(depth: int = 0, guides_menu: list[tuple[str, str]] | None = None) -> str:
    """The shared top navigation.

    Args:
        depth: Directory depth of the page (drives the link prefix).
        guides_menu: Optional ``(label, url)`` list for the Guides dropdown.
            ``None`` (the P1-0 default) renders the plain ``Guides`` link.

    Returns:
        The ``<nav>`` HTML block.
    """
    p = asset_prefix(depth)
    if guides_menu:
        guides_item = _guides_dropdown(p, guides_menu)
    else:
        guides_item = f'        <li><a href="{p}guides.html">Guides</a></li>'
    return f'''  <nav class="nav" aria-label="Main navigation">
    <div class="nav-inner">
      <a href="{p}index.html" class="nav-logo"><span class="icon" aria-hidden="true">📊</span> Local AI <span>Stack</span></a>
      <button class="nav-toggle" aria-label="Toggle navigation" aria-expanded="false" aria-controls="nav-links">☰</button>
      <ul class="nav-links" id="nav-links">
        <li><a href="{p}index.html">Home</a></li>
        <li><a href="{p}matrix.html">Matrix</a></li>
        <li><a href="{p}compare/">Compare</a></li>
        <li><a href="{p}recommend/">Recommend</a></li>
        <li><a href="{p}community.html">Community</a></li>
        <li><a href="{p}submit/">Submit</a></li>
        <li><a href="{GITHUB_REPO}/blob/main/CONTRIBUTING.md" target="_blank" rel="noopener">Contribute</a></li>
{guides_item}
        <li><a href="{p}about.html">About</a></li>
      </ul>
    </div>
  </nav>'''


def page_shell(title: str, description: str, body: str,
              depth: int = 0,
              guides_menu: list[tuple[str, str]] | None = None,
              extra_scripts: list[str] | None = None) -> str:
    """Assemble a complete HTML document around ``body``.

    Args:
        title: The ``<title>`` text (HTML-escaped).
        description: The meta description (HTML-escaped).
        body: The page's inner HTML (inside ``<main>``).
        depth: Directory depth of the output page (0 = repo root).
        guides_menu: Optional Guides-dropdown entries (see :func:`nav`).
        extra_scripts: Optional list of extra ``<script src>`` paths (relative
            to the repo root, e.g. ``"js/recommend.js"``). Each is prefixed with
            the depth-relative asset path and emitted after ``js/main.js``.
            ``None`` (the default) keeps the single-``main.js`` shell so the
            legacy pages stay byte-identical.

    Returns:
        The full ``<!DOCTYPE html>`` document as a string.
    """
    p = asset_prefix(depth)
    # All scripts are deferred: they sit at the end of <body> (already
    # non-render-blocking) and defer makes the intent explicit + guarantees
    # ordered execution after the document is parsed (P2-7).
    scripts = [f'<script src="{p}js/main.js" defer></script>']
    for s in (extra_scripts or []):
        scripts.append(f'<script src="{p}{s}" defer></script>')
    scripts_html = "\n".join(scripts)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="theme-color" content="#0a0e17">
    <title>{html_escape(title)}</title>
    <meta name="description" content="{html_escape(description)}">
{OG_TAGS}
    <link rel="stylesheet" href="{p}css/style.css">
</head>
<body>
<a class="skip-link" href="#main-content">Skip to content</a>
{nav(depth, guides_menu)}
<main class="container" id="main-content">
{body}
</main>
{footer(depth)}
{scripts_html}
</body>
</html>
'''
