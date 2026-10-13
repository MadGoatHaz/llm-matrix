"""``compare/index.html`` — the comparison view (P2-2).

Lets a reader line up 2–4 community submissions side by side with the
differing attributes highlighted. The page carries:

* a **picker** (four dropdowns of every submission) for when you arrive with
  no selection;
* a **diff table** (rows = attributes, columns = the selected setups) that
  ``js/compare.js`` fills by reading ``?a=&b=&c=&d=`` from the URL — so a
  comparison is a shareable deep link that restores on load;
* a short factual **takeaway** line (``aria-live``);
* a **launch-command** button per column (delegated to ``js/commands.js``);
* a **config island** (``#commands-config``) baking the trimmed submissions +
  the schema pick-lists, so the whole view runs client-side with no network
  request.

The page lives at ``compare/index.html`` (depth 1) and loads ``js/compare.js``
then ``js/commands.js`` after the shared ``js/main.js``.
"""

from __future__ import annotations

from .. import utils
from ..template import page_shell

#: The comparison page is one level below the repo root.
COMPARE_DEPTH = 1


def _picker() -> str:
    """The no-selection picker: four dropdowns + a Compare button.

    ``js/compare.js`` populates the ``<select>`` options from the
    ``#commands-config`` island and restores any ``?a=&b=…`` ids on load.
    """
    return '''
  <section class="compare-picker-card" id="compare-picker" aria-labelledby="compare-pick-title">
    <h2 id="compare-pick-title" class="section-title">Pick 2–4 setups to compare</h2>
    <p class="compare-pick-hint">Choose up to four submissions and we'll line them up side by side, highlighting exactly what's different. (Or tick 2–4 rows on the <a href="../matrix.html">Matrix</a> and hit Compare.)</p>
    <div class="compare-pick-grid">
      <select class="compare-pick" aria-label="Setup to compare 1"></select>
      <select class="compare-pick" aria-label="Setup to compare 2"></select>
      <select class="compare-pick" aria-label="Setup to compare 3"></select>
      <select class="compare-pick" aria-label="Setup to compare 4"></select>
    </div>
    <div class="compare-pick-actions">
      <button class="btn btn-primary compare-pick-go" type="button">Compare →</button>
    </div>
  </section>'''


def _table_area() -> str:
    """The takeaway line + (empty) diff-table wrapper + the B2/C3
    "Tradeoffs" paragraph + edit control.

    The Tradeoffs block (``#compare-tradeoffs``) is filled client-side by
    ``js/compare.js``: a short directional paragraph (3–5 sentences) stating
    which way each meaningful difference matters ("A is 2.3× faster decode
    than B, but uses 2× the VRAM"). It is hidden until a comparison is
    active and carries no overall winner.
    """
    return f'''
  <p class="compare-takeaway" id="compare-takeaway" role="status" aria-live="polite">Select at least 2 setups to compare them side by side.</p>
  <div class="table-wrapper compare-table-wrap is-hidden" id="compare-table-wrap"></div>
  <div class="compare-tradeoffs is-hidden" id="compare-tradeoffs">
    <h3 class="compare-tradeoffs-title">Tradeoffs</h3>
    <p class="compare-tradeoffs-text" id="compare-tradeoffs-text" aria-live="polite"></p>
  </div>
  <div class="compare-edit-row"><button class="btn" id="compare-edit" type="button" hidden>{utils.icon("✎")} Edit selection</button></div>'''


def render(subs: list[dict], schema: dict,
           guides_menu: list[tuple[str, str]] | None = None) -> str:
    """Render the comparison page document.

    Args:
        subs: Real (non-template) submissions.
        schema: The parsed ``schema.json`` (tiers, backends).
        guides_menu: Optional ``(label, url)`` list for the nav dropdown.

    Returns:
        The full ``compare/index.html`` document (depth 1).
    """
    intro = f'''
  <div class="page-header">
    <h1>Compare Setups</h1>
    <p class="subtitle">Line up 2–4 community submissions side by side — and see exactly where they differ.</p>
  </div>

  <div class="callout callout--info"><p><b>How it works:</b> each column is a real community submission. Values that <em>agree</em> stay plain; values that <em>differ</em> are tinted so the contrast jumps out. A green <b>▲ best</b> marks the leading value in each numeric row (speed, context, VRAM, power) when the lead is meaningful — close values are left uncrowned. Below the table, a short <strong>Tradeoffs</strong> paragraph states which way each difference matters ("2.3× faster decode, but 2× the VRAM"). Every column has a one-click <strong>launch command</strong> so you can try the setup on your own hardware. Your selection is a shareable URL — copy the address bar to send it to a friend.</p></div>'''

    body = f'''
{intro}
{_picker()}
{_table_area()}
{utils.commands_config_island(subs, schema)}'''

    title = "Compare Setups — The Local AI Stack"
    desc = ("Line up 2–4 community submissions side by side — model, hardware, VRAM, "
            "backend, quant, use case, speed, and notes — with the differences "
            "highlighted and a one-click launch command for each.")
    return page_shell(title, desc, body, depth=COMPARE_DEPTH,
                      guides_menu=guides_menu,
                      extra_scripts=["js/compare.js", "js/commands.js"])
