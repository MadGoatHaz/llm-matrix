# DEV LOG — Local LLM Matrix

@@@ ACTIVE_WORKERS @@@

@@@ HISTORY @@@
- [DONE] ID: root-output | AGENT: general (Implementation Agent) | BRANCH: main | FILES: tools/generate.py, dashboard/.gitkeep
  Moved dashboard output from dashboard/ to repo root for GitHub Pages. generate.py: (1) DASHBOARD_DIR = WORKSPACE
  (was WORKSPACE / "dashboard"), so index.html + data.json now write to the repo root, overwriting the existing root
  landing index.html when the pipeline runs; (2) docstring "Writes" section updated to root paths (index.html, data.json)
  and dropped the stale forum/bump_changelog.md line; (3) print statements auto-resolve to root via DASHBOARD_DIR.
  Removed dashboard/.gitkeep and the now-empty dashboard/ dir. py_compile clean; synthetic smoke test (DASHBOARD_DIR
  redirected to /tmp/kilo/matrix_root_out) 6/6 PASS — index.html + data.json at root, no nested dashboard/ subdir.
  Note: data/submissions.json not present, so a real run exits early (no render); root index.html (landing card)
  is overwritten only once pull.py->parse.py produces submissions.json. Committed to main + pushed. No lease contention.
- [DONE] ID: publish-pages | AGENT: general (Implementation Agent) | BRANCH: main | FILES: (deploy) + index.html
  Made repo MadGoatHaz/llm-matrix PUBLIC (was PRIVATE) via `gh repo edit --visibility public
  --accept-visibility-change-consequences`. GitHub Pages: the REST API `POST /pages` REJECTS
  source[path]=/dashboard (422: only `/` or `/docs` allowed), so Pages was enabled from source `/` on
  main -> html_url https://madgoathaz.github.io/llm-matrix/ (public:true, https_enforced:true, build_type:legacy).
  Added a minimal root index.html landing page (dark L1Techs-brand card: title, tagline, status pill,
  "Open the Dashboard" -> dashboard/ + forum-thread button, not-official-L1Techs note) so the root URL is not
  a dead 404. To serve ONLY the dashboard/ subfolder at the root, the source path must be set to /dashboard in
  the GitHub web UI (Settings -> Pages -> "Deploy from a branch" -> main + /dashboard); the API cannot do this.
  CAVEAT: dashboard/ still contains only .gitkeep (no index.html) — the pull.py->parse.py->generate.py pipeline
  has not run, so the dashboard has no rendered content yet. Secret scan clean (only ${{secrets.GITHUB_TOKEN}}
  placeholder in PLAN template; data/ has only .gitkeep, no PII). Committed branding changes (tools/generate.py,
  forum/post1_matrix.md, forum/post2_submissions.md) + index.html + this log; pushed to origin/main. No lease contention.
- [DONE] ID: dashboard-community-branding | AGENT: general (Implementation Agent) | FILES: tools/generate.py, forum/post1_matrix.md, forum/post2_submissions.md
  Rebranded dashboard + Post #3 + forum posts to represent the L1Techs community. generate.py: (1) header now has
  .branding div (title + .tagline + .forum-credit linking ML,LLMs&AI community at Level1Techs /t/256443), stats preserved;
  (2) new .how-it-works <details> collapsible between header and filters (read-only view, how to contribute via Post #2
  template, community-reported disclaimer, respect-contributors note); (3) table header "User"→"Contributor" +
  td:first-child bolder; (4) footer rewritten: .footer-main attribution, .footer-cta "Join the Discussion / Submit Your
  Setup" .btn-forum button, .footer-meta (date + forum link + not-official-L1Techs line); all CSS added f-string-safe
  (doubled braces). Post #3: header now "A community index of all submissions from the **Local LLM Matrix** thread"
  with dashboard quote-link (YOUR-USERNAME placeholder kept) + "full discussion lives here on the forum" line; footer now
  "auto-generated from thread data... see the [thread](/t/256443) for full context". post1_matrix.md: +dashboard quote-line
  after title (MadGoatHaz.github.io/llm-matrix-dashboard), +self-link bullet at top of Related Threads ("This thread (the
  data source): /t/256443"). post2_submissions.md: +dashboard quote-line after title. VERIFIED: py_compile clean; synthetic
  render smoke test 27/27 checks pass (output redirected to /tmp/kilo/matrix_out, real dashboard/ untouched — no
  submissions.json yet, run pull.py→parse.py first). No lease contention. Non-git dir, no branch/commit.
- [DONE] ID: tooling-infra-v1 | AGENT: general (Implementation Agent) | FILES: tools/*, data/*, dashboard/, forum/*, work/PLAN_dashboard.md, README.md
  Built the full Local LLM Matrix tooling workspace. (1) Created dirs: tools/, data/raw/,
  dashboard/, templates/, forum/, work/scratch/. (2) Moved 5 existing files:
  updated_forum_post.md→forum/post1_matrix.md, updated_post2_submissions.md→forum/post2_submissions.md,
  bump_post_v2.md→forum/bump_v2.md, bump_post_v2.1.md→forum/bump_v2.1.md, PLAN_dashboard.md→work/PLAN_dashboard.md.
  (3) Wrote tools/schema.json (v2.1: 6 tiers, 12 backends, 22 quants, os_drivers, use_cases, engine_modes,
  confidence, lifecycle) + tools/tags.json (3 highlighted submissions, 3 forum_feedback actions).
  (4) Wrote 4 Python tools: pull.py (Discourse fetch/import), diff.py (new/updated/removed vs last_seen),
  parse.py (canonical submissions.json + vendor inference + tier normalization + tag overrides),
  generate.py (dashboard/index.html + data.json + forum/post3_viewport.md). All 4 pass py_compile.
  (5) Wrote tools/README.md + top-level README.md. (6) Created .gitkeep in data/, data/raw/, dashboard/,
  templates/, work/scratch/. (7) chmod +x on all 4 scripts. PARSER NOT RUN: no data/raw/latest.json present
  (user must run pull.py first to fetch the thread, per exec notes). No git repo in dir, no branch/commit.
  No lease contention (ACTIVE_WORKERS was empty).
- [DONE] ID: bump-post-v2.1 | AGENT: general (Implementation Agent) | FILES: bump_post_v2.1.md
  Created 35-line Discourse bump post (v2.1): casual/community tone; opening + 5 visible highlight bullets
  (R9700 lookup, Strata hybrid, Radiance dual-R9700, NVFP4/MXFP4, DeepSeek 4.1 Flash); one <details> "Full
  v2.1 Changelog" (12-row table); Data Viewport engagement prompt; hybrid-flag closing. Matches v2.0 style.
  Non-git dir, no branch/commit. No lease contention.

- [DONE] ID: bump-post-v2 | AGENT: general (Implementation Agent) | FILES: bump_post_v2.md
  Created 38-line Discourse bump post (v2.0): casual/community tone; 4 visible highlight bullets; one
  <details> "Full v2.0 Changelog" (12-row table); re-read pitch; 3 CTA bullets; closing. Non-git dir, no
  branch/commit. No lease contention.
- [DONE] ID: unsloth-ecosystem-v1 | AGENT: general (Implementation Agent) | FILES: updated_forum_post.md, updated_post2_submissions.md
  Added Unsloth Desktop + Supporting Software & Ecosystem to both posts. POST 1 (1293→1524 lines):
  +QuickNav entry; +Hardware Vendor Notes para (Unsloth Desktop = primary all-in-one on CUDA/ROCm/Vulkan/
  Metal-MLX, Ollama/LM Studio kept as lighter alternatives); +Option D (Unsloth Desktop: GGUF/safetensors/
  FP8/MLX, llama.cpp core + vLLM backend) in Running Non-GGUF; +new top-level <details> "Supporting Software
  &amp; Ecosystem" (5 nested <details>: All-in-One Apps, Chat Frontends, Agentic Coding Harnesses,
  General-Purpose Agent Frameworks, Orchestration & Routing; 5 md-tables, 18 tool rows, closing stack note)
  placed after Non-GGUF and before Master Matrix. POST 2 (303→314 lines): +QuickNav entry (ref Post #1);
  Q3 "just want it to work" → Unsloth Desktop (Ollama/LM Studio as lighter alts); Q4 Apple + MLX via
  Unsloth Desktop; Backend table +Unsloth Desktop row (now 9 rows); Quick Decision chat → Unsloth Desktop
  (all-in-one) or Ollama (minimalist); +cross-ref note to Post #1 Supporting Software section before
  Golden Rule. All 10 replacements unique-match asserted; all 20+ HTML tag classes balanced; 33/33 content
  checks PASS (work/scratch/verify.log). No git repo in dir, no branch/commit. No lease contention.
- [DONE] ID: forum-post-v4 | AGENT: general (Implementation Agent) | FILES: updated_forum_post.md
  Rewrote to 1293 lines / 13 top-level <details> sections. ADDED: Quick GPU Lookup (6 tier separators +
  40 GPU rows), Use-Case Index (10 rows), Real-World Constraints (7 rows), Changelog (v1.0/v2.0, 2 rows).
  ENHANCED Master Matrix: +Status (confidence) first col & +Lifecycle (badge) last col on all 6 tiers,
  +per-tier italic tradeoff notes, +reading legend. PRESERVED all prior content (6 tier tables w/ Weight
  Precision, vendor notes 3 sub-details, non-GGUF guide, KV rule, community data 4 sub-details,
  architecture note, related threads). Verified: 25/25 details, 25/25 summary, 13/13 table, 118/118 tr,
  570/570 td, 93/93 th, 46 HF + 5 forum links, raw-& only in markdown prose. 12-entry Quick Nav updated.
  No git repo in dir, so no branch/commit performed. No lease contention.
- [DONE] ID: forum-post-v2 | AGENT: general (Implementation Agent) | FILES: updated_forum_post.md
  Created 270-line Discourse-ready post: 8 H2 sections, 6 collapsible tiers (Weight Precision column added),
  Community Verified Data, Tech Architecture Note, Related Threads. Verified table integrity (23 model rows)
  and balanced HTML/code fences. No lease contention (fresh dir).
- [DONE] ID: forum-post-v3 | AGENT: general (Implementation Agent) | FILES: updated_forum_post.md
  Rewrote post in Discourse raw-HTML format: 7 <details>/<summary> blocks (6 matrix tiers + Technical
  Architecture Note), 6 md-table divs, 23 model rows, 46 rel="noopener nofollow ugc" links, all td/th
  text-align:left, & escaped. Other sections (intro, KV rule, vendor notes, non-GGUF guide, community
  data, related threads) in standard markdown. Verified: balanced tags, 558 lines. No git repo in dir,
  so no branch/commit performed.
- [DONE] ID: forum-post2-submissions | AGENT: general (Implementation Agent) | FILES: updated_post2_submissions.md
  Created 140-line Discourse-ready Post #2 (community submissions/feedback): 4 <details>/<summary> sections
  (emoji-prefixed), 1 <hr> after intro, <ul> quick-nav, 3 <pre><code> blocks (submission template + 2 examples),
  <ol> 5-question intake list w/ nested <ul>, tier line updated to 6 tiers incl. new 16-24GB, & escaped as &amp;.
  Verified balanced tags (4/4 details, 4/4 summary, 3/3 pre, 8/8 code, 3/3 ul, 1/1 ol, 17/17 li). No git repo
  in dir, so no branch/commit performed. No lease contention (fresh file).
- [DONE] ID: forum-post2-submissions-v2 | AGENT: general (Implementation Agent) | FILES: updated_post2_submissions.md
  Rewrote Post #2 with 3 major additions: (1) "Start Here: New to Local LLMs?" decision-flow section
  (Q1-Q4 budget/use-case/comfort/vendor, styled HTML lists), (2) "Backend Selection Guide" section
  (8-row md-table: Ollama/LM Studio/llama.cpp/llama-swap/vLLM/TensorRT-LLM/MLX/Colibri with
  Quick Decision list + Golden Rule), (3) Quick Submit template added before Full Submit in
  Submission Templates section. Quick Nav updated to 6 items. All 4 original sections preserved
  verbatim. Verified: 303 lines, 6/6 details, 6/6 summary, 4/4 pre/code, 1 md-table div,
  6 th + 48 td all text-align:left, 1 hr, & escaped. No lease contention (active worker
  on updated_forum_post.md only). No git repo in dir, no branch/commit.
