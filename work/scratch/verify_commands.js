// Faithful DOM shim that runs the REAL js/commands.js against the REAL
// generated island (from compare/index.html) to verify the launch-command
// generator (P2-3): every one of the 12 submissions yields a plausible,
// backend-correct command; GUI backends get steps (no fabricated CLI);
// unknown backends degrade gracefully; VRAM is estimated and tips are
// contextual. No dependencies.
'use strict';
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '..', '..');

function htmlEscape(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
function makeEl(tag) {
  let inner = '';
  const el = {
    tagName: (tag || 'div').toUpperCase(),
    _listeners: {}, hidden: false, disabled: false, style: {},
    classList: {
      _s: new Set(),
      add(c) { this._s.add(c); }, remove(c) { this._s.delete(c); },
      toggle(c, f) { if (f === undefined) { this._s.has(c) ? this._s.delete(c) : this._s.add(c); } else if (f) { this._s.add(c); } else { this._s.delete(c); } return this._s.has(c); },
      contains(c) { return this._s.has(c); }
    },
    setAttribute(k, v) { this[k] = v; },
    getAttribute(k) { return this[k] != null ? this[k] : null; },
    addEventListener(t, cb) { (this._listeners[t] = this._listeners[t] || []).push(cb); },
    focus() {}, appendChild(c) { return c; },
    querySelector() { return null; }, querySelectorAll() { return []; }, closest() { return null; },
  };
  Object.defineProperty(el, 'innerHTML', { get() { return inner; }, set(v) { inner = v; } });
  Object.defineProperty(el, 'textContent', { get() { return inner; }, set(v) { inner = htmlEscape(v == null ? '' : String(v)); } });
  return el;
}

// Pull the #commands-config island out of the real generated page.
const pageHtml = fs.readFileSync(path.join(ROOT, 'compare', 'index.html'), 'utf-8');
const OPEN = '<script type="application/json" id="commands-config">';
const s = pageHtml.indexOf(OPEN);
const e = pageHtml.indexOf('</script>', s);
if (s === -1 || e === -1) { console.error('FATAL: commands-config island not found'); process.exit(1); }
const islandText = pageHtml.slice(s + OPEN.length, e);

const elements = { 'commands-config': { id: 'commands-config', textContent: islandText } };
global.window = global;
global.document = {
  getElementById: (id) => elements[id] || null,
  createElement: (tag) => makeEl(tag),
  body: makeEl('body'),
  activeElement: null,
  addEventListener: (t, cb) => { (global._docListeners = global._docListeners || {})[t] = (global._docListeners[t] || []).concat(cb); },
};
// (navigator.clipboard is only touched by copyText on a real click, which the
// pure-function tests below do not exercise; Node 26 makes `navigator` a
// read-only global, so we leave it alone.)

require(path.join(ROOT, 'js', 'commands.js'));

const LC = global.LaunchCommand;
if (!LC) { console.error('FATAL: window.LaunchCommand not exposed'); process.exit(1); }

const cfg = JSON.parse(islandText);
const subs = cfg.submissions;

let pass = true;
const check = (name, cond, detail) => {
  console.log((cond ? 'PASS' : 'FAIL') + '  ' + name + (detail ? '  [' + detail + ']' : ''));
  if (!cond) pass = false;
};

console.log('=== Backend normalization ===');
check('llamacpp -> llama.cpp', LC.normalizeBackend('llamacpp', cfg.backends) === 'llama.cpp');
check('vLLM (…MTP=8) -> vLLM', LC.normalizeBackend('vLLM (magiccodingman/vllm-radiance, adaptive MTP=8)', cfg.backends) === 'vLLM');
check('Strata 0.1.42 -> Strata', LC.normalizeBackend('Strata 0.1.42', cfg.backends) === 'Strata');
check('llama-swap (…ROCm) -> llama-swap', LC.normalizeBackend('llama-swap (llama.cpp subprocess, ROCm)', cfg.backends) === 'llama-swap');

console.log('\n=== Every one of the 12 submissions yields output ===');
subs.forEach((sub) => {
  const r = LC.generate(sub);
  const backend = LC.normalizeBackend(sub.backend, cfg.backends);
  const label = r.isGui ? 'GUI' : (r.isUnknown ? 'UNKNOWN' : r.command);
  console.log('  ' + sub.id + '  [' + backend + ']  ' + label);
  if (r.vram) console.log('       vram: ' + r.vram.text);
  const hasOutput = r.isGui || r.isUnknown || (r.command && r.command.length > 5);
  check('  ' + sub.id + ' produces output', hasOutput, r.isGui ? 'gui' : (r.isUnknown ? 'unknown' : 'cmd len ' + r.command.length));
});

console.log('\n=== Acceptance-criteria command shapes ===');
const lc = LC.generate(subs.find(x => LC.normalizeBackend(x.backend, cfg.backends) === 'llama.cpp'));
check('llama.cpp -> llama-server -m *.gguf -ngl 99 -c N', /llama-server -m .*\.gguf -ngl 99 -c \d+/.test(lc.command), lc.command);

const vv = LC.generate(subs.find(x => LC.normalizeBackend(x.backend, cfg.backends) === 'vLLM' && LC.countGpus(x.hardware.description) > 1));
check('vLLM 2-GPU -> vllm serve <model> --tensor-parallel-size 2', /vllm serve .*--tensor-parallel-size 2/.test(vv.command), vv.command);

const oo = LC.generate(subs.find(x => LC.normalizeBackend(x.backend, cfg.backends) === 'Ollama'));
check('Ollama -> ollama run <tag>', /^ollama run /.test(oo.command), oo.command);

const sw = LC.generate(subs.find(x => LC.normalizeBackend(x.backend, cfg.backends) === 'llama-swap'));
check('llama-swap -> llama-swap serve', /^llama-swap serve/.test(sw.command), sw.command);

const st = LC.generate(subs.find(x => LC.normalizeBackend(x.backend, cfg.backends) === 'Strata'));
check('Strata -> strata serve <model>', /^strata serve /.test(st.command), st.command);

console.log('\n=== GUI backends: steps, no fabricated CLI ===');
const lms = LC.generateForBackend('LM Studio');
check('LM Studio is GUI (steps, empty command)', lms.isGui === true && lms.gui && lms.gui.length >= 3 && !lms.command, (lms.gui || []).length + ' steps');
const uns = LC.generateForBackend('Unsloth Desktop');
check('Unsloth Desktop is GUI (steps, empty command)', uns.isGui === true && uns.gui && uns.gui.length >= 2 && !uns.command, (uns.gui || []).length + ' steps');

console.log('\n=== Unknown backend degrades gracefully ===');
const fake = { id: 'x', tier: 't1', backend: 'SomeBrandNewEngine', model: { name: 'TestModel-27B' }, hardware: { description: '1x GPU' }, quant: '', weight_precision: '', context: { stable: '8192', kv_cache: '' }, performance: { decode_tps: '50' }, notes: '', engine_mode: '' };
const unk = LC.generate(fake);
check('unknown -> isUnknown + empty command', unk.isUnknown === true && unk.command === '', 'isUnknown=' + unk.isUnknown);
check('unknown -> "check the guide" note', /guide/i.test(unk.note), unk.note);

console.log('\n=== VRAM estimate + contextual tips ===');
const m1 = LC.generate(subs[0]); // post_2_madgoat_1
check('VRAM pulled from notes (~12.7 GB)', /12\.7/.test(m1.vram.text), m1.vram.text);
check('MoE tip present for the A3B model', m1.tips.some(t => /Mixture-of-Experts/i.test(t)), m1.tips.length + ' tips');
const strataRes = LC.generate(subs.find(x => LC.normalizeBackend(x.backend, cfg.backends) === 'Strata'));
check('hybrid tip present for the Strata submission', strataRes.tips.some(t => /RAM\/SSD|RAM\b/i.test(t)), strataRes.tips.length + ' tips');

console.log('\n' + (pass ? 'ALL COMMAND CHECKS PASS' : 'SOME COMMAND CHECKS FAILED'));
process.exit(pass ? 0 : 1);
