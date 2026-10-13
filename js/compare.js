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

  // Context length in tokens from the "stable" string ("65536", "~240k",
  // "262,144 configured", …). Commas are stripped first, so grouped figures
  // parse as the full amount (a ratio built on "262" would be wrong).
  function parseContext(stable) {
    if (!stable) return 0;
    var m = String(stable).toLowerCase().replace(/,/g, '').match(/(\d+(?:\.\d+)?)\s*(k|m|million)?/);
    if (!m) return 0;
    var n = parseFloat(m[1]);
    if (m[2] === 'k') n *= 1000;
    else if (m[2] === 'm' || m[2] === 'million') n *= 1e6;
    return Math.round(n);
  }

  // First numeric token of a power-draw string, in watts.
  function parsePower(w) {
    if (!w) return 0;
    var m = String(w).match(/(\d+(?:\.\d+)?)/);
    return m ? parseFloat(m[1]) : 0;
  }

  // The first "N GB" figure in a string.
  function firstGb(s) {
    if (!s) return null;
    var m = String(s).match(/(\d+(?:\.\d+)?)\s*GB/i);
    return m ? parseFloat(m[1]) : null;
  }

  // Best-known VRAM footprint of a submission, in GB: an explicit "N GB" in
  // the notes, then the hardware description, then the tier band's ceiling.
  // The same honest-estimate convention as js/recommend.js (A3), so the
  // compare view and the recommend engine rank VRAM identically.
  function estimateVram(s) {
    var gb = firstGb(s.notes);
    if (gb !== null) return gb;
    gb = firstGb((s.hardware || {}).description);
    if (gb !== null) return gb;
    var tier = null;
    (config.tiers || []).forEach(function (t) { if (t.id === s.tier) tier = t; });
    if (tier && tier.range) return tier.range[1];
    return null;
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
    { key: 'power',   label: 'Power draw',   get: function (s) { return (s.performance || {}).power_w || ''; } },
    { key: 'notes',   label: 'Notes',        get: function (s) { return s.notes || ''; } }
  ];

  // ------------------------------------------------------------------
  // Decision support (B2/C3): numeric dimensions, winner markers, and the
  // directional "Tradeoffs" paragraph.
  //
  // Four dimensions are numeric and comparable: decode speed and context
  // window (more is better), VRAM and power draw (less is better). Every
  // other row (model, hardware, backend, quant, use case, KV, notes) is
  // qualitative — it shows the values but never a "winner", because there
  // is no objective best. A dimension only earns a winner when its best
  // value beats the next-best by at least 20%; closer than that and the
  // entries are "comparable" and no one is crowned. The ratios feed the
  // Tradeoffs paragraph, which states each difference directionally and
  // acknowledges the give-up — never an overall winner, which is the
  // user's call to make on their own priorities.
  // ------------------------------------------------------------------
  var MEANINGFUL = 1.2; // a >=20% relative difference

  var DIMS = {
    speed:   { dir: 'high', parse: function (s) { return parseSpeed((s.performance || {}).decode_tps); } },
    context: { dir: 'high', parse: function (s) { return parseContext((s.context || {}).stable); } },
    vram:    { dir: 'low',  parse: function (s) { return estimateVram(s); } },
    power:   { dir: 'low',  parse: function (s) { return parsePower((s.performance || {}).power_w); } }
  };

  // Format a ratio for prose: 2.3, 4, 12 — one decimal, trimmed.
  function fmtRatio(r) {
    var v = Math.round(r * 10) / 10;
    return (v % 1 === 0) ? String(v) : v.toFixed(1);
  }

  // The entries of ``sel`` that report a value for ``dim``, with their index.
  function entriesFor(dim, sel) {
    var out = [];
    sel.forEach(function (s, i) {
      var n = DIMS[dim].parse(s);
      if (n !== null && n > 0) out.push({ i: i, n: n });
    });
    return out;
  }

  // The best cell of a numeric row: the entry whose value leads by at
  // least MEANINGFUL over the next-best. Returns { winner, comparable }:
  //   winner     — index of the leading entry, or null
  //   comparable — true when the top two are within 20% (no winner called)
  // A single reported value is its own winner (nothing to compare against).
  function winnerFor(dim, sel) {
    var entries = entriesFor(dim, sel);
    if (!entries.length) return { winner: null, comparable: false };
    if (entries.length === 1) return { winner: entries[0].i, comparable: false };
    entries.sort(function (a, b) {
      return DIMS[dim].dir === 'high' ? b.n - a.n : a.n - b.n;
    });
    var best = entries[0].n, second = entries[1].n;
    var ratio = DIMS[dim].dir === 'high' ? best / second : second / best;
    if (ratio < MEANINGFUL) return { winner: null, comparable: true };
    return { winner: entries[0].i, comparable: false };
  }

  // One directional sentence per meaningful dimension, best vs worst.
  function tradeoffSentences(sel) {
    var out = [];
    Object.keys(DIMS).forEach(function (dim) {
      var entries = entriesFor(dim, sel);
      if (entries.length < 2) return;
      var sorted = entries.slice().sort(function (a, b) {
        return DIMS[dim].dir === 'high' ? b.n - a.n : a.n - b.n;
      });
      var best = sorted[0], worst = sorted[sorted.length - 1];
      var ratio = DIMS[dim].dir === 'high' ? best.n / worst.n : worst.n / best.n;
      if (ratio < MEANINGFUL) return; // close — "comparable", not a tradeoff
      var a = shortModel(sel[best.i]), b = shortModel(sel[worst.i]);
      var r = fmtRatio(ratio);
      var text;
      if (dim === 'speed') text = a + ' is ' + r + '× faster decode than ' + b;
      else if (dim === 'context') text = a + ' has ' + r + '× the context window of ' + b;
      else if (dim === 'vram') text = b + ' uses ' + r + '× more VRAM than ' + a;
      else text = a + ' draws ' + r + '× less power than ' + b;
      out.push({ ratio: ratio, text: text });
    });
    out.sort(function (x, y) { return y.ratio - x.ratio; }); // most significant first
    return out;
  }

  // The give-up clause: the setup that leads the loudest dimension usually
  // pays for it somewhere else — "fastest decode, but 2× the VRAM". Only
  // emitted when the speed leader is NOT the VRAM leader and the gap is
  // meaningful, so it never overstates a close race.
  function giveupSentence(sel) {
    var sp = entriesFor('speed', sel).sort(function (a, b) { return b.n - a.n; });
    var vr = entriesFor('vram', sel).sort(function (a, b) { return a.n - b.n; });
    if (sp.length < 2 || vr.length < 2) return null;
    var sBest = sp[0], vBest = vr[0];
    if (sBest.i === vBest.i) return null; // same entry leads both — no tension
    var sVram = DIMS.vram.parse(sel[sBest.i]);
    if (sVram === null || sVram <= 0) return null;
    var ratio = sVram / vBest.n;
    if (ratio < MEANINGFUL) return null;
    return shortModel(sel[sBest.i]) + ' is the fastest decode, but uses ' +
      fmtRatio(ratio) + '× the VRAM of ' + shortModel(sel[vBest.i]);
  }

  // The full "Tradeoffs" paragraph: the most significant directional
  // differences (max 4) plus the give-up clause (1) — 3–5 sentences, never
  // an overall winner. Empty string when nothing differs meaningfully.
  function tradeoffParagraph(sel) {
    var parts = tradeoffSentences(sel).slice(0, 4).map(function (o) { return o.text; });
    var give = giveupSentence(sel);
    if (give) parts.push(give);
    if (!parts.length) return '';
    return parts.join('. ') + '.';
  }

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

    var html = '<table class="compare-table"><caption class="sr-only">Side-by-side comparison of the selected community setups; rows are attributes, columns are setups</caption><thead><tr>' +
      '<th class="compare-attr" scope="col">Attribute</th>';
    sel.forEach(function (s) {
      html += '<th class="compare-col" scope="col">' +
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
      // B2/C3: numeric rows get a "best" marker on the leading cell — but
      // only when the lead is meaningful (>=20%); close values are
      // comparable and earn no crown.
      var win = DIMS[r.key] ? winnerFor(r.key, sel) : null;
      html += '<tr><th class="compare-attr" scope="row">' + esc(r.label) + '</th>';
      sel.forEach(function (s, i) {
        var v = vals[i];
        var isWinner = win && win.winner === i;
        html += '<td class="compare-cell' + (diff ? ' compare-diff' : '') +
          (isWinner ? ' compare-best' : '') + '">' +
          (v ? esc(v) : '<span class="compare-empty">—</span>') +
          (isWinner ? ' <span class="compare-winner" title="Best value in this column">▲ best</span>' : '') +
          '</td>';
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
      var sel = ids.map(function (id) { return byId[id]; }).filter(Boolean);
      if (picker) picker.classList.toggle('is-hidden', active);
      wrap.classList.toggle('is-hidden', !active);
      if (editBtn) editBtn.hidden = !active;
      var takeEl = document.getElementById('compare-takeaway');
      var tradeEl = document.getElementById('compare-tradeoffs');
      if (!active) {
        if (takeEl) takeEl.textContent = 'Select at least 2 setups to compare them side by side.';
        if (tradeEl) tradeEl.classList.add('is-hidden');
        return;
      }
      renderTable(ids);
      // B2/C3: the directional "Tradeoffs" paragraph below the table.
      if (tradeEl) {
        var tradeText = tradeoffParagraph(sel);
        var tradeTextEl = document.getElementById('compare-tradeoffs-text');
        if (tradeTextEl) tradeTextEl.textContent = tradeText;
        tradeEl.classList.toggle('is-hidden', !tradeText);
      }
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
    byId: byId,
    // B2/C3 decision support
    DIMS: DIMS,
    parseContext: parseContext,
    parsePower: parsePower,
    estimateVram: estimateVram,
    fmtRatio: fmtRatio,
    winnerFor: winnerFor,
    tradeoffSentences: tradeoffSentences,
    giveupSentence: giveupSentence,
    tradeoffParagraph: tradeoffParagraph
  };

  // Boot: pick the mode from what is present.
  if (document.getElementById('compare-table-wrap')) {
    initComparePage();
  } else {
    initMatrix();
  }
})();
