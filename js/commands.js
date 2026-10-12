// commands.js — the client-side launch-command generator (P2-3).
//
// Turns any community submission into a representative, copy-able command for
// its inference backend — plus an honest VRAM estimate, "what to expect" on a
// first run, and a couple of contextual tips. It runs entirely in the browser:
// the page bakes a #commands-config JSON island (the trimmed submissions + the
// schema's backend/tier lists) so there is no network request and it works
// offline straight from disk.
//
// Every command is clearly labeled an *example* (not a guarantee): the model
// path and a few flags will differ on your machine. Backends we have a solid
// template for (llama.cpp, llama-swap, Ollama, vLLM, Radiance, MLX, …) get a
// concrete command; GUI backends (LM Studio, Unsloth Desktop) get steps; and
// anything unknown degrades gracefully to the model + a "check the guide" note
// rather than a fabricated flag.
//
// Access points: a "🚀" button on each Matrix row, on each Recommend result
// card, and on each Compare column — all wired through ONE document-level
// click handler (event delegation), so dynamically-created buttons work too.
// The Backends guide also embeds a small "pick a backend → example command"
// picker that reuses the same map.
//
// The pure helpers are exposed on window.LaunchCommand for the test suite.

(function () {
  'use strict';

  var configEl = document.getElementById('commands-config');
  if (!configEl) return; // not a page that uses the command generator
  var config;
  try { config = JSON.parse(configEl.textContent); }
  catch (e) { console.error('commands.js: bad config island', e); return; }

  // id -> submission lookup.
  var byId = {};
  (config.submissions || []).forEach(function (s) { byId[s.id] = s; });

  // ------------------------------------------------------------------
  // Small helpers
  // ------------------------------------------------------------------
  function esc(value) {
    var div = document.createElement('div');
    div.textContent = (value == null) ? '' : String(value);
    return div.innerHTML;
  }

  // Replicates the generator's normalize_backend():
  // 'vLLM (…MTP=8)' -> 'vLLM', 'Strata 0.1.42' -> 'Strata', 'llamacpp' -> 'llama.cpp'.
  var BACKEND_ALIASES = {
    'llamacpp': 'llama.cpp',
    'llama-cpp': 'llama.cpp',
    'llama cpp': 'llama.cpp'
  };
  function normalizeBackend(raw, backends) {
    if (!raw) return '';
    var s = String(raw).trim();
    s = s.replace(/\(.*$/, '').trim();        // drop trailing parenthetical
    s = s.replace(/\s+\d[\w.]*$/, '').trim(); // drop trailing version
    if (!s) return '';
    var alias = BACKEND_ALIASES[s.toLowerCase()];
    if (alias) return alias;
    backends = backends || (config && config.backends) || [];
    for (var i = 0; i < backends.length; i++) {
      if (String(backends[i]).toLowerCase() === s.toLowerCase()) return backends[i];
    }
    return s;
  }

  // First model of a (possibly comma-separated) name, repo prefix + trailing
  // parenthetical stripped.
  function firstModel(name) {
    if (!name) return '';
    var s = String(name).split(',')[0].trim();
    s = s.replace(/\s*\([^)]*\)\s*$/g, '').trim();
    if (s.indexOf('/') !== -1 && s.indexOf('http') !== 0) s = s.split('/').pop();
    return s;
  }

  // A plausible local .gguf filename for llama.cpp / llama-swap / Strata.
  function modelFile(name) {
    var s = firstModel(name).replace(/\.gguf$/i, '').trim();
    if (!s) s = 'model';
    return s + '.gguf';
  }

  // A Hugging Face repo id (org/name) for vLLM / MLX / TensorRT-LLM.
  function repoId(name) {
    if (!name) return '<org/model>';
    var s = String(name).split(',')[0].trim().replace(/\s*\([^)]*\)\s*$/g, '').trim();
    if (s.indexOf('http') === 0) return s; // keep an explicit URL as-is
    if (s.indexOf('/') !== -1) return s;   // already org/name
    return s;
  }

  // A best-guess Ollama tag (name:size-quant). Clearly labeled a guess.
  function ollamaTag(name) {
    var s = firstModel(name).toLowerCase().replace(/\.gguf$/, '');
    var m = s.match(/^(.+?)-(\d+(?:\.\d+)?)b(-.+)?$/);
    if (m) return m[1] + ':' + m[2] + 'b' + (m[3] || '');
    return s;
  }

  // Context length in tokens from the free-text "stable" string.
  function parseContext(stable) {
    if (!stable) return 0;
    var s = String(stable).toLowerCase();
    var m = s.match(/(\d+(?:\.\d+)?)\s*(k|m|million)?/);
    if (!m) return 0;
    var n = parseFloat(m[1]);
    if (m[2] === 'k') n *= 1000;
    else if (m[2] === 'm' || m[2] === 'million') n *= 1e6;
    return Math.round(n) || 0;
  }

  function parseSpeed(tps) {
    if (!tps) return 0;
    var m = String(tps).match(/(\d+(?:\.\d+)?)/);
    return m ? parseFloat(m[1]) : 0;
  }

  // How many GPUs the hardware line implies ("2x R9700" -> 2).
  function countGpus(hw) {
    var s = String(hw || '').toLowerCase();
    var m = s.match(/(\d+)\s*[x×]\s/);
    if (m) return parseInt(m[1], 10);
    if (s.indexOf('dual') !== -1) return 2;
    return 1;
  }

  // Map a free-text KV-cache string to a llama.cpp --cache-type-k value.
  function kvQuant(kv) {
    var s = String(kv || '').toLowerCase();
    if (!s || s.indexOf('unquantized') !== -1 || s.indexOf('fp16') !== -1 || s.indexOf('f16') !== -1) return '';
    if (s.indexOf('q8') !== -1 || s.indexOf('int8') !== -1) return 'q8_0';
    if (s.indexOf('q4') !== -1 || s.indexOf('iq4') !== -1) return 'q4_0';
    if (s.indexOf('fp8') !== -1 || s.indexOf('f8') !== -1) return 'f8_0';
    return '';
  }

  // A specific "N GB" figure from the notes (usage), else the hardware line.
  function findGb(s) {
    if (!s) return null;
    var m = String(s).match(/(\d+(?:\.\d+)?)\s*GB\b/i);
    return m ? parseFloat(m[1]) : null;
  }

  function estimateVram(sub) {
    var tierInfo = null;
    (config.tiers || []).forEach(function (t) { if (t.id === sub.tier) tierInfo = t; });
    var label = tierInfo ? tierInfo.label : (sub.tier || '');
    var n = findGb(sub.notes);
    if (n == null) n = findGb((sub.hardware || {}).description);
    var text;
    if (n != null) text = '~' + n + ' GB (community-reported)';
    else if (label) text = 'Fits the ' + label + ' tier';
    else text = 'Not specified';
    return { text: text, gb: n, label: label };
  }

  // ------------------------------------------------------------------
  // The backend -> command map.
  // Each template receives ``m`` = { modelFile, repoId, ollamaTag, ctx,
  // kvQuant, gpus } and returns { command?, gui?, isGui?, expect, note? }.
  // ------------------------------------------------------------------
  var COMMAND_MAP = {
    'llama.cpp': function (m) {
      var cmd = 'llama-server -m ' + m.modelFile + ' -ngl 99 -c ' + m.ctx;
      if (m.kvQuant) cmd += ' --cache-type-k ' + m.kvQuant + ' --cache-type-v ' + m.kvQuant;
      if (m.gpus > 1) cmd += ' --tensor-parallel-size ' + m.gpus;
      return {
        command: cmd,
        expect: 'First run: download the .gguf from Hugging Face, then llama-server loads it into VRAM (10–60s for a 27B). It then serves a chat UI + OpenAI-compatible API on http://localhost:8080.'
      };
    },
    'llama-swap': function (m) {
      return {
        command: 'llama-swap serve --port 8080',
        expect: 'llama-swap runs one llama-server subprocess per model and keeps them warm, so switching models is near-instant. Add the model to your llama-swap config first — the underlying process is: llama-server -m ' + m.modelFile + ' -ngl 99 -c ' + m.ctx + '.'
      };
    },
    'Ollama': function (m) {
      return {
        command: 'ollama run ' + m.ollamaTag,
        expect: 'First run pulls the model from the Ollama registry (a few GB) — allow time for the download. After that `ollama run` starts it instantly and it stays cached.'
      };
    },
    'vLLM': function (m) {
      var cmd = 'vllm serve ' + m.repoId + ' --max-model-len ' + m.ctx;
      if (m.gpus > 1) cmd += ' --tensor-parallel-size ' + m.gpus;
      return {
        command: cmd,
        expect: 'First run: vLLM pulls the model (safetensors) and loads it — a longer cold start than llama.cpp. After that it serves an OpenAI-compatible API on http://localhost:8000, tuned for throughput.'
      };
    },
    'Radiance': function (m) {
      var cmd = 'vllm serve ' + m.repoId + ' --max-model-len ' + m.ctx;
      if (m.gpus > 1) cmd += ' --tensor-parallel-size ' + m.gpus;
      return {
        command: cmd,
        expect: 'Radiance is AMD\'s tuned vLLM build (the magiccodingman/vllm-radiance fork). Install it, then serve the model as shown — same OpenAI-compatible API with ROCm optimizations and speculative decoding.',
        note: 'AMD Radiance — a tuned vLLM.'
      };
    },
    'Strata': function (m) {
      return {
        command: 'strata serve ' + m.modelFile,
        expect: 'Strata is a hybrid engine: weights split across VRAM → RAM → SSD, so a big model fits on a small card. You need the system RAM this setup reports. The first load reads from NVMe, then it warms up.',
        note: 'Hybrid VRAM+RAM+SSD — see the Multi-GPU & Hybrid guide for the full config.'
      };
    },
    'MLX': function (m) {
      return {
        command: 'mlx_lm.server --model ' + m.repoId + ' --port 8080',
        expect: 'MLX runs on Apple\'s unified memory (no separate VRAM to size). First run downloads the model; after that it serves on http://localhost:8080.'
      };
    },
    'Colibri': function (m) {
      return {
        command: 'colibri serve ' + m.modelFile,
        expect: 'Colibri is a CPU+GPU hybrid for very large models (think 1TB-RAM boxes). Expect modest throughput — it trades speed for fitting models that would never fit in VRAM alone.',
        note: 'Representative command — check the Colibri docs for your version\'s exact flags.'
      };
    },
    'TensorRT-LLM': function (m) {
      return {
        command: 'trtllm-build --model ' + m.repoId + ' && trtllm-serve ' + m.repoId,
        expect: 'TensorRT-LLM needs a build step (trtllm-build) before it can serve. It is the fastest path on NVIDIA datacenter GPUs but the most setup.',
        note: 'NVIDIA only — two-step build + serve. See the Backends guide.'
      };
    },
    'LM Studio': function () {
      return {
        isGui: true,
        gui: [
          'Open LM Studio',
          'Go to “My Models” and search for the model — or import your local .gguf file',
          'Click “Load” and set GPU Offload to the maximum bars',
          'Switch to the “Chat” tab and start'
        ],
        expect: 'LM Studio is a GUI — no command line. It downloads the model for you, so the first load takes a while; after that loading is instant.'
      };
    },
    'Unsloth Desktop': function () {
      return {
        isGui: true,
        gui: [
          'Open Unsloth Desktop',
          'Search for the model, or load a local .gguf / safetensors file',
          'Set the GPU offload, then open the chat'
        ],
        expect: 'Unsloth Desktop is an all-in-one GUI (llama.cpp + a vLLM backend under the hood). It handles the download, loading, and serving for you.'
      };
    }
  };

  // ------------------------------------------------------------------
  // Generate the full result for a submission.
  // ------------------------------------------------------------------
  function buildTips(sub, backend, m) {
    var tips = [];
    var wp = String((sub.weight_precision || sub.quant) || '').toLowerCase();
    var name = String((sub.model || {}).name || '').toLowerCase();
    var highPrecision = /fp8|fp16|bf16|int8|w8a8|q8/.test(wp);
    if (highPrecision && name.indexOf('moe') === -1) {
      tips.push('If this doesn\'t fit your VRAM, try the Q4_K_M quant — it roughly halves the memory for a small quality cost.');
    }
    if (/moe|a3b|a4b|a2b/.test(name)) {
      tips.push('This is a Mixture-of-Experts model — it fits in far less VRAM than its total param count suggests, because only the active experts compute per token.');
    }
    if (String(sub.engine_mode || '').toLowerCase().indexOf('hybrid') !== -1) {
      tips.push('This setup offloads to system RAM/SSD — make sure you have the RAM the submission reports before running it.');
    }
    var sp = parseSpeed((sub.performance || {}).decode_tps);
    if (sp && sp < 20) {
      tips.push('This is a slow decode (a large dense model on a small card). For interactive use, a smaller or MoE model feels much snappier.');
    }
    if (backend === 'Ollama') {
      tips.push('Ollama pulls by tag from its registry — if this exact tag 404s, search the Ollama library or `ollama pull` the closest match.');
    }
    return tips.slice(0, 3);
  }

  function generate(sub) {
    var backend = normalizeBackend(sub.backend, config.backends);
    var m = {
      modelFile: modelFile((sub.model || {}).name),
      repoId: repoId((sub.model || {}).name),
      ollamaTag: ollamaTag((sub.model || {}).name),
      ctx: parseContext((sub.context || {}).stable) || 4096,
      kvQuant: kvQuant((sub.context || {}).kv_cache),
      gpus: countGpus((sub.hardware || {}).description)
    };
    var vram = estimateVram(sub);
    var tips = buildTips(sub, backend, m);
    var display = firstModel((sub.model || {}).name) || (sub.model || {}).name || 'Model';

    var fn = COMMAND_MAP[backend];
    if (!fn) {
      // Graceful degradation: no fabricated flags.
      return {
        backend: backend,
        isUnknown: true,
        command: '',
        model: display,
        vram: vram,
        expect: 'We don\'t have a command template for this backend yet.',
        note: 'Check the Backends guide for how to run ' + (backend || 'this setup') + '.',
        tips: tips
      };
    }
    var res = fn(m);
    res.backend = backend;
    res.model = display;
    res.vram = vram;
    res.tips = tips;
    res.isGui = !!res.isGui;
    res.gui = res.gui;
    res.isExample = true;
    return res;
  }

  // A generic per-backend example (used by the Backends guide picker).
  function generateForBackend(backend) {
    var m = {
      modelFile: '<your-model>.gguf',
      repoId: '<org/model>',
      ollamaTag: '<model>',
      ctx: 8192,
      kvQuant: '',
      gpus: 1
    };
    var fn = COMMAND_MAP[backend];
    if (!fn) {
      return {
        backend: backend, isUnknown: true, command: '',
        model: backend, vram: { text: 'Depends on your model + quant' },
        expect: 'We don\'t have a command template for this backend yet.',
        note: 'Check the Backends guide for how to run it.', tips: []
      };
    }
    var res = fn(m);
    res.backend = backend;
    res.model = backend + ' (example)';
    res.vram = { text: 'Depends on the model + quant you pick' };
    res.tips = [];
    res.isGui = !!res.isGui;
    res.gui = res.gui;
    res.isExample = true;
    return res;
  }

  // ------------------------------------------------------------------
  // The shared command dialog
  // ------------------------------------------------------------------
  var dialog = null;
  var lastFocused = null;

  function buildDialog() {
    var overlay = document.createElement('div');
    overlay.className = 'cmd-overlay';
    overlay.hidden = true;
    overlay.innerHTML =
      '<div class="cmd-dialog" role="dialog" aria-modal="true" aria-labelledby="cmd-title">' +
        '<div class="cmd-header">' +
          '<h2 id="cmd-title">🚀 Launch command</h2>' +
          '<button class="cmd-close" aria-label="Close dialog">✕</button>' +
        '</div>' +
        '<div class="cmd-model" id="cmd-model"></div>' +
        '<div class="cmd-note" id="cmd-note"></div>' +
        '<div class="cmd-body" id="cmd-body"></div>' +
      '</div>';
    document.body.appendChild(overlay);

    // Focus trap: keep Tab cycling inside the open dialog.
    overlay.addEventListener('keydown', function (e) {
      if (e.key !== 'Tab') return;
      var focusables = overlay.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      if (!focusables.length) return;
      var first = focusables[0];
      var last = focusables[focusables.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault(); last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault(); first.focus();
      }
    });
    return overlay;
  }

  function renderResultBody(result) {
    var html = '';
    if (result.isGui) {
      html += '<div class="cmd-steps"><ol>' +
        (result.gui || []).map(function (s) { return '<li>' + esc(s) + '</li>'; }).join('') +
        '</ol></div>';
    } else if (result.command) {
      html += '<div class="cmd-code-wrap">' +
        '<pre class="cmd-code"><code>' + esc(result.command) + '</code></pre>' +
        '<button class="btn btn-primary cmd-copy" data-copy="' + esc(result.command) + '">📋 Copy command</button>' +
        '</div>';
    }
    if (result.vram) {
      html += '<div class="cmd-meta"><span class="cmd-meta-label">Expected VRAM</span> ' +
        esc(result.vram.text) + '</div>';
    }
    if (result.expect) {
      html += '<div class="cmd-expect"><span class="cmd-meta-label">What to expect</span>' +
        '<p>' + esc(result.expect) + '</p></div>';
    }
    if (result.tips && result.tips.length) {
      html += '<div class="cmd-tips"><span class="cmd-meta-label">Good to know</span><ul>' +
        result.tips.map(function (t) { return '<li>' + esc(t) + '</li>'; }).join('') +
        '</ul></div>';
    }
    return html;
  }

  function setNote(result) {
    var el = document.getElementById('cmd-note');
    if (!el) return;
    if (result.isUnknown) {
      el.innerHTML = '<span class="cmd-flag cmd-flag--warn">⚠ ' + esc(result.note) + '</span>';
    } else if (result.isGui) {
      el.innerHTML = '<span class="cmd-flag">GUI application — no command line needed</span>';
    } else {
      var extra = result.note ? ' ' + esc(result.note) : '';
      el.innerHTML = '<span class="cmd-flag">Example command — adjust the model path / flags for your machine.' + extra + '</span>';
    }
  }

  function openDialog(result, triggerEl) {
    lastFocused = triggerEl || document.activeElement;
    var modelEl = document.getElementById('cmd-model');
    if (modelEl) {
      modelEl.innerHTML = '<strong>' + esc(result.model) + '</strong>' +
        (result.backend ? ' <span class="cmd-backend">· ' + esc(result.backend) + '</span>' : '');
    }
    setNote(result);
    var body = document.getElementById('cmd-body');
    if (body) body.innerHTML = renderResultBody(result);
    dialog.hidden = false;
    document.body.classList.add('cmd-open');
    var focusTarget = dialog.querySelector('.cmd-copy') || dialog.querySelector('.cmd-close');
    if (focusTarget) focusTarget.focus();
  }

  function closeDialog() {
    if (!dialog || dialog.hidden) return;
    dialog.hidden = true;
    document.body.classList.remove('cmd-open');
    if (lastFocused && typeof lastFocused.focus === 'function') lastFocused.focus();
  }

  function copyText(text, btn) {
    function done(ok) {
      if (!btn) return;
      var orig = btn.textContent;
      btn.textContent = ok ? '✓ Copied' : 'Copy failed';
      btn.disabled = true;
      setTimeout(function () { btn.textContent = orig; btn.disabled = false; }, 1500);
    }
    function fallback() {
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
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(
        function () { done(true); },
        function () { done(fallback()); }
      );
    } else {
      done(fallback());
    }
  }

  // ------------------------------------------------------------------
  // One document-level handler (event delegation) covers every access point.
  // ------------------------------------------------------------------
  document.addEventListener('click', function (e) {
    // Launch button for a specific submission.
    var launchBtn = e.target.closest ? e.target.closest('[data-launch-sub]') : null;
    if (launchBtn) {
      var sub = byId[launchBtn.getAttribute('data-launch-sub')];
      if (sub) {
        e.preventDefault();
        openDialog(generate(sub), launchBtn);
      }
      return;
    }
    // Copy button (inside the dialog or a guide picker output).
    var copyBtn = e.target.closest ? e.target.closest('.cmd-copy') : null;
    if (copyBtn) {
      e.preventDefault();
      copyText(copyBtn.getAttribute('data-copy'), copyBtn);
      return;
    }
    // Close the dialog (button or backdrop).
    if (dialog && !dialog.hidden) {
      if (e.target.closest ? e.target.closest('.cmd-close') : null) { closeDialog(); return; }
      if (e.target === dialog) { closeDialog(); return; }
    }
    // The Backends guide "pick a backend" picker.
    var pickBtn = e.target.closest ? e.target.closest('[data-cmd-generate]') : null;
    if (pickBtn) {
      var picker = pickBtn.closest('[data-cmd-picker]');
      if (picker) {
        var sel = picker.querySelector('select');
        var out = picker.querySelector('[data-cmd-output]');
        if (sel && out) out.innerHTML = renderResultBody(generateForBackend(sel.value));
      }
      return;
    }
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && dialog && !dialog.hidden) closeDialog();
  });

  // ------------------------------------------------------------------
  // Boot
  // ------------------------------------------------------------------
  dialog = buildDialog();

  // Expose the pure helpers for the test suite / console.
  window.LaunchCommand = {
    generate: generate,
    generateForBackend: generateForBackend,
    normalizeBackend: normalizeBackend,
    modelFile: modelFile,
    repoId: repoId,
    ollamaTag: ollamaTag,
    parseContext: parseContext,
    countGpus: countGpus,
    estimateVram: estimateVram,
    buildTips: buildTips,
    byId: byId
  };
})();
