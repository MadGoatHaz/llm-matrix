Big update to the matrix — **v2.0 is live in Post #1.**

Took a while, overhauled the whole thing from the ground up, and I'm genuinely stoked about where it landed. Short version of what changed:

- **16–24GB tier is in** — that awkward gap in the middle of the matrix is gone
- **GPU Quick-Lookup** — find your exact card, jump straight to your tier
- **Use-Case Index** — pick your task, get matched models
- **Your data made it in** — Radeon VII, R9700, 96GB, and 1TB hybrid setups are all formalized now

<details>
<summary>📋 Full v2.0 Changelog</summary>

| Section | Change |
|---------|--------|
| Tiers | Added Tier 2 (16-24GB). Renumbered to 6 total tiers. |
| Matrix columns | Added "Weight Precision" and "Status" (confidence) and "Lifecycle" columns |
| GPU Quick-Lookup | NEW — 40+ specific GPUs mapped to tiers |
| Use-Case Index | NEW — 10 task types cross-referenced to best models |
| Supporting Software | NEW — All-in-one apps, chat frontends, coding agents, agent frameworks, orchestration |
| Hardware Notes | Expanded AMD section (Radeon VII, 7900 XT/XTX, MI210/MI250/MI300X). Added Apple unified memory notes. |
| Non-GGUF Guide | Added Unsloth Desktop as Option D. Clarified vLLM launch commands. |
| Models | Added ukisai/Swift-1.5-Qwen3.8-27b and ukisai/Swift-1.5-Qwen3.8-Flash-Next across Tiers 2-6 |
| Community Data | Formalized s1ugh34d (Radeon VII), digitalscream (R9700), Patrick_M (96GB LiteLLM), manoreken2 (1TB hybrid) submissions |
| KV Cache Rule | Added "Batch/Unattended Workloads" as acceptable quantization case |
| Real-World Constraints | NEW — power, thermals, PCIe, RAM, storage, OS maturity |
| Changelog | NEW — version tracking for future updates |
| Post #2 | Added "Start Here" decision flow, Quick Submit (30-sec template), Backend Selection Guide |

</details>

**Why bother re-reading Post #1?** If you bookmarked the original matrix, the new GPU lookup + use-case index means you can go from "I have a [your GPU]" to "here's exactly what to run" in about 30 seconds. Worth a refresh.

**Let's keep it rolling:**
- If your GPU isn't in the Quick-Lookup table, drop it below and I'll add it.
- Running something that's not in the matrix? Use the **Quick Submit** in Post #2 — 30 seconds, no template gymnastics.
- What's missing? What would make THIS more useful to you specifically?

Thanks to everyone who's submitted data so far — this is genuinely becoming the best local LLM reference on the forum. Keep it coming. 🚀
