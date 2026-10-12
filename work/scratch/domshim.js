// Minimal faithful DOM shim for running the REAL js/main.js in Node
// (extracted from work/scratch/verify_p245.js, extended for P4-2:
// compound class+attribute selectors, multi-select menus, chips).
'use strict';

function htmlEscape(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

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
  Object.keys(attrs).forEach(k => {
    if (k.startsWith('data-')) {
      el.dataset[k.replace('data-', '').replace(/-([a-z])/g, (m, c) => c.toUpperCase())] = attrs[k];
    }
  });
  if (attrs.id) el.id = attrs.id;
  if (attrs.value !== undefined) el._value = attrs.value;
  // className keeps the classList in sync (browser semantics).
  Object.defineProperty(el, 'className', {
    get() { return [...el.classList._s].join(' '); },
    set(v) { el.classList._s = new Set(String(v).split(/\s+/).filter(Boolean)); },
    configurable: true,
  });
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
  el.focus = function () { global.__document && (global.__document.activeElement = this); };
  // Browser semantics: appending a node that already has a parent MOVES it.
  el.appendChild = function (c) {
    if (c._parent) {
      const i = c._parent.children.indexOf(c);
      if (i !== -1) c._parent.children.splice(i, 1);
    }
    c._parent = this;
    this.children.push(c);
    return c;
  };
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

// One compound selector part: tag, .class, #id, [attr], [attr="val"],
// and the :checked pseudo (e.g. "input[type=checkbox]:checked").
function matchesPart(el, part) {
  part = part.trim();
  if (!part) return false;
  if (part.includes(':checked')) {
    if (!el.checked) return false;
    part = part.replace(':checked', '').trim();
  }
  const m = part.match(/^([a-z]+)?(?:\.([a-z0-9-]+))?(?:#([a-z0-9-]+))?(?:\[([a-z-]+)(?:="([^"]*)")?\])?$/i);
  if (!m) return false;
  const [, tag, cls, id, attr, attrVal] = m;
  if (tag && el.tagName.toLowerCase() !== tag.toLowerCase()) return false;
  if (cls && !el.classList.contains(cls)) return false;
  if (id && el.id !== id) return false;
  if (attr) {
    if (attrVal !== undefined) return el._attrs[attr] === attrVal;
    return attr in el._attrs;
  }
  return true;
}

function matches(el, sel) {
  sel = sel.trim();
  if (!sel) return false;
  if (sel.includes(',')) return sel.split(',').some(s => matches(el, s));
  return sel.split(/\s+/).every(p => matchesPart(el, p));
}

function qsel(root, sel, first) {
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

module.exports = { makeEl, qsel, matches, htmlEscape };
