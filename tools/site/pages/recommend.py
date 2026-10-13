"""``recommend/index.html`` — the recommendation engine (P2-1).

Answers the site's core question — "what should I run, on what I have, for
what I need?" — with a fully client-side tool. The page carries:

* the explainer copy from ``content/recommend.md``;
* an interactive form (VRAM tier required; use case / vendor / priority
  optional) using progressive disclosure (the advanced options sit in a
  collapsible ``<details>``);
* a **config island** (``<script type="application/json"
  id="recommend-config">``) that embeds the schema's tier / use-case / vendor
  lists, so the client needs no extra network request for them;
* a results container that ``js/recommend.js`` fills by ranking the sibling
  ``#commands-config`` island (the baked submissions) — no network request,
  so the page works offline straight from disk (file://).

The page lives at ``recommend/index.html`` (depth 1) and loads the extra
``js/recommend.js`` after the shared ``js/main.js``.
"""

from __future__ import annotations

from pathlib import Path

from .. import markdown as md
from .. import utils
from ..template import page_shell

#: The recommendation page is one level below the repo root.
RECOMMEND_DEPTH = 1


def _config_island(schema: dict) -> str:
    """Embed the schema's pick-lists as a JSON island for the client.

    The client ranks the sibling ``#commands-config`` island (the baked
    submissions) and needs the canonical tier / use-case / vendor lists.
    Baking them in at generation time means the whole tool runs fully
    client-side — no network request for the schema and none for the data.
    The payload is compact (P2-7) and brace-safe for the template-leak check
    via :func:`utils.compact_json`.
    """
    config = {
        "tiers": schema.get("tiers", []),
        "use_cases": schema.get("use_cases", []),
        "vendors": schema.get("hardware_vendors", []),
    }
    payload = utils.compact_json(config)
    return (
        '  <script type="application/json" id="recommend-config">\n'
        f"{payload}\n"
        "  </script>"
    )


def _tier_options(schema: dict) -> str:
    opts = ['        <option value="" disabled selected>Select your VRAM…</option>']
    for t in schema.get("tiers", []):
        opts.append(
            f'        <option value="{utils.html_escape(t["id"])}">'
            f'{utils.html_escape(t["label"])}</option>'
        )
    return "\n".join(opts)


def _use_case_options(schema: dict) -> str:
    opts = ['        <option value="">Any use</option>']
    for u in schema.get("use_cases", []):
        opts.append(
            f'        <option value="{utils.html_escape(u)}">{utils.html_escape(u)}</option>'
        )
    return "\n".join(opts)


def _vendor_options(schema: dict) -> str:
    opts = ['        <option value="">Doesn\'t matter</option>']
    for v in schema.get("hardware_vendors", []):
        opts.append(
            f'        <option value="{utils.html_escape(v)}">{utils.html_escape(v)}</option>'
        )
    return "\n".join(opts)


def render(subs: list[dict], schema: dict, content_dir: Path,
           guides_menu: list[tuple[str, str]] | None = None) -> str:
    """Render the recommendation page document.

    Args:
        subs: Real (non-template) submissions (baked into the
            ``#commands-config`` island for the launch-command generator).
        schema: The parsed ``schema.json`` (tiers, use cases, vendors).
        content_dir: The authored-content directory (``content/``); the
            explainer is read from ``content_dir/recommend.md``.
        guides_menu: Optional ``(label, url)`` list for the nav dropdown.

    Returns:
        The full ``recommend/index.html`` document (depth 1).

    Raises:
        FileNotFoundError: if ``content/recommend.md`` does not exist.
    """
    md_path = content_dir / "recommend.md"
    meta, body_md = md.split_front_matter(md_path.read_text(encoding="utf-8"))
    intro_html = md.render_markdown(body_md)

    form_html = f'''
  <section class="recommend-tool" aria-labelledby="rec-tool-title">
    <h2 id="rec-tool-title" class="section-title">{utils.icon("🎯")} What should you run?</h2>
    <form class="rec-form" id="rec-form" autocomplete="off">
      <div class="rec-field rec-field--primary">
        <label for="rec-tier">How much video memory (VRAM) does your GPU have?</label>
        <select id="rec-tier" name="tier">
{_tier_options(schema)}
        </select>
      </div>

      <details class="rec-advanced">
        <summary>More options <span class="rec-advanced-hint">(optional — refine your results)</span></summary>
        <div class="rec-advanced-body">
          <div class="rec-field">
            <label for="rec-usecase">What do you want to do with it?</label>
            <select id="rec-usecase" name="use_case">
{_use_case_options(schema)}
            </select>
          </div>
          <div class="rec-field">
            <label for="rec-vendor">Which GPU vendor do you have?</label>
            <select id="rec-vendor" name="vendor">
{_vendor_options(schema)}
            </select>
          </div>
          <div class="rec-field">
            <label for="rec-priority">What matters most to you?</label>
            <select id="rec-priority" name="priority">
              <option value="balanced" selected>Balanced (a bit of everything)</option>
              <option value="speed">Speed — tokens per second</option>
              <option value="quality">Quality — model precision</option>
              <option value="context">Context — how much it can remember</option>
            </select>
          </div>
        </div>
      </details>
    </form>

    <div class="rec-results" id="rec-results" role="status" aria-live="polite">
      <div class="rec-placeholder">
        <p>Pick your VRAM above and the community's best fits will appear here.</p>
      </div>
    </div>
  </section>'''

    how_html = '''
  <section class="recommend-how" aria-labelledby="rec-how-title">
    <h2 id="rec-how-title" class="section-title">How the ranking works</h2>
    <div class="card">
      <p><strong>Fit first.</strong> Results are filtered to your VRAM class — a setup only appears if its estimated VRAM fits within your card. A setup in your class may still need tuning to fit your exact card, so check the VRAM estimate in the details.</p>
      <p><strong>Then your needs.</strong> Pick a use case and we match it against what each setup was actually used for. Pick a vendor and matching hardware ranks higher. Your priority (speed / quality / context) sets the main sort order.</p>
      <p><strong>Always honest.</strong> Every card is a real community submission with a plain-English "why this matched." The numbers are community-reported, not lab-tested — a starting point, not a guarantee.</p>
    </div>
  </section>'''

    body = f'''
  <div class="page-header">
    <h1>Find Your Model</h1>
    <p class="subtitle">Tell us what you have and what you need — we'll rank the community's real fits.</p>
  </div>

{intro_html}
{form_html}
{how_html}
{_config_island(schema)}
{utils.commands_config_island(subs, schema)}'''

    title = f'{meta.get("title", "Find Your Model")} — The Local AI Stack'
    desc = meta.get("description", "")
    return page_shell(title, desc, body, depth=RECOMMEND_DEPTH,
                      guides_menu=guides_menu,
                      extra_scripts=["js/recommend.js", "js/commands.js"])
