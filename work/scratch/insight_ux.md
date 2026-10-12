# Dashboard UX Opportunities Analysis

## Key Use Cases to Serve

### 1. The "3 AM Search" (Specific hardware + specific task)
- Fastest path: GPU filter → use case filter → sorted by speed
- Needs: Single combined filter, not 5 separate dropdowns
- "I have a 4090 and I want to code" → 2 clicks to answer

### 2. The "Building a Rig" (Planning a purchase)
- Needs: Cost-per-performance comparison, power efficiency, VRAM efficiency
- Side-by-side: "4x R9700 vs 2x 4090 vs Mac Studio 128GB"
- Currently impossible: no cost data in submissions

### 3. The "What's New" (Regular checker)
- Needs: Timestamp-based "new since last visit" indicator
- Highlight breakthroughs (Strata, Radiance 200t/s)
- Show model lifecycle changes (new supersedes old)

### 4. The "Prove It to My Friend" (Shareable)
- Needs: Clean URL with all filters encoded
- Printable/shareable card view of a single submission
- "Here's what I'm running" one-pager

### 5. The "AMD vs NVIDIA" (Recurring thread theme)
- Needs: Side-by-side at same VRAM tier
- "What can I do with 48GB on AMD vs 48GB on NVIDIA?"
- Show backend differences (Radiance vs vLLM)

### 6. The "Hybrid Confusion" (Strata, offload)
- Needs: Clear visual distinction between VRAM-only and hybrid
- "This model needs X GB VRAM + Y GB RAM" not just "Tier 3"
- Engine mode as a first-class filter dimension

## Information Density
- **Signal:** Model name, quant, decode speed, stable context, hardware, backend
- **Noise (for scanning):** ttft_cold, prefill (only relevant for specific use cases), power (relevant for rig builders)
- **Right per row:** 6-8 columns max. Expandable detail for the rest.

## Trust Signals
- Multiple sources = more trust (show "2 users report this")
- OP-verified badge
- Time since submission (fresh vs stale)
- "Published output linked" = high trust
- Full launch command included = verifiable

## Mobile vs Desktop
- **Mobile (phone in coffee shop):** Quick lookup. "I have a 4090, what should I run?" → 3 results. Card view. No tables.
- **Desktop (at the rig):** Full table. All columns. Comparison mode. Charts. Filtering.
- Responsive: cards on mobile, table on desktop. Same data.

## Design Principles for This Community
- **Dark mode default** (they're at their rigs at night)
- **Monospace for numbers** (tok/s, GB, watts)
- **No fluff** (this is a spec reference, not a marketing page)
- **Credit contributors prominently** (their name on every row)
- **Link back to forum always visible** (the discussion context matters)
- **Fast** (static HTML, no API calls, instant load)
