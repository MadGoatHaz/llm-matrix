"""``index.html`` — the homepage.

Hero, headline stats, the data-driven Community Highlights (trending models,
popular backends, fastest setups), How It Works, and Related Resources.
"""

from __future__ import annotations

from .. import utils
from ..template import page_shell


def render(subs: list[dict], schema: dict, stats: dict) -> str:
    """Render the homepage document.

    Args:
        subs: Real (non-template) submissions.
        schema: The parsed ``schema.json``.
        stats: Headline counts from :func:`tools.site.utils.compute_stats`.

    Returns:
        The full ``index.html`` document.
    """
    # --- Stats row ---
    stats_html = '''
  <div class="stats-row">
    <div class="stat-card"><div class="value">{submissions}</div><div class="label">Submissions</div></div>
    <div class="stat-card"><div class="value">{contributors}</div><div class="label">Contributors</div></div>
    <div class="stat-card"><div class="value">{vendors}</div><div class="label">Hardware Vendors</div></div>
    <div class="stat-card"><div class="value">{backends}</div><div class="label">Backends</div></div>
  </div>'''.format(**stats)

    # --- Community Highlights (all data-driven, from submissions.json) ---

    # Trending Models: top 3 model families by submission count.
    trend_cards = []
    for fam, count, note in utils.trending_models(subs, n=3):
        trend_cards.append(f'''
    <div class="card">
      <h3>🔥 {utils.html_escape(fam)}</h3>
      <p><span class="badge badge-blue">{count} submission{'s' if count != 1 else ''}</span></p>
      <p class="mono">{utils.html_escape(note)}</p>
    </div>''')
    trend_html = (
        f'\n  <div class="card-grid">\n{chr(10).join(trend_cards)}\n  </div>'
        if trend_cards else "")

    # Popular Backends: top 3 backends by usage.
    backend_items = []
    for backend, count in utils.popular_backends(subs, schema, n=3):
        backend_items.append(
            f'    <div class="stat-card"><div class="value">{count}</div>'
            f'<div class="label">{utils.html_escape(backend)}</div></div>')
    backend_html = (
        f'\n  <div class="stats-row">\n{chr(10).join(backend_items)}\n  </div>'
        if backend_items else "")

    # Fastest Setups: top 3 submissions by decode speed.
    fast_cards = []
    for username, model, speed, hardware in utils.fastest_setups(subs, n=3):
        fast_cards.append(f'''
    <div class="card">
      <h3>⚡ {speed:g} t/s</h3>
      <p>{utils.html_escape(utils.short_model(model))}</p>
      <p class="mono">{utils.html_escape(utils.clean_value(hardware))}</p>
      <p>by <strong>{utils.html_escape(username)}</strong> · <a href="matrix.html">See in the matrix →</a></p>
    </div>''')
    fast_html = (
        f'\n  <div class="card-grid">\n{chr(10).join(fast_cards)}\n  </div>'
        if fast_cards else "")

    highlights_html = f'''
  <section>
    <h2 class="section-title">🏆 Community Highlights</h2>

    <h3 style="margin: 1rem 0 0.5rem; color: var(--text-secondary); font-size: 0.9rem; text-transform: uppercase;">Trending Models</h3>
{trend_html}

    <h3 style="margin: 1.5rem 0 0.5rem; color: var(--text-secondary); font-size: 0.9rem; text-transform: uppercase;">Popular Backends</h3>
{backend_html}

    <h3 style="margin: 1.5rem 0 0.5rem; color: var(--text-secondary); font-size: 0.9rem; text-transform: uppercase;">Fastest Setups</h3>
{fast_html}
  </section>'''

    # --- How It Works (kept as-is) ---
    how_html = '''
  <h2 class="section-title">🔄 How It Works</h2>
  <div class="card-grid">
    <div class="card">
      <h3>1. 📝 Submit</h3>
      <p>Head to the <a href="''' + utils.FORUM_THREAD + '''">forum thread</a> and use the Quick Submit template in Post #2. 30 seconds: tier, hardware, model, speed.</p>
    </div>
    <div class="card">
      <h3>2. ⚙️ We Parse</h3>
      <p>The pipeline pulls the thread, parses every submission, and organizes it by VRAM tier, hardware vendor, backend, and model.</p>
    </div>
    <div class="card">
      <h3>3. 📊 You Browse</h3>
      <p>Filter the matrix by your hardware. See exactly what the community runs, at what speed, in what context.</p>
    </div>
  </div>'''

    # --- Related Resources (curated community links) ---
    related_html = '''
  <section>
    <h2 class="section-title">🔗 Related Resources</h2>
    <div class="card-grid">
      <a class="guide-card" href="https://forum.level1techs.com/t/crucible-llm-bench-your-llm-and-server-is-it-fast-enough-for-everyone/257531">
        <div class="guide-icon">⚗️</div>
        <h3>Crucible: LLM Bench</h3>
        <p>Benchmark your LLM server. Is it fast enough for everyone? Community-driven performance testing.</p>
        <div class="guide-meta">L1Techs Thread</div>
      </a>
      <a class="guide-card" href="https://forum.level1techs.com/t/post-show-off-your-ai-rig-whatchya-got-in-there/255709">
        <div class="guide-icon">🖥️</div>
        <h3>Show Off Your AI Rig</h3>
        <p>The community hardware showcase. What are people building? 40+ rigs and counting.</p>
        <div class="guide-meta">L1Techs Thread</div>
      </a>
      <a class="guide-card" href="https://forum.level1techs.com/c/high-performance-computing/deep-machine-learning-ai/155">
        <div class="guide-icon">🤖</div>
        <h3>ML, LLMs &amp; AI Category</h3>
        <p>The full L1Techs AI category. Benchmarks, guides, discussions, and results.</p>
        <div class="guide-meta">L1Techs Forum</div>
      </a>
      <a class="guide-card" href="https://forum.level1techs.com/t/256443">
        <div class="guide-icon">💬</div>
        <h3>This Project's Thread</h3>
        <p>The Local AI Stack — where the community submits data and discusses models.</p>
        <div class="guide-meta">L1Techs Thread</div>
      </a>
    </div>
  </section>'''

    body = f'''
  <section class="hero">
    <h1>The <span>Local AI Stack</span></h1>
    <p class="tagline">Your community-driven guide to running AI models on your own hardware</p>
    <div class="actions">
      <a href="matrix.html" class="btn-large btn-large-primary">Browse the Matrix →</a>
      <a href="guides.html" class="btn-large btn-large-secondary">Explore Guides →</a>
    </div>
  </section>

{stats_html}
{highlights_html}
{how_html}
{related_html}'''

    title = "The Local AI Stack — Community-Driven Local LLM Reference"
    desc = ("Your community-driven guide to running AI models on your own hardware. "
            "Browse the matrix, explore guides, and see what the community is running.")
    return page_shell(title, desc, body)
