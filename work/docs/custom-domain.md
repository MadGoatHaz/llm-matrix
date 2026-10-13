# Custom Domain — Setup Guide

> ## ⚠️ WARNING — Read this first
>
> **DO NOT add a `CNAME` file to the repo until your domain's DNS is fully
> configured (A record → 185.199.108.153, CNAME → `username.github.io`).
> Adding `CNAME` before DNS is ready will BREAK your site.**
>
> When a `CNAME` file is present, GitHub Pages stops serving the default
> `https://username.github.io/repo/` URL and redirects **all** traffic to the
> custom domain. If that domain's DNS does not yet point at GitHub Pages,
> visitors get a blank page / connection error instead of the site. The
> `CNAME` must be added **only after** the DNS records below are live and
> verified.

**Status:** No `CNAME` is committed at the repo root — the site is served
exclusively at `https://madgoathaz.github.io/llm-matrix/`. The domain
`localaistack.com` is a **placeholder** — purchasing the domain, pointing DNS
at it, *and only then* adding the `CNAME` file is an operator task (outside the
repo). This document is the complete, step-by-step guide for doing that, plus
the small code changes that follow once the domain is live.

---

## How it works

GitHub Pages serves a custom domain from two things:

1. **A `CNAME` file at the repo root** — one domain per line, no `https://`,
   no trailing slash. Ours is **not** committed yet (the target domain is
   `localaistack.com`); it is added *only after* step 2's DNS is live.
2. **Your DNS** — pointing the domain at GitHub Pages' edge IPs.

Once both are in place, GitHub Pages **automatically provisions a TLS
certificate** and serves the site over HTTPS. No certificate files, no
server config — that's the whole job.

The default URL (`https://madgoathaz.github.io/llm-matrix/`) **keeps working**
in parallel; GitHub Pages serves both. Existing bookmarks and the forum
featured link do not break.

---

## Step-by-step

### 1. Buy the domain

Any registrar works (Porkbun, Cloudflare, Namecheap, Google Domains, …).
`localaistack.com` is the intended domain. **No `CNAME` file exists in the
repo yet** — it is created (with your final domain) only *after* the DNS
records in step 2 are live. If you register a different domain, use that
domain in the `CNAME` file you add later:

```
localaistack.com
```

(one line, bare domain, trailing newline)

### 2. Point DNS at GitHub Pages

In your registrar's DNS control panel for `localaistack.com`:

**Apex domain (`localaistack.com`) — add four A records:**

| Type | Host | Value        | TTL  |
|------|------|--------------|------|
| A    | @    | 185.199.108.1 | 3600 |
| A    | @    | 185.199.109.1 | 3600 |
| A    | @    | 185.199.110.1 | 3600 |
| A    | @    | 185.199.111.1 | 3600 |

**`www` subdomain (`www.localaistack.com`) — add one CNAME record:**

| Type  | Host | Value             | TTL  |
|-------|------|-------------------|------|
| CNAME | www  | localaistack.com  | 3600 |

(If you don't want `www`, skip it — or reverse it: make `www` the apex-like
target and point the bare domain at `www`. One of the two must resolve to
the four A records above.)

**Remove** any existing A/CNAME/MX records for these hosts that point
elsewhere (a stale record is the #1 cause of "domain not working").

### 3. Wait for propagation + the certificate

- DNS propagation: minutes to ~48h (usually well under an hour).
- GitHub Pages TLS: the certificate is auto-provisioned, typically within
  **24 hours** (occasionally up to a few days). You can watch it in
  **GitHub → repo → Settings → Pages** — the custom domain section shows the
  status and a "Create SSL certificate" button appears while it's pending.

Verify:

```bash
# DNS resolves to GitHub's edge
dig +short localaistack.com A
# → 185.199.108.1 (and the other three, in rotation)

# Site is up over HTTPS
curl -I https://localaistack.com/
# → HTTP/2 200, valid TLS

# The old URL still works (bookmarks safe)
curl -I https://madgoathaz.github.io/llm-matrix/
# → HTTP/2 200
```

### 4. Add the `CNAME` + update the code to the real domain (one small commit)

DNS is now verified live, so it is safe to point GitHub Pages at the domain.
**Create the `CNAME` file at the repo root** with your domain (one bare line,
trailing newline) — this is the moment the default URL starts redirecting, so
only do it once `curl -I https://<domain>/` returns 200 from step 3.

The site's absolute URLs currently point at the GitHub Pages URL. With the
domain live, update **three constants** and re-generate:

| File | Constant | Old value | New value |
|------|----------|-----------|-----------|
| `tools/site/utils.py` | `SITE_URL` | `https://madgoathaz.github.io/llm-matrix` | `https://localaistack.com` |
| `tools/site/template.py` | `OG_TAGS` → `og:url` | `https://madgoathaz.github.io/llm-matrix/` | `https://localaistack.com/` |
| `tools/site/template.py` | `OG_TAGS` → `og:image` | `https://madgoathaz.github.io/llm-matrix/og-image.png` | `https://localaistack.com/og-image.png` |

Then:

```bash
make build     # regenerate all pages
make golden    # re-baseline the golden files (the nav/OG changed on purpose)
make check     # lint + validate + test — must be green
git add -A && git commit -m "chore(domain): point absolute URLs at localaistack.com" && git push
```

The CI deploy job pushes the regenerated pages to `main`, and GitHub Pages
picks up the `CNAME` on the next build — the domain goes live.

### 5. Update the forum + references

- The **L1Techs featured link / onebox** on the [matrix thread](https://forum.level1techs.com/t/256443)
  → point it at `https://localaistack.com/` (the OG image now resolves from
  the new domain automatically).
- `og-image.svg` contains the URL text `madgoathaz.github.io/llm-matrix` —
  edit the SVG and re-rasterize the PNG (see the P0-2 note in
  `work/DEV_LOG.md`) if you want the brand image to match.
- Any bookmarks, forum posts, or social links that reference the old URL:
  the old URL keeps serving, so nothing breaks — migrate them at your
  convenience.

### 6. (Optional) Hard 301 from the old URL

GitHub Pages does **not** auto-redirect the default URL to a custom domain —
it serves both. If you want a true 301 (search engines, one canonical URL):

- **Recommended: keep both alive.** The default URL is free, stable, and the
  forum ecosystem links to it. Two URLs serving the same content is normal
  for GitHub Pages custom domains; add a `<link rel="canonical">` tag to the
  pages (in `tools/site/template.py`) pointing at the custom domain so search
  engines consolidate ranking on it.
- **If you must 301:** the clean option is a tiny `301.html`-style stub —
  but since the *whole site* lives at the old path, a hard 301 means
  migrating the site off the default URL entirely, which GitHub Pages does
  not support for project pages. The canonical-tag approach above is the
  practical, standard solution.

---

## Troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| `curl` → connection timeout | DNS not propagated yet, or a stale record still pointing elsewhere. Check `dig +short localaistack.com A` returns the four IPs. |
| `curl` → 404 from GitHub | The `CNAME` file is missing, not at the repo root, or has extra text (must be exactly the bare domain, one line). |
| HTTPS fails / cert error | The certificate is still being provisioned (up to 24h+). Check the Pages settings page for the status. |
| Works at apex, not `www` | The `www` CNAME is missing or points at the wrong target. |
| Old URL stopped working | It shouldn't have — a custom domain never disables the default URL. If it did, the `CNAME` file content is malformed (fix: one bare domain per line). |

---

## Checklist

- [ ] Domain purchased
- [ ] 4× A records for the apex → 185.199.108.1 / .109.1 / .110.1 / .111.1
- [ ] CNAME `www` → apex domain (if using www)
- [ ] Stale DNS records removed
- [ ] `curl -I https://<domain>/` → 200 with valid TLS (DNS fully live)
- [ ] `CNAME` file created at repo root (**only after** the above is verified)
- [ ] `curl -I https://madgoathaz.github.io/llm-matrix/` → 200 (still live)
- [ ] `SITE_URL` / `og:url` / `og:image` updated + `make golden` + `make check` green
- [ ] Forum featured link updated
- [ ] (Optional) `<link rel="canonical">` added in `tools/site/template.py`
