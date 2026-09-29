# edo-portfolio

Personal portfolio page for **Edo Mzhavanadze** (SiTech Agency, Batumi): a single
self-contained HTML file, served as a static site from a Cloudflare Worker.

- Live: https://edo.sitech.ge/
- Hosting: Cloudflare **Worker** `edo-portfolio` with static assets. Deliberately *not* a
  Cloudflare Pages project (the account sits at the 100-project Pages cap).
- Design source of truth: `index.html` in the repo root (inline CSS, no build step, no CDN,
  no web fonts, no analytics, no cookies, no JavaScript).
- `DESIGN.md` is the visual system spec from the design subtask; `tools/verify-page.py`
  is the design-side verifier.

## Deploy (one line, from the repo root)

```bash
export CLOUDFLARE_API_TOKEN=...  && export CLOUDFLARE_ACCOUNT_ID=...
./scripts/deploy.sh
```

That copies `index.html` into the assets directory `public/` and runs `wrangler deploy`;
the new version is live at the edge in seconds. There is no build step and no CI.

## Layout

| Path | Published? | Purpose |
|---|---|---|
| `index.html` | yes (copied to `public/index.html`) | the page |
| `public/index.html` | yes | generated copy of `index.html` (do not edit by hand) |
| `public/404.html` | yes | not-found page |
| `public/favicon.svg` | yes | standalone favicon (the page also carries an inline data-URI favicon) |
| `public/robots.txt` | yes | crawler policy |
| `wrangler.jsonc` | no | worker name, assets dir, `edo.sitech.ge` custom-domain route |
| `DESIGN.md`, `tools/` | no | design spec and verifier |

`wrangler.jsonc` owns the worker name, the `public/` assets directory and the
`edo.sitech.ge` custom domain, so CI or a laptop deployment produces the identical target.

## Constraints (project brief)

- Georgian copy, no em dash or en dash anywhere, „…“ quotes; Latin brand names and
  acronyms stay Latin, a Georgian case marker on a Latin word takes a hyphen (`Amazon-მა`).
- WCAG AA contrast, keyboard navigable, semantic landmarks, alt text, `prefers-reduced-motion`.
- Never publish server IPs, internal paths, API keys, AI model names, client PII or phone numbers.
- `sitech.ge` and every other client site stay untouched.
