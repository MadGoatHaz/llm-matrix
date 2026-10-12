// Runs the REAL js/main.js against a DOM built from the REAL generated
// matrix.html to verify P4-2 (advanced filtering): multi-select OR/AND,
// full-field search (notes via data-search), chips, result count, the sort
// dropdown (vram/size/speed/date + direction), reset, URL sync with
// repeated params. No dependencies.
'use strict';
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '..', '..');
const { makeEl, qsel } = require('./domshim');

const pageHtml = fs.readFileSync(path.join(ROOT, 'matrix.html'), 'utf-8');

// --- extract the real multiselect menus (checkbox values, in page order) ---
function menuValues(axis) {
  const start = pageHtml.indexOf(`data-filter="${axis}"`);
  if (start === -1) throw new Error('multiselect ' + axis + ' not in page');
  const seg = pageHtml.slice(start, pageHtml.indexOf('</div>\n    </div>', start));
  return [...seg.matchAll(/<input type="checkbox" value="([^"]*)">/g)].map(m => m[1]);
}
const backendOpts = menuValues('backend');
const useCaseOpts = menuValues('use-case');

// --- extract the real row attribute tags (verbatim from the page) ---------
const rowTags = {};
[...pageHtml.matchAll(/<tr id="([^"]+)"[^>]*>/g)].forEach(m => {
  if (!/class="data-row/.test(m[0])) return;
  rowTags[m[1]] = m[0];
});
const originalRowIds = Object.keys(rowTags);
if (originalRowIds.length !== 12) throw new Error('expected 12 rows, got ' + originalRowIds.length);

// tier headers in original order
const tierHeaderIds = [...pageHtml.matchAll(/<tr class="tier-header" data-tier="([^"]+)"/g)].map(m => m[1]);

// --- select with option validation (keeps '' for unknown values) ---------
function makeSelect(id, opts, extra) {
  const sel = makeEl('select', Object.assign({ id: id || '' }, extra || {}));
  const desc = Object.getOwnPropertyDescriptor(sel, 'value');
  Object.defineProperty(sel, 'value', {
    get() { return desc.get.call(sel); },
    set(v) { desc.set.call(sel, (v === '' || opts.includes(v)) ? v : ''); },
    configurable: true,
  });
  return sel;
}

// --- build the DOM ---------------------------------------------------------
const search = makeEl('input', { id: 'filter-search' });
const tierSel = makeSelect('', ['t1', 't2', 't3', 't4', 't5', 't6'], { 'class': 'filter-select', 'data-filter': 'tier' });
const vendorSel = makeSelect('', ['AMD', 'NVIDIA'], { 'class': 'filter-select', 'data-filter': 'vendor' });
const modeSel = makeSelect('', ['VRAM-only', 'Hybrid (VRAM+RAM)', 'Hybrid (VRAM+RAM+SSD)', 'CPU+GPU', 'CPU-only'],
  { 'class': 'filter-select', 'data-filter': 'mode' });
const sortSel = makeSelect('filter-sort', ['default', 'vram', 'size', 'speed', 'date'], { 'class': 'filter-select' });
const dirBtn = makeEl('button', { id: 'filter-dir', 'class': 'btn', 'aria-pressed': 'false' });
dirBtn.textContent = '↑';
const chipsEl = makeEl('div', { id: 'filter-chips' });
const countEl = makeEl('p', { id: 'filter-count' });
const resetBtn = makeEl('button', { id: 'filter-reset' });
const shareBtn = makeEl('button', { id: 'filter-share' });
const emptyEl = makeEl('div', { id: 'filter-empty' });
emptyEl.hidden = true;
const emptyClear = makeEl('button', { id: 'filter-empty-clear' });
emptyEl.appendChild(emptyClear);

function makeMultiselect(axis, options) {
  const wrap = makeEl('div', { 'class': 'multiselect', 'data-filter': axis });
  const toggle = makeEl('button', { 'class': 'multiselect-toggle', 'aria-expanded': 'false' });
  const label = makeEl('span', { 'class': 'multiselect-label' });
  label.textContent = axis === 'backend' ? 'All Backends' : 'All Use Cases';
  toggle.appendChild(label);
  const menu = makeEl('div', { 'class': 'multiselect-menu' });
  menu.hidden = true;
  options.forEach(v => {
    const lab = makeEl('label', { 'class': 'multiselect-option' });
    const cb = makeEl('input', { type: 'checkbox', value: v });
    lab.appendChild(cb);
    menu.appendChild(lab);
  });
  wrap.appendChild(toggle);
  wrap.appendChild(menu);
  return wrap;
}
const backendMs = makeMultiselect('backend', backendOpts);
const useCaseMs = makeMultiselect('use-case', useCaseOpts);

const table = makeEl('table', { id: 'data-table' });
const thead = makeEl('thead');
table.appendChild(thead);
const tbody = makeEl('tbody');
table.appendChild(tbody);

// original tbody sequence: tier headers + their rows (as generated)
tierHeaderIds.forEach(tid => {
  const h = makeEl('tr', { 'class': 'tier-header', 'data-tier': tid });
  tbody.appendChild(h);
  originalRowIds.filter(id => {
    const m = rowTags[id].match(/data-tier="([^"]*)"/);
    return m && m[1] === tid;
  }).forEach(id => tbody.appendChild(makeRow(id)));
});

function makeRow(id) {
  const tr = makeEl('tr');
  // apply the real attributes verbatim from the generated page
  [...rowTags[id].matchAll(/([a-z-]+)="([^"]*)"/g)].forEach(m => {
    tr._attrs[m[1]] = m[2];
    if (m[1] === 'id') tr.id = m[2];
    if (m[1] === 'class') tr.classList._s = new Set(m[2].split(/\s+/).filter(Boolean));
    if (m[1].startsWith('data-')) {
      tr.dataset[m[1].replace('data-', '').replace(/-([a-z])/g, (x, c) => c.toUpperCase())] = m[2];
    }
  });
  tr.textContent = id;
  return tr;
}

const scrim = makeEl('div', { id: 'detail-scrim' });
const panel = makeEl('aside', { id: 'detail-panel' });
panel.inert = true;
const dTitle = makeEl('h2', { id: 'detail-title' });
const dClose = makeEl('button', { id: 'detail-close' });
const dBody = makeEl('div', { id: 'detail-body' });
panel.appendChild(dTitle);
panel.appendChild(dClose);
panel.appendChild(dBody);
panel.querySelector = function (sel) {
  if (sel === '.detail-body') return dBody;
  if (sel === '.detail-close') return dClose;
  return qsel(this, sel, true);
};

const body = makeEl('body');
[search, tierSel, vendorSel, backendMs, useCaseMs, modeSel,
  sortSel, dirBtn, resetBtn, shareBtn, chipsEl, countEl, emptyEl,
  table, scrim, panel]
  .forEach(el => body.appendChild(el));

// --- globals ----------------------------------------------------------------
const historyCalls = { push: [], replace: [] };
global.window = global;
global.addEventListener = () => {};
global.location = { pathname: '/matrix.html', search: '', hash: '' };
function applyUrl(url) {
  const i = url.indexOf('#');
  const noHash = i === -1 ? url : url.slice(0, i);
  const q = noHash.indexOf('?');
  global.location.pathname = q === -1 ? noHash : noHash.slice(0, q);
  global.location.search = q === -1 ? '' : noHash.slice(q);
  global.location.hash = i === -1 ? '' : url.slice(i);
}
global.location.href = global.location.pathname + global.location.search + global.location.hash;
global.history = {
  pushState(d, t, url) { historyCalls.push.push(url); applyUrl(url); global.location.href = url; },
  replaceState(d, t, url) { historyCalls.replace.push(url); applyUrl(url); global.location.href = url; },
};
global.URLSearchParams = URLSearchParams;
Object.defineProperty(global, 'navigator', {
  configurable: true,
  value: { clipboard: { writeText: (t) => { global._copied = t; return Promise.resolve(); } } },
});
global.CSS = { escape: (s) => s };
global.Event = Event;
global.__document = {
  _els: {
    'filter-search': search, 'filter-sort': sortSel, 'filter-dir': dirBtn,
    'filter-chips': chipsEl, 'filter-count': countEl, 'filter-reset': resetBtn,
    'filter-share': shareBtn, 'filter-empty': emptyEl,
    'filter-empty-clear': emptyClear, 'data-table': table,
    'detail-scrim': scrim, 'detail-panel': panel, 'detail-title': dTitle,
    'detail-close': dClose, 'detail-body': dBody,
    'commands-config': { id: 'commands-config', textContent: '{"submissions":[],"tiers":[]}' },
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
global.document = global.__document;

let pass = true;
const check = (name, cond, detail) => {
  console.log((cond ? 'PASS' : 'FAIL') + '  ' + name + (detail !== undefined ? '  [' + detail + ']' : ''));
  if (!cond) pass = false;
};

// Read the table in CURRENT DOM order (not original id order) — that's what
// a sort verification needs.
const domRows = () => Array.from(tbody.children).filter(c => c.classList.contains('data-row'));
const visibleRows = () => domRows().filter(tr => tr.style.display !== 'none');
const chipLabels = () => chipsEl.children.map(c => c.getAttribute('aria-label'));
const checkedVals = (ms) => [...ms.querySelectorAll('input[type="checkbox"]')].filter(cb => cb.checked).map(cb => cb.value);
const domHeaders = () => Array.from(tbody.children).filter(c => c.classList.contains('tier-header'));

// --- boot -------------------------------------------------------------------
require(path.join(ROOT, 'js', 'main.js'));
(document._listeners['DOMContentLoaded'] || []).forEach(cb => cb.call(document));

console.log('\n=== P4-2 initial state ===');
check('all 12 rows visible on load', visibleRows().length === 12, visibleRows().length);
check('count reads "Showing 12 of 12 submissions"',
  countEl.textContent === 'Showing 12 of 12 submissions', countEl.textContent);
check('no chips initially', chipsEl.children.length === 0, chipsEl.children.length);

console.log('\n=== P4-2 multi-select: OR within an axis ===');
const bMenu = backendMs.querySelector('.multiselect-menu');
bMenu.hidden = false;
const vllmCb = [...bMenu.querySelectorAll('input')].find(cb => cb.value === 'vLLM');
const lcppCb = [...bMenu.querySelectorAll('input')].find(cb => cb.value === 'llama.cpp');
vllmCb.checked = true; vllmCb.fire('change');
lcppCb.checked = true; lcppCb.fire('change');
check('vLLM + llama.cpp rows visible (OR within axis): 4',
  visibleRows().length === 4, visibleRows().map(r => r.id).join(','));
check('visible rows are exactly the vLLM/llama.cpp ones',
  visibleRows().every(r => ['vLLM', 'llama.cpp'].includes(r.dataset.backend)));
check('toggle label summarizes first-checked +N (llama.cpp +1)',
  backendMs.querySelector('.multiselect-label').textContent === 'llama.cpp +1',
  backendMs.querySelector('.multiselect-label').textContent);
check('toggle shows active styling', backendMs.querySelector('.multiselect-toggle').classList.contains('active'));
check('chips: one per checked value',
  JSON.stringify(chipLabels().sort()) === JSON.stringify([
    'Remove filter: Backend: vLLM', 'Remove filter: Backend: llama.cpp'].sort()),
  chipLabels().join(' | '));
check('count updated to 4 of 12', countEl.textContent === 'Showing 4 of 12 submissions', countEl.textContent);
check('URL carries BOTH backend params (repeated)',
  (location.search.match(/backend=/g) || []).length === 2, location.search);

console.log('\n=== P4-2 AND across axes (tier single-select + backend multi) ===');
const attr = (id, name) => ((rowTags[id].match(new RegExp(name + '="([^"]*)"')) || [])[1]);
const expectedT1Bk = originalRowIds.filter(id =>
  attr(id, 'data-tier') === 't1' && ['vLLM', 'llama.cpp'].includes(attr(id, 'data-backend')));
tierSel.value = 't1'; tierSel.fire('change');
check(`t1 AND (vLLM|llama.cpp) => ${expectedT1Bk.length} rows`,
  visibleRows().length === expectedT1Bk.length, visibleRows().map(r => r.id).join(','));
check('all visible rows are t1', visibleRows().every(r => r.dataset.tier === 't1'));
check('chip set now includes the tier chip',
  chipLabels().some(l => l === 'Remove filter: VRAM tier: t1'), chipLabels().join(' | '));
check('URL: tier + 2x backend',
  /tier=t1/.test(location.search) && (location.search.match(/backend=/g) || []).length === 2, location.search);

console.log('\n=== P4-2 use-case multi-select (3rd axis) ===');
const uMenu = useCaseMs.querySelector('.multiselect-menu');
uMenu.hidden = false;
const agCb = [...uMenu.querySelectorAll('input')].find(cb => cb.value === 'Agentic Coding');
agCb.checked = true; agCb.fire('change');
const expected = originalRowIds.filter(id => {
  const tr = rowTags[id];
  const t = (tr.match(/data-tier="([^"]*)"/) || [])[1];
  const b = (tr.match(/data-backend="([^"]*)"/) || [])[1];
  const u = (tr.match(/data-use-case="([^"]*)"/) || [])[1];
  return t === 't1' && ['vLLM', 'llama.cpp'].includes(b) && u === 'Agentic Coding';
});
check('t1 AND (vLLM|llama.cpp) AND Agentic Coding => ' + expected.length + ' rows',
  visibleRows().length === expected.length,
  visibleRows().map(r => r.id).join(',') + ' vs ' + expected.join(','));
check('use-case chip present',
  chipLabels().some(l => l === 'Remove filter: Use case: Agentic Coding'), chipLabels().join(' | '));
check('count matches', countEl.textContent === `Showing ${expected.length} of 12 submissions`, countEl.textContent);

console.log('\n=== P4-2 chip removal (✕ on one chip) ===');
const vllmChip = chipsEl.children.find(c => c.dataset.value === 'vLLM' && c.dataset.axis === 'backend');
vllmChip.fire('click');
check('vLLM checkbox unchecked after chip click', !vllmCb.checked);
check('llama.cpp still checked', lcppCb.checked);
check('vLLM chip gone, llama.cpp chip remains',
  !chipLabels().includes('Remove filter: Backend: vLLM') &&
  chipLabels().includes('Remove filter: Backend: llama.cpp'), chipLabels().join(' | '));
const expected2 = originalRowIds.filter(id => {
  const tr = rowTags[id];
  const t = (tr.match(/data-tier="([^"]*)"/) || [])[1];
  const b = (tr.match(/data-backend="([^"]*)"/) || [])[1];
  const u = (tr.match(/data-use-case="([^"]*)"/) || [])[1];
  return t === 't1' && b === 'llama.cpp' && u === 'Agentic Coding';
});
check('visible rows now = t1 AND llama.cpp AND Agentic Coding (' + expected2.length + ')',
  visibleRows().length === expected2.length, visibleRows().map(r => r.id).join(','));
check('URL now has a single backend param',
  (location.search.match(/backend=/g) || []).length === 1 && /backend=llama\.cpp/.test(location.search),
  location.search);
check('toggle label back to single value',
  backendMs.querySelector('.multiselect-label').textContent === 'llama.cpp',
  backendMs.querySelector('.multiselect-label').textContent);

console.log('\n=== P4-2 full-field search (notes via data-search) ===');
tierSel.value = ''; tierSel.fire('change');
agCb.checked = false; agCb.fire('change');
lcppCb.checked = false; lcppCb.fire('change');
const pushesBeforeTyping = historyCalls.push.length;
search.value = '9B compute'; search.fire('input');
const expected3 = originalRowIds.filter(id => (rowTags[id].match(/data-search="([^"]*)"/) || [])[1].includes('9b compute'));
check('search "9B compute" (a NOTES phrase) matches ' + expected3.length + ' row(s)',
  visibleRows().length === expected3.length, visibleRows().map(r => r.id).join(','));
check('search chip present with quotes',
  chipLabels().some(l => l.includes('Search:')), chipLabels().join(' | '));
check('typing used replaceState (no new pushes)', historyCalls.push.length === pushesBeforeTyping,
  'pushes=' + historyCalls.push.length);
search.value = 'zzzznotfound'; search.fire('input');
check('second keystroke-burst still no new pushes', historyCalls.push.length === pushesBeforeTyping,
  'pushes=' + historyCalls.push.length);
check('dead-end search shows the empty state', emptyEl.hidden === false);
check('empty state: 0 of 12', countEl.textContent === 'Showing 0 of 12 submissions', countEl.textContent);

console.log('\n=== P4-2 sort dropdown ===');
const resetLabel = (pageHtml.match(/<button id="filter-reset"[^>]*>([^<]*)<\/button>/) || [])[1];
check('reset button label is "Clear all filters"', resetLabel === 'Clear all filters', resetLabel);
resetBtn.fire('click');
check('reset clears search/chips/sort and restores all rows',
  visibleRows().length === 12 && chipsEl.children.length === 0 && location.search === '',
  location.search);

sortSel.value = 'size'; sortSel.fire('change');
check('size sort: all 12 rows visible (sort is not a filter)', visibleRows().length === 12);
const sizeOrder = domRows().map(r => r.dataset.sortSize);
check('size sort ascending (unknowns last)',
  JSON.stringify(sizeOrder) === JSON.stringify([...sizeOrder].sort((a, b) =>
    (a === '' ? Infinity : +a) - (b === '' ? Infinity : +b))),
  sizeOrder.join(','));
check('global sort: tier headers removed from the table',
  domHeaders().length === 0, domHeaders().length);
check('URL carries sort=size (no dir for asc)', /sort=size/.test(location.search) && !/dir=/.test(location.search), location.search);

dirBtn.fire('click');
check('direction toggled to desc (aria-pressed=true, ↓)',
  dirBtn.getAttribute('aria-pressed') === 'true' && dirBtn.textContent === '↓');
const sizeOrderDesc = domRows().map(r => r.dataset.sortSize);
check('size desc: 35…4 first, unknowns last',
  sizeOrderDesc.slice(0, 9).every((v, i, arr) => i === 0 || +arr[i - 1] >= +v) &&
    sizeOrderDesc[9] === '' && sizeOrderDesc[10] === '',
  sizeOrderDesc.join(','));
check('URL carries dir=desc', /dir=desc/.test(location.search), location.search);

sortSel.value = 'vram'; sortSel.fire('change');
check('vram sort keeps tier grouping (headers back in the table)',
  domHeaders().length === tierHeaderIds.length, domHeaders().length + ' headers');
check('vram sort: within the t1 group, desc (dir persists across axes)',
  (() => {
    const t1 = domRows().filter(r => r.dataset.tier === 't1');
    const vals = t1.map(r => r.dataset.sortVram === '' ? -Infinity : +r.dataset.sortVram);
    return vals.every((v, i) => i === 0 || vals[i - 1] >= v);
  })(),
  domRows().filter(r => r.dataset.tier === 't1').map(r => r.dataset.sortVram).join(','));

sortSel.value = 'date'; sortSel.fire('change');
const dateOrder = domRows().map(r => r.dataset.sortDate || '0000');
check('date sort: lexicographic desc (2026-09-28 first)',
  dateOrder.every((v, i) => i === 0 || dateOrder[i - 1] >= v), dateOrder.join(','));

sortSel.value = 'default'; sortSel.fire('change');
check('default sort restores the original row sequence',
  domRows().map(r => r.id).join(',') === originalRowIds.join(','),
  domRows().map(r => r.id).join(','));
check('default sort restores the tier headers', domHeaders().length === tierHeaderIds.length);
check('dir resets to ↑ (asc) with the default order',
  dirBtn.textContent === '↑' && dirBtn.getAttribute('aria-pressed') === 'false');
check('URL clean after default (no stale dir)', location.search === '', location.search);

console.log('\n=== P4-2 column-header click after a dropdown sort ===');
// initSorting already booted (no <th> in the shim thead), so verify the
// coordination hook in source: a th click resets an active dropdown sort
// before applying the within-group column sort.
const mainSrc = fs.readFileSync(path.join(ROOT, 'js', 'main.js'), 'utf-8');
check('th click resets an active dropdown sort first (source hook)',
  mainSrc.includes("if (matrixSort.axis !== 'default') resetToDefaultSort();"));

console.log('\n' + (pass ? 'ALL P4-2 CHECKS PASS' : 'SOME P4-2 CHECKS FAILED'));
process.exit(pass ? 0 : 1);
