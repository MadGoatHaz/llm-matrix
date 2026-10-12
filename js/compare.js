// compare.js — the comparison view (P2-2) + the Matrix checkbox selection.
//
// Two modes, chosen by what is on the page:
//
//  * **Matrix page** — a checkbox on each row plus a "Compare (N) →" bar.
//    Checking 2–4 rows builds a shareable `/compare/?a=&b=&c=&d=` deep link.
//
//  * **Compare page** — reads `?a=&b=&c=&d=` from the URL and renders a diff
//    table (rows = attributes, columns = the selected setups) with *differing*
//    cells accent-tinted, a short factual takeaway line, and a launch-command
//    button per column (handled by commands.js). Arriving with no selection
//    shows a picker of dropdowns instead.
//
// Both run entirely client-side from the #commands-config island (the trimmed
// submissions + schema tier/backend lists) — no network request, works offline.
// The table scrolls horizontally on narrow screens; nothing is forced to wrap.

(function () {
  'use strict';

  var configEl = document.getElementById('commands-config');
  if (!configEl) return;
  var config;
  try { config = JSON.parse(configEl.textContent); }
  catch (e) { console.error('compare.js: bad config island', e); return; }

  var subs = config.submissions || [];
  var byId = {};
  subs.forEach(function (s) { byId[s.id] = s; });
  var tierLabel = {};
  (config.tiers || []).forEach(function (t) { tierLabel[t.id] = t.label; });

  var MAX = 4;
  var KEYS = ['a', 'b', 'c', 'd'];

  function esc(v) {
    var d = document.createElement('div');
    d.textContent = (v == null) ? '' : String(v);
    return d.innerHTML;
  }
  function shortModel(s) {
    var name = (s.model && s.model.name) || '';
    var first = String(name).split(',')[0].trim().replace(/\s*\([^)]*\)\s*$/g, '').trim();
    if (first.indexOf('/') !== -1 && first.indexOf('http') !== 0) first = first.split('/').pop();
    return first || name || 'Setup';
  }
  function normBackend(raw) {
    var aliases = { 'llamacpp': 'llama.cpp', 'llama-cpp': 'llama.cpp', 'llama cpp': 'llama.cpp' };
    if (!raw) return '';
    var s = String(raw).trim().replace(/\(.*$/, '').trim().replace(/\s+\d[\w.]*$/, '').trim();
    if (!s) return '';
    var a = aliases[s.toLowerCase()];
    if (a) return a;
    for (var i = 0; i < (config.backends || []).length; i++) {
      if (String(config.backends[i]).toLowerCase() === s.toLowerCase()) return config.backends[i];
    }
    return s;
  }
  function parseSpeed(tps) {
    if (!tps) return 0;
    var m = String(tps).match(/(\d+(?:\.\d+)?)/);
    return m ? parseFloat(m[1]) : 0;
  }

  // The attributes shown as rows in the diff table.
  var ROWS = [
    { key: 'model',   label: 'Model',        get: function (s) { return shortModel(s); } },
    { key: 'hardware',label: 'Hardware',     get: function (s) { return (s.hardware || {}).description || ''; } },
    { key: 'vram',    label: 'VRAM tier',    get: function (s) { return tierLabel[s.tier] || s.tier || ''; } },
    { key: 'backend', label: 'Backend',      get: function (s) { return normBackend(s.backend); } },
    { key: 'quant',   label: 'Quant',        get: function (s) { return s.quant || s.weight_precision || ''; } },
    { key: 'usecase', label: 'Use case',     get: function (s) { return s.use_cases || ''; } },
    { key: 'speed',   label: 'Speed (decode)', get: function (s) { return (s.performance || {}).decode_tps || ''; } },
    { key: 'context', label: 'Context',      get: function (s) { return (s.context || {}).stable || ''; } },
    { key: 'kv',      label: 'KV cache',     get: function (s) { return (s.context || {}).kv_cache || ''; } },
    { key: 'notes',   label: 'Notes',        get: function (s) { return s.notes || ''; } }
  ];

  // ------------------------------------------------------------------
  // MATRIX mode
  // ------------------------------------------------------------------
  function initMatrix() {
    var checks = Array.prototype.slice.call(document.querySelectorAll('.compare-check'));
    var bar = document.getElementById('compare-bar');
    if (!checks.length || !bar) return;

    var countEl = bar.querySelector('.compare-count');
    var goBtn = bar.querySelector('.compare-go');
    var clearBtn = bar.querySelector('.compare-clear');

    function selected() {
      return checks.filter(function (c) { return c.checked; })
                   .map(function (c) { return c.getAttribute('data-sub-id'); });
    }
    function update() {
      var n = selected().length;
      bar.classList.toggle('active', n >= 2);
      if (countEl) countEl.textContent = String(n);
      if (goBtn) goBtn.disabled = n < 2 || n > MAX;
      checks.forEach(function (c) { if (!c.checked) c.disabled = n >= MAX; });
    }
    checks.forEach(function (c) {
      c.addEventListener('change', function () {
        if (c.checked && selected().length > MAX) { c.checked = false; return; }
        update();
      });
    });
    if (goBtn) goBtn.addEventListener('click', function () {
      var ids = selected();
      if (ids.length < 2) return;
      var qs = ids.map(function (id, i) { return KEYS[i] + '=' + encodeURIComponent(id); }).join('&');
      var base = window.location.pathname.replace(/matrix\.html$/, '');
      window.location.href = base + 'compare/?' + qs;
    });
    if (clearBtn) clearBtn.addEventListener('click', function () {
      checks.forEach(function (c) { c.checked = false; c.disabled = false; });
      update();
    });
    update();
  }

  // ------------------------------------------------------------------
  // COMPARE PAGE mode
  // ------------------------------------------------------------------
  function idsFromUrl() {
    var params = new URLSearchParams(window.location.search);
    var out = [];
    KEYS.forEach(function (k) {
      var v = params.get(k);
      if (v && byId[v] && out.indexOf(v) === -1) out.push(v);
    });
    return out;
  }
  function syncUrl(ids) {
    var parts = ids.slice(0, MAX).map(function (id, i) { return KEYS[i] + '=' + encodeURIComponent(id); });
    var qs = parts.join('&');
    history.replaceState(null, '', window.location.pathname + (qs ? '?' + qs : ''));
  }
  function matrixBase() { return '../'; } // compare/ is one level deep

  function computeDiff(vals) {
    var nonEmpty = vals.filter(Boolean);
    if (!nonEmpty.length) return false;
    var uniq = Array.from(new Set(nonEmpty)).length;
    return uniq > 1 || nonEmpty.length < vals.length;
  }

  function takeaway(sel) {
    var differing = [];
    ROWS.forEach(function (r) {
      if (computeDiff(sel.map(function (s) { return r.get(s).trim(); }))) differing.push(r.label);
    });
    var speeds = sel.map(function (s) { return parseSpeed((s.performance || {}).decode_tps); }).filter(Boolean);
    var parts = ['Compared ' + sel.length + ' setups'];
    parts.push(differing.length ? 'they differ in: ' + differing.join(', ') : 'they match on every tracked attribute');
    if (speeds.length) parts.push('decode speeds range ' + Math.min.apply(null, speeds) + '–' + Math.max.apply(null, speeds) + ' t/s');
    return parts.join('; ') + '.';
  }

  function renderTable(ids) {
    var wrap = document.getElementById('compare-table-wrap');
    if (!wrap) return;
    var sel = ids.map(function (id) { return byId[id]; });

    var html = '<table class="compare-table"><thead><tr>' +
      '<th class="compare-attr">Attribute</th>';
    sel.forEach(function (s) {
      html += '<th class="compare-col">' +
        '<div class="compare-col-head">' +
          '<span class="compare-model">' + esc(shortModel(s)) + '</span>' +
          '<span class="compare-col-meta">' + esc(normBackend(s.backend)) + ' · ' + esc(tierLabel[s.tier] || s.tier) + '</span>' +
          '<a class="compare-matrix-link" href="' + matrixBase() + 'matrix.html#' + esc(s.id) + '">View in Matrix →</a>' +
        '</div></th>';
    });
    html += '</tr></thead><tbody>';

    ROWS.forEach(function (r) {
      var vals = sel.map(function (s) { return r.get(s).trim(); });
      var diff = computeDiff(vals);
      html += '<tr><th class="compare-attr" scope="row">' + esc(r.label) + '</th>';
      sel.forEach(function (s, i) {
        var v = vals[i];
        html += '<td class="compare-cell' + (diff ? ' compare-diff' : '') + '">' +
          (v ? esc(v) : '<span class="compare-empty">—</span>') + '</td>';
      });
      html += '</tr>';
    });

    html += '<tr class="compare-actions"><th class="compare-attr" scope="row">Launch</th>';
    sel.forEach(function (s) {
      html += '<td class="compare-cell"><button class="btn btn-primary compare-launch" data-launch-sub="' + esc(s.id) + '">🚀 Copy launch command</button></td>';
    });
    html += '</tr></tbody></table>';
    wrap.innerHTML = html;

    var takeEl = document.getElementById('compare-takeaway');
    if (takeEl) takeEl.textContent = takeaway(sel);
  }

  function initComparePage() {
    var picker = document.getElementById('compare-picker');
    var wrap = document.getElementById('compare-table-wrap');
    var editBtn = document.getElementById('compare-edit');
    if (!wrap) return;

    var selects = picker ? Array.prototype.slice.call(picker.querySelectorAll('select.compare-pick')) : [];
    var initial = idsFromUrl();

    if (picker) {
      selects.forEach(function (sel, i) {
        var opts = ['<option value="">Setup ' + (i + 1) + '…</option>'];
        subs.forEach(function (s) {
          opts.push('<option value="' + esc(s.id) + '">' +
            esc(shortModel(s)) + ' · ' + esc(normBackend(s.backend)) + ' · ' + esc(tierLabel[s.tier] || s.tier) + '</option>');
        });
        sel.innerHTML = opts.join('');
        if (initial[i]) sel.value = initial[i];
        sel.setAttribute('aria-label', 'Setup to compare ' + (i + 1));
        sel.addEventListener('change', onPick);
      });
      var go = picker.querySelector('.compare-pick-go');
      if (go) go.addEventListener('click', onPick);
    }

    function pickerIds() {
      var seen = {}, out = [];
      selects.forEach(function (s) { if (s.value && !seen[s.value]) { seen[s.value] = true; out.push(s.value); } });
      return out;
    }
    function onPick() {
      var ids = pickerIds();
      syncUrl(ids);
      show(ids);
    }
    function show(ids) {
      var active = ids.length >= 2;
      if (picker) picker.classList.toggle('is-hidden', active);
      wrap.classList.toggle('is-hidden', !active);
      if (editBtn) editBtn.hidden = !active;
      var takeEl = document.getElementById('compare-takeaway');
      if (!active) {
        if (takeEl) takeEl.textContent = 'Select at least 2 setups to compare them side by side.';
        return;
      }
      renderTable(ids);
    }
    if (editBtn) editBtn.addEventListener('click', function () {
      if (picker) picker.classList.remove('is-hidden');
      wrap.classList.add('is-hidden');
      editBtn.hidden = true;
      var takeEl = document.getElementById('compare-takeaway');
      if (takeEl) takeEl.textContent = 'Update your selection below, then compare again.';
    });

    show(initial);
  }

  // Expose the pure helpers for the test suite / console.
  window.Compare = {
    renderTable: renderTable,
    takeaway: takeaway,
    computeDiff: computeDiff,
    shortModel: shortModel,
    normBackend: normBackend,
    ROWS: ROWS,
    byId: byId
  };

  // Boot: pick the mode from what is present.
  if (document.getElementById('compare-table-wrap')) {
    initComparePage();
  } else {
    initMatrix();
  }
})();
