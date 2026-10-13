"""``submit/index.html`` — the community submission form (P3-4).

A fully static, client-side form that lowers the barrier to contributing. The
user fills in their setup (the fields mirror ``schema.json`` and the forum's
``[COMMUNITY-SUBMISSION]`` template); ``js/submit.js`` assembles a
ready-to-post block and offers two paths:

* **Copy for the forum** — puts the block on the clipboard and links to the
  thread to paste it;
* **Open a GitHub issue** — builds a pre-filled ``issues/new`` URL carrying the
  block in the body.

No server, no account, no storage — pure static HTML + client JS. The schema
pick-lists (tiers, vendors, backends, …) are baked into a JSON config island at
generation time, so the form needs no extra network request.

The page lives at ``submit/index.html`` (depth 1) and loads the extra
``js/submit.js`` after the shared ``js/main.js``.
"""

from __future__ import annotations

from pathlib import Path

from .. import markdown as md
from .. import utils
from ..template import page_shell

#: The submit page is one level below the repo root.
SUBMIT_DEPTH = 1

#: The forum thread the "Copy for the forum" path posts into.
FORUM_THREAD = utils.FORUM_THREAD
#: The GitHub repo the "Open a GitHub issue" path targets.
GITHUB_REPO = utils.GITHUB_REPO


def _config_island(schema: dict) -> str:
    """Embed the schema pick-lists as a JSON island for the form's selects.

    Baked at generation time so the client populates every ``<select>`` with
    no extra request — the page works offline straight from disk. Compact and
    brace-safe (no ``{{``/``}}``) via :func:`utils.compact_json`.
    """
    config = {
        "tiers": schema.get("tiers", []),
        "vendors": schema.get("hardware_vendors", []),
        "backends": schema.get("backends", []),
        "os_drivers": schema.get("os_drivers", []),
        "quant_formats": schema.get("quant_formats", []),
        "kv_cache_types": schema.get("kv_cache_types", []),
        "use_cases": schema.get("use_cases", []),
        "engine_modes": schema.get("engine_modes", []),
        "forum_thread": FORUM_THREAD,
        "github_repo": GITHUB_REPO,
    }
    payload = utils.compact_json(config)
    return (
        '  <script type="application/json" id="submit-config">\n'
        f"{payload}\n"
        "  </script>"
    )


def _tier_options(schema: dict) -> str:
    opts = ['          <option value="" disabled selected>Select your VRAM…</option>']
    for t in schema.get("tiers", []):
        opts.append(
            f'          <option value="{utils.html_escape(t["id"])}">'
            f'{utils.html_escape(t["label"])}</option>'
        )
    return "\n".join(opts)


def _string_options(schema: dict, key: str, first_label: str) -> str:
    """``<option>`` list for a string-valued schema enum (optional first row)."""
    opts = [f'          <option value="">{first_label}</option>']
    for v in schema.get(key, []):
        opts.append(
            f'          <option value="{utils.html_escape(v)}">'
            f'{utils.html_escape(v)}</option>'
        )
    return "\n".join(opts)


def _quant_datalist(schema: dict) -> str:
    opts = "\n".join(
        f'        <option value="{utils.html_escape(v)}"></option>'
        for v in schema.get("quant_formats", [])
    )
    return f'  <datalist id="quant-list">\n{opts}\n  </datalist>'


def render(schema: dict, content_dir: Path,
           guides_menu: list[tuple[str, str]] | None = None) -> str:
    """Render the submission page document.

    Args:
        schema: The parsed ``schema.json`` (tiers, vendors, backends, …).
        content_dir: The authored-content directory (``content/``); the
            explainer is read from ``content_dir/submit.md``.
        guides_menu: Optional ``(label, url)`` list for the nav dropdown.

    Returns:
        The full ``submit/index.html`` document (depth 1).

    Raises:
        FileNotFoundError: if ``content/submit.md`` does not exist.
    """
    md_path = content_dir / "submit.md"
    meta, body_md = md.split_front_matter(md_path.read_text(encoding="utf-8"))
    intro_html = md.render_markdown(body_md)

    form_html = f'''
  <section class="submit-tool" aria-labelledby="submit-tool-title">
    <h2 id="submit-tool-title" class="section-title">{utils.icon("📥")} Build your submission</h2>
    <noscript>
      <div class="callout callout--warning"><p><b>JavaScript is required.</b> This form assembles your submission block right in your browser. Please enable JavaScript — or copy the <code>[COMMUNITY-SUBMISSION]</code> template directly from the <a href="{FORUM_THREAD}" target="_blank" rel="noopener">forum thread</a>.</p></div>
    </noscript>
    <form class="submit-form" id="submit-form" autocomplete="off" novalidate>

      <fieldset class="submit-group">
        <legend>Your hardware</legend>
        <div class="submit-field">
          <label for="sub-tier">VRAM <span class="req" title="Required">*</span></label>
          <select id="sub-tier" name="tier" required aria-required="true" aria-describedby="sub-tier-err">
{_tier_options(schema)}
          </select>
          <p class="field-hint">Total video memory across all your GPUs.</p>
          <p class="field-err" id="sub-tier-err" role="alert" hidden></p>
        </div>
        <div class="submit-field">
          <label for="sub-vendor">GPU vendor <span class="opt">(optional)</span></label>
          <select id="sub-vendor" name="vendor">
{_string_options(schema, "hardware_vendors", "Auto-detect from hardware")}
          </select>
        </div>
        <div class="submit-field">
          <label for="sub-hardware">Hardware <span class="req" title="Required">*</span></label>
          <input type="text" id="sub-hardware" name="hardware" required aria-required="true"
                 placeholder="e.g. 2x RX 7900 XTX 24GB, 128GB RAM" aria-describedby="sub-hardware-err">
          <p class="field-err" id="sub-hardware-err" role="alert" hidden></p>
        </div>
        <div class="submit-field">
          <label for="sub-backend">Backend <span class="opt">(optional)</span></label>
          <select id="sub-backend" name="backend" aria-describedby="sub-backend-err">
{_string_options(schema, "backends", "Select a backend…")}
          </select>
          <p class="field-hint">Adding your backend and quant helps others find your setup!</p>
          <p class="field-err" id="sub-backend-err" role="alert" hidden></p>
        </div>
        <div class="submit-field">
          <label for="sub-os">OS / driver <span class="opt">(optional)</span></label>
          <select id="sub-os" name="os_driver">
{_string_options(schema, "os_drivers", "Not sure / other")}
          </select>
        </div>
      </fieldset>

      <fieldset class="submit-group">
        <legend>Your model</legend>
        <div class="submit-field">
          <label for="sub-model">Model name <span class="req" title="Required">*</span></label>
          <input type="text" id="sub-model" name="model_name" required aria-required="true"
                 placeholder="e.g. d0xin/Swift-Qwen3.8-27B-Uncensored-FP8" aria-describedby="sub-model-err">
          <p class="field-err" id="sub-model-err" role="alert" hidden></p>
        </div>
        <div class="submit-field">
          <label for="sub-quant">Quant / precision <span class="opt">(optional)</span></label>
          <input type="text" id="sub-quant" name="quant_package"
                 list="quant-list" placeholder="e.g. GGUF Q4_K_M, FP8, I-Nano" aria-describedby="sub-quant-err">
          <p class="field-err" id="sub-quant-err" role="alert" hidden></p>
        </div>
        <div class="submit-field">
          <label for="sub-precision">Weight precision <span class="opt">(optional)</span></label>
          <input type="text" id="sub-precision" name="weight_precision" placeholder="e.g. FP8 (native), ~2.5bpw">
        </div>
        <div class="submit-field">
          <label for="sub-url">Download link <span class="opt">(optional)</span></label>
          <input type="url" id="sub-url" name="download_url" placeholder="https://huggingface.co/…" aria-describedby="sub-url-err">
          <p class="field-err" id="sub-url-err" role="alert" hidden></p>
        </div>
      </fieldset>

      <fieldset class="submit-group">
        <legend>How you use it</legend>
        <div class="submit-field">
          <label for="sub-usecase">Primary use case <span class="opt">(optional)</span></label>
          <select id="sub-usecase" name="primary_use_case" aria-describedby="sub-usecase-err">
{_string_options(schema, "use_cases", "Select a use case…")}
          </select>
          <p class="field-hint">Not sure? Pick the closest — or leave it blank and we'll figure it out.</p>
          <p class="field-err" id="sub-usecase-err" role="alert" hidden></p>
        </div>
        <div class="submit-field">
          <label for="sub-context">Stable context tested <span class="opt">(optional)</span></label>
          <input type="text" id="sub-context" name="stable_context_tested" placeholder="e.g. 32k tokens (NIAH hit)">
        </div>
        <div class="submit-field">
          <label for="sub-kv">KV cache setting <span class="opt">(optional)</span></label>
          <select id="sub-kv" name="kv_cache_setting">
{_string_options(schema, "kv_cache_types", "Not sure / default")}
          </select>
        </div>
        <div class="submit-field">
          <label for="sub-mode">Engine mode <span class="opt">(optional)</span></label>
          <select id="sub-mode" name="engine_mode">
{_string_options(schema, "engine_modes", "VRAM-only (default)")}
          </select>
          <p class="field-hint">Set this if you run a hybrid (VRAM+RAM+SSD) or CPU+GPU setup.</p>
        </div>
      </fieldset>

      <fieldset class="submit-group">
        <legend>Performance <span class="group-opt">(optional)</span></legend>
        <div class="submit-field">
          <label for="sub-decode">Decode speed <span class="opt">tok/s</span></label>
          <input type="text" id="sub-decode" name="throughput_tps" placeholder="e.g. 54.4" aria-describedby="sub-decode-err">
          <p class="field-err" id="sub-decode-err" role="alert" hidden></p>
        </div>
        <div class="submit-field">
          <label for="sub-prefill">Prefill speed <span class="opt">tok/s</span></label>
          <input type="text" id="sub-prefill" name="prefill_tps" placeholder="e.g. 215">
        </div>
        <div class="submit-field">
          <label for="sub-ttft">TTFT (cold) <span class="opt">seconds</span></label>
          <input type="text" id="sub-ttft" name="ttft_cold" placeholder="e.g. 19.3s">
        </div>
        <div class="submit-field">
          <label for="sub-power">Power draw <span class="opt">watts</span></label>
          <input type="text" id="sub-power" name="power_draw" placeholder="e.g. 150W peak">
        </div>
      </fieldset>

      <fieldset class="submit-group">
        <legend>Notes</legend>
        <div class="submit-field">
          <label for="sub-notes">Setup notes <span class="opt">(optional)</span></label>
          <textarea id="sub-notes" name="setup_notes" rows="4"
                    placeholder="Launch flags, quirks, what worked, what didn't…" aria-describedby="sub-notes-err"></textarea>
          <p class="field-err" id="sub-notes-err" role="alert" hidden></p>
        </div>
      </fieldset>

    </form>

    <div class="submit-actions">
      <button type="button" class="btn btn-primary" id="submit-copy">
        {utils.icon("📋")} Copy for the forum
      </button>
      <a class="btn" id="submit-issue" href="#" target="_blank" rel="noopener">
        {utils.icon("🐙")} Open a GitHub issue
      </a>
      <span class="sr-only" id="submit-status" role="status" aria-live="polite"></span>
    </div>

    <div class="submit-preview" id="submit-preview" hidden>
      <h3>Preview — copy this block</h3>
      <pre id="submit-preview-text" tabindex="0"></pre>
      <p class="submit-preview-link" id="submit-preview-link"></p>
    </div>
  </section>'''

    next_html = f'''
  <section class="submit-next" aria-labelledby="submit-next-title">
    <h2 id="submit-next-title" class="section-title">What happens next</h2>
    <div class="card">
      <p><strong>Reviewed weekly.</strong> Submissions are read, questions are asked in-thread when a number looks off, and valid entries are parsed into the dataset.</p>
      <p><strong>It appears in the index.</strong> Your entry shows up in the <a href="../matrix.html">Matrix</a> and the forum index, credited to you.</p>
      <p><strong>Corroboration promotes it.</strong> When an entry is confirmed by 2+ independent sources — or tested by the maintainer — it's promoted to the master matrix. No submission is too small to matter.</p>
    </div>
  </section>'''

    body = f'''
  <div class="page-header">
    <h1>Submit Your Setup</h1>
    <p class="subtitle">Add your local LLM to the community matrix — no account, no server.</p>
  </div>

{intro_html}
{form_html}
{next_html}
{_quant_datalist(schema)}
{_config_island(schema)}'''

    title = f'{meta.get("title", "Submit Your Setup")} — The Local AI Stack'
    desc = meta.get("description", "")
    return page_shell(title, desc, body, depth=SUBMIT_DEPTH,
                      guides_menu=guides_menu,
                      extra_scripts=["js/submit.js"])
