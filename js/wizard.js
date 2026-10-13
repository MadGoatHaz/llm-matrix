// wizard.js — the "Start Here" 3-step wizard on the recommend page (C1).
//
// Turns a first-time visitor into a result in three taps, BEFORE the full
// form: (1) what you have → VRAM tier, (2) what you want to do → use-case
// filter, (3) what matters most → priority. It writes straight into the
// SAME form controls the recommend engine already reads
// (#rec-tier / #rec-usecase / #rec-priority) and triggers the engine's
// existing change handler — no second ranking path, no new data.
//
// Mapping is deliberately conservative (a tap never promises more VRAM than
// the card describes): gaming → t2, high-end → t3, multi-GPU/server → t5,
// Mac → t2 (unified memory). "Not sure" skips to manual entry; "Just
// exploring" applies no use-case filter.
//
// Returning users: "Skip to advanced options" jumps straight to the form;
// touching the form while the wizard is up dismisses it. After the wizard
// completes (or is skipped), "Refine your search" opens the advanced
// options and "Start over" resets everything.
//
// A11y: the cards are real <button> elements (the visible title +
// description is the accessible name; the emoji icons are aria-hidden),
// each step's heading takes focus on entry (tabindex="-1"), and the results
// are announced by the recommend engine's existing aria-live region.

(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    var wizard = document.getElementById('wizard');
    if (!wizard) return; // not the recommend page

    var steps = [
      document.getElementById('wizard-step-1'),
      document.getElementById('wizard-step-2'),
      document.getElementById('wizard-step-3')
    ];
    if (!steps[0] || !steps[1] || !steps[2]) return;

    var actions = document.getElementById('wizard-actions');
    var skipLink = document.getElementById('wizard-skip');
    var refineLink = document.getElementById('wizard-refine');
    var resetBtn = document.getElementById('wizard-reset');
    var form = document.getElementById('rec-form');
    var tierSel = document.getElementById('rec-tier');
    var useSel = document.getElementById('rec-usecase');
    var prioSel = document.getElementById('rec-priority');
    var advanced = document.getElementById('rec-advanced');
    var results = document.getElementById('rec-results');

    var state = { tier: '', useCase: '', priority: '' };
    var active = true; // the wizard is on screen

    function smooth() {
      return !window.matchMedia ||
        !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }

    function scrollTo(el) {
      if (el) el.scrollIntoView({ behavior: smooth() ? 'smooth' : 'auto',
                                  block: 'start' });
    }

    // Reveal step n (1-based) and move focus to its heading.
    function showStep(n) {
      for (var i = 0; i < steps.length; i++) steps[i].hidden = (i !== n - 1);
      var h = steps[n - 1].querySelector('h2');
      if (h) h.focus();
    }

    // Write the wizard's choices into the form controls and fire the
    // recommend engine's existing change handler. The {wizard: true}
    // detail marks script-dispatched events so a real user change on the
    // form can be told apart (it dismisses the wizard, below).
    function fireChange(el) {
      if (!el) return;
      el.dispatchEvent(new CustomEvent('change', { detail: { wizard: true } }));
    }

    function applySelection() {
      if (state.tier) tierSel.value = state.tier;
      if (state.useCase) useSel.value = state.useCase;
      if (state.priority) prioSel.value = state.priority;
      fireChange(tierSel);
      fireChange(useSel);
      fireChange(prioSel);
    }

    // Hide the wizard, reveal the refine/start-over row, and scroll the
    // user to where they land next.
    function dismiss(target) {
      active = false;
      wizard.hidden = true;
      if (actions) actions.hidden = false;
      scrollTo(target);
    }

    steps.forEach(function (step, idx) {
      var cards = step.querySelectorAll('button.wizard-card');
      for (var c = 0; c < cards.length; c++) {
        (function (card) {
          card.addEventListener('click', function () {
            var value = card.getAttribute('data-value') || '';
            if (idx === 0) {
              if (value === '') { // "Not sure" → manual entry
                dismiss(form);
                if (tierSel) tierSel.focus();
                return;
              }
              state.tier = value;
            } else if (idx === 1) {
              state.useCase = value; // '' = "Just exploring" → no filter
            } else {
              state.priority = value;
            }
            if (idx < 2) {
              showStep(idx + 2);
            } else {
              applySelection();
              dismiss(results);
              if (refineLink) refineLink.focus();
            }
          });
        })(cards[c]);
      }
      var back = step.querySelector('button.wizard-back');
      if (back) {
        back.addEventListener('click', function () {
          showStep(parseInt(back.getAttribute('data-back'), 10));
        });
      }
    });

    if (skipLink) {
      skipLink.addEventListener('click', function (e) {
        e.preventDefault();
        dismiss(advanced || form);
        if (tierSel) tierSel.focus();
      });
    }

    if (refineLink) {
      refineLink.addEventListener('click', function (e) {
        e.preventDefault();
        if (advanced) advanced.open = true;
        scrollTo(form);
        if (tierSel) tierSel.focus();
      });
    }

    if (resetBtn) {
      resetBtn.addEventListener('click', function () {
        state = { tier: '', useCase: '', priority: '' };
        if (tierSel) tierSel.value = '';
        if (useSel) useSel.value = '';
        if (prioSel) prioSel.value = 'balanced';
        fireChange(tierSel);
        fireChange(useSel);
        fireChange(prioSel);
        if (actions) actions.hidden = true;
        wizard.hidden = false;
        active = true;
        showStep(1);
      });
    }

    // A returning user drives the form directly (any non-wizard change) →
    // the wizard steps out of the way.
    [tierSel, useSel, prioSel].forEach(function (el) {
      if (!el) return;
      el.addEventListener('change', function (e) {
        if (active && !(e.detail && e.detail.wizard)) dismiss(el);
      });
    });
  });
})();
