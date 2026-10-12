// main.js — shared client behavior for The Local AI Stack.
//
//   * mobile nav toggle, active nav link, Guides dropdown
//   * matrix table sorting (within VRAM-tier groups)
//   * URL-synced filters (P2-4): search + tier + vendor + backend +
//     use case + engine mode. The filter state lives in the query string
//     (?tier=&vendor=&backend=&use_case=&mode=&q=) — loading a URL with
//     params restores that exact view, and the 🔗 Share button copies it.
//     Works on the Matrix (rows) and the Community page (setup lists).
//   * row detail panel (P2-5): clicking a Matrix row (or its ⓘ button)
//     opens a slide-in panel with the full submission — focus-trapped,
//     ESC to close, focus restored, and deep-linkable via the row's #id
//     anchor (matrix.html#post_2_madgoat_1 auto-opens that row).
//
// Vanilla, zero dependencies. Page-specific tools (compare.js,
// commands.js, recommend.js) load after this file where needed.

document.addEventListener('DOMContentLoaded', () => {
    initNav();
    initSorting();
    initFilters();
    initDetailPanel();
});

// history.* throws on file:// in some browsers; callers degrade to
// "feature works, URL doesn't sync" — never a page crash.
function safeHistory(fn) {
    try { fn(); } catch (e) { /* no URL sync from this context */ }
}

// ---------------------------------------------------------------------------
// Navigation
// ---------------------------------------------------------------------------
function initNav() {
    const toggle = document.querySelector('.nav-toggle');
    const links = document.querySelector('.nav-links');
    if (toggle && links) {
        toggle.addEventListener('click', () => links.classList.toggle('open'));
    }

    // Set active nav link. Handles both flat root pages (index.html,
    // matrix.html, …) and directory-based guide URLs (guides/<slug>/).
    const currentLeaf = window.location.pathname.split('/').pop() || 'index.html';
    const currentPath = window.location.pathname.replace(/\/+$/, '');
    document.querySelectorAll('.nav-links a').forEach(a => {
        const href = a.getAttribute('href');
        if (!href) return;
        let active = (href === currentLeaf);
        if (!active) {
            try {
                const resolved = new URL(href, window.location.href).pathname.replace(/\/+$/, '');
                active = (resolved === currentPath);
            } catch (e) { /* ignore malformed hrefs */ }
        }
        if (active) a.classList.add('active');
    });

    // Guides dropdown toggle (P1-9 populates the menu; no-op while absent).
    // A click toggles an .open state for mobile/keyboard users; the CSS
    // :hover / :focus-within rules also open it on desktop.
    document.querySelectorAll('.nav-dropdown').forEach(dd => {
        const dt = dd.querySelector('.nav-dropdown-toggle');
        if (!dt) return;
        dt.addEventListener('click', (e) => {
            if (window.innerWidth <= 768) return; // let the link navigate on mobile
            e.preventDefault();
            dd.classList.toggle('open');
        });
        document.addEventListener('click', (e) => {
            if (!dd.contains(e.target)) dd.classList.remove('open');
        });
    });
}

// ---------------------------------------------------------------------------
// Table sorting (matrix page)
// ---------------------------------------------------------------------------
function initSorting() {
    const table = document.querySelector('#data-table');
    if (!table) return;

    let sortState = {};
    table.querySelectorAll('th').forEach((th, colIdx) => {
        // The "Actions" column (detail/compare/launch buttons) is not a
        // data column — it carries data-nosort and is skipped here.
        if (th.hasAttribute('data-nosort')) return;
        th.addEventListener('click', () => {
            sortState[colIdx] = -(sortState[colIdx] || -1);
            sortTable(table, colIdx, sortState);
        });
    });
}

function sortTable(table, col, sortState) {
    const tbody = table.querySelector('tbody');
    const groups = [];
    let current = { header: null, rows: [] };

    tbody.querySelectorAll('tr').forEach(row => {
        if (row.classList.contains('tier-header')) {
            if (current.header || current.rows.length) groups.push(current);
            current = { header: row, rows: [] };
        } else {
            current.rows.push(row);
        }
    });
    if (current.header || current.rows.length) groups.push(current);

    groups.forEach(group => {
        group.rows.sort((a, b) => {
            const av = a.cells[col]?.textContent || '';
            const bv = b.cells[col]?.textContent || '';
            const an = parseFloat(av.replace(/[^\d.-]/g, ''));
            const bn = parseFloat(bv.replace(/[^\d.-]/g, ''));
            if (!isNaN(an) && !isNaN(bn)) return (an - bn) * (sortState[col] || 1);
            return av.localeCompare(bv, undefined, {numeric: true}) * (sortState[col] || 1);
        });
    });

    tbody.innerHTML = '';
    groups.forEach(group => {
        if (group.header) tbody.appendChild(group.header);
        group.rows.forEach(r => tbody.appendChild(r));
    });

    table.querySelectorAll('th').forEach((th, i) => {
        th.classList.remove('sort-asc', 'sort-desc');
        if (sortState[i]) th.classList.add(sortState[i] === 1 ? 'sort-asc' : 'sort-desc');
    });
}

// ---------------------------------------------------------------------------
// Filters (P2-4) — URL-synced, shareable.
//
// Matrix: filters the table rows (tier-group headers hide when empty).
// Community: filters each contributor's setup list; cards with no visible
// setups hide. Both pages share one filter bar + one query-string contract:
//   ?tier=&vendor=&backend=&use_case=&mode=&q=
// Discrete changes (selects, reset) push a history entry; continuous typing
// (search) replaces it, so the back button isn't flooded with per-keystroke
// states. Loading a URL with these params restores the exact view.
// ---------------------------------------------------------------------------
function initFilters() {
    const search = document.getElementById('filter-search');
    const selects = Array.from(document.querySelectorAll('.filter-select'));
    const resetBtn = document.getElementById('filter-reset');
    const shareBtn = document.getElementById('filter-share');
    const table = document.getElementById('data-table');
    const cards = Array.from(document.querySelectorAll('.contributor-card'));
    const emptyEl = document.getElementById('filter-empty');
    if (!search || (!table && !cards.length)) return;

    // data-filter value -> dataset property name ("use-case" -> "useCase").
    const dsKey = (f) => f.replace(/-([a-z])/g, (_, c) => c.toUpperCase());
    // data-filter value -> URL param key ("use-case" -> "use_case").
    const urlKey = (s) => s.dataset.filter.replace(/-/g, '_');
    // Fixed param order, so shared URLs are stable and diff-friendly.
    const PARAM_ORDER = ['tier', 'vendor', 'backend', 'use_case', 'mode', 'q'];

    function readState() {
        const state = { q: search.value };
        selects.forEach(s => { state[urlKey(s)] = s.value; });
        return state;
    }

    function writeState(state) {
        if (state.q !== undefined) search.value = state.q;
        selects.forEach(s => {
            const v = state[urlKey(s)];
            if (v !== undefined) s.value = v; // unmatched values keep ''
        });
    }

    function syncUrl(state, push) {
        const params = new URLSearchParams();
        PARAM_ORDER.forEach(k => { if (state[k]) params.set(k, state[k]); });
        const qs = params.toString();
        const url = window.location.pathname + (qs ? '?' + qs : '') + window.location.hash;
        safeHistory(() => (push ? history.pushState : history.replaceState)({ filters: state }, '', url));
    }

    function visibleCount() {
        if (table) {
            let n = 0;
            table.querySelectorAll('tbody tr').forEach(row => {
                if (row.classList.contains('tier-header')) return;
                if (row.style.display !== 'none') n++;
            });
            return n;
        }
        let n = 0;
        cards.forEach(card => {
            card.querySelectorAll('.setup-list li').forEach(li => {
                if (li.style.display !== 'none') n++;
            });
        });
        return n;
    }

    function matches(state, el) {
        const q = (state.q || '').toLowerCase();
        if (q && !el.textContent.toLowerCase().includes(q)) return false;
        for (const s of selects) {
            const val = s.value;
            if (val && el.dataset[dsKey(s.dataset.filter)] !== val) return false;
        }
        return true;
    }

    function apply(push) {
        const state = readState();

        if (table) {
            table.querySelectorAll('tbody tr').forEach(row => {
                if (row.classList.contains('tier-header')) {
                    row.style.display = '';
                    return;
                }
                row.style.display = matches(state, row) ? '' : 'none';
            });
            // Hide tier headers whose group is fully filtered out.
            table.querySelectorAll('.tier-header').forEach(header => {
                let next = header.nextElementSibling;
                let hasVisible = false;
                while (next && !next.classList.contains('tier-header')) {
                    if (next.style.display !== 'none') hasVisible = true;
                    next = next.nextElementSibling;
                }
                header.style.display = hasVisible ? '' : 'none';
            });
        } else {
            cards.forEach(card => {
                card.querySelectorAll('.setup-list li').forEach(li => {
                    li.style.display = matches(state, li) ? '' : 'none';
                });
                const anyVisible = Array.from(card.querySelectorAll('.setup-list li'))
                    .some(li => li.style.display !== 'none');
                card.style.display = anyVisible ? '' : 'none';
            });
        }

        if (emptyEl) {
            const active = (state.q && state.q.trim()) || selects.some(s => s.value);
            emptyEl.hidden = !(active && visibleCount() === 0);
        }

        syncUrl(state, push !== false);
    }

    search.addEventListener('input', () => apply(false));
    selects.forEach(s => s.addEventListener('change', () => apply(true)));

    function reset() {
        search.value = '';
        selects.forEach(s => { s.value = ''; });
        apply(true);
    }
    if (resetBtn) resetBtn.addEventListener('click', reset);
    const emptyClear = document.getElementById('filter-empty-clear');
    if (emptyClear) emptyClear.addEventListener('click', reset);

    // 🔗 Share: the URL is already in sync, so copy the address.
    if (shareBtn) {
        shareBtn.addEventListener('click', () => {
            const url = window.location.href;
            const done = (ok) => {
                const orig = shareBtn.textContent;
                shareBtn.textContent = ok ? '✓ Copied!' : 'Copy failed';
                shareBtn.disabled = true;
                setTimeout(() => { shareBtn.textContent = orig; shareBtn.disabled = false; }, 1500);
            };
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(url).then(
                    () => done(true),
                    () => done(fallbackCopy(url))
                );
            } else {
                done(fallbackCopy(url));
            }
        });
    }

    function fallbackCopy(text) {
        try {
            const ta = document.createElement('textarea');
            ta.value = text;
            ta.style.position = 'fixed';
            ta.style.opacity = '0';
            document.body.appendChild(ta);
            ta.select();
            const ok = document.execCommand('copy');
            document.body.removeChild(ta);
            return ok;
        } catch (e) { return false; }
    }

    // Restore a shared/deep-linked view on load.
    const p = new URLSearchParams(window.location.search);
    const state = { q: p.get('q') || '' };
    selects.forEach(s => {
        const v = p.get(urlKey(s));
        if (v) state[urlKey(s)] = v;
    });
    writeState(state);
    apply(false);

    // Back/forward through filter states (pushState entries).
    window.addEventListener('popstate', () => {
        const pp = new URLSearchParams(window.location.search);
        const st = { q: pp.get('q') || '' };
        selects.forEach(s => {
            const v = pp.get(urlKey(s));
            if (v) st[urlKey(s)] = v;
        });
        writeState(st);
        apply(false);
    });
}

// ---------------------------------------------------------------------------
// Row detail panel (P2-5)
//
// Clicking a Matrix row (or its ⓘ button) opens a slide-in dialog with the
// full submission: hardware, quant, use case, context/KV, performance,
// engine mode, the submitter's notes, the original forum deep link, a
// launch-command button (reuses js/commands.js), and comparison actions.
// Accessible: role=dialog + aria-modal, focus moved in on open and trapped,
// ESC closes, focus restored to the trigger, inert while closed. The row's
// #id anchor is written to the URL on open (and removed on close), so
// matrix.html#<row-id> deep links (e.g. from Recommend) auto-open the panel.
// ---------------------------------------------------------------------------
function initDetailPanel() {
    const table = document.getElementById('data-table');
    const panel = document.getElementById('detail-panel');
    const scrim = document.getElementById('detail-scrim');
    const configEl = document.getElementById('commands-config');
    if (!table || !panel || !scrim || !configEl) return;

    let config;
    try { config = JSON.parse(configEl.textContent); }
    catch (e) { console.error('detail panel: bad config island', e); return; }

    const byId = {};
    (config.submissions || []).forEach(s => { byId[s.id] = s; });
    const tierLabel = {};
    (config.tiers || []).forEach(t => { tierLabel[t.id] = t.label; });

    const body = panel.querySelector('.detail-body');
    const title = document.getElementById('detail-title');
    const closeBtn = document.getElementById('detail-close');
    const FORUM_THREAD = 'https://forum.level1techs.com/t/256443';

    let openId = null;
    let lastFocused = null;

    function esc(v) {
        const d = document.createElement('div');
        d.textContent = (v == null) ? '' : String(v);
        return d.innerHTML;
    }

    function shortModel(name) {
        if (!name) return '';
        let s = String(name).split(',')[0].trim();
        if (s.indexOf('/') !== -1 && s.indexOf('http') !== 0) s = s.split('/')[1];
        s = s.replace(/\s*\([^)]*\)\s*$/g, '').trim();
        return s;
    }

    function shortBackend(b) {
        return String(b || '').replace(/\(.*$/, '').trim();
    }

    // Original forum post: https://forum.level1techs.com/t/256443/#post-<id>
    function forumUrl(s) {
        const src = s.source || {};
        return src.post_id ? FORUM_THREAD + '#post-' + src.post_id : FORUM_THREAD;
    }

    function populate(s) {
        title.textContent = shortModel((s.model || {}).name) || 'Setup details';

        const hw = s.hardware || {};
        const perf = s.performance || {};
        const ctx = s.context || {};
        const fields = [
            ['Hardware', [hw.description, hw.vendor].filter(Boolean).join(' · ')],
            ['Backend', s.backend],
            ['Quant', [s.quant, s.weight_precision].filter(Boolean).join(' · ')],
            ['Use case', s.use_cases],
            ['Context (stable)', ctx.stable],
            ['KV cache', ctx.kv_cache],
            ['Decode speed', perf.decode_tps],
            ['Prefill speed', perf.prefill_tps],
            ['TTFT (cold)', perf.ttft_cold],
            ['Power draw', perf.power_w],
            ['Engine mode', s.engine_mode],
        ];

        let html = '<div class="detail-badges">';
        html += '<span class="badge badge-amber">' + esc(tierLabel[s.tier] || s.tier || '—') + '</span>';
        html += '<span class="badge badge-blue">' + esc(shortBackend(s.backend) || '—') + '</span>';
        if (s.highlight) html += '<span class="badge badge-green">★ Community highlight</span>';
        html += '</div>';

        html += '<dl class="detail-grid">';
        fields.forEach(pair => {
            if (!pair[1]) return;
            html += '<div class="detail-item"><dt>' + esc(pair[0]) + '</dt><dd>' + esc(pair[1]) + '</dd></div>';
        });
        html += '</dl>';

        if (s.notes) {
            html += '<div class="detail-notes"><h3>Submitter notes</h3><p>' + esc(s.notes) + '</p></div>';
        }

        const src = s.source || {};
        if (src.username) {
            const when = src.submitted_at ? String(src.submitted_at).slice(0, 10) : '';
            html += '<div class="detail-credit">Submitted by <strong>' + esc(src.username) + '</strong>' +
                (when ? ' on ' + esc(when) : '') + '</div>';
        }

        html += '<div class="detail-actions">';
        html += '<button class="btn btn-primary" type="button" data-launch-sub="' + esc(s.id) + '">🚀 Copy launch command</button>';
        html += '<button class="btn detail-add-compare" type="button" aria-pressed="false">➕ Add to comparison</button>';
        html += '<a class="btn" href="compare/?a=' + encodeURIComponent(s.id) + '">Compare this setup →</a>';
        html += '<a class="btn" href="' + esc(forumUrl(s)) + '" target="_blank" rel="noopener">💬 Read the forum post</a>';
        const mu = (s.model || {}).url;
        if (mu && /^https?:/.test(mu)) {
            html += '<a class="btn" href="' + esc(mu) + '" target="_blank" rel="noopener">⬇ Download the model</a>';
        }
        html += '</div>';
        body.innerHTML = html;

        // "Add to comparison" toggles the row's checkbox; compare.js
        // listens for its change event and updates the Compare (N) bar.
        const addBtn = body.querySelector('.detail-add-compare');
        if (addBtn) {
            addBtn.addEventListener('click', () => {
                const check = table.querySelector(
                    '.compare-check[data-sub-id="' + (window.CSS && CSS.escape ? CSS.escape(s.id) : s.id) + '"]');
                if (!check) return;
                check.checked = !check.checked;
                check.dispatchEvent(new Event('change', { bubbles: true }));
                addBtn.setAttribute('aria-pressed', String(check.checked));
                addBtn.textContent = check.checked ? '✓ In comparison — click to remove' : '➕ Add to comparison';
            });
        }
    }

    function open(id, trigger) {
        const s = byId[id];
        if (!s) return;
        openId = id;
        lastFocused = trigger || document.activeElement;
        populate(s);
        panel.classList.add('open');
        scrim.classList.add('open');
        panel.setAttribute('aria-hidden', 'false');
        if ('inert' in panel) panel.inert = false;
        document.body.classList.add('detail-open');
        // Deep link: the row's #id anchor becomes the shareable URL.
        safeHistory(() => history.replaceState(null, '',
            window.location.pathname + window.location.search + '#' + id));
        // Move focus into the panel (the close button = predictable exit).
        (closeBtn || panel).focus();
    }

    function close() {
        if (!openId) return;
        openId = null;
        panel.classList.remove('open');
        scrim.classList.remove('open');
        panel.setAttribute('aria-hidden', 'true');
        if ('inert' in panel) panel.inert = true;
        document.body.classList.remove('detail-open');
        safeHistory(() => history.replaceState(null, '',
            window.location.pathname + window.location.search));
        if (lastFocused && typeof lastFocused.focus === 'function') lastFocused.focus();
        lastFocused = null;
    }

    // Row interaction: the ⓘ button opens directly; any other click on the
    // row (but not on the checkbox / launch button / links) opens too.
    table.addEventListener('click', (e) => {
        const detailBtn = e.target.closest ? e.target.closest('[data-detail-sub]') : null;
        if (detailBtn) {
            e.preventDefault();
            e.stopPropagation();
            open(detailBtn.getAttribute('data-detail-sub'), detailBtn);
            return;
        }
        if (e.target.closest && e.target.closest('button, input, a, label')) return;
        const row = e.target.closest ? e.target.closest('tr.data-row') : null;
        if (row && row.id) open(row.id, row);
    });

    // Keyboard: Enter / Space on a focused row opens the panel.
    table.addEventListener('keydown', (e) => {
        if (e.key !== 'Enter' && e.key !== ' ') return;
        const row = e.target.closest ? e.target.closest('tr.data-row') : null;
        if (row && row === document.activeElement && row.id) {
            e.preventDefault();
            open(row.id, row);
        }
    });

    if (closeBtn) closeBtn.addEventListener('click', close);
    scrim.addEventListener('click', close);

    // Focus trap: Tab cycles inside the open panel; ESC closes it.
    panel.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            e.stopPropagation();
            close();
            return;
        }
        if (e.key !== 'Tab') return;
        const focusables = panel.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (!focusables.length) return;
        const first = focusables[0];
        const last = focusables[focusables.length - 1];
        if (e.shiftKey && document.activeElement === first) {
            e.preventDefault();
            last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
            e.preventDefault();
            first.focus();
        }
    });

    // Deep link: matrix.html#<row-id> (e.g. from a Recommend card) opens
    // that row's panel on load.
    const m = window.location.hash.match(/^#(.+)$/);
    if (m) {
        const id = decodeURIComponent(m[1]);
        if (byId[id]) open(id);
    }
}
