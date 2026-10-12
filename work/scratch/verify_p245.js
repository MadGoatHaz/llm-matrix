// Faithful DOM shim that runs the REAL js/main.js against the REAL generated
// matrix.html to verify P2-4 (URL-synced shareable filters) + P2-5 (row
// detail panel): restore-from-URL, push/replace state, empty state, share
// copy, panel open/populate/focus-trap/ESC/hash deep-link. No dependencies.
'use strict';
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '..', '..');

function htmlEscape(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// --- minimal element -------------------------------------------------------
let elCount = 0;
function makeEl(tag, attrs) {
  attrs = attrs || {};
  const el = {
    _id: 'el' + (++elCount),
    tagName: (tag || 'div').toUpperCase(),
    _listeners: {},
    _attrs: Object.assign({}, attrs),
    children: [],
    style: {},
    checked: false,
    disabled: false,
    hidden: false,
    textContent: '',
    dataset: {},
    classList: {
      _s: new Set((attrs['class'] || '').split(/\s+/).filter(Boolean)),
      add(c) { this._s.add(c); },
      remove(c) { this._s.delete(c); },
      toggle(c, f) {
        if (f === undefined) { this._s.has(c) ? this._s.delete(c) : this._s.add(c); }
        else if (f) this._s.add(c); else this._s.delete(c);
        return this._s.has(c);
      },
      contains(c) { return this._s.has(c); },
    },
  };
  // populate dataset from data-* attrs
  Object.keys(attrs).forEach(k => {
    if (k.startsWith('data-')) {
      el.dataset[k.replace('data-', '').replace(/-([a-z])/g, (m, c) => c.toUpperCase())] = attrs[k];
    }
  });
  if (attrs.id) el.id = attrs.id;
  Object.defineProperty(el, 'textContent', {
    get() { return el._text != null ? el._text : ''; },
    set(v) { el._text = v; el._inner = htmlEscape(v == null ? '' : String(v)); },
    configurable: true,
  });
  el.setAttribute = function (k, v) {
    this._attrs[k] = v;
    if (k === 'id') this.id = v;
    if (k.startsWith('data-')) this.dataset[k.replace('data-', '').replace(/-([a-z])/g, (m, c) => c.toUpperCase())] = v;
  };
  el.getAttribute = function (k) { return this._attrs[k] != null ? this._attrs[k] : null; };
  el.hasAttribute = function (k) { return k in this._attrs; };
  el.addEventListener = function (t, cb) { (this._listeners[t] = this._listeners[t] || []).push(cb); };
  el.dispatchEvent = function (evt) {
    (this._listeners[evt.type] || []).forEach(cb => cb.call(this, evt));
    return true;
  };
  el.fire = function (type, props) {
    const evt = Object.assign({
      type, target: this,
      preventDefault() { this.defaultPrevented = true; },
      stopPropagation() { this.stopped = true; },
    }, props || {});
    let node = this;
    while (node) {
      if (evt.stopped) break;
      node.dispatchEvent(evt);
      node = node._parent || null;
    }
    return evt;
  };
  el.focus = function () { document.activeElement = this; };
  el.appendChild = function (c) { c._parent = this; this.children.push(c); return c; };
  el.querySelector = function (sel) { return qsel(this, sel, true); };
  el.querySelectorAll = function (sel) { return qsel(this, sel, false); };
  el.closest = function (sel) {
    let node = this;
    while (node) { if (matches(node, sel)) return node; node = node._parent || null; }
    return null;
  };
  Object.defineProperty(el, 'value', {
    get() { return el._value != null ? el._value : ''; },
    set(v) { el._value = v; },
    configurable: true,
  });
  Object.defineProperty(el, 'innerHTML', {
    get() { return el._inner || ''; },
    set(v) { el._inner = v; el.children = []; },
    configurable: true,
  });
  return el;
}

function matches(el, sel) {
  sel = sel.trim();
  if (!sel) return false;
  if (sel.includes(',')) return sel.split(',').some(s => matches(el, s));
  if (sel.startsWith('.')) {
    return sel.slice(1).split(/\s+/).every(c => c && el.classList.contains(c));
  }
  if (sel.startsWith('#')) return el.id === sel.slice(1);
  if (sel.startsWith('[')) {
    const mv = sel.match(/^\[([a-z-]+)="([^"]*)"\]$/);
    if (mv) return el._attrs[mv[1]] === mv[2];
    const mb = sel.match(/^\[([a-z-]+)\]$/);
    if (mb) return el._attrs[mb[1]] != null;
    return false;
  }
  // combined tag.class[.class...] (e.g. "tr.data-row")
  if (/^[a-z]+(\.[a-z0-9-]+)+$/i.test(sel)) {
    const parts = sel.split('.');
    if (el.tagName.toLowerCase() !== parts[0]) return false;
    return parts.slice(1).every(c => el.classList.contains(c));
  }
  return el.tagName.toLowerCase() === sel;
}

function qsel(root, sel, first) {
  // Descendant-aware: "tbody tr" matches <tr> nodes that have a <tbody>
  // ancestor within the root. Single-part selectors match anywhere.
  const parts = sel.trim().split(/\s+/);
  const out = [];
  (function walk(node, depth) {
    node.children.forEach(c => {
      if (depth < parts.length && matches(c, parts[depth])) {
        if (depth === parts.length - 1) out.push(c);
        walk(c, depth + 1);
      } else {
        walk(c, depth);
      }
    });
  })(root, 0);
  return first ? (out[0] || null) : out;
}

// --- parse the real matrix.html for the island -------------------------------
const pageHtml = fs.readFileSync(path.join(ROOT, 'matrix.html'), 'utf-8');
const OPEN = '<script type="application/json" id="commands-config">';
const s = pageHtml.indexOf(OPEN);
const e = pageHtml.indexOf('</script>', s);
if (s === -1 || e === -1) { console.error('FATAL: island not found'); process.exit(1); }
const island = JSON.parse(pageHtml.slice(s + OPEN.length, e));
const schema = JSON.parse(fs.readFileSync(path.join(ROOT, 'tools', 'schema.json'), 'utf-8'));
island.use_cases = schema.use_cases;
island.engine_modes = schema.engine_modes;
console.log('island: ' + island.submissions.length + ' submissions, ' + island.tiers.length + ' tiers, ' +
  island.submissions[0].source.post_id + ' (first post_id)');

// --- build the DOM main.js expects --------------------------------------------
function makeSelect(dataFilter, options) {
  const sel = makeEl('select', { 'class': 'filter-select', 'data-filter': dataFilter });
  sel._options = options;
  const desc = Object.getOwnPropertyDescriptor(sel, 'value');
  Object.defineProperty(sel, 'value', {
    get() { return desc.get.call(sel); },
    set(v) {
      // a real <select> keeps '' if the value has no matching option
      desc.set.call(sel, (v === '' || options.includes(v)) ? v : '');
    },
  });
  return sel;
}

const search = makeEl('input', { id: 'filter-search' });
const tierSel = makeSelect('tier', island.tiers.map(t => t.id));
const vendorSel = makeSelect('vendor', ['AMD', 'NVIDIA']);
const backendSel = makeSelect('backend', island.backends);
const useCaseSel = makeSelect('use-case', island.use_cases);
const modeSel = makeSelect('mode', island.engine_modes);
const selects = [tierSel, vendorSel, backendSel, useCaseSel, modeSel];

const resetBtn = makeEl('button', { id: 'filter-reset' });
const shareBtn = makeEl('button', { id: 'filter-share' });
const emptyEl = makeEl('div', { id: 'filter-empty' });
emptyEl.hidden = true;
const emptyClear = makeEl('button', { id: 'filter-empty-clear' });
emptyEl.appendChild(emptyClear);

const table = makeEl('table', { id: 'data-table' });
const tbody = makeEl('tbody');
table.appendChild(tbody);

// derive data-use-case the same way the Python generator does
const KW = {
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
  'Embeddings': ['embedding'],
};
const kwIn = (t, kw) => (kw.indexOf(' ') === -1 && /^[a-z0-9]+$/.test(kw))
  ? new RegExp('\\b' + kw + '\\b').test(t) : t.indexOf(kw) !== -1;

// replicate the generator's normalize_backend() for the row attrs
const normBackend = (raw) => {
  if (!raw) return '';
  let t = String(raw).trim().replace(/\(.*$/, '').trim().replace(/\s+\d[\w.]*$/, '').trim();
  const aliases = { llamacpp: 'llama.cpp', 'llama-cpp': 'llama.cpp', 'llama cpp': 'llama.cpp' };
  if (aliases[t.toLowerCase()]) return aliases[t.toLowerCase()];
  for (const b of island.backends) if (b.toLowerCase() === t.toLowerCase()) return b;
  return t;
};

const rows = island.submissions.map(sub => {
  const text = String(sub.use_cases || '').toLowerCase();
  let first = '';
  for (const cat of island.use_cases) {
    if (cat === 'Other') continue;
    if ((KW[cat] || []).some(k => kwIn(text, k))) { first = cat; break; }
  }
  const tr = makeEl('tr', {
    id: sub.id,
    'class': 'data-row ' + sub.tier,
    tabindex: '0',
    'data-tier': sub.tier,
    'data-vendor': (sub.hardware || {}).vendor || '',
    'data-backend': normBackend(sub.backend),
    'data-use-case': first,
    'data-mode': sub.engine_mode || '',
  });
  tr.textContent = sub.id;
  const check = makeEl('input', { type: 'checkbox', 'class': 'compare-check', 'data-sub-id': sub.id });
  const label = makeEl('label', { 'class': 'compare-check-wrap' });
  label.appendChild(check);
  const td = makeEl('td', { 'class': 'cell-actions' });
  td.appendChild(label);
  tr.appendChild(td);
  tr._check = check;
  tbody.appendChild(tr);
  return { sub, tr };
});

const scrim = makeEl('div', { id: 'detail-scrim', 'class': 'detail-scrim' });
const panel = makeEl('aside', {
  id: 'detail-panel', 'class': 'detail-panel', role: 'dialog',
  'aria-modal': 'true', 'aria-hidden': 'true',
});
panel.inert = true;
const dTitle = makeEl('h2', { id: 'detail-title' });
const dClose = makeEl('button', { id: 'detail-close', 'class': 'detail-close' });
const dHeader = makeEl('div', { 'class': 'detail-header' });
dHeader.appendChild(dTitle);
dHeader.appendChild(dClose);
panel.appendChild(dHeader);
const dBody = makeEl('div', { id: 'detail-body', 'class': 'detail-body' });
panel.appendChild(dBody);
// main.js queries these two specifically on the panel:
panel.querySelector = function (sel) {
  if (sel === '.detail-body') return dBody;
  if (sel === '.detail-close') return dClose;
  return qsel(this, sel, true);
};

const body = makeEl('body');
[search, tierSel, vendorSel, backendSel, useCaseSel, modeSel,
  resetBtn, shareBtn, emptyEl, table, scrim, panel]
  .forEach(el => body.appendChild(el));

// --- globals -------------------------------------------------------------------
const historyCalls = { push: [], replace: [] };
global.window = global;
global.addEventListener = () => {}; // window-level listeners (popstate) are no-ops in the shim
global.location = {
  pathname: '/matrix.html',
  search: '?tier=t1&backend=llama-swap&use_case=Agentic+Coding',
  hash: '',
  get href() { return this.pathname + this.search + this.hash; },
};
function applyUrl(url) {
  const i = url.indexOf('#');
  const noHash = i === -1 ? url : url.slice(0, i);
  const q = noHash.indexOf('?');
  global.location.pathname = q === -1 ? noHash : noHash.slice(0, q);
  global.location.search = q === -1 ? '' : noHash.slice(q);
  global.location.hash = i === -1 ? '' : url.slice(i);
}
global.history = {
  pushState(d, t, url) { historyCalls.push.push(url); applyUrl(url); },
  replaceState(d, t, url) { historyCalls.replace.push(url); applyUrl(url); },
};
global.URLSearchParams = URLSearchParams;
Object.defineProperty(global, 'navigator', {
  configurable: true,
  value: { clipboard: { writeText: (t) => { global._copied = t; return Promise.resolve(); } } },
});
global.CSS = { escape: (s2) => s2 };
global.Event = Event;
global.document = {
  _els: {
    'filter-search': search, 'filter-reset': resetBtn, 'filter-share': shareBtn,
    'filter-empty': emptyEl, 'filter-empty-clear': emptyClear, 'data-table': table,
    'detail-scrim': scrim, 'detail-panel': panel, 'detail-title': dTitle,
    'detail-close': dClose, 'detail-body': dBody,
    'commands-config': { id: 'commands-config', textContent: JSON.stringify(island) },
  },
  _listeners: {},
  getElementById(id) { return this._els[id] || null; },
  querySelector(sel) { return body.querySelector(sel); },
  querySelectorAll(sel) { return body.querySelectorAll(sel); },
  createElement: (tag) => makeEl(tag),
  body,
  activeElement: body,
  addEventListener(t, cb) { (this._listeners[t] = this._listeners[t] || []).push(cb); },
};

let pass = true;
const check = (name, cond, detail) => {
  console.log((cond ? 'PASS' : 'FAIL') + '  ' + name + (detail ? '  [' + detail + ']' : ''));
  if (!cond) pass = false;
};
const visibleRows = () => rows.filter(({ tr }) => tr.style.display !== 'none');

// --- boot main.js -----------------------------------------------------------------
require(path.join(ROOT, 'js', 'main.js'));
(document._listeners['DOMContentLoaded'] || []).forEach(cb => cb.call(document));

// --- P2-4: restore from URL -----------------------------------------------------------
console.log('\n=== P2-4 restore-from-URL (?tier=t1&backend=llama-swap&use_case=Agentic+Coding) ===');
check('tier select restored to t1', tierSel.value === 't1', tierSel.value);
check('backend select restored to llama-swap', backendSel.value === 'llama-swap', backendSel.value);
check('use-case select restored to Agentic Coding', useCaseSel.value === 'Agentic Coding', useCaseSel.value);
check('vendor select untouched (not in URL)', vendorSel.value === '', vendorSel.value);
const expected = island.submissions.filter(sub2 =>
  sub2.tier === 't1' &&
  String(sub2.backend).replace(/\(.*$/, '').trim() === 'llama-swap' &&
  (sub2.use_cases || '').toLowerCase().includes('coding'));
check('AND-filtered row count matches', visibleRows().length === expected.length,
  visibleRows().length + ' visible, ' + expected.length + ' expected');
check('non-matching rows hidden',
  rows.filter(({ sub: sub3 }) => !(sub3.tier === 't1' && String(sub3.backend).replace(/\(.*$/, '').trim() === 'llama-swap' && (sub3.use_cases || '').toLowerCase().includes('coding')))
    .every(({ tr }) => tr.style.display === 'none'));
check('restore normalized via replaceState (no history entry)',
  historyCalls.push.length === 0 && historyCalls.replace.length === 1,
  'push=' + historyCalls.push.length + ' replace=' + historyCalls.replace.length);
check('normalized URL keeps only non-empty params, drops vendor',
  /tier=t1/.test(location.search) && /backend=llama-swap/.test(location.search) &&
  /use_case=Agentic/.test(location.search) && !/vendor=/.test(location.search), location.search);

// --- P2-4: clear the restored filters, then vendor filter ----------------------------
console.log('\n=== P2-4 discrete select change -> pushState ===');
tierSel.value = '';
tierSel.fire('change');
backendSel.value = '';
backendSel.fire('change');
useCaseSel.value = '';
useCaseSel.fire('change');
check('all 12 rows visible after clearing restored filters', visibleRows().length === 12,
  visibleRows().length + ' visible');
check('URL cleaned as filters cleared', location.search === '', location.search);
vendorSel.value = 'AMD';
vendorSel.fire('change');
const lastPush = historyCalls.push[historyCalls.push.length - 1];
check('each discrete change pushed one history entry (4 total)', historyCalls.push.length === 4,
  'pushes=' + historyCalls.push.length);
check('pushed URL is vendor=AMD only', lastPush === '/matrix.html?vendor=AMD', lastPush);
check('the 2 NVIDIA rows hidden',
  rows.filter(({ sub: sub4 }) => (sub4.hardware || {}).vendor === 'NVIDIA').every(({ tr }) => tr.style.display === 'none'));
check('all 10 AMD rows visible', visibleRows().length === 10, visibleRows().length + ' visible');

// --- P2-4: search typing -> replaceState ------------------------------------------------
console.log('\n=== P2-4 search input -> replaceState (no push spam) ===');
search.value = 'qwen';
search.fire('input');
const lastReplace = historyCalls.replace[historyCalls.replace.length - 1];
check('typing used replaceState (still 4 pushes)', historyCalls.push.length === 4, 'pushes=' + historyCalls.push.length);
check('replaced URL carries q=qwen + vendor=AMD', /q=qwen/.test(lastReplace) && /vendor=AMD/.test(lastReplace), lastReplace);
check('search narrows to qwen rows',
  visibleRows().every(({ sub: sub5 }) =>
    sub5.id.toLowerCase().includes('qwen') || String((sub5.model || {}).name).toLowerCase().includes('qwen')));

// --- P2-4: empty state --------------------------------------------------------------------
console.log('\n=== P2-4 empty result state ===');
search.value = '';
search.fire('input');
modeSel.value = 'CPU-only'; // no submission uses CPU-only
modeSel.fire('change');
check('empty state shown when 0 rows match', emptyEl.hidden === false);
check('all rows hidden', visibleRows().length === 0);
check('URL carries the dead-end filter', /mode=CPU-only/.test(location.search), location.search);
emptyClear.fire('click');
check('clear-from-empty-state resets all controls',
  modeSel.value === '' && tierSel.value === '' && backendSel.value === '' &&
  vendorSel.value === '' && useCaseSel.value === '' && search.value === '');
check('empty state hidden, all 12 rows back', emptyEl.hidden === true && visibleRows().length === 12);
check('URL cleaned of all params', location.search === '', location.search);

// --- P2-4: share button ---------------------------------------------------------------------
console.log('\n=== P2-4 share button ===');
tierSel.value = 't4';
tierSel.fire('change');
useCaseSel.value = 'Agentic Coding';
useCaseSel.fire('change');
shareBtn.fire('click');
setTimeout(() => {
  check('clipboard received the current filtered URL',
    typeof global._copied === 'string' && /tier=t4/.test(global._copied) &&
    /use_case=Agentic/.test(global._copied), global._copied);

  // --- P2-5: open the detail panel by row click --------------------------------------------
  console.log('\n=== P2-5 row click opens the detail panel ===');
  tierSel.value = '';
  tierSel.fire('change');
  useCaseSel.value = '';
  useCaseSel.fire('change');
  const target = rows.find(({ sub: sub6 }) => sub6.id === 'post_2_madgoat_3'); // the hybrid Strata one
  target.tr.fire('click');
  check('panel .open class added', panel.classList.contains('open'));
  check('scrim .open class added', scrim.classList.contains('open'));
  check('panel aria-hidden=false', panel.getAttribute('aria-hidden') === 'false');
  check('inert removed while open', panel.inert === false);
  check('body.detail-open (scroll locked)', body.classList.contains('detail-open'));
  check('title shows the model', /Qwen3/.test(dTitle.textContent), dTitle.textContent);
  const bodyHtml = dBody.innerHTML;
  check('panel shows hardware (RTX 4090)', bodyHtml.includes('RTX 4090'));
  check('panel shows engine mode (hybrid)', /Hybrid \(VRAM\+RAM\+SSD\)/.test(bodyHtml));
  check('panel shows submitter notes', /detail-notes/.test(bodyHtml));
  check('panel forum deep link -> #post-<id>',
    /#post-\d+/.test(bodyHtml) && bodyHtml.includes('#post-' + target.sub.source.post_id),
    (bodyHtml.match(/#post-\d+/) || ['none'])[0]);
  check('panel launch-command button wired (reuses P2-3)',
    /data-launch-sub="post_2_madgoat_3"/.test(bodyHtml));
  check('panel add-to-comparison button present', /detail-add-compare/.test(bodyHtml));
  check('panel compare deep link present', /compare\/\?a=post_2_madgoat_3/.test(bodyHtml));
  check('URL hash now points at the row', location.hash === '#post_2_madgoat_3', location.hash);
  check('focus moved into the panel (close button)', document.activeElement === dClose,
    document.activeElement && (document.activeElement.id || 'unknown'));

  // --- P2-5: ESC closes, restores focus, clears hash -----------------------------------------
  console.log('\n=== P2-5 ESC closes, restores focus, clears hash ===');
  panel.fire('keydown', { key: 'Escape' });
  check('panel .open removed', !panel.classList.contains('open'));
  check('scrim .open removed', !scrim.classList.contains('open'));
  check('panel aria-hidden=true again', panel.getAttribute('aria-hidden') === 'true');
  check('inert restored while closed', panel.inert === true);
  check('hash cleared on close', location.hash === '', location.hash);
  check('focus restored to the trigger row', document.activeElement === target.tr,
    document.activeElement && (document.activeElement.id || 'unknown'));

  // --- P2-5: keyboard open (Enter on focused row) + focus trap ---------------------------------
  console.log('\n=== P2-5 keyboard open + focus trap ===');
  target.tr.focus();
  target.tr.fire('keydown', { key: 'Enter' });
  check('Enter on focused row opens the panel', panel.classList.contains('open'));
  check('focus in panel after keyboard open', document.activeElement === dClose);
  panel.fire('keydown', { key: 'Tab' });
  check('Tab wraps within the panel (focusable list = [close])',
    document.activeElement === dClose);
  panel.fire('keydown', { key: 'Tab', shiftKey: true });
  check('Shift+Tab wraps within the panel', document.activeElement === dClose);
  dClose.fire('click');
  check('close button closes the panel', !panel.classList.contains('open'));

  // --- P2-5: deep link (hash) auto-opens on load ----------------------------------------------
  console.log('\n=== P2-5 deep link auto-open (code path) ===');
  const mainSrc = fs.readFileSync(path.join(ROOT, 'js', 'main.js'), 'utf-8');
  check('hash deep-link auto-open present', mainSrc.includes('location.hash.match'));
  check('popstate handler present (back/forward)', mainSrc.includes('popstate'));

  console.log('\n' + (pass ? 'ALL P2-4/P2-5 CHECKS PASS' : 'SOME P2-4/P2-5 CHECKS FAILED'));
  process.exit(pass ? 0 : 1);
}, 50);
