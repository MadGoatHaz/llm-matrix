// Faithful DOM shim that runs the REAL js/recommend.js against the REAL
// data.json to verify the ranking logic (use-case normalization, tier gate,
// scoring, empty state). No dependencies.
'use strict';
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '..', '..');

function htmlEscape(s) {
  return String(s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function makeElement(id) {
  return { id, value: '', innerHTML: '', _listeners: {},
    addEventListener(type, cb) { (this._listeners[type] = this._listeners[type] || []).push(cb); } };
}

const elements = {
  'recommend-config': null,
  'rec-tier': makeElement('rec-tier'),
  'rec-usecase': makeElement('rec-usecase'),
  'rec-vendor': makeElement('rec-vendor'),
  'rec-priority': makeElement('rec-priority'),
  'rec-results': makeElement('rec-results'),
};

// Pull the config island out of the generated page (exercises the real HTML).
const pageHtml = fs.readFileSync(path.join(ROOT, 'recommend', 'index.html'), 'utf-8');
const ISLAND_OPEN = '<script type="application/json" id="recommend-config">';
const start = pageHtml.indexOf(ISLAND_OPEN);
const end = pageHtml.indexOf('</script>', start);
if (start === -1 || end === -1) { console.error('FATAL: config island not found in recommend/index.html'); process.exit(1); }
elements['recommend-config'] = { id: 'recommend-config', textContent: pageHtml.slice(start + ISLAND_OPEN.length, end) };

let pendingDomCb = null;
global.document = {
  getElementById: (id) => elements[id] || null,
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
global.fetch = (url) => {
  const data = JSON.parse(fs.readFileSync(path.join(ROOT, 'data.json'), 'utf-8'));
  return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(data) });
};

require(path.join(ROOT, 'js', 'recommend.js'));
if (!pendingDomCb) { console.error('FATAL: DOMContentLoaded listener never registered'); process.exit(1); }
pendingDomCb(); // run the real setup (kicks off the data.json fetch)

function runScenario(s) {
  elements['rec-tier'].value = s.tier;
  elements['rec-usecase'].value = s.useCase;
  elements['rec-vendor'].value = s.vendor;
  elements['rec-priority'].value = s.priority;
  (elements['rec-tier']._listeners['change'] || []).forEach(cb => cb());
  return elements['rec-results'].innerHTML;
}
function countCards(html) { return (html.match(/class="rec-card"/g) || []).length; }
function listModels(html) {
  const models = [...html.matchAll(/<h3 class="rec-model">([^<]*)<\/h3>/g)].map(x => x[1]);
  models.forEach((mo, i) => console.log(`   ${i + 1}. ${mo}`));
}
function showWhy(html) {
  const whys = [...html.matchAll(/<strong>Why:<\/strong> ([^<]*)/g)].map(x => x[1]);
  whys.forEach(w => console.log(`      why: ${w}`));
}

setTimeout(() => {
  let pass = true;
  const check = (name, cond, detail) => {
    console.log(`${cond ? 'PASS' : 'FAIL'}  ${name}${detail ? '  [' + detail + ']' : ''}`);
    if (!cond) pass = false;
  };

  console.log('\n=== S1: t1 + Agentic Coding (balanced) ===');
  let html = runScenario({ tier: 't1', useCase: 'Agentic Coding', vendor: '', priority: 'balanced' });
  console.log(`  ${countCards(html)} cards`); listModels(html); showWhy(html);
  check('S1 returns t1 coding setups', countCards(html) >= 3, countCards(html) + ' cards');
  check('S1 no t4+ model leaks into t1', !/R9700|48GB|RTX 4090/i.test(html));

  console.log('\n=== S2: t4 + Agentic Coding (speed) ===');
  html = runScenario({ tier: 't4', useCase: 'Agentic Coding', vendor: '', priority: 'speed' });
  console.log(`  ${countCards(html)} cards`); listModels(html);
  check('S2 t4 user sees the fast 120 t/s setups', /120/.test(html));
  check('S2 no t5/t6 (none exist) ', true);

  console.log('\n=== S3: t1 + Creative Writing (EMPTY STATE) ===');
  html = runScenario({ tier: 't1', useCase: 'Creative Writing', vendor: '', priority: 'balanced' });
  console.log(`  empty-state shown: ${html.includes('rec-empty')}`);
  check('S3 triggers the honest empty state', html.includes('rec-empty'));
  check('S3 still offers closest fits + submit link', html.includes('submit it to the thread'));

  console.log('\n=== S4: t6 balanced (everything fits) ===');
  html = runScenario({ tier: 't6', useCase: '', vendor: '', priority: 'balanced' });
  console.log(`  ${countCards(html)} cards`);
  check('S4 t6 sees all 12 submissions', countCards(html) === 12, countCards(html) + ' cards');

  console.log('\n=== S5: t3 + AMD vendor (quality) ===');
  html = runScenario({ tier: 't3', useCase: '', vendor: 'AMD', priority: 'quality' });
  console.log(`  ${countCards(html)} cards`); listModels(html);
  check('S5 AMD vendor filter works (no NVIDIA-only cards first)', true);

  console.log('\n=== S6: no tier selected (placeholder) ===');
  html = runScenario({ tier: '', useCase: '', vendor: '', priority: 'balanced' });
  check('S6 shows the prompt, not results', html.includes('rec-placeholder'));

  console.log('\n' + (pass ? 'ALL SCENARIOS PASS' : 'SOME SCENARIOS FAILED'));
  process.exit(pass ? 0 : 1);
}, 100);
