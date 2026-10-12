"""``community.html`` — the contributor showcase.

One card per contributor (avatar initial, submission count, and the setups
they've submitted), plus a call-to-action linking back to the forum thread.
"""

from __future__ import annotations

from .. import utils
from ..template import page_shell


def render(subs: list[dict], schema: dict, stats: dict) -> str:
    """Render the community document.

    Args:
        subs: Real (non-template) submissions.
        schema: The parsed ``schema.json`` (unused directly; kept for a
            uniform renderer signature).
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
            parts = [f'<strong>{utils.html_escape(utils.short_model(utils.model_name(s)))}</strong>']
            hw_desc = utils.clean_value(utils.hw(s).get("description"))
            speed = utils.clean_value(utils.perf(s).get("decode_tps"))
            if hw_desc:
                parts.append(f" — {utils.html_escape(hw_desc)}")
            if speed:
                parts.append(f" · {utils.html_escape(speed)}")
            items.append("          <li>" + "".join(parts) + "</li>")
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

    body = f'''
  <div class="page-header">
    <h1>The Community</h1>
    <p class="subtitle">The people behind the data</p>
    <p class="meta">{stats["contributors"]} contributors · {stats["submissions"]} submissions</p>
  </div>

  <div class="card-grid">
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
    return page_shell(title, desc, body)
