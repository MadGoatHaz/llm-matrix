"""``recommend/index.html`` — the recommendation engine (P2-1).

Answers the site's core question — "what should I run, on what I have, for
what I need?" — with a fully client-side tool. The page carries:

* the explainer copy from ``content/recommend.md``;
* a **"Start Here" 3-step wizard** (C1) — big tappable cards that ask
  "what do you have / want to do / matters most" and feed the form below —
  skippable via "Skip to advanced options";
* an interactive form (VRAM tier required; use case / vendor / priority
  optional) using progressive disclosure (the advanced options sit in a
  collapsible ``<details>``);
* a **config island** (``<script type="application/json"
  id="recommend-config">``) that embeds the schema's tier / use-case / vendor
  lists, so the client needs no extra network request for them;
* a results container that ``js/recommend.js`` fills by ranking the sibling
  ``#commands-config`` island (the baked submissions) — no network request,
  so the page works offline straight from disk (file://).

The wizard (``js/wizard.js``) writes straight into the form's own controls
and fires their existing change handlers — the engine sees one path, not
two. After the wizard completes (or is skipped), a "Refine your search"
link opens the advanced options and "Start over" resets the wizard.

The page lives at ``recommend/index.html`` (depth 1) and loads the extra
``js/recommend.js`` + ``js/wizard.js`` after the shared ``js/main.js``.
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


def _wizard_card(icon: str, title: str, desc: str, value: str) -> str:
    """One tappable wizard card.

    The card is a real ``<button>`` (keyboard operable, focusable). Its
    accessible name is the visible title + description; the emoji ``icon``
    is decorative (``aria-hidden``). ``value`` is written into the form
    control by ``js/wizard.js`` (``""`` = "no filter / manual entry").
    """
    return (
        f'        <button type="button" class="wizard-card" data-value="{utils.html_escape(value)}">\n'
        f'          <span class="icon" aria-hidden="true">{icon}</span>\n'
        f'          <span class="wizard-card-title">{utils.html_escape(title)}</span>\n'
        f'          <span class="wizard-card-desc">{utils.html_escape(desc)}</span>\n'
        '        </button>'
    )


def _wizard_html() -> str:
    """The "Start Here" 3-step wizard (C1), shown before the form.

    Three taps set the form's own controls (``js/wizard.js``):

    * **Step 1 — "What do you have?"** maps plain hardware to a VRAM tier,
      conservatively (a tap never promises more VRAM than the card
      describes): gaming → t2, high-end → t3, multi-GPU/server → t5,
      Mac → t2 (unified memory). "Not sure" skips to manual entry.
    * **Step 2 — "What do you want to do?"** maps goals to the schema's
      use-case categories: chat → General Chat, code/agents → Agentic
      Coding, documents → RAG. "Just exploring" applies no filter.
    * **Step 3 — "What matters most to you?"** sets the priority (the
      engine's main sort key): speed / quality / context / balanced.

    Each step heading carries ``tabindex="-1"`` so ``js/wizard.js`` can move
    focus to it on entry (screen readers announce the new step). The
    "Skip to advanced options" link serves returning users; the
    refine / start-over actions appear once the wizard is dismissed.
    """
    step1_cards = "\n".join([
        _wizard_card("🎮", "Gaming GPU", "NVIDIA or AMD · 8–24 GB", "t2"),
        _wizard_card("🚀", "High-end GPU", "24–48 GB of video memory", "t3"),
        _wizard_card("🖥️", "Multi-GPU / Server", "48 GB and up", "t5"),
        _wizard_card("🍎", "Mac", "Apple Silicon · unified memory", "t2"),
        _wizard_card("🤔", "Not sure", "I'll pick my VRAM manually", ""),
    ])
    step2_cards = "\n".join([
        _wizard_card("💬", "Chat with AI", "Daily assistant, Q&A",
                     "General Chat"),
        _wizard_card("👨‍💻", "Help me code", "Coding assistant, code generation",
                     "Agentic Coding"),
        _wizard_card("📚", "Read long documents", "Summarization, RAG", "RAG"),
        _wizard_card("🤖", "Run agents", "Autonomous tasks, tool use",
                     "Agentic Coding"),
        _wizard_card("🧪", "Just exploring", "No specific goal yet", ""),
    ])
    step3_cards = "\n".join([
        _wizard_card("⚡", "Speed", "Fast responses", "speed"),
        _wizard_card("🏆", "Quality", "Best output", "quality"),
        _wizard_card("🧠", "Long conversations", "Big context", "context"),
        _wizard_card("⚖️", "Balance", "A bit of everything", "balanced"),
    ])
    return f'''
  <section class="wizard" id="wizard">
    <div class="wizard-top">
      <a class="wizard-skip" href="#rec-form" id="wizard-skip">Skip to advanced options →</a>
    </div>

    <div class="wizard-step" id="wizard-step-1">
      <p class="wizard-progress" aria-hidden="true">Step 1 of 3</p>
      <h2 id="wizard-step-1-title" tabindex="-1">What do you have?</h2>
      <p class="wizard-sub">Pick the hardware you'd run a model on — no specs needed.</p>
      <div class="wizard-cards" role="group" aria-label="Your hardware">
{step1_cards}
      </div>
    </div>

    <div class="wizard-step" id="wizard-step-2" hidden>
      <button type="button" class="wizard-back" data-back="1">← Back</button>
      <p class="wizard-progress" aria-hidden="true">Step 2 of 3</p>
      <h2 id="wizard-step-2-title" tabindex="-1">What do you want to do?</h2>
      <p class="wizard-sub">No wrong answers — we match what the community actually runs for this.</p>
      <div class="wizard-cards" role="group" aria-label="What you want to do">
{step2_cards}
      </div>
    </div>

    <div class="wizard-step" id="wizard-step-3" hidden>
      <button type="button" class="wizard-back" data-back="2">← Back</button>
      <p class="wizard-progress" aria-hidden="true">Step 3 of 3</p>
      <h2 id="wizard-step-3-title" tabindex="-1">What matters most to you?</h2>
      <p class="wizard-sub">This sets the main sort order — you can change it any time.</p>
      <div class="wizard-cards" role="group" aria-label="Your priority">
{step3_cards}
      </div>
    </div>
  </section>'''


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

      <details class="rec-advanced" id="rec-advanced">
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

    <div class="wizard-actions" id="wizard-actions" hidden>
      <a class="btn" href="#rec-form" id="wizard-refine">Refine your search</a>
      <button type="button" class="btn" id="wizard-reset">Start over</button>
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
{_wizard_html()}
{form_html}
{how_html}
{_config_island(schema)}
{utils.commands_config_island(subs, schema)}'''

    title = f'{meta.get("title", "Find Your Model")} — The Local AI Stack'
    desc = meta.get("description", "")
    return page_shell(title, desc, body, depth=RECOMMEND_DEPTH,
                      guides_menu=guides_menu,
                      extra_scripts=["js/recommend.js", "js/wizard.js",
                                     "js/commands.js"])
