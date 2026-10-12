"""``matrix.html`` — the data table.

A filterable, sortable table of every real submission, grouped under VRAM-tier
headers. Cells render the full value and rely on CSS ellipsis + a ``title``
tooltip for overflow (no Python-side string slicing).
"""

from __future__ import annotations

from .. import utils
from ..template import page_shell

#: Column order for the table (also the ``colspan`` for tier headers).
MATRIX_COLUMNS = [
    "Contributor", "Hardware", "Vendor", "Backend", "Model", "Quant",
    "Use Case", "Speed", "Context", "KV", "Power", "Mode",
]


def td(value) -> str:
    """A table cell: full escaped value with a matching hover tooltip."""
    v = utils.html_escape(utils.clean_value(value))
    return f'<td title="{v}">{v}</td>'


def render(subs: list[dict], schema: dict, stats: dict,
           guides_menu: list[tuple[str, str]] | None = None) -> str:
    """Render the matrix document.

    Args:
        subs: Real (non-template) submissions.
        schema: The parsed ``schema.json`` (provides the tier list).
        stats: Headline counts from :func:`tools.site.utils.compute_stats`.

    Returns:
        The full ``matrix.html`` document.
    """
    tiers = schema.get("tiers", [])
    labels = {t["id"]: t["label"] for t in tiers}

    # --- Filter options ---
    vendor_set = set()
    backend_set = set()
    for s in subs:
        v = utils.hw(s).get("vendor", "")
        if v and not utils.is_placeholder(v):
            vendor_set.add(v)
        b = utils.normalize_backend(s.get("backend", ""), schema)
        if b:
            backend_set.add(b)

    tier_opts = "".join(
        f'<option value="{utils.html_escape(t["id"])}">{utils.html_escape(t["label"])}</option>'
        for t in tiers)
    vendor_opts = "".join(
        f'<option value="{utils.html_escape(v)}">{utils.html_escape(v)}</option>'
        for v in sorted(vendor_set))
    backend_opts = "".join(
        f'<option value="{utils.html_escape(b)}">{utils.html_escape(b)}</option>'
        for b in sorted(backend_set))

    # --- Table body: tier groups ---
    body_rows = []
    for tier_id, _label, tier_subs in utils.group_by_tier(subs, tiers):
        body_rows.append(
            f'        <tr class="tier-header" data-tier="{utils.html_escape(tier_id)}">'
            f'<td colspan="{len(MATRIX_COLUMNS)}">{utils.html_escape(labels.get(tier_id, tier_id))}</td></tr>'
        )
        for s in tier_subs:
            highlight = ' highlighted' if s.get("highlight") else ''
            vendor = utils.clean_value(utils.hw(s).get("vendor"))
            backend = utils.normalize_backend(s.get("backend", ""), schema)
            body_rows.append(f'''        <tr class="{utils.html_escape(tier_id)}{highlight}" data-tier="{utils.html_escape(tier_id)}" data-vendor="{utils.html_escape(vendor)}" data-backend="{utils.html_escape(backend)}">
          {td(s["source"]["username"])}
          {td(utils.hw(s).get("description"))}
          {td(utils.hw(s).get("vendor"))}
          {td(s.get("backend"))}
          {td(utils.model_name(s))}
          {td(s.get("quant"))}
          {td(s.get("use_cases"))}
          {td(utils.perf(s).get("decode_tps"))}
          {td(utils.ctx(s).get("stable"))}
          {td(utils.ctx(s).get("kv_cache"))}
          {td(utils.perf(s).get("power_w"))}
          {td(s.get("engine_mode"))}
        </tr>''')

    header_cells = "".join(f"<th>{c}</th>" for c in MATRIX_COLUMNS)

    updated = schema.get("last_updated", "")
    body = f'''
  <div class="page-header">
    <h1>The Matrix</h1>
    <p class="subtitle">All community submissions, filterable and sortable</p>
    <p class="meta">{stats["submissions"]} submissions · {stats["contributors"]} contributors · {stats["vendors"]} vendors · {stats["backends"]} backends · updated {utils.html_escape(updated)}</p>
  </div>

  <div class="filter-bar">
    <input type="text" id="filter-search" placeholder="Search models, hardware, backends...">
    <select class="filter-select" data-filter="tier">
      <option value="">All Tiers</option>
      {tier_opts}
    </select>
    <select class="filter-select" data-filter="vendor">
      <option value="">All Vendors</option>
      {vendor_opts}
    </select>
    <select class="filter-select" data-filter="backend">
      <option value="">All Backends</option>
      {backend_opts}
    </select>
    <button id="filter-reset" class="btn">Reset</button>
  </div>

  <div class="table-wrapper">
    <table id="data-table">
      <thead>
        <tr>{header_cells}</tr>
      </thead>
      <tbody>
{chr(10).join(body_rows)}
      </tbody>
    </table>
  </div>

  <div class="card">
    <h3>ℹ️ Reading the matrix</h3>
    <p>Click any column header to sort (within each tier). Cells show the full value on hover.
       <strong>Speed</strong> is community-reported decode throughput; <strong>Context</strong> is the
       stable context tested; <strong>KV</strong> is the KV-cache precision; <strong>Mode</strong> is how the
       engine splits weights across VRAM/RAM/SSD. All data is community-reported — treat numbers as
       user-experienced, not lab-tested. <a href="{utils.FORUM_THREAD}">Discussion lives in the forum thread →</a></p>
  </div>'''

    title = "The Matrix — The Local AI Stack"
    desc = ("All community submissions, filterable and sortable: VRAM tier, hardware, vendor, "
            "backend, model, quant, use case, speed, context, KV cache, power, engine mode.")
    return page_shell(title, desc, body, guides_menu=guides_menu)
