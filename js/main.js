// main.js — shared client behavior for The Local AI Stack.
//
//   * mobile nav toggle, active nav link, Guides dropdown
//   * matrix table sorting (within VRAM-tier groups)
//   * URL-synced filters (P2-4, extended by P4-2): search + tier + vendor
//     + backend + use case + engine mode. The filter state lives in the
//     query string — loading a URL with params restores that exact view,
//     and the 🔗 Share button copies it. Works on the Matrix (rows) and
//     the Community page (setup lists).
//     P4-2 adds: multi-select Backend / Use Case (OR within an axis,
//     AND across axes), full-field text search (each row's data-search
//     blob covers notes and every other field), a sort dropdown
//     (VRAM / model size / speed / date + direction), removable active-
//     filter chips, a live "Showing N of M" result count, and smooth
//     row transitions (prefers-reduced-motion respected). The URL
//     contract extends P2-4: repeated backend= / use_case= params plus
//     sort= and dir=desc.
//   * row detail panel (P2-5): clicking a Matrix row (or its ⓘ button)
//     opens a slide-in panel with the full submission — focus-trapped,
//     ESC to close, focus restored, and deep-linkable via the row's #id
//     anchor (matrix.html#post_2_madgoat_1 auto-opens that row).
//
// Vanilla, zero dependencies. Page-specific tools (compare.js,
// commands.js, recommend.js) load after this file where needed.

// ---------------------------------------------------------------------------
// Shared numeric parsers (E7) — the ONE client-side implementation of the
// generator's speed / context conventions. Exposed on window so the
// page-specific tools (recommend.js, commands.js) parse identically
// instead of each carrying a private copy (they all load after this file).
// ---------------------------------------------------------------------------

// First numeric token of a decode-speed string, as a float (the Python
// parse_speed convention: "120t/s code, 70t/s chat" -> 120).
function parseSpeed(tps) {
    if (!tps) return 0;
    var m = String(tps).match(/(\d+(?:\.\d+)?)/);
    return m ? parseFloat(m[1]) : 0;
}

// Context length in tokens from the free-text "stable" string
// ("65536" -> 65536, "~240k" -> 240000, "1.5m"/"million" -> 1500000).
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

// Explicit window binding: the contract the other scripts rely on.
window.parseSpeed = parseSpeed;
window.parseContext = parseContext;

// P4-2 sort coordination: shared between initSorting (column headers) and
// initFilters (the sort dropdown). Clicking a column header while a
// dropdown sort is active returns the table to the default tier grouping
// first, so the two mechanisms never fight.
var matrixSort = { axis: 'default', dir: 1, applyDefault: null };
function resetToDefaultSort() {
    matrixSort.axis = 'default';
    matrixSort.dir = 1;
    if (matrixSort.applyDefault) matrixSort.applyDefault();
}

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
        toggle.addEventListener('click', () => {
            const open = links.classList.toggle('open');
            // ARIA state so screen readers know the menu is expanded.
            toggle.setAttribute('aria-expanded', String(open));
        });
        // Escape closes the mobile menu and returns focus to the toggle.
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && links.classList.contains('open')) {
                links.classList.remove('open');
                toggle.setAttribute('aria-expanded', 'false');
                toggle.focus();
            }
        });
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
    // :hover / :focus-within rules also open it on desktop. The toggle's
    // aria-expanded is kept in sync so the disclosure state is announced.
    document.querySelectorAll('.nav-dropdown').forEach(dd => {
        const dt = dd.querySelector('.nav-dropdown-toggle');
        if (!dt) return;
        const setOpen = (open) => {
            dd.classList.toggle('open', open);
            dt.setAttribute('aria-expanded', String(open));
        };
        dt.addEventListener('click', (e) => {
            if (window.innerWidth <= 768) return; // let the link navigate on mobile
            e.preventDefault();
            setOpen(!dd.classList.contains('open'));
        });
        document.addEventListener('click', (e) => {
            if (!dd.contains(e.target)) setOpen(false);
        });
        // Escape closes the menu and returns focus to the toggle.
        dd.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && dd.classList.contains('open')) {
                e.stopPropagation();
                setOpen(false);
                dt.focus();
            }
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
        // Sortable headers carry a <button> (keyboard focusable; Enter/Space
        // natively activate it), so the click below also covers keyboard.
        if (th.hasAttribute('data-nosort')) return;
        th.addEventListener('click', () => {
            // If a dropdown sort (P4-2) is active, return to the default
            // tier-grouped order before applying the column sort.
            if (matrixSort.axis !== 'default') resetToDefaultSort();
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
        const btn = th.querySelector('.th-btn');
        if (btn) btn.classList.remove('sort-asc', 'sort-desc');
        // aria-sort is the ARIA state for a sortable column (WCAG 1.3.1);
        // the visual arrow class rides on the button (its ::after).
        if (sortState[i]) {
            const cls = sortState[i] === 1 ? 'sort-asc' : 'sort-desc';
            if (btn) btn.classList.add(cls);
            th.classList.add(cls);
            th.setAttribute('aria-sort', sortState[i] === 1 ? 'ascending' : 'descending');
        } else {
            th.setAttribute('aria-sort', 'none');
        }
    });
}

// ---------------------------------------------------------------------------
// Filters (P2-4, extended by P4-2) — URL-synced, shareable, multi-select.
//
// Matrix: filters the table rows (tier-group headers hide when empty),
// sorts them (dropdown: VRAM / size / speed / date, or a column header),
// shows active filters as removable chips, and announces a live
// "Showing N of M submissions" count.
// Community: filters each contributor's setup list; cards with no visible
// setups hide (single-select axes only — the P4-2 controls degrade away
// when absent).
//
// Query-string contract (fixed param order, stable and diff-friendly):
//   ?tier=&vendor=&backend=&use_case=&mode=&q=&sort=&dir=
//   * single-value axes: tier / vendor / mode / q
//   * multi-value axes: backend / use_case (repeated params; OR within
//     the axis, AND across axes)
//   * sort: default / vram / size / speed / date; dir: desc (asc is
//     omitted — the default)
// Discrete changes (selects, chips, sort, reset) push a history entry;
// continuous typing (search) replaces it, so the back button isn't
// flooded with per-keystroke states. Loading a URL with these params
// restores the exact view.
// ---------------------------------------------------------------------------
function initFilters() {
    const search = document.getElementById('filter-search');
    const singles = Array.from(document.querySelectorAll('.filter-select[data-filter]'));
    const multiselects = Array.from(document.querySelectorAll('.multiselect[data-filter]'));
    const sortSel = document.getElementById('filter-sort');
    const dirBtn = document.getElementById('filter-dir');
    const chipsEl = document.getElementById('filter-chips');
    const countEl = document.getElementById('filter-count');
    const resetBtn = document.getElementById('filter-reset');
    const shareBtn = document.getElementById('filter-share');
    const table = document.getElementById('data-table');
    const cards = Array.from(document.querySelectorAll('.contributor-card'));
    const emptyEl = document.getElementById('filter-empty');
    if (!search || (!table && !cards.length)) return;

    // data-filter value -> dataset property name ("use-case" -> "useCase").
    const dsKey = (f) => f.replace(/-([a-z])/g, (_, c) => c.toUpperCase());
    // data-filter value -> URL param key ("use-case" -> "use_case").
    const urlKey = (el) => el.dataset.filter.replace(/-/g, '_');
    // Human labels for chips.
    const AXIS_LABELS = {
        tier: 'VRAM tier', vendor: 'Vendor', backend: 'Backend',
        use_case: 'Use case', mode: 'Engine mode',
    };
    // Fixed param order, so shared URLs are stable and diff-friendly.
    const PARAM_ORDER = ['tier', 'vendor', 'backend', 'use_case', 'mode', 'q', 'sort', 'dir'];

    function esc(v) {
        const d = document.createElement('span');
        d.textContent = (v == null) ? '' : String(v);
        return d.innerHTML;
    }

    // --- Multi-select dropdowns (P4-2) ------------------------------------
    multiselects.forEach(ms => {
        const toggle = ms.querySelector('.multiselect-toggle');
        const menu = ms.querySelector('.multiselect-menu');
        const label = ms.querySelector('.multiselect-label');
        if (label) label.dataset.placeholder = label.textContent;
        if (toggle && menu) {
            toggle.addEventListener('click', (e) => {
                e.stopPropagation();
                const wasOpen = !menu.hidden;
                closeAllMenus();
                if (!wasOpen) {
                    menu.hidden = false;
                    toggle.setAttribute('aria-expanded', 'true');
                }
            });
            // Keep clicks inside the menu from closing it (document handler).
            menu.addEventListener('click', (e) => e.stopPropagation());
        }
        ms.querySelectorAll('input[type="checkbox"]').forEach(cb =>
            cb.addEventListener('change', () => {
                updateMsLabel(ms);
                apply(true);
            }));
    });

    function closeAllMenus() {
        multiselects.forEach(ms => {
            const menu = ms.querySelector('.multiselect-menu');
            const toggle = ms.querySelector('.multiselect-toggle');
            if (menu) menu.hidden = true;
            if (toggle) toggle.setAttribute('aria-expanded', 'false');
        });
    }

    function updateMsLabel(ms) {
        const label = ms.querySelector('.multiselect-label');
        const toggle = ms.querySelector('.multiselect-toggle');
        if (!label) return;
        const checked = Array.from(ms.querySelectorAll('input[type="checkbox"]:checked'))
            .map(cb => cb.value);
        label.textContent = !checked.length
            ? label.dataset.placeholder
            : (checked.length === 1 ? checked[0]
                                    : checked[0] + ' +' + (checked.length - 1));
        if (toggle) toggle.classList.toggle('active', checked.length > 0);
    }

    // Close open menus on outside click; Escape returns focus to the toggle.
    document.addEventListener('click', closeAllMenus);
    document.addEventListener('keydown', (e) => {
        if (e.key !== 'Escape') return;
        multiselects.forEach(ms => {
            const menu = ms.querySelector('.multiselect-menu');
            const toggle = ms.querySelector('.multiselect-toggle');
            if (menu && !menu.hidden && menu.contains(document.activeElement)) {
                closeAllMenus();
                if (toggle) toggle.focus();
            }
        });
    });

    // --- State -------------------------------------------------------------
    function readState() {
        const state = {
            q: search.value,
            sort: sortSel ? sortSel.value : 'default',
            dir: dirBtn && dirBtn.getAttribute('aria-pressed') === 'true' ? -1 : 1,
        };
        singles.forEach(s => { state[urlKey(s)] = s.value; });
        multiselects.forEach(ms => {
            state[urlKey(ms)] = Array.from(
                ms.querySelectorAll('input[type="checkbox"]:checked')
            ).map(cb => cb.value);
        });
        return state;
    }

    function writeState(state) {
        if (state.q !== undefined) search.value = state.q;
        singles.forEach(s => {
            const v = state[urlKey(s)];
            if (v !== undefined) s.value = v; // unmatched values keep ''
        });
        multiselects.forEach(ms => {
            const vals = state[urlKey(ms)] || [];
            ms.querySelectorAll('input[type="checkbox"]').forEach(cb => {
                cb.checked = vals.includes(cb.value);
            });
            updateMsLabel(ms);
        });
        if (sortSel) {
            sortSel.value = state.sort || 'default';
            matrixSort.axis = sortSel.value;
        }
        if (dirBtn) {
            matrixSort.dir = state.dir === -1 ? -1 : 1;
            updateDirBtn();
        }
    }

    function updateDirBtn() {
        if (!dirBtn) return;
        dirBtn.textContent = matrixSort.dir === 1 ? '↑' : '↓';
        dirBtn.setAttribute('aria-pressed', String(matrixSort.dir === -1));
    }

    function syncUrl(state, push) {
        const params = new URLSearchParams();
        PARAM_ORDER.forEach(k => {
            const v = state[k];
            if (v === undefined || v === null) return;
            if (Array.isArray(v)) {
                v.forEach(item => { if (item) params.append(k, item); });
            } else if (k === 'dir') {
                if (v === -1) params.set(k, 'desc'); // asc is the default
            } else if (k === 'sort') {
                if (v && v !== 'default') params.set(k, v);
            } else if (v) {
                params.set(k, v);
            }
        });
        const qs = params.toString();
        const url = window.location.pathname + (qs ? '?' + qs : '') + window.location.hash;
        safeHistory(() => (push ? history.pushState : history.replaceState)({ filters: state }, '', url));
    }

    function stateFromUrl() {
        const p = new URLSearchParams(window.location.search);
        const st = {
            q: p.get('q') || '',
            sort: p.get('sort') || 'default',
            dir: p.get('dir') === 'desc' ? -1 : 1,
        };
        singles.forEach(s => {
            const v = p.get(urlKey(s));
            if (v) st[urlKey(s)] = v;
        });
        multiselects.forEach(ms => {
            st[urlKey(ms)] = p.getAll(urlKey(ms)).filter(v => v);
        });
        return st;
    }

    // --- Matching: AND across axes, OR within a multi-select axis ----------
    function matches(state, el) {
        const q = (state.q || '').toLowerCase().trim();
        if (q) {
            // data-search (gen-time blob of every field incl. notes) is the
            // primary haystack; fall back to visible text where absent.
            const blob = el.dataset.search || el.textContent.toLowerCase();
            if (!blob.includes(q)) return false;
        }
        for (const s of singles) {
            const val = s.value;
            if (val && el.dataset[dsKey(s.dataset.filter)] !== val) return false;
        }
        for (const ms of multiselects) {
            const vals = state[urlKey(ms)] || [];
            if (!vals.length) continue;
            const dv = el.dataset[dsKey(ms.dataset.filter)] || '';
            if (!vals.includes(dv)) return false;
        }
        return true;
    }

    // --- Sorting (P4-2 dropdown; column headers stay within-group) --------
    const tbody = table ? table.querySelector('tbody') : null;
    const originalSeq = tbody ? Array.from(tbody.children) : [];
    const GLOBAL_AXES = { size: 1, speed: 1, date: 1 };

    function clearColumnSort() {
        if (!table) return;
        table.querySelectorAll('th').forEach(th => {
            th.classList.remove('sort-asc', 'sort-desc');
            th.setAttribute('aria-sort', 'none');
            const btn = th.querySelector('.th-btn');
            if (btn) btn.classList.remove('sort-asc', 'sort-desc');
        });
    }

    function applySort() {
        if (!tbody) return;
        const axis = matrixSort.axis;
        const dir = matrixSort.dir;

        if (axis === 'default') {
            originalSeq.forEach(el => tbody.appendChild(el));
            tbody.querySelectorAll('.tier-header').forEach(h => h.style.display = '');
            clearColumnSort();
            return;
        }

        // Group the (original) sequence into tier blocks.
        const groups = [];
        let cur = { header: null, rows: [] };
        originalSeq.forEach(el => {
            if (el.classList.contains('tier-header')) {
                if (cur.header || cur.rows.length) groups.push(cur);
                cur = { header: el, rows: [] };
            } else {
                cur.rows.push(el);
            }
        });
        if (cur.header || cur.rows.length) groups.push(cur);

        const dsName = { vram: 'sortVram', size: 'sortSize', speed: 'sortSpeed', date: 'sortDate' }[axis];
        const numeric = axis !== 'date';
        const valueOf = (el) => {
            const raw = el.dataset[dsName] || '';
            if (numeric) {
                const v = parseFloat(raw);
                // Unknown values sort last (ascending) / first (descending).
                return isNaN(v) ? (dir === 1 ? Infinity : -Infinity) : v;
            }
            return raw === '' ? (dir === 1 ? '99999999' : '00000000') : raw;
        };
        const cmp = (a, b) => {
            const av = valueOf(a), bv = valueOf(b);
            return (av < bv ? -1 : av > bv ? 1 : 0) * dir;
        };

        tbody.innerHTML = '';
        if (GLOBAL_AXES[axis]) {
            // Global sort: tier headers are hidden (grouping is meaningless
            // when rows interleave across tiers).
            const all = groups.flatMap(g => g.rows);
            all.sort(cmp);
            all.forEach(r => tbody.appendChild(r));
            groups.forEach(g => { if (g.header) g.header.style.display = 'none'; });
        } else {
            // VRAM sort keeps the tier grouping (within-group order only).
            groups.forEach(g => {
                if (g.header) tbody.appendChild(g.header);
                g.rows.sort(cmp);
                g.rows.forEach(r => tbody.appendChild(r));
            });
        }
        clearColumnSort();
    }

    matrixSort.applyDefault = () => {
        if (sortSel) sortSel.value = 'default';
        if (dirBtn) updateDirBtn();
        apply(true);
    };

    // --- Active-filter chips (P4-2) ----------------------------------------
    function renderChips(state) {
        if (!chipsEl) return;
        chipsEl.innerHTML = '';
        const seen = new Set(); // guard against duplicate (axis, value) pairs
        const mk = (axis, value, label) => {
            const key = axis + '\u0000' + value;
            if (seen.has(key)) return;
            seen.add(key);
            const b = document.createElement('button');
            b.type = 'button';
            b.className = 'filter-chip';
            b.dataset.axis = axis;
            b.dataset.value = value;
            b.setAttribute('aria-label', 'Remove filter: ' + label);
            b.innerHTML = '<span>' + esc(label) + '</span>' +
                '<span class="chip-x" aria-hidden="true">✕</span>';
            chipsEl.appendChild(b);
        };
        if (state.q && state.q.trim()) {
            mk('q', state.q.trim(), 'Search: “' + state.q.trim() + '”');
        }
        singles.forEach(s => {
            const v = state[urlKey(s)];
            if (v) mk(urlKey(s), v, (AXIS_LABELS[urlKey(s)] || urlKey(s)) + ': ' + v);
        });
        multiselects.forEach(ms => {
            (state[urlKey(ms)] || []).forEach(v =>
                mk(urlKey(ms), v, (AXIS_LABELS[urlKey(ms)] || urlKey(ms)) + ': ' + v));
        });
    }

    if (chipsEl) {
        chipsEl.addEventListener('click', (e) => {
            const chip = e.target.closest ? e.target.closest('.filter-chip') : null;
            if (!chip) return;
            const axis = chip.dataset.axis;
            if (axis === 'q') {
                search.value = '';
            } else {
                const single = singles.find(s => urlKey(s) === axis);
                if (single) {
                    single.value = '';
                } else {
                    const ms = multiselects.find(m => urlKey(m) === axis);
                    if (ms) {
                        ms.querySelectorAll('input[type="checkbox"]').forEach(cb => {
                            if (cb.value === chip.dataset.value) cb.checked = false;
                        });
                        updateMsLabel(ms);
                    }
                }
            }
            apply(true);
        });
    }

    // --- Result count (P4-2) ----------------------------------------------
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

    function totalCount() {
        if (table) {
            let n = 0;
            table.querySelectorAll('tbody tr').forEach(row => {
                if (!row.classList.contains('tier-header')) n++;
            });
            return n;
        }
        let n = 0;
        cards.forEach(card => {
            n += card.querySelectorAll('.setup-list li').length;
        });
        return n;
    }

    function updateCount() {
        if (!countEl) return;
        countEl.textContent = 'Showing ' + visibleCount() + ' of ' + totalCount() + ' submissions';
    }

    // --- Apply: sort -> filter -> chips/count/empty-state -> URL ----------
    function apply(push) {
        const state = readState();

        if (table) {
            applySort();
            const global = GLOBAL_AXES[matrixSort.axis];
            table.querySelectorAll('tbody tr').forEach(row => {
                if (row.classList.contains('tier-header')) {
                    row.style.display = global ? 'none' : '';
                    return;
                }
                const show = matches(state, row);
                if (show && row.style.display === 'none') {
                    // Re-entering row: fade it in (killed by the
                    // prefers-reduced-motion block for reduced-motion users).
                    row.style.display = '';
                    row.classList.add('row-enter');
                    row.addEventListener('animationend',
                        () => row.classList.remove('row-enter'), { once: true });
                } else if (!show && row.style.display !== 'none') {
                    row.style.display = 'none';
                }
            });
            // Hide tier headers whose group is fully filtered out
            // (global sorts already hide every header).
            if (!global) {
                table.querySelectorAll('.tier-header').forEach(header => {
                    let next = header.nextElementSibling;
                    let hasVisible = false;
                    while (next && !next.classList.contains('tier-header')) {
                        if (next.style.display !== 'none') hasVisible = true;
                        next = next.nextElementSibling;
                    }
                    header.style.display = hasVisible ? '' : 'none';
                });
            }
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

        renderChips(state);
        updateCount();

        if (emptyEl) {
            const active = (state.q && state.q.trim())
                || singles.some(s => s.value)
                || multiselects.some(ms =>
                    ms.querySelectorAll('input[type="checkbox"]:checked').length > 0);
            emptyEl.hidden = !(active && visibleCount() === 0);
        }

        syncUrl(state, push !== false);
    }

    search.addEventListener('input', () => apply(false));
    singles.forEach(s => s.addEventListener('change', () => apply(true)));
    if (sortSel) sortSel.addEventListener('change', () => {
        matrixSort.axis = sortSel.value;
        // The default (tier) order has no direction; reset it so the URL
        // and the toggle read cleanly.
        if (matrixSort.axis === 'default') matrixSort.dir = 1;
        updateDirBtn();
        apply(true);
    });
    if (dirBtn) dirBtn.addEventListener('click', () => {
        matrixSort.dir = matrixSort.dir === 1 ? -1 : 1;
        updateDirBtn();
        apply(true);
    });

    function reset() {
        search.value = '';
        singles.forEach(s => { s.value = ''; });
        multiselects.forEach(ms => {
            ms.querySelectorAll('input[type="checkbox"]').forEach(cb => { cb.checked = false; });
            updateMsLabel(ms);
        });
        matrixSort.axis = 'default';
        matrixSort.dir = 1;
        if (sortSel) sortSel.value = 'default';
        if (dirBtn) updateDirBtn();
        apply(true);
    }
    if (resetBtn) resetBtn.addEventListener('click', reset);
    const emptyClear = document.getElementById('filter-empty-clear');
    if (emptyClear) emptyClear.addEventListener('click', reset);

    // 🔗 Share: the URL is already in sync, so copy the address. The
    // button's nested .sr-only span is a polite live region, so the
    // "Copied" feedback is announced to screen readers (P2-6).
    if (shareBtn) {
        const shareLabel = shareBtn.querySelector('.share-label');
        const shareStatus = shareBtn.querySelector('.sr-only');
        const origText = shareLabel ? shareLabel.textContent : '🔗 Share';
        shareBtn.addEventListener('click', () => {
            const url = window.location.href;
            const done = (ok) => {
                if (shareLabel) shareLabel.textContent = ok ? '✓ Copied!' : 'Copy failed';
                if (shareStatus) shareStatus.textContent = ok ? 'Link copied to clipboard' : 'Copy failed';
                shareBtn.disabled = true;
                setTimeout(() => {
                    if (shareLabel) shareLabel.textContent = origText;
                    shareBtn.disabled = false;
                    if (shareStatus) shareStatus.textContent = '';
                }, 1500);
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
    writeState(stateFromUrl());
    apply(false);

    // Back/forward through filter states (pushState entries).
    window.addEventListener('popstate', () => {
        writeState(stateFromUrl());
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

    // B4/C4: a clear confidence line for the panel header. The same three
    // color states as the matrix dots (green = verified, blue =
    // community-reported, gray = unverified), spelled out in words so the
    // detail view is unambiguous.
    function confidenceLine(s) {
        const map = {
            'op-verified': ['detail-conf-verified', '✓ Verified by maintainer'],
            'community-verified': ['detail-conf-verified', '✓ Verified by community'],
            'community-reported': ['detail-conf-community', 'Community-reported'],
            'unverified': ['detail-conf-unverified', 'Unverified'],
        };
        const entry = map[s.confidence] || map['community-reported'];
        return '<div class="detail-confidence ' + entry[0] + '">' + entry[1] + '</div>';
    }

    // B4/C4: a lifecycle warning for stale entries. Superseded setups are
    // flagged as possibly outdated; discontinued ones as no longer
    // recommended. Current / watch entries render nothing.
    function lifecycleLine(s) {
        const life = s.lifecycle || 'current';
        if (life === 'superseded') {
            return '<div class="detail-lifecycle detail-lifecycle-superseded">⚠ This setup may be outdated — it has been superseded.</div>';
        }
        if (life === 'discontinued') {
            return '<div class="detail-lifecycle detail-lifecycle-discontinued">⛔ This setup is no longer recommended.</div>';
        }
        return '';
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
            ['OS / driver', s.os_driver],
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

        // B4/C4: the confidence line + any lifecycle warning, up front so
        // the reader knows how much to trust (and how current) this setup
        // before reading the details.
        html += confidenceLine(s);
        html += lifecycleLine(s);

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

        // Decorative leading icons are aria-hidden; the text labels carry
        // the meaning (P2-6 a11y audit).
        html += '<div class="detail-actions">';
        html += '<button class="btn btn-primary" type="button" data-launch-sub="' + esc(s.id) + '"><span class="icon" aria-hidden="true">🚀</span> Copy launch command</button>';
        html += '<button class="btn detail-add-compare" type="button" aria-pressed="false"><span class="icon" aria-hidden="true">➕</span> Add to comparison</button>';
        html += '<a class="btn" href="compare/?a=' + encodeURIComponent(s.id) + '">Compare this setup →</a>';
        html += '<a class="btn" href="' + esc(forumUrl(s)) + '" target="_blank" rel="noopener"><span class="icon" aria-hidden="true">💬</span> Read the forum post</a>';
        const mu = (s.model || {}).url;
        if (mu && /^https?:/.test(mu)) {
            html += '<a class="btn" href="' + esc(mu) + '" target="_blank" rel="noopener"><span class="icon" aria-hidden="true">⬇</span> Download the model</a>';
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
                addBtn.innerHTML = check.checked
                    ? '✓ In comparison — click to remove'
                    : '<span class="icon" aria-hidden="true">➕</span> Add to comparison';
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
