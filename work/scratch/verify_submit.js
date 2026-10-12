// Faithful DOM shim that runs the REAL js/submit.js against the REAL
// submit/index.html config island to verify the form logic:
//   * block assembly (the exact [COMMUNITY-SUBMISSION] shape parse.py expects)
//   * required-field + reasonable-value validation
//   * the two submit paths (copy-for-forum, open-GitHub-issue)
// No dependencies.
'use strict';
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '..', '..');

function htmlEscape(s) {
  return String(s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// ---- Build the DOM elements submit.js touches -----------------------------
const elements = {};

function makeField(id, name, type) {
  const tag = type === 'textarea' ? 'TEXTAREA' : (type === 'select' ? 'SELECT' : 'INPUT');
  return {
    id, name, type, tagName: tag,
    value: '',
    _cls: new Set(),
    classList: {
      add: (...c) => c.forEach(x => elements[id]._cls.add(x)),
      remove: (...c) => c.forEach(x => elements[id]._cls.delete(x)),
      contains: (c) => elements[id]._cls.has(c),
    },
    _attrs: {},
    setAttribute(k, v) { this._attrs[k] = v; },
    removeAttribute(k) { delete this._attrs[k]; },
    _listeners: {},
    addEventListener(t, cb) { (this._listeners[t] = this._listeners[t] || []).push(cb); },
    focus() {},
    scrollIntoView() {},
    querySelectorAll() { return []; },
  };
}

// required + optional form fields
[
  ['sub-tier', 'tier', 'select'],
  ['sub-vendor', 'vendor', 'select'],
  ['sub-hardware', 'hardware', 'text'],
  ['sub-backend', 'backend', 'select'],
  ['sub-os', 'os_driver', 'select'],
  ['sub-model', 'model_name', 'text'],
  ['sub-quant', 'quant_package', 'text'],
  ['sub-precision', 'weight_precision', 'text'],
  ['sub-url', 'download_url', 'url'],
  ['sub-usecase', 'primary_use_case', 'select'],
  ['sub-context', 'stable_context_tested', 'text'],
  ['sub-kv', 'kv_cache_setting', 'select'],
  ['sub-mode', 'engine_mode', 'select'],
  ['sub-decode', 'throughput_tps', 'text'],
  ['sub-prefill', 'prefill_tps', 'text'],
  ['sub-ttft', 'ttft_cold', 'text'],
  ['sub-power', 'power_draw', 'text'],
  ['sub-notes', 'setup_notes', 'textarea'],
].forEach(([id, name, type]) => { elements[id] = makeField(id, name, type); });

// per-field error slots
['sub-tier', 'sub-hardware', 'sub-backend', 'sub-model', 'sub-quant',
 'sub-usecase', 'sub-url', 'sub-decode', 'sub-notes'].forEach((id) => {
  elements[id + '-err'] = { id: id + '-err', hidden: true, textContent: '' };
});

// actions / status / preview
elements['submit-copy'] = { id: 'submit-copy', _listeners: {}, addEventListener(t, cb) { (this._listeners[t] = this._listeners[t] || []).push(cb); } };
elements['submit-issue'] = { id: 'submit-issue', _listeners: {}, addEventListener(t, cb) { (this._listeners[t] = this._listeners[t] || []).push(cb); } };
elements['submit-status'] = { id: 'submit-status', textContent: '' };
elements['submit-preview'] = { id: 'submit-preview', hidden: true };
elements['submit-preview-text'] = { id: 'submit-preview-text', textContent: '' };
elements['submit-preview-link'] = { id: 'submit-preview-link', innerHTML: '' };

// the form
const form = {
  id: 'submit-form',
  _listeners: {},
  addEventListener(t, cb) { (this._listeners[t] = this._listeners[t] || []).push(cb); },
  querySelectorAll(sel) {
    if (sel === '[id]') return Object.values(elements).filter(e => e.id && e.name && e.id.indexOf('sub-') === 0);
    return [];
  },
};
elements['submit-form'] = form;

// the config island, pulled from the real generated page
const pageHtml = fs.readFileSync(path.join(ROOT, 'submit', 'index.html'), 'utf-8');
const ISLAND_OPEN = '<script type="application/json" id="submit-config">';
const start = pageHtml.indexOf(ISLAND_OPEN);
const end = pageHtml.indexOf('</script>', start);
if (start === -1 || end === -1) { console.error('FATAL: submit-config island not found'); process.exit(1); }
elements['submit-config'] = { id: 'submit-config', textContent: pageHtml.slice(start + ISLAND_OPEN.length, end) };

// ---- global shims ---------------------------------------------------------
let pendingDomCb = null;
global._copied = null;
global._openedUrl = null;
Object.defineProperty(globalThis, 'navigator', {
  configurable: true,
  value: { clipboard: { writeText: (t) => { global._copied = t; return Promise.resolve(); } } },
});
global.window = {
  open: (url) => { global._openedUrl = url; return {}; },
};
global.document = {
  getElementById: (id) => elements[id] || null,
  querySelectorAll: (sel) => {
    if (sel === '.field-err') return Object.values(elements).filter(e => e.id && e.id.indexOf('-err') === e.id.length - 4);
    if (sel === '.invalid') return Object.values(elements).filter(e => e.classList && e.classList.contains('invalid'));
    return [];
  },
  addEventListener: (type, cb) => { if (type === 'DOMContentLoaded') pendingDomCb = cb; },
  createElement: (tag) => {
    let inner = '';
    const el = {};
    Object.defineProperty(el, 'textContent', {
      set(v) { inner = htmlEscape(v == null ? '' : String(v)); },
      get() { return inner; }
    });
    Object.defineProperty(el, 'innerHTML', { get() { return inner; } });
    return el;
  },
};

require(path.join(ROOT, 'js', 'submit.js'));
if (!pendingDomCb) { console.error('FATAL: DOMContentLoaded listener never registered'); process.exit(1); }
pendingDomCb();

function fill(obj) { Object.keys(obj).forEach((k) => { if (elements[k]) elements[k].value = obj[k]; }); }
function clickCopy() { (elements['submit-copy']._listeners['click'] || []).forEach(cb => cb()); }
function clickIssue(e) { (elements['submit-issue']._listeners['click'] || []).forEach(cb => cb(e || { preventDefault() {} })); }

setTimeout(() => {
  let pass = true;
  const check = (name, cond, detail) => {
    console.log(`${cond ? 'PASS' : 'FAIL'}  ${name}${detail ? '  [' + detail + ']' : ''}`);
    if (!cond) pass = false;
  };

  // ---- S1: a full, valid submission -> copy path --------------------------
  console.log('\n=== S1: full valid submission (copy for forum) ===');
  fill({
    'sub-tier': 't4', 'sub-vendor': 'AMD', 'sub-hardware': '2x AMD R9700 (48GB total)',
    'sub-backend': 'vLLM', 'sub-os': 'Linux/ROCm', 'sub-model': 'd0xin/Swift-Qwen3.8-27B-Uncensored-FP8',
    'sub-quant': 'FP8', 'sub-precision': 'FP8 (native)', 'sub-url': 'https://huggingface.co/d0xin/Swift-Qwen3.8-27B-Uncensored-FP8',
    'sub-usecase': 'Agentic Coding', 'sub-context': '~240k tokens', 'sub-kv': 'FP16', 'sub-mode': 'VRAM-only',
    'sub-decode': '120 (code) / 70 (chat)', 'sub-prefill': '5200', 'sub-ttft': '19.3s', 'sub-power': '600W',
    'sub-notes': 'Uncensored variant for security work. Adaptive MTP=8.',
  });
  clickCopy();
  const block = global._copied;
  console.log('  --- generated block ---\n' + (block ? block.split('\n').map(l => '  ' + l).join('\n') : '  (nothing copied)'));
  check('S1 clipboard received the block', !!block);
  check('S1 block opens with [COMMUNITY-SUBMISSION]', block && block.startsWith('[COMMUNITY-SUBMISSION]'));
  check('S1 block closes with [/COMMUNITY-SUBMISSION]', block && block.trim().endsWith('[/COMMUNITY-SUBMISSION]'));
  check('S1 tier line present', block && block.includes('tier: t4'));
  check('S1 hardware line present', block && block.includes('hardware: 2x AMD R9700 (48GB total)'));
  check('S1 backend line present', block && block.includes('backend: vLLM'));
  check('S1 os_driver line present', block && block.includes('os_driver: Linux/ROCm'));
  check('S1 model_name line present', block && block.includes('model_name: d0xin/Swift-Qwen3.8-27B-Uncensored-FP8'));
  check('S1 quant_package line present', block && block.includes('quant_package: FP8'));
  check('S1 weight_precision line present', block && block.includes('weight_precision: FP8 (native)'));
  check('S1 download_url line present', block && block.includes('download_url: https://huggingface.co/'));
  check('S1 primary_use_case line present', block && block.includes('primary_use_case: Agentic Coding'));
  check('S1 stable_context_tested line present', block && block.includes('stable_context_tested: ~240k tokens'));
  check('S1 kv_cache_setting line present', block && block.includes('kv_cache_setting: FP16'));
  check('S1 engine_mode line present', block && block.includes('engine_mode: VRAM-only'));
  check('S1 throughput_tps line present', block && block.includes('throughput_tps: 120 (code) / 70 (chat)'));
  check('S1 prefill_tps line present', block && block.includes('prefill_tps: 5200'));
  check('S1 ttft_cold line present', block && block.includes('ttft_cold: 19.3s'));
  check('S1 power_draw line present', block && block.includes('power_draw: 600W'));
  check('S1 setup_notes line present', block && block.includes('setup_notes: Uncensored variant'));
  check('S1 preview revealed', elements['submit-preview'].hidden === false);
  check('S1 preview text matches clipboard', elements['submit-preview-text'].textContent === block);
  check('S1 preview has forum link', /forum\.level1techs\.com/.test(elements['submit-preview-link'].innerHTML));

  // ---- S2: minimal (required-only) submission -> omits optional fields -----
  console.log('\n=== S2: minimal submission (optional fields omitted) ===');
  fill({
    'sub-tier': 't1', 'sub-vendor': '', 'sub-hardware': '1x Radeon VII 16GB',
    'sub-backend': 'llama.cpp', 'sub-os': '', 'sub-model': 'Qwen3.5-4B',
    'sub-quant': 'GGUF Q4_K_M', 'sub-precision': '', 'sub-url': '',
    'sub-usecase': 'General Chat', 'sub-context': '', 'sub-kv': '', 'sub-mode': '',
    'sub-decode': '', 'sub-prefill': '', 'sub-ttft': '', 'sub-power': '',
    'sub-notes': 'Fast little generalist.',
  });
  clickCopy();
  const block2 = global._copied;
  console.log('  --- generated block ---\n' + (block2 ? block2.split('\n').map(l => '  ' + l).join('\n') : '  (nothing)'));
  check('S2 has the 7 required keys', ['tier: t1', 'hardware: 1x Radeon VII 16GB', 'backend: llama.cpp',
    'model_name: Qwen3.5-4B', 'quant_package: GGUF Q4_K_M', 'primary_use_case: General Chat',
    'setup_notes: Fast little generalist.'].every(l => block2 && block2.includes(l)));
  check('S2 omits empty optional fields (no os_driver)', block2 && !block2.includes('os_driver:'));
  check('S2 omits empty optional fields (no download_url)', block2 && !block2.includes('download_url:'));
  check('S2 omits empty optional fields (no engine_mode)', block2 && !block2.includes('engine_mode:'));
  check('S2 omits empty optional fields (no throughput_tps)', block2 && !block2.includes('throughput_tps:'));

  // ---- S3: validation catches a missing required field --------------------
  console.log('\n=== S3: missing required field is rejected ===');
  fill({
    'sub-tier': 't2', 'sub-vendor': '', 'sub-hardware': '',   // hardware empty
    'sub-backend': 'Ollama', 'sub-os': '', 'sub-model': 'gemma:7b',
    'sub-quant': 'Q4_K_M', 'sub-precision': '', 'sub-url': '',
    'sub-usecase': 'General Chat', 'sub-context': '', 'sub-kv': '', 'sub-mode': '',
    'sub-decode': '', 'sub-prefill': '', 'sub-ttft': '', 'sub-power': '',
    'sub-notes': 'quick one',
  });
  global._copied = null;
  clickCopy();
  check('S3 did NOT copy (validation blocked)', global._copied === null);
  check('S3 hardware error shown', elements['sub-hardware-err'].hidden === false && /required/i.test(elements['sub-hardware-err'].textContent));
  check('S3 status announces the problem', /fix the highlighted/i.test(elements['submit-status'].textContent));

  // ---- S4: validation catches a malformed URL -----------------------------
  console.log('\n=== S4: malformed download URL is rejected ===');
  fill({
    'sub-tier': 't2', 'sub-vendor': '', 'sub-hardware': '1x RTX 4060 16GB',
    'sub-backend': 'Ollama', 'sub-os': '', 'sub-model': 'gemma:7b',
    'sub-quant': 'Q4_K_M', 'sub-precision': '', 'sub-url': 'not a url',
    'sub-usecase': 'General Chat', 'sub-context': '', 'sub-kv': '', 'sub-mode': '',
    'sub-decode': '', 'sub-prefill': '', 'sub-ttft': '', 'sub-power': '',
    'sub-notes': 'quick one',
  });
  global._copied = null;
  clickCopy();
  check('S4 did NOT copy (bad URL blocked)', global._copied === null);
  check('S4 url error shown', elements['sub-url-err'].hidden === false && /http/i.test(elements['sub-url-err'].textContent));

  // ---- S5: GitHub issue path ----------------------------------------------
  console.log('\n=== S5: open-a-GitHub-issue path ===');
  fill({
    'sub-tier': 't3', 'sub-vendor': 'NVIDIA', 'sub-hardware': '1x RTX 4090 24GB, 128GB RAM',
    'sub-backend': 'Strata', 'sub-os': 'Windows/WSL2', 'sub-model': 'Qwen/Qwen3.8-Flash-Next (GGUF IQ3_S)',
    'sub-quant': 'GGUF IQ3_S', 'sub-precision': 'IQ3_S', 'sub-url': '',
    'sub-usecase': 'Agentic Coding', 'sub-context': '131072 configured', 'sub-kv': 'INT8', 'sub-mode': 'Hybrid (VRAM+RAM+SSD)',
    'sub-decode': '99-128', 'sub-prefill': '', 'sub-ttft': '', 'sub-power': '450W',
    'sub-notes': '125B MoE on single 24GB card.',
  });
  global._openedUrl = null;
  clickIssue();
  const url = global._openedUrl;
  console.log('  opened: ' + url);
  check('S5 opened an issues/new URL', url && url.includes('/issues/new?'));
  check('S5 URL has a title param', url && /title=/.test(url));
  check('S5 title includes the model family', url && /Qwen3\.8-Flash-Next/.test(decodeURIComponent(url)));
  check('S5 title includes the tier label', url && /24-32GB/.test(decodeURIComponent(url)));
  check('S5 URL has a body param', url && /body=/.test(url));
  const body = decodeURIComponent(url.split('body=')[1] || '');
  check('S5 body contains the fenced block', body.includes('```text') && body.includes('[COMMUNITY-SUBMISSION]'));
  check('S5 body contains the hybrid engine_mode', body.includes('engine_mode: Hybrid (VRAM+RAM+SSD)'));

  console.log('\n' + (pass ? 'ALL SCENARIOS PASS' : 'SOME SCENARIOS FAILED'));
  process.exit(pass ? 0 : 1);
}, 50);
