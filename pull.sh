#!/bin/bash
# ============================================================================
# The Local AI Stack — One-Click Data Pull
#
# Usage:
#   ./pull.sh              # Full cycle: pull -> diff -> parse -> validate ->
#                          # generate site -> commit -> push
#   ./pull.sh --dry-run    # Everything EXCEPT commit/push (inspect what would
#                          # change, then re-run for real)
#   ./pull.sh --no-push    # Commit locally but do NOT push to origin/main
#
# Works from a fresh clone: it creates the project virtualenv if missing and
# installs the content dependency (`markdown`) only when it is absent.
#
# The data pipeline (tools/pull.py, diff.py, parse.py, parse_thread.py) is
# stdlib-only; the site generator needs `markdown`, which `pip install -e .`
# provides. Every step runs through the venv interpreter.
# ============================================================================

set -euo pipefail

# --- Always operate from the repo root (where this script lives) -------------
cd "$(dirname "$0")"

# --- Colors (degrade gracefully when there is no TTY / color is off) --------
if [ -t 1 ] && [ -z "${NO_COLOR:-}" ] && [ "${TERM:-}" != "dumb" ]; then
  BOLD=$'\033[1m';  RESET=$'\033[0m'
  GREEN=$'\033[32m'; RED=$'\033[31m'; YELLOW=$'\033[33m'; CYAN=$'\033[36m'
else
  BOLD=""; RESET=""; GREEN=""; RED=""; YELLOW=""; CYAN=""
fi

# --- Small output helpers ----------------------------------------------------
step() { echo; echo "${BOLD}${CYAN}━━━ $1 ━━━${RESET}"; }
ok()   { echo "${GREEN}✓${RESET} $1"; }
info() { echo "  $1"; }
warn() { echo "${YELLOW}⚠ ${1}${RESET}"; }
err()  { echo "${RED}✗ ${1}${RESET}" >&2; }

usage() {
  cat <<'EOF'
The Local AI Stack — one-click data pull

Usage:
  ./pull.sh              Run the full cycle and commit + push to origin/main
  ./pull.sh --dry-run    Run everything except the commit/push (inspect first)
  ./pull.sh --no-push    Commit locally, but skip `git push`
  ./pull.sh -h, --help   Show this help
EOF
}

# --- Argument parsing --------------------------------------------------------
DRY_RUN=0
NO_PUSH=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --no-push) NO_PUSH=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $arg" >&2; echo; usage; exit 1 ;;
  esac
done

# Track the current step so an unexpected failure reports useful context.
CURRENT_STEP="startup"
trap 'err "Pipeline failed during: ${CURRENT_STEP} (line ${LINENO})."; exit 1' ERR

echo "${BOLD}The Local AI Stack — one-click data pull${RESET}"
[ "$DRY_RUN" -eq 1 ] && warn "DRY RUN: will NOT commit or push."
[ "$NO_PUSH" -eq 1 ] && warn "NO PUSH: will commit locally but NOT push."

# ============================================================================
# STEP 1 — Environment: ensure a working venv + the `markdown` dependency
# ============================================================================
CURRENT_STEP="environment setup"
step "STEP 1: Environment"

# Pick a Python >= 3.14 to build the venv with (prefer the explicit version).
PY_BIN="$(command -v python3.14 || command -v python3 || true)"
if [ -z "$PY_BIN" ]; then
  die="No python3 interpreter found on PATH. Install Python 3.14+ and re-run."
  err "$die"; exit 1
fi

# Create the venv if it is missing (or broken: no usable python binary).
if [ ! -d .venv ] || [ ! -x .venv/bin/python ]; then
  if [ -d .venv ]; then
    warn "Existing .venv has no usable python binary — recreating it."
    rm -rf .venv
  fi
  info "Creating virtualenv with $PY_BIN ($("$PY_BIN" --version 2>&1)) ..."
  "$PY_BIN" -m venv .venv
  ok "Virtualenv created."
else
  ok "Virtualenv present (.venv)."
fi

PY=".venv/bin/python"

# The site generator needs `markdown`; the data pipeline is stdlib-only.
# `pip install -e .` is idempotent, so we only pay for it when the dep is missing.
if "$PY" -c "import markdown" >/dev/null 2>&1; then
  ok "Dependencies ready (markdown $("$PY" -c 'import markdown; print(markdown.__version__)')) — skipping install."
else
  info "Installing project + dependencies (pip install -e .) ..."
  "$PY" -m pip install --quiet -e .
  ok "Dependencies installed."
fi

# The commit/push step needs git; fail fast with a clear message.
if ! command -v git >/dev/null 2>&1; then
  err "git is not on PATH — required for the commit/push step."
  exit 1
fi
ok "Environment ready."

# ============================================================================
# STEP 2 — Pull: re-fetch every monitored forum thread
# ============================================================================
CURRENT_STEP="pull"
step "STEP 2: Pull (fetch forum threads)"
info "Fetching all monitored threads from forum.level1techs.com ..."
# pull.py reports per-thread fetch errors in its summary rather than crashing,
# so a forum 403 degrades to "no new data" instead of aborting the cycle.
"$PY" tools/pull.py

# ============================================================================
# STEP 3 — Diff: what changed since the last seen state?
# ============================================================================
CURRENT_STEP="diff"
step "STEP 3: Diff (what changed since last pull)"

# diff.py updates data/last_seen.json as a side effect; capture its output so we
# can both show it and decide whether there is anything new to process.
diff_output="$("$PY" tools/diff.py)"
echo "$diff_output"

# Determine change count + a number for the commit message.
N_SUBS=0
HAS_CHANGES=0
if echo "$diff_output" | grep -q "FIRST RUN"; then
  # No previous baseline: every post is new.
  HAS_CHANGES=1
  N_SUBS="$(echo "$diff_output" | grep -cE '^  # ' || true)"
  [ -z "$N_SUBS" ] && N_SUBS=0
  ok "First run — baseline established, ${N_SUBS} post(s) in the thread."
elif diff_line="$(echo "$diff_output" | grep -E 'DIFF: [0-9]+ new, [0-9]+ updated, [0-9]+ removed')"; then
  new_count="$(echo "$diff_line"  | sed -E 's/.*DIFF: ([0-9]+) new.*/\1/')"
  upd_count="$(echo  "$diff_line" | sed -E 's/.* ([0-9]+) updated.*/\1/')"
  N_SUBS=$(( new_count + upd_count ))
  [ "$N_SUBS" -gt 0 ] && HAS_CHANGES=1
else
  # Could not parse a summary line — assume there may be changes (safe default).
  HAS_CHANGES=1
  N_SUBS=0
  warn "Could not parse the diff summary; proceeding with the pipeline."
fi

if [ "$HAS_CHANGES" -eq 0 ]; then
  ok "No new data. Nothing to do."
  echo
  exit 0
fi
info "${N_SUBS} new/updated post(s) detected — continuing the pipeline."

# ============================================================================
# STEP 4 — Parse: main thread + secondary threads
# ============================================================================
CURRENT_STEP="parse"
step "STEP 4: Parse (submissions + secondary threads)"

parse_output="$("$PY" tools/parse.py)"
echo "$parse_output"
subs_line="$(echo "$parse_output" | grep -E 'Parsed [0-9]+ real submissions' | head -1 || true)"
[ -n "$subs_line" ] && ok "$subs_line"

info "Parsing secondary threads (benchmarks / hardware / category) ..."
"$PY" tools/parse_thread.py
ok "Parsing complete."

# ============================================================================
# STEP 5 — Validate: the data-quality gate
# ============================================================================
CURRENT_STEP="validate"
step "STEP 5: Validate (data-quality gate)"

# A hard validation failure must NOT commit/push; warnings are informational.
if "$PY" tools/validate.py; then
  ok "Data is valid (any warnings are informational)."
else
  err "Validation FAILED — the data does not pass a hard check."
  err "Not committing or pushing. Fix the failing checks above, then re-run."
  exit 1
fi

# ============================================================================
# STEP 6 — Generate the static site
# ============================================================================
CURRENT_STEP="site generation"
step "STEP 6: Generate site"

site_output="$("$PY" -m tools.site)"
echo "$site_output"
site_line="$(echo "$site_output" | grep -E 'Site generated:' | head -1 || true)"
[ -n "$site_line" ] && ok "$site_line"
ok "Site pages regenerated."

# ============================================================================
# STEP 7 — Commit + push (skipped/limited by --dry-run / --no-push)
# ============================================================================
CURRENT_STEP="commit + push"
step "STEP 7: Commit + Push"

git add -A
if git diff --staged --quiet; then
  ok "No file changes. Done."
  echo
  exit 0
fi

info "Files that will be committed:"
git diff --staged --name-only | sed 's/^/    /'

# --dry-run: stop here, after staging, so the user can inspect the changes.
if [ "$DRY_RUN" -eq 1 ]; then
  warn "DRY RUN — changes are staged but NOT committed or pushed."
  info "Inspect:  git diff --staged"
  info "Commit:   re-run ./pull.sh (without --dry-run)"
  echo
  exit 0
fi

commit_msg="data: pull $(date +%F) — ${N_SUBS} new/updated submissions"
git commit -m "$commit_msg"
ok "Committed: ${commit_msg}"

if [ "$NO_PUSH" -eq 1 ]; then
  warn "NO PUSH — committed locally but NOT pushed (per --no-push)."
  info "Push with: git push origin main"
else
  info "Pushing to origin/main ..."
  git push origin main
  ok "Pushed to origin/main."
fi

# ============================================================================
# STEP 8 — Done: summary
# ============================================================================
CURRENT_STEP="summary"
step "STEP 8: Done"

SITE_URL="https://madgoathaz.github.io/llm-matrix/"
echo "${BOLD}Summary${RESET}"
info "Pulled:    all monitored forum threads"
info "Changed:   ${N_SUBS} new/updated post(s) this run"
info "Validated: data passes all hard checks"
info "Site:      regenerated from the fresh data"
if [ "$DRY_RUN" -eq 1 ]; then
  info "Status:    DRY RUN (nothing committed/pushed)"
elif [ "$NO_PUSH" -eq 1 ]; then
  info "Status:    committed locally, not pushed"
else
  info "Status:    committed + pushed to origin/main"
fi
echo
ok "View the live site: ${CYAN}${SITE_URL}${RESET}"
