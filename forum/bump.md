**v2.1 is live in Post #1** — and this one's a big deal for AMD and hybrid-offload users.

If you're running cards outside the classic VRAM tiers, or you've got a beefy-RAM + mid-tier-GPU setup, this release is for you. Short version of what changed:

- **R9700 is in the GPU lookup** — 1x, 2x, and 4x configurations mapped to their tiers. Thanks @digitalscream for the nudge.
- **Strata just changed the game** — a 125B Flash-Next model running on a *single* 4090 + 128GB RAM at 108 tok/s with 90% prompt cache hits. The "VRAM tier" model gets a "hybrid" flag now.
- **Radiance on dual R9700 is absurd** — 200+ tok/s decode, 5200-6200 prefill on Swift 1.5 Flash Next. @digitalscream's words: "this thing is nuts."
- **NVFP4 / MXFP4** called out as the emerging golden ticket. If you're on Blackwell or waiting for MI400, this is your format.
- **DeepSeek 4.1 Flash** added to the matrix — @lhl's evals have it slightly edging out Flash-Next and GLM 5.3 in both quality and speed.

<details>
<summary>📋 Full v2.1 Changelog</summary>

| Section | Change |
|---------|--------|
| GPU Lookup | Added R9700 (1x/2x/4x), AMD v620 (4x) |
| Engines | Added Strata (hybrid offload) and Radiance (AMD RDNA3/4) |
| Quant Formats | Added NVFP4/MXFP4 emerging format note |
| Matrix Tier 3 | Added DeepSeek-4.1-Flash (NVFP4) |
| Matrix Tier 4 | Added Qwen3.8-Flash-Next Q4_K_M (2x W7900) |
| Matrix Tier 5 | Added Flash-Next NVFP4, Flash-Next AWQ W4A16 (4x v620) |
| Hybrid Concept | New "Hybrid/Offload" note — VRAM tier no longer tells the full story |
| Community Data | 4 new entries: PawingUnplug, SgtAwesomesauce, Kif/Strata, digitalscream/Radiance |
| Use-Case Index | Updated speculative decoding row with NVFP4 + Strata |
| Management | Added "Data Viewport" tracking (s1ugh34d's request) |
| Changelog | v2.1 entry |
| Post #2 | Added Strata + Radiance to backend guide, hybrid example submission, engine_mode field |

</details>

Worth a refresh: with the hybrid flag and the R9700 lookup, "my setup doesn't fit a tier" stops being a dead end — most of those rigs are mapped now.

The thread's data is getting dense enough that @s1ugh34d asked about a proper index/viewport. If you've got a script or tool that parses the [COMMUNITY-SUBMISSION] blocks into a queryable table, I want to see it. DM me or post it — don't want two people building the same thing.

Also: if you're running Strata, Radiance, or any hybrid setup and it's not in the matrix yet — drop a submission. The 'hybrid' flag means your 24GB card + 128GB RAM rig is just as valid an entry as a 256GB beast. This matrix is for real hardware doing real work. 🚀
