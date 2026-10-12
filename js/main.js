// Navigation toggle (mobile)
document.addEventListener('DOMContentLoaded', () => {
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
        const toggle = dd.querySelector('.nav-dropdown-toggle');
        if (!toggle) return;
        toggle.addEventListener('click', (e) => {
            if (window.innerWidth <= 768) return; // let the link navigate on mobile
            e.preventDefault();
            dd.classList.toggle('open');
        });
        document.addEventListener('click', (e) => {
            if (!dd.contains(e.target)) dd.classList.remove('open');
        });
    });

    // Table sorting (for matrix page)
    initSorting();

    // Filters (for matrix page)
    initFilters();
});

function initSorting() {
    const table = document.querySelector('#data-table');
    if (!table) return;

    let sortState = {};
    table.querySelectorAll('th').forEach((th, colIdx) => {
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

function initFilters() {
    const search = document.getElementById('filter-search');
    const selects = document.querySelectorAll('.filter-select');
    const table = document.getElementById('data-table');
    if (!search || !table) return;

    function apply() {
        const q = search.value.toLowerCase();
        const filters = {};
        selects.forEach(s => filters[s.dataset.filter] = s.value);

        table.querySelectorAll('tbody tr').forEach(row => {
            if (row.classList.contains('tier-header')) {
                row.style.display = '';
                return;
            }
            const text = row.textContent.toLowerCase();
            let show = true;
            if (q && !text.includes(q)) show = false;
            for (const [key, val] of Object.entries(filters)) {
                if (val && row.dataset[key] !== val) show = false;
            }
            row.style.display = show ? '' : 'none';
        });

        // Hide empty tier headers
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

    search.addEventListener('input', apply);
    selects.forEach(s => s.addEventListener('change', apply));

    const resetBtn = document.getElementById('filter-reset');
    if (resetBtn) resetBtn.addEventListener('click', () => {
        search.value = '';
        selects.forEach(s => s.value = '');
        apply();
    });
}
