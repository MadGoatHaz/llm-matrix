// Faithful DOM shim that runs the REAL js/compare.js against the REAL
// generated island to verify the comparison view (P2-2): the diff-highlight
// rule, the model/backend label helpers, and the rendered diff table (one
// column per selected setup, differing cells tinted, a launch button per
// column, a factual takeaway line). No dependencies.
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
    _listeners: {}, hidden: false, disabled: false, style: {}, value: '',
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

// Island from the real compare page.
const pageHtml = fs.readFileSync(path.join(ROOT, 'compare', 'index.html'), 'utf-8');
const OPEN = '<script type="application/json" id="commands-config">';
const s = pageHtml.indexOf(OPEN);
const e = pageHtml.indexOf('</script>', s);
if (s === -1 || e === -1) { console.error('FATAL: commands-config island not found'); process.exit(1); }
const islandText = pageHtml.slice(s + OPEN.length, e);

// Build the DOM compare.js expects (picker + table wrap + takeaway + edit).
function makeSelect() { return makeEl('select'); }
const selects = [makeSelect(), makeSelect(), makeSelect(), makeSelect()];
const picker = makeEl('section');
picker.querySelectorAll = (sel) => (sel === 'select.compare-pick' ? selects : []);
picker.querySelector = (sel) => (sel === '.compare-pick-go' ? makeEl('button') : null);
const tableWrap = makeEl('div');
const editBtn = makeEl('button');
const takeaway = makeEl('p');

const elements = {
  'commands-config': { id: 'commands-config', textContent: islandText },
  'compare-picker': picker,
  'compare-table-wrap': tableWrap,
  'compare-edit': editBtn,
  'compare-takeaway': takeaway,
};

global.window = global;
global.location = { pathname: '/compare/', search: '?a=post_2_madgoat_1&b=post_2_madgoat_2&c=post_2_madgoat_3' };
global.history = { replaceState: () => {} };
global.URLSearchParams = URLSearchParams;
global.document = {
  getElementById: (id) => elements[id] || null,
  createElement: (tag) => makeEl(tag),
  body: makeEl('body'),
  activeElement: null,
  addEventListener: () => {},
};

require(path.join(ROOT, 'js', 'compare.js'));

const C = global.Compare;
if (!C) { console.error('FATAL: window.Compare not exposed'); process.exit(1); }

let pass = true;
const check = (name, cond, detail) => {
  console.log((cond ? 'PASS' : 'FAIL') + '  ' + name + (detail ? '  [' + detail + ']' : ''));
  if (!cond) pass = false;
};

console.log('=== computeDiff (the highlight rule) ===');
check('differing values -> diff', C.computeDiff(['a', 'b']) === true);
check('identical values -> no diff', C.computeDiff(['x', 'x', 'x']) === false);
check('all empty -> no diff', C.computeDiff(['', '']) === false);
check('some empty, some not -> diff', C.computeDiff(['a', '']) === true);

console.log('\n=== shortModel / normBackend helpers ===');
check('shortModel strips repo prefix', C.shortModel({ model: { name: 'samuelcardillo/Carnice-Qwen3.6-MoE-35B-A3B' } }) === 'Carnice-Qwen3.6-MoE-35B-A3B');
check('normBackend llamacpp -> llama.cpp', C.normBackend('llamacpp') === 'llama.cpp');

console.log('\n=== renderTable (3 setups from ?a=&b=&c=) ===');
let html = tableWrap.innerHTML;
const colCount = (html.match(/class="compare-col"/g) || []).length;
const rowCount = (html.match(/<tr/g) || []).length;
const diffCount = (html.match(/compare-diff/g) || []).length;
const launchCount = (html.match(/data-launch-sub=/g) || []).length;
check('3 setup columns rendered', colCount === 3, colCount + ' cols');
check('attribute + launch rows present', rowCount >= 11, rowCount + ' rows');
check('differing cells are highlighted', diffCount > 0, diffCount + ' diff cells');
check('each column has a launch-command button', launchCount === 3, launchCount + ' buttons');
console.log('  takeaway: ' + takeaway.textContent);
check('takeaway is a factual "Compared N" sentence', /Compared 3 setups/.test(takeaway.textContent));
check('table shows a real model/hardware string', /Qwen|R9700|4090/.test(html));

console.log('\n=== 2-setup render ===');
C.renderTable(['post_8_s1ugh34d_3', 'post_8_s1ugh34d_4']);
html = tableWrap.innerHTML;
check('2-column table renders', (html.match(/class="compare-col"/g) || []).length === 2, (html.match(/class="compare-col"/g) || []).length + ' cols');
console.log('  takeaway: ' + takeaway.textContent);

console.log('\n' + (pass ? 'ALL COMPARE CHECKS PASS' : 'SOME COMPARE CHECKS FAILED'));
process.exit(pass ? 0 : 1);
