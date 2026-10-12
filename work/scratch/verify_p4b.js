// P4-2 part 2: (a) booting with a deep-linked URL that carries repeated
// multi-select params + sort + dir restores the exact view; (b) the
// Community page (single-selects only, no P4-2 controls) still works —
// main.js degrades gracefully.
'use strict';
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '..', '..');
const { makeEl } = require('./domshim');

function makeSelect(opts, extra) {
  const sel = makeEl('select', extra || {});
  const desc = Object.getOwnPropertyDescriptor(sel, 'value');
  Object.defineProperty(sel, 'value', {
    get() { return desc.get.call(sel); },
    set(v) { desc.set.call(sel, (v === '' || opts.includes(v)) ? v : ''); },
    configurable: true,
  });
  return sel;
}

function buildCommonDom() {
  const search = makeEl('input', { id: 'filter-search' });
  const tierSel = makeSelect(['t1', 't2', 't3', 't4', 't5', 't6'],
    { 'class': 'filter-select', 'data-filter': 'tier' });
  const vendorSel = makeSelect(['AMD', 'NVIDIA'],
    { 'class': 'filter-select', 'data-filter': 'vendor' });
  const useCaseSel = makeSelect(['Agentic Coding', 'General Chat', 'Other'],
    { 'class': 'filter-select', 'data-filter': 'use-case' });
  const modeSel = makeSelect(['VRAM-only', 'Hybrid (VRAM+RAM)', 'Hybrid (VRAM+RAM+SSD)', 'CPU+GPU', 'CPU-only'],
    { 'class': 'filter-select', 'data-filter': 'mode' });
  const resetBtn = makeEl('button', { id: 'filter-reset' });
  const shareBtn = makeEl('button', { id: 'filter-share' });
  const emptyEl = makeEl('div', { id: 'filter-empty' });
  emptyEl.hidden = true;
  const emptyClear = makeEl('button', { id: 'filter-empty-clear' });
  emptyEl.appendChild(emptyClear);
  return { search, tierSel, vendorSel, useCaseSel, modeSel, resetBtn, shareBtn, emptyEl, emptyClear };
}

// dom: { pathname, search, ...elements } — every element value is appended
// to a fresh body; pathname/search seed window.location before main.js boots.
function bootDom(dom) {
  const body = makeEl('body');
  Object.values(dom).forEach(el => el && el.tagName && body.appendChild(el));
  global.window = global;
  global.addEventListener = () => {};
  global.location = { pathname: dom.pathname, search: dom.urlSearch, hash: '' };
  function applyUrl(url) {
    const i = url.indexOf('#');
    const noHash = i === -1 ? url : url.slice(0, i);
    const q = noHash.indexOf('?');
    global.location.pathname = q === -1 ? noHash : noHash.slice(0, q);
    global.location.search = q === -1 ? '' : noHash.slice(q);
    global.location.hash = i === -1 ? '' : url.slice(i);
  }
  global.history = {
    pushState(d, t, url) { applyUrl(url); },
    replaceState(d, t, url) { applyUrl(url); },
  };
  global.URLSearchParams = URLSearchParams;
  Object.defineProperty(global, 'navigator', {
    configurable: true,
    value: { clipboard: { writeText: (t) => Promise.resolve() } },
  });
  global.CSS = { escape: (s) => s };
  global.Event = Event;
  global.__document = {
    _els: {
      'filter-search': dom.search, 'filter-reset': dom.resetBtn,
      'filter-share': dom.shareBtn, 'filter-empty': dom.emptyEl,
      'filter-empty-clear': dom.emptyClear,
      'filter-sort': dom.sortSel || null, 'filter-dir': dom.dirBtn || null,
      'filter-chips': dom.chipsEl || null, 'filter-count': dom.countEl || null,
      'data-table': dom.table || null,
      'detail-scrim': dom.scrim || null, 'detail-panel': dom.panel || null,
      'commands-config': dom.config || null,
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
  require(path.join(ROOT, 'js', 'main.js'));
  (global.__document._listeners['DOMContentLoaded'] || []).forEach(cb => cb.call(global.__document));
}

let pass = true;
const check = (name, cond, detail) => {
  console.log((cond ? 'PASS' : 'FAIL') + '  ' + name + (detail !== undefined ? '  [' + detail + ']' : ''));
  if (!cond) pass = false;
};

// ===========================================================================
console.log('=== (a) deep-link restore: repeated multi params + sort + dir ===');
{
  // Fresh require of main.js for this scenario
  delete require.cache[require.resolve(path.join(ROOT, 'js', 'main.js'))];
  const pageHtml = fs.readFileSync(path.join(ROOT, 'matrix.html'), 'utf-8');
  const rowTags = {};
  [...pageHtml.matchAll(/<tr id="([^"]+)"[^>]*>/g)].forEach(m => {
    if (/class="data-row/.test(m[0])) rowTags[m[1]] = m[0];
  });
  const originalRowIds = Object.keys(rowTags);

  const d = buildCommonDom();
  // multi-selects exactly as the page generates them
  function msFromPage(axis) {
    const start = pageHtml.indexOf(`data-filter="${axis}"`);
    const seg = pageHtml.slice(start, pageHtml.indexOf('</div>\n    </div>', start));
    const vals = [...seg.matchAll(/<input type="checkbox" value="([^"]*)">/g)].map(m => m[1]);
    const wrap = makeEl('div', { 'class': 'multiselect', 'data-filter': axis });
    const toggle = makeEl('button', { 'class': 'multiselect-toggle', 'aria-expanded': 'false' });
    const label = makeEl('span', { 'class': 'multiselect-label' });
    label.textContent = 'x';
    toggle.appendChild(label);
    const menu = makeEl('div', { 'class': 'multiselect-menu' });
    menu.hidden = true;
    vals.forEach(v => {
      const lab = makeEl('label', { 'class': 'multiselect-option' });
      lab.appendChild(makeEl('input', { type: 'checkbox', value: v }));
      menu.appendChild(lab);
    });
    wrap.appendChild(toggle);
    wrap.appendChild(menu);
    return wrap;
  }
  d.backendMs = msFromPage('backend');
  d.useCaseMs = msFromPage('use-case');
  d.sortSel = makeSelect(['default', 'vram', 'size', 'speed', 'date'], { id: 'filter-sort', 'class': 'filter-select' });
  d.dirBtn = makeEl('button', { id: 'filter-dir', 'class': 'btn' });
  d.dirBtn.textContent = '↑';
  d.chipsEl = makeEl('div', { id: 'filter-chips' });
  d.countEl = makeEl('p', { id: 'filter-count' });

  const table = makeEl('table', { id: 'data-table' });
  const tbody = makeEl('tbody');
  table.appendChild(tbody);
  d.table = table;
  const attr = (id, name) => ((rowTags[id].match(new RegExp(name + '="([^"]*)"')) || [])[1]);
  const tierIds = [...pageHtml.matchAll(/<tr class="tier-header" data-tier="([^"]+)"/g)].map(m => m[1]);
  tierIds.forEach(tid => {
    tbody.appendChild(makeEl('tr', { 'class': 'tier-header', 'data-tier': tid }));
    originalRowIds.filter(id => attr(id, 'data-tier') === tid).forEach(id => {
      const tr = makeEl('tr');
      [...rowTags[id].matchAll(/([a-z-]+)="([^"]*)"/g)].forEach(m => {
        tr._attrs[m[1]] = m[2];
        if (m[1] === 'id') tr.id = m[2];
        if (m[1] === 'class') tr.classList._s = new Set(m[2].split(/\s+/).filter(Boolean));
        if (m[1].startsWith('data-')) {
          tr.dataset[m[1].replace('data-', '').replace(/-([a-z])/g, (x, c) => c.toUpperCase())] = m[2];
        }
      });
      tr.textContent = id;
      tbody.appendChild(tr);
    });
  });
  d.scrim = makeEl('div', { id: 'detail-scrim' });
  d.panel = makeEl('aside', { id: 'detail-panel' });
  d.panel.inert = true;

  // The real matrix page has NO single use-case select (it's a multi-select)
  delete d.useCaseSel;
  Object.assign(d, {
    pathname: '/matrix.html',
    // deep link: two backends (OR), one use case, a search, date desc
    urlSearch: '?backend=vLLM&backend=llama.cpp&use_case=Agentic+Coding&q=rocm&sort=date&dir=desc',
  });
  bootDom(d);

  const visible = () => Array.from(tbody.children)
    .filter(c => c.classList.contains('data-row') && c.style.display !== 'none');

  check('both backend checkboxes restored from repeated params',
    [...d.backendMs.querySelectorAll('input')].filter(cb => cb.checked).map(cb => cb.value).sort()
      .join(',') === 'llama.cpp,vLLM',
    [...d.backendMs.querySelectorAll('input')].filter(cb => cb.checked).map(cb => cb.value).join(','));
  check('use-case checkbox restored',
    [...d.useCaseMs.querySelectorAll('input')].filter(cb => cb.checked).map(cb => cb.value).join(',') === 'Agentic Coding');
  check('search box restored', d.search.value === 'rocm', d.search.value);
  check('sort select restored to date', d.sortSel.value === 'date', d.sortSel.value);
  check('dir restored to desc (↓, aria-pressed=true)',
    d.dirBtn.textContent === '↓' && d.dirBtn.getAttribute('aria-pressed') === 'true');

  // expected: backend in {vLLM, llama.cpp} AND use-case Agentic Coding AND q 'rocm' in data-search
  const expected = originalRowIds.filter(id =>
    ['vLLM', 'llama.cpp'].includes(attr(id, 'data-backend')) &&
    attr(id, 'data-use-case') === 'Agentic Coding' &&
    attr(id, 'data-search').includes('rocm'));
  check('restored view = ' + expected.length + ' rows (AND across axes, OR within backend)',
    visible().length === expected.length, visible().map(r => r.id).join(','));
  check('date-desc order applied (2026-09-28 rows first)',
    visible().every(r => r.dataset.sortDate === '2026-09-28') || visible().length === 0,
    visible().map(r => r.dataset.sortDate).join(','));
  check('chips restored: 2 backend + 1 use-case + 1 search',
    d.chipsEl.children.length === 4, d.chipsEl.children.map(c => c.getAttribute('aria-label')).join(' | '));
  check('count line restored',
    d.countEl.textContent === `Showing ${expected.length} of 12 submissions`, d.countEl.textContent);
}

// ===========================================================================
console.log('\n=== (b) Community page: no P4-2 controls, graceful degradation ===');
{
  delete require.cache[require.resolve(path.join(ROOT, 'js', 'main.js'))];
  const d = buildCommonDom();
  const mkCard = (name, setups) => {
    const card = makeEl('div', { 'class': 'contributor-card' });
    const ul = makeEl('ul', { 'class': 'setup-list' });
    setups.forEach(s => {
      const li = makeEl('li', {
        'data-sub-id': s.id, 'data-tier': s.tier, 'data-vendor': s.vendor,
        'data-backend': s.backend, 'data-use-case': s.useCase, 'data-mode': s.mode,
      });
      li.textContent = s.text;
      ul.appendChild(li);
    });
    card.appendChild(ul);
    return card;
  };
  d.card1 = mkCard('MadGoat', [
    { id: 'a', tier: 't1', vendor: 'AMD', backend: 'llama-swap', useCase: 'Agentic Coding', mode: '', text: 'Qwen3.6 MoE 35B' },
    { id: 'b', tier: 't4', vendor: 'AMD', backend: 'vLLM', useCase: 'Agentic Coding', mode: '', text: 'Qwen3.8 27B FP8' },
  ]);
  d.card2 = mkCard('s1ugh34d', [
    { id: 'c', tier: 't1', vendor: 'AMD', backend: 'llama.cpp', useCase: 'General Chat', mode: '', text: 'gemma-4' },
  ]);

  // The community page has NO multiselects / chips / count / sort — verify
  // main.js boots and the P2-4 single-select behavior still works.
  Object.assign(d, { pathname: '/community.html', urlSearch: '?vendor=AMD&use_case=Agentic+Coding' });
  bootDom(d);

  // after boot, cards are in document.body
  const allCards = Array.from(global.__document.body.children).filter(c => c.classList.contains('contributor-card'));
  const visibleLis = () => allCards.flatMap(c =>
    Array.from(c.querySelectorAll('.setup-list li')).filter(li => li.style.display !== 'none'));

  check('no crash without P4-2 controls; vendor=AMD AND use_case=Agentic Coding => 2 setups',
    visibleLis().length === 2, visibleLis().map(li => li.textContent).join(','));
  check('visible setups are the two Agentic-Coding AMD rows (a, b)',
    visibleLis().map(li => li.dataset.subId).join(',') === 'a,b',
    visibleLis().map(li => li.dataset.subId).join(','));
  check('card with no visible setups (s1ugh34d) is hidden',
    allCards.length === 2 && allCards[1].style.display === 'none');
  check('empty-state region behaves (no multi-selects involved)',
    d.emptyEl.hidden === true);
  // clear via the reset button
  d.resetBtn.fire('click');
  check('reset restores all setups on the community page', visibleLis().length === 3, visibleLis().length);
}

console.log('\n' + (pass ? 'ALL P4-2b CHECKS PASS' : 'SOME P4-2b CHECKS FAILED'));
process.exit(pass ? 0 : 1);
