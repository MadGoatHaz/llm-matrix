"""``about.html`` — about the project.

Static content: what it is, how it works, the connection to Level1Techs,
how to contribute, and credits.
"""

from __future__ import annotations

from .. import utils
from ..template import page_shell


def render(guides_menu: list[tuple[str, str]] | None = None) -> str:
    """Render the about document.

    Returns:
        The full ``about.html`` document.
    """
    body = f'''
  <div class="page-header">
    <h1>About The Local AI Stack</h1>
    <p class="subtitle">A community-driven resource for running AI models on your own hardware</p>
  </div>

  <div class="card">
    <h2>{utils.icon("📖")} What It Is</h2>
    <p>A community-driven resource for running AI models on your own hardware. Born from the
       Level1Techs forum, built for the broader local AI community.</p>
  </div>

  <div class="card">
    <h2>{utils.icon("🔄")} How It Works</h2>
    <p>Community members submit their setups. We parse, organize, and display the data. The more
       submissions, the better the resource.</p>
  </div>

  <div class="card">
    <h2>{utils.icon("🤝")} Connection to L1Techs</h2>
    <p>This project originated in the <a href="{utils.FORUM_CATEGORY}">Machine Learning, LLMs &amp; AI category</a>
       on <a href="https://forum.level1techs.com">Level1Techs</a>. The forum thread is where the
       discussion happens — this site is where the reference lives.</p>
  </div>

  <div class="card">
    <h2>{utils.icon("✍️")} How to Contribute</h2>
    <p>Three free paths: the <a href="submit/">submission form</a> (30 seconds, no account),
       a <a href="{utils.GITHUB_REPO}/issues/new?template=submission.yml" target="_blank" rel="noopener">GitHub issue</a>,
       or the <a href="{utils.FORUM_THREAD}">forum thread</a>. What makes a great entry, how to run the
       pipeline, and the PR process are all written down in
       <a href="{utils.GITHUB_REPO}/blob/main/CONTRIBUTING.md" target="_blank" rel="noopener">CONTRIBUTING.md</a>.</p>
  </div>

  <div class="card">
    <h2>{utils.icon("🔌")} The Data API</h2>
    <p>Every dataset the site shows is published as <a href="api/">stable, versioned JSON</a> —
       fetch <code>data.json</code> from your own scripts or sites, validate it against the
       <a href="api/v1/schema.json">JSON Schema</a>, and build your own tools on the community's data.</p>
  </div>

  <div class="card">
    <h2>{utils.icon("👤")} Credits</h2>
    <p>Built and maintained by <a href="https://forum.level1techs.com/u/MadGoat">MadGoat</a> with
       data from the L1Techs community.</p>
    <p><a href="{utils.GITHUB_REPO}">GitHub →</a></p>
  </div>'''

    title = "About — The Local AI Stack"
    desc = ("About The Local AI Stack — a community-driven resource for running AI models on your "
            "own hardware, born from the Level1Techs forum.")
    return page_shell(title, desc, body, guides_menu=guides_menu)
