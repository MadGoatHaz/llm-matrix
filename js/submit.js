// submit.js — the client-side community submission form (P3-4).
//
// A static form (no server, no account, no storage). Filling it assembles a
// ready-to-post [COMMUNITY-SUBMISSION] block that tools/parse.py understands,
// then offers two paths:
//   * "Copy for the forum"  -> the block goes to the clipboard + a link to the
//                              thread to paste it in;
//   * "Open a GitHub issue" -> a pre-filled issues/new URL carrying the block.
//
// The schema pick-lists and target URLs come from the #submit-config island
// (baked at generation time), so the page makes no network request. Vanilla,
// zero dependencies — mirrors the clipboard + validation patterns in main.js.

(function () {
  'use strict';

  // form field id -> canonical [COMMUNITY-SUBMISSION] key.
  var FIELDS = {
    'sub-tier': 'tier',
    'sub-hardware': 'hardware',
    'sub-backend': 'backend',
    'sub-os': 'os_driver',
    'sub-model': 'model_name',
    'sub-quant': 'quant_package',
    'sub-precision': 'weight_precision',
    'sub-url': 'download_url',
    'sub-usecase': 'primary_use_case',
    'sub-context': 'stable_context_tested',
    'sub-kv': 'kv_cache_setting',
    'sub-mode': 'engine_mode',
    'sub-decode': 'throughput_tps',
    'sub-prefill': 'prefill_tps',
    'sub-ttft': 'ttft_cold',
    'sub-power': 'power_draw',
    'sub-notes': 'setup_notes'
  };

  // The canonical block order (matches the forum template + parse.py).
  var ORDER = [
    'tier', 'hardware', 'backend', 'os_driver', 'model_name', 'quant_package',
    'weight_precision', 'download_url', 'primary_use_case', 'stable_context_tested',
    'kv_cache_setting', 'engine_mode', 'throughput_tps', 'prefill_tps',
    'ttft_cold', 'power_draw', 'setup_notes'
  ];

  // Fields that must be filled before a block is produced.
  var REQUIRED = ['sub-tier', 'sub-hardware', 'sub-backend', 'sub-model',
                  'sub-quant', 'sub-usecase', 'sub-notes'];

  // ------------------------------------------------------------------
  // Small helpers
  // ------------------------------------------------------------------
  function esc(value) {
    var div = document.createElement('div');
    div.textContent = (value == null) ? '' : String(value);
    return div.innerHTML;
  }

  function val(field) {
    var el = document.getElementById(field);
    return el ? el.value.trim() : '';
  }

  function shortModel(name) {
    if (!name) return 'a model';
    var s = String(name).split(',')[0].trim();
    if (s.indexOf('/') !== -1 && s.indexOf('http') !== 0) s = s.split('/')[1];
    s = s.replace(/\s*\([^)]*\)\s*$/g, '').trim();
    if (s.length > 40) s = s.slice(0, 37) + '…';
    return s;
  }

  function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text).then(function () { return true; })
        .catch(function () { return fallbackCopy(text); });
    }
    return Promise.resolve(fallbackCopy(text));
  }

  function fallbackCopy(text) {
    try {
      var ta = document.createElement('textarea');
      ta.value = text;
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      var ok = document.execCommand('copy');
      document.body.removeChild(ta);
      return ok;
    } catch (e) { return false; }
  }

  // ------------------------------------------------------------------
  // Boot
  // ------------------------------------------------------------------
  document.addEventListener('DOMContentLoaded', function () {
    var form = document.getElementById('submit-form');
    var configEl = document.getElementById('submit-config');
    if (!form || !configEl) return; // not the submit page

    var config;
    try { config = JSON.parse(configEl.textContent); }
    catch (e) { console.error('submit.js: bad config island', e); return; }

    var tierLabel = {};
    (config.tiers || []).forEach(function (t) { tierLabel[t.id] = t.label; });

    var statusEl = document.getElementById('submit-status');
    var previewEl = document.getElementById('submit-preview');
    var previewText = document.getElementById('submit-preview-text');
    var previewLink = document.getElementById('submit-preview-link');

    function setStatus(msg) { if (statusEl) statusEl.textContent = msg || ''; }

    // ----------------------------------------------------------------
    // Validation
    // ----------------------------------------------------------------
    function validate() {
      var errors = {};
      REQUIRED.forEach(function (id) {
        if (val(id) === '') errors[id] = 'This field is required.';
      });
      var url = val('sub-url');
      if (url && !/^https?:\/\//.test(url)) {
        errors['sub-url'] = 'Must be a full link starting with http:// or https://';
      }
      var decode = val('sub-decode');
      if (decode && !/\d/.test(decode)) {
        errors['sub-decode'] = 'Include a number (tokens per second).';
      }
      return errors;
    }

    function showErrors(errors) {
      Object.keys(errors).forEach(function (id) {
        var errEl = document.getElementById(id + '-err');
        var input = document.getElementById(id);
        if (errEl) { errEl.textContent = errors[id]; errEl.hidden = false; }
        if (input) { input.classList.add('invalid'); input.setAttribute('aria-invalid', 'true'); }
      });
    }

    function clearErrors() {
      document.querySelectorAll('.field-err').forEach(function (el) {
        el.hidden = true; el.textContent = '';
      });
      document.querySelectorAll('.invalid').forEach(function (el) {
        el.classList.remove('invalid'); el.removeAttribute('aria-invalid');
      });
    }

    function clearErrorFor(id) {
      var errEl = document.getElementById(id + '-err');
      var input = document.getElementById(id);
      if (errEl) { errEl.hidden = true; errEl.textContent = ''; }
      if (input) { input.classList.remove('invalid'); input.removeAttribute('aria-invalid'); }
    }

    function focusFirstInvalid(errors) {
      var ids = Object.keys(errors);
      if (ids.length) {
        var el = document.getElementById(ids[0]);
        if (el) { el.focus(); el.scrollIntoView({ behavior: 'smooth', block: 'center' }); }
      }
    }

    // ----------------------------------------------------------------
    // Block assembly
    // ----------------------------------------------------------------
    function buildBlock() {
      var lines = ['[COMMUNITY-SUBMISSION]'];
      ORDER.forEach(function (key) {
        var field = null;
        for (var id in FIELDS) { if (FIELDS[id] === key) { field = id; break; } }
        var v = field ? val(field) : '';
        if (v) lines.push(key + ': ' + v);
      });
      lines.push('[/COMMUNITY-SUBMISSION]');
      return lines.join('\n');
    }

    function showPreview(block) {
      if (previewText) previewText.textContent = block;
      if (previewLink) {
        previewLink.innerHTML =
          'Now paste it into the ' +
          '<a href="' + esc(config.forum_thread) + '" target="_blank" rel="noopener">forum thread →</a>';
      }
      if (previewEl) previewEl.hidden = false;
    }

    function issueUrl(block) {
      var tier = tierLabel[val('sub-tier')] || val('sub-tier') || 'your VRAM tier';
      var title = 'Community submission: ' + shortModel(val('sub-model')) + ' (' + tier + ')';
      var body =
        "I'm submitting a new setup for the Local AI Stack matrix.\n\n" +
        '```text\n' + block + '\n```\n\n' +
        '_Generated from the [submission form](https://madgoathaz.github.io/llm-matrix/submit/). ' +
        'Please integrate it in the next weekly rollup._';
      return config.github_repo + '/issues/new?' +
        'title=' + encodeURIComponent(title) +
        '&body=' + encodeURIComponent(body);
    }

    // ----------------------------------------------------------------
    // Actions
    // ----------------------------------------------------------------
    function handleAction(action) {
      clearErrors();
      var errors = validate();
      if (Object.keys(errors).length) {
        showErrors(errors);
        focusFirstInvalid(errors);
        setStatus('Please fix the highlighted fields before submitting.');
        return;
      }
      var block = buildBlock();
      showPreview(block);
      if (action === 'copy') {
        copyText(block).then(function (ok) {
          setStatus(ok
            ? 'Copied to clipboard — paste it into the forum thread (link in the preview).'
            : 'Copy failed — select the text in the preview below.');
        });
      } else if (action === 'issue') {
        window.open(issueUrl(block), '_blank', 'noopener');
        setStatus('Opened a pre-filled GitHub issue in a new tab.');
      }
    }

    var copyBtn = document.getElementById('submit-copy');
    var issueBtn = document.getElementById('submit-issue');
    if (copyBtn) copyBtn.addEventListener('click', function () { handleAction('copy'); });
    if (issueBtn) issueBtn.addEventListener('click', function (e) {
      e.preventDefault();
      handleAction('issue');
    });
    // Enter in a field submits the form -> treat it as the copy path.
    form.addEventListener('submit', function (e) { e.preventDefault(); handleAction('copy'); });

    // Clear a field's error as soon as the user edits it (live feedback).
    form.querySelectorAll('[id]').forEach(function (el) {
      if (!el.id || el.id.indexOf('sub-') !== 0) return;
      var evt = (el.tagName === 'SELECT' || el.type === 'url') ? 'change' : 'input';
      el.addEventListener(evt, function () {
        if (validate()[el.id] === undefined) clearErrorFor(el.id);
      });
    });
  });
})();
