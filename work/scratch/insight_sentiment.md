# Community Sentiment Analysis — "The Local LLM Matrix" Thread

- **Source:** https://forum.level1techs.com/t/256443
- **Captured:** 2026-10-12 ~15:40 UTC
- **Scope:** 29 posts total; 27 fully analyzed

## Key Findings

### Unanswered Questions
1. **FiftyTifty #14** — "How do we use that 20GB AutoRound model?" — Never directly replied to
2. **Onno #11** — "Does any of this apply to AMD users?" — Resolved implicitly in v2.1 but never directly answered
3. **mashie #9** — DeepSeek V4 Vision link pointed to non-vision model — No fix confirmation
4. **s1ugh34d #27** — "Have we made the index/viewport yet?" — Answered with "Working on it" but no timeline
5. **Patrick_M #16** — Wants weight sizes in GB in the table — Partially addressed

### Recurring Themes
- **AMD gap-filling arc:** Onno flags → digitalscream nudges → Strawberry shows up → OP closes loop in v2.1 with public credit
- **Hybrid/offload breaks VRAM tiers:** Kif's thesis — "VRAM tier alone no longer describes what fits"
- **NVFP4 → MXFP4 is the coming format:** Two independent users converged
- **Data is not human-organizable:** s1ugh34d raised twice
- **Eval culture, not vibes:** Participants bring workload-validated evidence
- **Model selection >> parameter count** for niche work
- **Participants submit diffs:** They treat the OP post as a living spec

### Frustrations
1. Data unorganizable (s1ugh34d)
2. Format confusion for newcomers (FiftyTifty)
3. Feeling excluded as AMD user (Onno, night one)
4. VRAM tiers dishonest for hybrid rigs (Kif)
5. Undocumented OS paths (Kif/WSL2)
6. Table granularity (Patrick_M)
7. Broken link (mashie)
8. 16GB dense-model speed floor (s1ugh34d: 13.9 tok/s)
9. Alignment refusals in niche content (manoreken2)
10. Power/cost at the low end (Burhan: 75W cap)

### Enthusiasm Signals
- Calvin: "I love this, especially since you go down to the pleb tier"
- digitalscream: "this thing is nuts" (200t/s on R9700)
- Kif: 1000-word fully instrumented Strata submission
- manoreken2: 3 posts in 5 days, published outputs on GitHub Pages
- s1ugh34d: 54-minute 5-model benchmark marathon
- Bump days are peak-activity days (Sep 28: 5 posts; Oct 12: 4 posts within 5 hours)

### Demographics
- **AMD: 6 users** (s1ugh34d, digitalscream, Strawberry, SgtAwesomesauce, PawingUnplug, Patrick_M)
- **NVIDIA: 4 users** (Burhan, Kif, manoreken2, Patrick_M secondary)
- **Apple: 0** (biggest hole)
- **Use cases:** Agentic coding dominates (7/11 contributors). Niche translation (manoreken2). Zero creative writing, zero vision.
- **OS:** Linux/ROCm dominant. Zero macOS.

### Gaps in Coverage
1. **Apple Silicon** — zero submissions despite 5 tier rows
2. **True entry-level 8-12GB** — no data
3. **Mainstream 24GB NVIDIA (3090/4090)** — only Kif via Strata hybrid
4. **Non-coding workloads** — essentially no submissions
5. **Vision/multimodal on consumer** — none
6. **Cost data** — no one reports hardware $
7. **Multi-user/production serving** — no in-thread submission

### Retention Mechanics (what makes people come back)
1. Your data visibly changes the reference (submit → appear in changelog → come back)
2. Bump posts as release notes (bump days = peak activity)
3. Quote-backs (OP reuses contributors' words)
4. Open invitation with low floor (Quick Submit, "drop your GPU below")
5. New-model fast-track (external heartbeat)
6. Legitimation of the weird (niche setups get same treatment)
7. Hub gravity (Related Threads route adjacent conversations in)

**What breaks the loop:** missed bump cycle, creditless incorporation, viewport promise going stale.
