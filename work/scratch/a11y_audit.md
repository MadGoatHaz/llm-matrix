# P2-6 — Accessibility Audit (WCAG 2.1 AA)

**Date:** 2026-10-12
**Scope:** all 16 generated pages — `index`, `matrix`, `community`, `guides.html` (stub), `about`, `compare/`, `recommend/`, `guides/` index + 8 guide pages.
**Method:** static audit of the generated HTML + the stylesheet tokens (contrast computed with the WCAG 2.1 relative-luminance formula, `work/scratch/contrast_check.py`), reviewed against every WCAG 2.1 AA success criterion in the task list. Findings are enforced long-term by `tests/test_a11y.py` (22 tests) so regressions fail CI.
**Result:** every issue found was fixed at the source (stylesheet tokens, `tools/site` generators, `js/`, guide content). No generated HTML was hand-edited — the generator is the single writer.

---

## 1. Color contrast (WCAG 1.4.3)

The audit computed **46 foreground/background pairs** used in `css/style.css`. **15 failed** 4.5:1. All are fixed by re-tuning four design tokens (values verified ≥ 4.5:1 on the darkest surface each sits on):

| Token | Before (ratio on worst surface) | After (ratio) |
|---|---|---|
| `--text-muted` | `#64748b` (3.32:1 on `--surface-2`) | `#8494ab` (5.12:1) |
| `--accent` (links, tier headers, badges) | `#3b82f6` (4.29:1 on `--surface-2`) | `#5b9dff` (5.80:1) |
| `--accent-strong` (NEW — primary button fills) | white on `#3b82f6` = **3.68:1 FAIL** | white on `#2563eb` = 5.17:1 |
| `--purple` (badge) | `#8b5cf6` (3.47:1 on its 15% tint) | `#a78bfa` (5.01:1) |

Consequences of the re-tune (all re-verified):

- `--accent-glow` / `.badge-blue` tints regenerated from the new accent → badge-blue 4.98:1.
- `.btn-primary` and `.btn-large-primary` now use `--accent-strong` (white text 5.17:1); hover keeps `--accent-hover` (identical value, 5.17:1).
- Already-passing pairs re-checked and unchanged: `--text` 12.8–15.7:1, `--text-secondary` 6.16–7.53:1, `--success`/`--warning`/`--cyan` badges 5.37/6.23/5.59:1, tier headers (large-text 3:1 rule) 5.80:1.

**Verified by:** `tests/test_a11y.py::test_text_tokens_meet_45_to_1_on_every_surface`, `::test_accent_and_badge_tokens_meet_45_to_1`, `::test_white_on_primary_button_fill_meets_45_to_1` — the tokens are re-extracted from the CSS and the ratios recomputed in the test, so any future token edit that breaks contrast fails the suite.

## 2. Heading hierarchy (WCAG 1.3.1 / 2.4.6)

Found & fixed:

- **`matrix.html`** — "Reading the matrix" card used `<h3>` directly under the page `<h1>` (level skip). → now `<h2>`.
- **`community.html`** — "Want to be here?" card used `<h3>` under `<h1>`. → now `<h2>`.
- **`about.html`** — all five cards used `<h3>` under `<h1>`. → now `<h2>`.
- **`guides/backends/index.html`** — the embedded "Try the launch-command generator" picker used `<h3>` immediately after the guide `<h1>`, before the first `<h2>`. → promoted to `<h2>` in `content/guides/backends.md` (it is a top-level section); `.cmd-picker h3` CSS selector updated to `h2`.
- Every other page already had a clean h1 → h2 → h3 flow (guides index, recommend, compare, all 7 other guides).

**Verified by:** `test_a11y.py::test_every_page_has_one_h1_and_no_heading_skips` parses all 16 pages with `html.parser` and fails on any level jump > 1.

## 3. Keyboard accessibility (WCAG 2.1.1)

Found & fixed:

- **Sortable table headers were mouse-only** (click handler on `<th>`, no focus, no key handling) — the single worst keyboard gap on the site. Fix: each sortable `<th>` now contains a real `<button class="th-btn">` (natively focusable; Enter/Space activate it). The `<th>` carries the ARIA state: `aria-sort="none|ascending|descending"` is maintained by `js/main.js::sortTable()`, and the visual ↑/↓ arrow moved onto the button's `::after`. The non-interactive "Actions" header keeps `data-nosort` and stays plain.
- **Mobile nav toggle** now exposes `aria-expanded`/`aria-controls="nav-links"` (synced on click) and **Escape closes it**, returning focus to the toggle.
- **Guides dropdown** (a disclosure, not a menu) now exposes `aria-expanded`/`aria-controls="guides-menu"` on the toggle; `js/main.js` syncs the attribute on open/close and **Escape closes it**, returning focus to the toggle. The menu was already reachable via `:focus-within` + Tab.
- All other interactive elements were already keyboard-operable and re-verified: filter inputs/selects, Reset/Share/Compare/Edit buttons, matrix rows (`tabindex="0"` + Enter/Space opens the detail panel), detail-panel & command-dialog (focus trap, ESC closes, focus restored to the trigger), compare picker selects, recommend form selects, guide TOC/related links.

**Verified by:** `test_a11y.py::test_sortable_headers_are_real_buttons_with_aria_sort`, `::test_nav_toggle_and_dropdown_expose_expanded_state`, plus the pre-existing `test_detail.py` focus-trap contract tests.

## 4. ARIA labels on icons / buttons without text (WCAG 4.1.2)

Found & fixed:

- All icon-only buttons already had `aria-label` (nav toggle, ⓘ detail, 🚀 launch, ✕ closers, 🔗 Share) — **kept and re-verified**.
- **Decorative emoji** are now wrapped in `<span class="icon" aria-hidden="true">` so screen readers read the text label only and never announce "trophy"/"fire"/"rocket": nav logo 📊, Guides ▾, all homepage section/card icons (🏆 🔄 🔗 🔥 ⚡ 📝 ⚙️ 📊 🎯), matrix 🔍/ℹ️/🔗, community 🙌, all five about-page icons, compare ✎, recommend 🎯, detail-panel action buttons (🚀 ➕ 💬 ⬇), command-dialog header 🚀 / copy 📋, and the backends-guide picker 🚀. Applied in the generators (`utils.icon()`), in `js/` templates, and in `content/guides/backends.md`.
- `.guide-icon` divs (guides index + homepage related cards) got `aria-hidden="true"` via a post-pass in `tools/site/markdown.py` (covers all current and future guide cards without touching content).
- Contributor avatar initials (decorative; the name sits beside) → `aria-hidden="true"`.

## 5. Alt text on images

**No `<img>` elements exist on the site** — every visual is text, emoji, or a CSS-only diagram (the P1 design decision). The only raster is `og-image.png`, referenced from `og:image` meta (no alt needed; not in-document). All CSS diagrams carry real text labels (`.diagram-label`, `.diagram-cell`), so they are inherently screen-reader readable. **No changes required.**

## 6. Touch targets ≥ 44×44px (WCAG 2.5.x)

Measured and fixed (CSS `css/style.css`):

| Element | Before | After |
|---|---|---|
| `.nav-links a`, `.nav-dropdown-toggle` | ~40px | 45.4px (0.7rem pad) |
| `.nav-dropdown-menu li a` | ~30px | 45.4px (0.7rem pad, 0.9rem font) |
| `.nav-toggle` | ~38px | `min-width/min-height: 44px` + flex-centered |
| `.nav-logo` | ~28px | 44px (0.5rem/0.75rem pad) |
| `.filter-bar input/select` | 42.2px | 45.4px |
| `.btn` (Reset, Share, Compare, Edit, clear…) | 41px | 44.2px |
| `.launch-btn`, `.detail-btn` | 40px | 44px |
| `.cmd-close`, `.detail-close` | 40px | 44px |
| `.compare-check` (18px checkbox) | 18px | **45px hit area** via negative-margin padding on the wrapping label (visual layout unchanged) |
| table data rows (clickable) | 42.6px | 44.2px (td padding) |
| `.th-btn` sort headers | n/a (new) | `min-height: 44px` |
| `.rec-actions a` (View in Matrix / Download) | ~24px | 45.4px |
| `.launch-card-btn` (recommend cards) | 28px | 44px |
| `.compare-matrix-link` | ~13px | 43.8px (0.9rem font, 0.65rem pad) |
| `.guide .toc a`, `.guide-related a` | ~16–25px | 43.8–46px (block, 0.65rem pad) |
| `.cmd-picker-select` | 42.2px | 45.4px |

**Documented deviation:** `.footer a` (secondary content links) meets the WCAG 2.1 AA *minimum* 24px target (SC 2.5.8) at ~33px; the stricter 44px standard is applied to all primary/functional controls. Inline prose links (e.g. "See in the matrix →") are 24px+ text links, the standard for running text.

## 7. Form labels (WCAG 3.3.2 / 1.3.1)

- Recommend form: all four selects have visible `<label for=…>` — **kept**.
- Filter bars (matrix/community): selects + search carry `aria-label` (programmatic names; no visible labels by design) — **kept and re-verified**.
- Compare picker: four selects with `aria-label="Setup to compare N"` — **kept**.
- Backends-guide picker: `<label for="cmd-picker-select">Backend</label>` — **kept**.
- Compare checkbox per row: `aria-label="Compare <model>"` — **kept**.

## 8. Focus management (WCAG 2.4.3 / 2.4.7)

- **Skip link added on every page** (WCAG 2.4.1 Bypass Blocks): `<a class="skip-link" href="#main-content">Skip to content</a>` — visually hidden until focused, then a high-contrast bar at the top; `<main>` carries `id="main-content"`.
- **Global `:focus-visible` ring** (2px `--accent`, offset 2px) for every focusable element; components with their own ring (inputs, launch/detail/close buttons) keep theirs via higher specificity.
- Existing focus management re-verified: detail panel & command dialog move focus in on open, trap Tab/Shift+Tab, close on ESC, restore focus to the trigger.

## 9. Screen-reader announcements for dynamic content (WCAG 4.1.3)

- Recommend results: `role="status" aria-live="polite"` — **kept**.
- Compare takeaway: `role="status" aria-live="polite"` — **kept**.
- Filter-empty state: `role="status"` — **kept**.
- **Share button**: copy feedback ("✓ Copied!") was visual-only. Now the button wraps its label in `.share-label` and carries a nested `<span class="sr-only" role="status" aria-live="polite">` that `js/main.js` fills with "Link copied to clipboard" / "Copy failed".
- **Command-dialog copy button**: created with `aria-live="polite"` in `js/commands.js` so "✓ Copied" is announced.
- **Tables**: matrix table now has an sr-only `<caption>` describing structure/interaction; compare table renders an sr-only caption; all `<th>` carry `scope` (matrix columns + every guide/compare table via the `markdown.py` post-pass) so screen readers associate cells with headers.

## 10. Motion (WCAG 2.3.3)

- `prefers-reduced-motion: reduce` block **expanded from 3 rules to site-wide**: all transitions/animations are forced to 0.01ms (panel slide, card hover-lift, nav/dropdown transitions, smooth scrolling → instant). The detail panel/scrim keep their explicit `transition: none` and `html { scroll-behavior: auto }`.

## 11. Language & landmarks (WCAG 3.1.1 / 1.3.1)

- `<html lang="en">` on every page — **kept**.
- Landmarks on every page: `<nav aria-label="Main navigation">`, `<main id="main-content">`, `<footer>` — **kept; nav gained the aria-label**.
- Sections use `aria-labelledby` where they have headings (teaser, recommend tool, compare picker).

## 12. Mobile breakpoints (360 / 768 / 1024px)

Static verification (no browser available in this environment; reasoned from the CSS):

- **No page-level horizontal scroll:** the only fixed-width element is `.compare-table { min-width: 640px }`, which sits inside `.table-wrapper { overflow-x: auto }` — the *table* scrolls, the page doesn't. All other layouts are fluid (`max-width` + `width: 100%` + flex/grid wrap).
- **360px:** the 768px breakpoint switches the filter bar to a single column (full-width inputs at 44px+), stats to a column, card grids to 1 column, the detail panel to full-screen, diagrams wrap (`diagram--flow` is `flex-wrap: wrap`; KV bars shrink to `min-width: 4px`), and the nav collapses to the ☰ toggle.
- **768px / 1024px:** 2-column card grids via `repeat(auto-fill, minmax(300px, 1fr))`; nav stays inline.
- **Diagrams stack cleanly:** all three diagram systems (`--kv`, `--stack`, `--flow`) use flex column/wrap with no absolute positioning.

## 13. Lighthouse projection

Lighthouse itself requires a real browser (none available in this environment — see `perf_audit.md` for the same note on the perf score). Against the Lighthouse a11y audit rules, the post-fix state is:

| Lighthouse a11y audit | Status |
|---|---|
| `aria-allowed-attr`, `aria-required-attr`, `aria-roles`, `aria-valid-attr-value` | pass (only `aria-label/expanded/controls/sort/hidden/pressed/live/modal/haspopup/labelledby` used, all valid on their elements) |
| `button-name`, `link-name` | pass (every icon button has `aria-label`; decorative glyphs `aria-hidden`) |
| `color-contrast` | pass (all 46 pairs re-verified ≥ 4.5:1 / 3:1) |
| `html-has-lang` | pass |
| `image-alt` | pass (no `<img>` in-document) |
| `label` | pass |
| `landmark-one-main`, `page-title`, `heading-order`, `tabindex` | pass |
| `table-dup-name`, `table-headers` (scope) | pass |
| `meta-viewport` | pass (`user-scalable` not restricted) |

Projected score: **100** (every audited rule passes; the suite enforces the subset that maps to these rules).

## Files touched

- `css/style.css` — tokens, skip link, sr-only, focus-visible, touch targets, th buttons, reduced-motion, subheading
- `tools/site/template.py` — skip link, `#main-content`, nav aria-label, theme-color, `defer`, dropdown disclosure
- `tools/site/pages/{homepage,matrix,community,about,compare,recommend}.py`, `tools/site/guides.py` (via markdown), `tools/site/markdown.py`, `tools/site/utils.py` — headings, scopes, icons, live regions, compact islands
- `js/main.js`, `js/compare.js`, `js/commands.js` — ARIA state, live regions, scope, icon spans
- `content/guides/backends.md` — picker heading h3 → h2
- `tests/test_a11y.py` (new, 20 tests) — locks all of the above in
