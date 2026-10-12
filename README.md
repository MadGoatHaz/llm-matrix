# The Local LLM Matrix

Workspace for maintaining the [L1Techs Local LLM Matrix](https://forum.level1techs.com/t/256443) forum thread and its companion interactive dashboard.

## What's Here

| Directory | Contents |
|-----------|----------|
| `tools/` | Python scripts: pull, diff, parse, generate. Plus schema + tags (your editable config) |
| `data/` | Raw thread JSON snapshots + parsed `submissions.json` |
| `dashboard/` | Generated static site (deployed to GitHub Pages) |
| `forum/` | Forum post files (Post #1 matrix, Post #2 submissions, Post #3 viewport, bump posts) |
| `templates/` | (Future) Jinja2 templates for complex generation |
| `work/` | Scratch space, plans, notes |

## The Weekly Cycle

```bash
python tools/pull.py      # Get fresh data
python tools/diff.py      # See what's new
# ... review, edit schema/tags as needed ...
python tools/parse.py     # Normalize
python tools/generate.py  # Produce outputs
git commit && git push    # Deploy
```

## Forum Posts

- **Post #1** (`forum/post1_matrix.md`): The Master Matrix — VRAM tiers, models, specs
- **Post #2** (`forum/post2_submissions.md`): Submissions guide, backend selector, "Start Here"
- **Post #3** (`forum/post3_viewport.md`): Auto-generated data viewport (multiple views of all submissions)
- **Bump posts** (`forum/bump_*.md`): Changelog announcements

## Dashboard

Static site in `dashboard/`. Deploy via GitHub Pages. Filterable table of all community submissions with vendor/backend/tier filters.

Live at: `https://<username>.github.io/llm-matrix-dashboard/`
