// recommend.js — the client-side recommendation engine (P2-1).
//
// Answers "what should I run, on what I have, for what I need?" entirely in
// the browser. It reads the schema pick-lists from the #recommend-config
// island, fetches the local data.json (one request, cached), and ranks the
// community's real submissions against the user's VRAM tier, use case,
// vendor, and priority. No server, no frameworks, no dependencies.
//
// The hard gate is VRAM: a setup only appears if it fits the user's tier (or
// a smaller one). Use case, vendor, and priority shape the ranking. Every
// result carries a plain-English "why this matched" and a deep link to its
// row in the Matrix.

(function () {
  'use strict';

  // ------------------------------------------------------------------
  // Free-text use case -> schema category.
  // A submission's use_cases is free text; we match keywords against the
  // canonical schema use cases so a user picking "Agentic Coding" finds
  // "LLM-assisted coding / technical documentation".
  // ------------------------------------------------------------------
  var USE_CASE_KEYWORDS = {
    'Agentic Coding': ['coding', 'code', 'agentic', 'programming', 'developer', 'software', 'judge', 'opencode'],
    'Repo Editing': ['repo', 'repository', 'codebase'],
    'Deep Reasoning': ['reasoning', 'deep reason', 'think', 'analysis'],
    'Math/Logic': ['math', 'logic', 'arithmetic', 'calculat'],
    'RAG': ['rag', 'retrieval'],
    'Document Ingestion': ['document', 'ingest', 'q&a', 'qa'],
    'Creative Writing': ['creative', 'writing', 'story', 'fiction'],
    'Roleplay': ['roleplay', 'character'],
    'General Chat': ['chat', 'conversation', 'general', 'brainstorm', 'planning'],
    'Translation': ['translation', 'translate', 'language'],
    'Security Research': ['security', 'dos', 'vulnerab', 'exploit'],
    'Multimodal': ['multimodal', 'vision', 'image', 'audio', 'video'],
    'Production Serving': ['production', 'serving', 'api', 'openai-compatible'],
    'Embeddings': ['embedding']
  };

  // True if ``kw`` occurs in ``text`` (already lowercased). Single
  // alphanumeric tokens require word boundaries (so "rag" never matches
  // "storage"); multi-word / punctuated tokens use a substring match.
  function keywordIn(text, kw) {
    if (kw.indexOf(' ') === -1 && /^[a-z0-9]+$/.test(kw)) {
      return new RegExp('\\b' + kw + '\\b').test(text);
    }
    return text.indexOf(kw) !== -1;
  }

  // The set of schema use-case categories a free-text string covers.
  function matchUseCases(raw) {
    if (!raw) return [];
    var s = String(raw).toLowerCase();
    var out = [];
    Object.keys(USE_CASE_KEYWORDS).forEach(function (cat) {
      var kws = USE_CASE_KEYWORDS[cat];
      for (var i = 0; i < kws.length; i++) {
        if (keywordIn(s, kws[i])) { out.push(cat); break; }
      }
    });
    return out;
  }

  // ------------------------------------------------------------------
  // Model precision -> a 0-100 quality rank. Higher = more bits = better
  // quality (and more VRAM). Derived from weight_precision, falling back to
  // the quant string. Longest token first so "q4_k_m" beats "q4".
  // ------------------------------------------------------------------
  var PRECISION_RANKS = [
    ['fp16', 100], ['bf16', 95],
    ['fp8', 85], ['int8', 85], ['w8a8', 85],
    ['q8_0', 70], ['q8', 70],
    ['q6_k', 60], ['q6', 60],
    ['q5_k_m', 52], ['q5', 50],
    ['q4_k_m', 40], ['ud-q4', 40], ['q4', 40],
    ['iq4_xs', 35], ['iq4', 35],
    ['iq3_s', 30], ['iq3', 30], ['q3', 25],
    ['i-nano', 15], ['nano', 15], ['ud-q2', 15], ['q2', 15]
  ];
  PRECISION_RANKS.sort(function (a, b) { return b[0].length - a[0].length; });

  function precisionRank(sub) {
    // weight_precision first, then quant, then the model name (several real
    // submissions leave the first two empty but carry the quant in the name,
    // e.g. "Qwen3.8-Flash-Next-Q4_K_M").
    var src = String(
      sub.weight_precision || sub.quant || (sub.model && sub.model.name) || ''
    ).toLowerCase();
    if (!src) return { key: 'unknown', rank: 50 };
    for (var i = 0; i < PRECISION_RANKS.length; i++) {
      if (src.indexOf(PRECISION_RANKS[i][0]) !== -1) {
        return { key: PRECISION_RANKS[i][0], rank: PRECISION_RANKS[i][1] };
      }
    }
    return { key: 'unknown', rank: 50 };
  }

  // First numeric token of a decode-speed string, as a float (matches the
  // Python parse_speed convention).
  function parseSpeed(tps) {
    if (!tps) return 0;
    var m = String(tps).match(/(\d+(?:\.\d+)?)/);
    return m ? parseFloat(m[1]) : 0;
  }

  // Context length in tokens from the "stable" string ("65536", "~240k", …).
  function parseContext(stable) {
    if (!stable) return 0;
    var m = String(stable).toLowerCase().match(/(\d+(?:\.\d+)?)\s*(k|m|million)?/);
    if (!m) return 0;
    var n = parseFloat(m[1]);
    if (m[2] === 'k') n *= 1000;
    else if (m[2] === 'm' || m[2] === 'million') n *= 1e6;
    return Math.round(n);
  }

  // ------------------------------------------------------------------
  // Small helpers
  // ------------------------------------------------------------------
  function esc(value) {
    var div = document.createElement('div');
    div.textContent = (value == null) ? '' : String(value);
    return div.innerHTML;
  }

  function shortModel(name) {
    if (!name) return '';
    var s = String(name).split(',')[0].trim();
    if (s.indexOf('/') !== -1 && s.indexOf('http') !== 0) s = s.split('/')[1];
    return s;
  }

  function shortBackend(b) {
    if (!b) return '';
    return String(b).replace(/\(.*$/, '').trim();
  }

  // The submission path: the static /submit/ form (P3-4). The recommend page
  // lives at depth 1, so the form is reached at ../submit/.
  var SUBMIT_URL = '../submit/';

  // ------------------------------------------------------------------
  // Boot
  // ------------------------------------------------------------------
  document.addEventListener('DOMContentLoaded', function () {
    var configEl = document.getElementById('recommend-config');
    var tierSel = document.getElementById('rec-tier');
    var useSel = document.getElementById('rec-usecase');
    var vendorSel = document.getElementById('rec-vendor');
    var prioritySel = document.getElementById('rec-priority');
    var resultsEl = document.getElementById('rec-results');
    if (!configEl || !tierSel || !resultsEl) return; // not the recommend page

    var config = JSON.parse(configEl.textContent);
    var tierIndex = {}, tierLabel = {};
    config.tiers.forEach(function (t, i) { tierIndex[t.id] = i; tierLabel[t.id] = t.label; });

    var subs = [];
    var ready = false;

    // Precompute the derived fields once, up front.
    function preload(data) {
      subs = (data.submissions || []).map(function (s) {
        return {
          id: s.id,
          tier: s.tier,
          tierIdx: (s.tier && tierIndex[s.tier] != null) ? tierIndex[s.tier] : 99,
          vendor: (s.hardware && s.hardware.vendor) ? s.hardware.vendor : '',
          hardware: (s.hardware && s.hardware.description) ? s.hardware.description : '',
          backend: s.backend || '',
          model: (s.model && s.model.name) ? s.model.name : '',
          modelUrl: (s.model && s.model.url) ? s.model.url : '',
          username: (s.source && s.source.username) ? s.source.username : '',
          useCases: matchUseCases(s.use_cases),
          speed: parseSpeed(s.performance && s.performance.decode_tps),
          context: parseContext(s.context && s.context.stable),
          precision: precisionRank(s)
        };
      });
      ready = true;
      render();
    }

    // data.json sits at the repo root; this page is one level down. The
    // relative path resolves against the document URL, not the script.
    fetch('../data.json')
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then(preload)
      .catch(function (err) {
        resultsEl.innerHTML =
          '<div class="rec-error"><p>Couldn\'t load the community data ' +
          '(<code>data.json</code>). If you opened this file straight from ' +
          'disk, serve it over HTTP — the rankings run entirely in your ' +
          'browser.</p></div>';
        console.error('recommend.js: failed to load data.json', err);
      });

    [tierSel, useSel, vendorSel, prioritySel].forEach(function (el) {
      if (el) el.addEventListener('change', render);
    });

    // ----------------------------------------------------------------
    // Ranking
    // ----------------------------------------------------------------
    function currentSelection() {
      return {
        tier: tierSel.value,
        useCase: useSel ? useSel.value : '',
        vendor: vendorSel ? vendorSel.value : '',
        priority: prioritySel ? prioritySel.value : 'balanced'
      };
    }

    // Score + sort a pool of submissions for the given selection.
    function scorePool(pool, sel) {
      if (!pool.length) return [];
      var maxSpeed = 0, maxContext = 0;
      pool.forEach(function (s) {
        if (s.speed > maxSpeed) maxSpeed = s.speed;
        if (s.context > maxContext) maxContext = s.context;
      });
      return pool.map(function (s) {
        var speedScore = maxSpeed ? (s.speed / maxSpeed) * 100 : 0;
        var contextScore = maxContext ? (s.context / maxContext) * 100 : 0;
        var qualityScore = s.precision.rank;
        var primary;
        if (sel.priority === 'speed') primary = speedScore;
        else if (sel.priority === 'quality') primary = qualityScore;
        else if (sel.priority === 'context') primary = contextScore;
        else primary = (speedScore + qualityScore + contextScore) / 3;

        var vendorBonus = (sel.vendor && s.vendor === sel.vendor) ? 8 : 0;
        var tierBonus = (s.tier === sel.tier) ? 6 : 2; // fits; exact tier preferred

        return {
          sub: s,
          total: primary + vendorBonus + tierBonus
        };
      }).sort(function (a, b) { return b.total - a.total; });
    }

    // A one-line, plain-English "why this matched".
    function whyLine(s, sel) {
      var parts = [];
      var label = tierLabel[s.tier] || s.tier;
      if (s.tier === sel.tier) parts.push('Sized for your ' + label + ' card');
      else parts.push('Fits in ' + label + ' — less VRAM than you have');
      if (sel.useCase && s.useCases.indexOf(sel.useCase) !== -1) {
        parts.push('Built for ' + sel.useCase);
      }
      if (sel.vendor && s.vendor === sel.vendor) parts.push('runs on ' + s.vendor);
      if (sel.priority === 'speed' && s.speed) parts.push(s.speed + ' t/s decode');
      else if (sel.priority === 'quality' && s.precision.key !== 'unknown') parts.push(s.precision.key + ' precision');
      else if (sel.priority === 'context' && s.context) parts.push(s.context.toLocaleString() + ' tokens of context');
      return parts.slice(0, 3).join(' · ');
    }

    function cardHtml(rank, entry, sel) {
      var s = entry.sub;
      var badges = [];
      if (s.speed) badges.push('<span class="badge badge-blue">' + s.speed + ' t/s</span>');
      if (s.context) badges.push('<span class="badge badge-cyan">' + s.context.toLocaleString() + ' ctx</span>');
      if (s.precision.key !== 'unknown') badges.push('<span class="badge badge-purple">' + esc(s.precision.key) + '</span>');
      badges.push('<span class="badge badge-amber">' + esc(tierLabel[s.tier] || s.tier) + '</span>');

      var actions = '<button class="btn launch-card-btn" data-launch-sub="' + esc(s.id) + '" aria-label="Copy launch command for ' + esc(shortModel(s.model)) + '">🚀 Copy launch command</button>' +
        ' <a href="../matrix.html#' + esc(s.id) + '">View in the Matrix →</a>';
      if (s.modelUrl && /^https?:/.test(s.modelUrl)) {
        actions += ' <a href="' + esc(s.modelUrl) + '" target="_blank" rel="noopener">Download</a>';
      }

      return '' +
        '<article class="rec-card">' +
          '<div class="rec-rank" aria-hidden="true">' + rank + '</div>' +
          '<div class="rec-body">' +
            '<h3 class="rec-model">' + esc(shortModel(s.model)) + '</h3>' +
            '<div class="rec-meta">' + esc(s.hardware) +
              (s.vendor ? ' · ' + esc(s.vendor) : '') +
              (s.backend ? ' · ' + esc(shortBackend(s.backend)) : '') + '</div>' +
            '<div class="rec-badges">' + badges.join(' ') + '</div>' +
            '<p class="rec-why"><strong>Why:</strong> ' + esc(whyLine(s, sel)) + '</p>' +
            '<div class="rec-actions">' + actions + '</div>' +
            '<div class="rec-contributor">by <strong>' + esc(s.username) + '</strong></div>' +
          '</div>' +
        '</article>';
    }

    // ----------------------------------------------------------------
    // Render
    // ----------------------------------------------------------------
    function render() {
      if (!ready) return;
      var sel = currentSelection();

      if (!sel.tier) {
        resultsEl.innerHTML =
          '<div class="rec-placeholder"><p>Pick your VRAM above and the ' +
          'community\'s best fits will appear here.</p></div>';
        return;
      }

      var userTierIdx = tierIndex[sel.tier];
      // Hard gate: the setup must fit (its tier index <= the user's).
      var compatible = subs.filter(function (s) { return s.tierIdx <= userTierIdx; });

      var pool = compatible;
      var emptyForUseCase = false;
      if (sel.useCase) {
        var matched = compatible.filter(function (s) {
          return s.useCases.indexOf(sel.useCase) !== -1;
        });
        if (matched.length) pool = matched;
        else emptyForUseCase = true;
      }

      var ranked = scorePool(pool, sel);
      var html = '';

      if (emptyForUseCase) {
        var label = tierLabel[sel.tier] || sel.tier;
        html +=
          '<div class="rec-empty">' +
            '<h3>No ' + esc(sel.useCase) + ' setups in your ' + esc(label) + ' tier yet</h3>' +
            '<p>The community hasn\'t submitted a ' + esc(sel.useCase) + ' model that ' +
            'fits ' + esc(label) + ' VRAM. Here are the closest fits in your tier ' +
            '(any use case) — and if you know one that would work, ' +
            '<a href="' + SUBMIT_URL + '">submit it to the thread →</a></p>' +
          '</div>';
      }

      if (ranked.length) {
        html += '<div class="rec-list">';
        ranked.forEach(function (entry, i) {
          html += cardHtml(i + 1, entry, sel);
        });
        html += '</div>';
        html += '<p class="rec-count">' + ranked.length +
          (ranked.length === 1 ? ' setup' : ' setups') +
          ' fit your selection · all community-reported</p>';
      } else if (!emptyForUseCase) {
        html +=
          '<div class="rec-empty"><h3>Nothing fits yet</h3>' +
          '<p>No community setup matches that combination. Try clearing an ' +
          'option, or <a href="' + SUBMIT_URL + '">submit the first one →</a></p></div>';
      }

      resultsEl.innerHTML = html;
    }
  });
})();
