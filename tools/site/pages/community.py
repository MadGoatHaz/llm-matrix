"""``community.html`` — the contributor showcase.

One card per contributor (avatar initial, submission count, and the setups
they've submitted), plus a call-to-action linking back to the forum thread.
The setup lists are filterable (the same URL-synced axes as the Matrix:
tier / vendor / backend / use case / engine mode / search).
"""

from __future__ import annotations

from .. import utils
from ..template import page_shell


def render(subs: list[dict], schema: dict, stats: dict,
           guides_menu: list[tuple[str, str]] | None = None) -> str:
    """Render the community document.

    Args:
        subs: Real (non-template) submissions.
        schema: The parsed ``schema.json`` (filter option lists + the
            use-case keyword map).
        stats: Headline counts from :func:`tools.site.utils.compute_stats`.

    Returns:
        The full ``community.html`` document.
    """
    cards = []
    for username, user_subs in utils.group_by_contributor(subs):
        initial = (username[:1] or "?").upper()
        n = len(user_subs)
        role = f"{n} submission{'s' if n != 1 else ''}"

        items = []
        for s in user_subs:
            vendor = utils.clean_value(utils.hw(s).get("vendor"))
            backend = utils.normalize_backend(s.get("backend", ""), schema)
            use_case = utils.match_use_cases(s.get("use_cases"), schema)
            use_case_attr = use_case[0] if use_case else ''
            mode = utils.clean_value(s.get("engine_mode"))
            parts = [f'<strong>{utils.html_escape(utils.short_model(utils.model_name(s)))}</strong>']
            hw_desc = utils.clean_value(utils.hw(s).get("description"))
            speed = utils.clean_value(utils.perf(s).get("decode_tps"))
            if hw_desc:
                parts.append(f" — {utils.html_escape(hw_desc)}")
            if speed:
                parts.append(f" · {utils.html_escape(speed)}")
            items.append(
                f'          <li data-sub-id="{utils.html_escape(s["id"])}" '
                f'data-tier="{utils.html_escape(s.get("tier", ""))}" '
                f'data-vendor="{utils.html_escape(vendor)}" '
                f'data-backend="{utils.html_escape(backend)}" '
                f'data-use-case="{utils.html_escape(use_case_attr)}" '
                f'data-mode="{utils.html_escape(mode)}">'
                + "".join(parts) + "</li>")
        setup_list = (
            '          <ul class="setup-list">\n' + "\n".join(items) + "\n          </ul>"
            if items else '          <ul class="setup-list"><li>See the matrix</li></ul>')

        cards.append(f'''
    <div class="contributor-card">
      <div class="contributor-header">
        <div class="avatar">{utils.html_escape(initial)}</div>
        <div>
          <div class="contributor-name">{utils.html_escape(username)}</div>
          <div class="contributor-role">{utils.html_escape(role)}</div>
        </div>
      </div>
{setup_list}
    </div>''')

    # --- Filter options (same axes as the Matrix, P2-4) ---
    tier_opts = "".join(
        f'<option value="{utils.html_escape(t["id"])}">{utils.html_escape(t["label"])}</option>'
        for t in schema.get("tiers", []))
    vendor_set = set()
    backend_set = set()
    for s in subs:
        v = utils.hw(s).get("vendor", "")
        if v and not utils.is_placeholder(v):
            vendor_set.add(v)
        b = utils.normalize_backend(s.get("backend", ""), schema)
        if b:
            backend_set.add(b)
    vendor_opts = "".join(
        f'<option value="{utils.html_escape(v)}">{utils.html_escape(v)}</option>'
        for v in sorted(vendor_set))
    backend_opts = "".join(
        f'<option value="{utils.html_escape(b)}">{utils.html_escape(b)}</option>'
        for b in sorted(backend_set))
    use_case_opts = "".join(
        f'<option value="{utils.html_escape(c)}">{utils.html_escape(c)}</option>'
        for c in schema.get("use_cases", []) if c != "Other")
    mode_opts = "".join(
        f'<option value="{utils.html_escape(m)}">{utils.html_escape(m)}</option>'
        for m in schema.get("engine_modes", []))

    body = f'''
  <div class="page-header">
    <h1>The Community</h1>
    <p class="subtitle">The people behind the data</p>
    <p class="meta">{stats["contributors"]} contributors · {stats["submissions"]} submissions</p>
  </div>

  <div class="filter-bar" role="group" aria-label="Filter submissions">
    <input type="text" id="filter-search" placeholder="Search models, hardware, backends..." aria-label="Search submissions">
    <select class="filter-select" data-filter="tier" aria-label="Filter by VRAM tier">
      <option value="">All Tiers</option>
      {tier_opts}
    </select>
    <select class="filter-select" data-filter="vendor" aria-label="Filter by GPU vendor">
      <option value="">All Vendors</option>
      {vendor_opts}
    </select>
    <select class="filter-select" data-filter="backend" aria-label="Filter by backend">
      <option value="">All Backends</option>
      {backend_opts}
    </select>
    <select class="filter-select" data-filter="use-case" aria-label="Filter by use case">
      <option value="">All Use Cases</option>
      {use_case_opts}
    </select>
    <select class="filter-select" data-filter="mode" aria-label="Filter by engine mode">
      <option value="">All Engine Modes</option>
      {mode_opts}
    </select>
    <button id="filter-reset" class="btn" type="button">Reset</button>
    <button id="filter-share" class="btn" type="button" aria-label="Copy a shareable link to the current filters">🔗 Share</button>
  </div>

  <div class="filter-empty" id="filter-empty" role="status" hidden>
    <p>🔍 No setups match the current filters.</p>
    <button class="btn" id="filter-empty-clear" type="button">Clear all filters</button>
  </div>

  <div class="card-grid" id="contributor-grid">
{chr(10).join(cards)}
  </div>

  <div class="card">
    <h3>🙌 Want to be here?</h3>
    <p>Submit your setup in the <a href="{utils.FORUM_THREAD}">forum thread</a> using the Quick Submit
       template in Post #2. It takes 30 seconds, and your data appears in the matrix on the next
       update. Every row in <a href="matrix.html">the matrix</a> started exactly this way.</p>
    <p><a href="{utils.FORUM_THREAD}" class="btn btn-primary">Submit your setup →</a></p>
  </div>'''

    title = "Community — The Local AI Stack"
    desc = ("The people behind the data. A showcase of every contributor to the Local AI Stack "
            "and the setups they run.")
    return page_shell(title, desc, body, guides_menu=guides_menu)
