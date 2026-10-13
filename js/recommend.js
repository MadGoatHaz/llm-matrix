// recommend.js — the client-side recommendation engine (P2-1).
//
// Answers "what should I run, on what I have, for what I need?" entirely in
// the browser. It reads the schema pick-lists from the #recommend-config
// island and the community submissions from the baked #commands-config
// island (no network request — the page works offline straight from disk,
// including file://), and ranks them against the user's VRAM tier, use case,
// vendor, and priority. A data.json fetch is kept only as a fallback for the
// (rare) case where the island is missing. No server, no frameworks, no
// dependencies.
//
// The hard gate is VRAM, estimated honestly (A3): a setup only appears if
// its ESTIMATED VRAM — an explicit "N GB" in its notes, else in its hardware
// description, else its tier band's ceiling — fits within the LOWER bound of
// the user's tier. Tiers are ranges ("16–23 GB"), so the floor is the only
// amount the user is guaranteed to have; a 16 GB card is shown only setups
// estimated at 16 GB or less, never the band's top. A setup that cannot be
// estimated never appears (no fit guarantee). Use case, vendor, and priority
// shape the ranking, and the submission's confidence + lifecycle state weight
// it (a superseded or discontinued setup ranks below a current one, and
// lower-corroborated reports rank below verified ones). The "quality"
// priority scores model capability (60%) blended with quant precision (40%)
// (B1) — matching the project's own quantization guide, where the model you
// pick matters more than the quant you pick. Every result carries a
// plain-English "why this matched" and a deep link to its row in the Matrix.

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
  // B1: quality = model capability (60%) + quant precision (40%).
  //
  // The project's own quantization guide says "the model you pick matters
  // more than the quant you pick" — a 35B-A3B I-Nano MoE beats a dense
  // 27B Q4 on a 16 GB card. Scoring the quality priority on quant bits
  // alone sank the community's best 16 GB answer (an I-Nano entry scored
  // 15 while a 27B Q4_K_M scored 40), so the quality rank is now a
  // weighted blend: the model's size/family does the heavy lifting and
  // the quant refines it. It is a HEURISTIC for ranking, not a physics
  // simulation — the goal is "don't sink capable small-quant models."
  // ------------------------------------------------------------------

  // Quant precision -> a 0-100 rank (B1: rebalanced scale). Higher = more
  // bits = less quality loss (and more VRAM). This is the 40% quant half
  // of the quality score; the 60% model half is modelCapabilityScore().
  // Derived from weight_precision, falling back to the quant string, then
  // the model name (several real submissions carry the quant only in the
  // name, e.g. "Qwen3.8-Flash-Next-Q4_K_M"). Longest token first so
  // "q4_k_m" beats "q4".
  var PRECISION_RANKS = [
    ['fp16', 100], ['bf16', 100],
    ['fp8', 85],
    ['int8', 75], ['w8a8', 75],
    ['q8_0', 75], ['q8', 75],
    ['q6_k', 60], ['q6', 60],
    ['q5_k_m', 50], ['q5', 50],
    ['q4_k_m', 40],
    ['ud-q4', 35], ['q4', 35],
    ['iq4_xs', 35], ['iq4', 35],
    ['iq3_s', 20], ['iq3', 20], ['q3', 20],
    ['i-nano', 20], ['nano', 20],
    ['ud-q2', 10], ['q2', 10]
  ];
  PRECISION_RANKS.sort(function (a, b) { return b[0].length - a[0].length; });

  function precisionRank(sub) {
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

  // Model capability -> a 0-100 score (B1: the 60% model half of quality).
  // Larger models and more capable families score higher:
  //   100B+ : 90 · 70B+ : 80 · 35B+ (or a MoE with 30B+ active) : 70 ·
  //   27B : 60 · 20B : 50 · 8-14B : 35 · <8B : 20
  // The size comes from model.params_total / model.params_active when the
  // data carries them; otherwise it is estimated from the model name
  // ("27B", "120B", "35B-A3B" — MoE names state total-then-active). No
  // size stated -> 50 (neutral, never sunk or inflated).
  function modelCapabilityScore(sub) {
    var model = (sub && sub.model) || {};
    var total = null, active = null;
    if (model.params_total != null && !isNaN(parseFloat(model.params_total))) {
      total = parseFloat(model.params_total);
    }
    if (model.params_active != null && !isNaN(parseFloat(model.params_active))) {
      active = parseFloat(model.params_active);
    }
    if (total == null) {
      var name = String(model.name || '').toUpperCase();
      var m = name.match(/(\d+(?:\.\d+)?)B(?:\s*-\s*A\s*(\d+(?:\.\d+)?)\s*B)?/);
      if (m) {
        total = parseFloat(m[1]);
        active = m[2] ? parseFloat(m[2]) : null;
      }
    }
    if (total == null || isNaN(total)) return 50;
    if (total >= 100) return 90;
    if (total >= 70) return 80;
    if (total >= 35 || (active != null && active >= 30)) return 70;
    if (total >= 27) return 60;
    if (total >= 20) return 50;
    if (total >= 8) return 35;
    return 20;
  }

  // A short model-size label for the "why this matched" line ("120B",
  // "35B-A3B"). Empty when the name states no size.
  function modelSizeLabel(sub) {
    var model = (sub && sub.model) || {};
    if (model.params_total != null && !isNaN(parseFloat(model.params_total))) {
      return parseFloat(model.params_total) + 'B';
    }
    var name = String(model.name || '').toUpperCase();
    var m = name.match(/(\d+(?:\.\d+)?)B(?:\s*-\s*A\s*(\d+(?:\.\d+)?)\s*B)?/);
    return m ? m[0].replace(/\s+/g, '') : '';
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
    var dataEl = document.getElementById('commands-config');
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
          precision: precisionRank(s),
          modelScore: modelCapabilityScore(s), // B1: 60% of quality
          modelSize: modelSizeLabel(s),
          confidence: s.confidence || 'community-reported',
          lifecycle: s.lifecycle || 'current'
        };
      });
      ready = true;
      render();
    }

    // A4: the submissions live in the baked #commands-config island (the same
    // island the Matrix detail panel reads), so the page makes no network
    // request and works offline straight from disk (file://). The island
    // carries every field the engine ranks on, including confidence +
    // lifecycle. A data.json fetch is the fallback, used only if the island is
    // missing for some reason (e.g. an older page).
    function boot() {
      var island = null;
      if (dataEl) {
        try { island = JSON.parse(dataEl.textContent); } catch (e) { island = null; }
      }
      if (island && Array.isArray(island.submissions) && island.submissions.length) {
        preload(island);
        return;
      }
      // Fallback: fetch data.json (it sits at the repo root; this page is one
      // level down, so the relative path resolves against the document URL).
      fetch('../data.json')
        .then(function (r) {
          if (!r.ok) throw new Error('HTTP ' + r.status);
          return r.json();
        })
        .then(preload)
        .catch(function (err) {
          resultsEl.innerHTML =
            '<div class="rec-error"><p>Couldn\'t load the community data. ' +
            'Reload the page — the rankings run entirely in your browser.</p></div>';
          console.error('recommend.js: failed to load data', err);
        });
    }
    boot();

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

    // A2: weight a submission by how well-corroborated and current it is.
    // Lifecycle is the strongest signal (a discontinued setup is shown last,
    // a superseded one clearly below the current field); within a lifecycle
    // tier the confidence level refines the weight. The multiplier keeps the
    // relative ordering inside each trust band intact while pushing lower-
    // trust entries down the list.
    function trustWeight(s) {
      var lifecycle = s.lifecycle || 'current';
      if (lifecycle === 'discontinued') return 0.2;
      if (lifecycle === 'superseded') return 0.4;
      if (lifecycle === 'watch') return 0.85; // between current and superseded
      var confidence = s.confidence || 'community-reported';
      if (confidence === 'op-verified') return 1.0;
      if (confidence === 'community-verified') return 0.95;
      if (confidence === 'community-reported') return 0.9;
      if (confidence === 'unverified') return 0.75;
      return 1.0;
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
        // B1: quality blends model capability (60%) with quant precision
        // (40%) — a capable small-quant model is no longer sunk.
        var qualityScore = s.modelScore * 0.6 + s.precision.rank * 0.4;
        var primary;
        if (sel.priority === 'speed') primary = speedScore;
        else if (sel.priority === 'quality') primary = qualityScore;
        else if (sel.priority === 'context') primary = contextScore;
        else primary = (speedScore + qualityScore + contextScore) / 3;

        var vendorBonus = (sel.vendor && s.vendor === sel.vendor) ? 8 : 0;
        var tierBonus = (s.tier === sel.tier) ? 6 : 2; // fits; exact tier preferred

        return {
          sub: s,
          total: (primary + vendorBonus + tierBonus) * trustWeight(s)
        };
      }).sort(function (a, b) { return b.total - a.total; });
    }

    // A2: a plain-English confidence phrase for the "why this matched" line —
    // the trust level a user can weigh when two setups score alike.
    function confidencePhrase(s) {
      var c = s.confidence || '';
      if (c === 'op-verified') return 'Op-verified setup';
      if (c === 'community-verified') return 'Community-verified setup';
      if (c === 'unverified') return 'Unverified report';
      return 'Recently reported';
    }

    // A one-line, plain-English "why this matched".
    function whyLine(s, sel) {
      var parts = [];
      var label = tierLabel[s.tier] || s.tier;
      // A3: "In your VRAM class" — the tier is a range, not a guarantee
      // (the card may need tuning to fit the user's exact GPU).
      if (s.tier === sel.tier) parts.push('In your ' + label + ' VRAM class');
      else parts.push('Fits in ' + label + ' — less VRAM than you have');
      if (sel.useCase && s.useCases.indexOf(sel.useCase) !== -1) {
        parts.push('Built for ' + sel.useCase);
      }
      if (sel.vendor && s.vendor === sel.vendor) parts.push('runs on ' + s.vendor);
      if (sel.priority === 'speed' && s.speed) parts.push(s.speed + ' t/s decode');
      else if (sel.priority === 'quality') {
        // B1: the quality blend is model + quant — show both halves.
        var qparts = [];
        if (s.modelSize) qparts.push(s.modelSize + ' model');
        if (s.precision.key !== 'unknown') qparts.push(s.precision.key + ' precision');
        if (qparts.length) parts.push(qparts.join(' · '));
      }
      else if (sel.priority === 'context' && s.context) parts.push(s.context.toLocaleString() + ' tokens of context');
      parts.push(confidencePhrase(s)); // A2: surface the trust level
      return parts.slice(0, 4).join(' · ');
    }

    // A2 + B4/C4: a small badge next to the contributor name showing how
    // well-corroborated the report is (green = verified, blue = community,
    // gray = unverified). It pairs the same colored dot the Matrix uses
    // (`.confidence-dot`) with the word label, so the trust system reads
    // identically across the matrix, the detail panel, and the results.
    function confidenceBadge(s) {
      var c = s.confidence || '';
      var dot, label, title;
      if (c === 'op-verified' || c === 'community-verified') {
        dot = 'verified'; label = '✓ verified'; title = 'Verified report';
      } else if (c === 'unverified') {
        dot = 'unverified'; label = 'unverified'; title = 'Unverified report';
      } else {
        dot = 'community'; label = 'community'; title = 'Community-reported';
      }
      return ' <span class="confidence-dot ' + dot + '" role="img" aria-label="' + title + '" title="' + title + '">●</span>' +
        ' <span class="rec-conf rec-conf-' + dot + '" title="' + title + '">' + label + '</span>';
    }

    // A2: a subtle label for non-current entries (superseded / discontinued),
    // so a stale setup is clearly marked without being hidden.
    function lifecycleLabel(s) {
      var l = s.lifecycle || 'current';
      if (l === 'superseded') {
        return '<div class="rec-lifecycle rec-lifecycle-superseded">older option</div>';
      }
      if (l === 'discontinued') {
        return '<div class="rec-lifecycle rec-lifecycle-discontinued">no longer recommended</div>';
      }
      return '';
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
            lifecycleLabel(s) +
            '<div class="rec-meta">' + esc(s.hardware) +
              (s.vendor ? ' · ' + esc(s.vendor) : '') +
              (s.backend ? ' · ' + esc(shortBackend(s.backend)) : '') + '</div>' +
            '<div class="rec-badges">' + badges.join(' ') + '</div>' +
            '<p class="rec-why"><strong>Why:</strong> ' + esc(whyLine(s, sel)) + '</p>' +
            '<div class="rec-actions">' + actions + '</div>' +
            '<div class="rec-contributor">by <strong>' + esc(s.username) + '</strong>' + confidenceBadge(s) + '</div>' +
          '</div>' +
        '</article>';
    }

    // ----------------------------------------------------------------
    // A3: honest VRAM fitting (client-side port of the generator's
    // estimate_vram_gb, which is the single source of truth)
    // ----------------------------------------------------------------

    // The first "N GB" figure in a string.
    function firstGb(s) {
      if (!s) return null;
      var m = String(s).match(/(\d+(?:\.\d+)?)\s*GB/i);
      return m ? parseFloat(m[1]) : null;
    }

    // Best-known VRAM footprint of a submission, in GB: an explicit
    // "N GB" in the notes, then the hardware description, then the tier
    // band's ceiling (the documented fallback). Null when none of the
    // three yields a number — no estimate means no fit guarantee.
    function estimateVram(s) {
      var gb = firstGb(s.notes);
      if (gb !== null) return gb;
      gb = firstGb(s.hardware);
      if (gb !== null) return gb;
      var tier = null;
      (config.tiers || []).forEach(function (t) {
        if (t.id === s.tier) tier = t;
      });
      if (tier && tier.range) return tier.range[1];
      return null;
    }

    // The user's VRAM ceiling = the LOWER bound of their tier. A tier is a
    // range, so a user at its bottom can only guarantee the floor. t1's
    // floor is 0 (uninformative), so 8 GB — the practical floor of small
    // cards — serves as its ceiling.
    function vramCeiling(tierId) {
      var tier = null;
      (config.tiers || []).forEach(function (t) {
        if (t.id === tierId) tier = t;
      });
      if (!tier || !tier.range) return null;
      return Math.max(tier.range[0], 8);
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

      // A3: hard gate on ESTIMATED VRAM, not tier order. The setup's
      // estimate (notes > hardware > tier-band ceiling) must fit within the
      // LOWER bound of the user's tier — the only amount the user is
      // guaranteed to have. A setup that cannot be estimated never appears.
      var ceiling = vramCeiling(sel.tier);
      var compatible = (ceiling !== null) ?
        subs.filter(function (s) {
          var est = estimateVram(s);
          return est !== null && est <= ceiling;
        }) :
        [];

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
