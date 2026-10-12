# LLM Matrix Tools

Local tooling for maintaining the [Local LLM Matrix](https://forum.level1techs.com/t/256443) forum thread and its interactive dashboard.

## Quick Start (Weekly Cycle)

```bash
# 1. Pull latest thread data
python tools/pull.py

# 2. See what's new since last time
python tools/diff.py

# 3. (Optional) Edit tools/schema.json or tools/tags.json
#    - Add new backends, quant formats, tiers as the field evolves
#    - Tag highlighted submissions, set confidence levels

# 4. Parse all submissions into canonical data
python tools/parse.py

# 5. Generate all outputs
python tools/generate.py

# 6. Deploy
git add . && git commit -m "Weekly rollup $(date +%Y-%m-%d)" && git push
#    → GitHub Pages auto-deploys dashboard/
#    → Copy forum/post3_viewport.md into the forum
```

## Files

| File | Purpose |
|------|---------|
| `tools/pull.py` | Fetch thread JSON from Discourse API |
| `tools/diff.py` | Show new/changed posts since last pull |
| `tools/parse.py` | Extract + normalize submissions → `data/submissions.json` |
| `tools/generate.py` | Produce dashboard HTML + Post #3 viewport |
| `tools/schema.json` | **You edit this.** Valid tiers, backends, quants, use cases |
| `tools/tags.json` | **You edit this.** Curation overrides, highlights, confidence |

## Data Flow

```
Discourse API → pull.py → data/raw/latest.json
                                    ↓
                              diff.py (shows you what's new)
                                    ↓
                              parse.py → data/submissions.json
                                    ↓
                              generate.py → dashboard/ + forum/post3_viewport.md
```

## Extending

When the field changes (new engine, new quant format, new hardware):
1. Add it to `tools/schema.json` (e.g., new backend name)
2. If it needs special handling, update `parse.py`
3. Re-run the pipeline
4. Done. No frontend changes needed for new data values.

When you want a new dashboard feature:
1. Edit `tools/generate.py` (the HTML template is inline)
2. Or split it into `templates/` Jinja2 files for complex features
3. Re-run `generate.py`
