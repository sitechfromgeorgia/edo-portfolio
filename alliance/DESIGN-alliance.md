# DESIGN — Alliance proposal page (`alliance.sitech.ge`)

A corporate, executive-identity page built for **Alliance Group** (Batumi): one self-contained
HTML file, inline CSS, no webfonts, no images, no JavaScript, no external request.
Companion page: `edo.sitech.ge` — same craft, different identity (see §7).

Concept: **the investment memo**. A numbered document, not a landing page: a hairline column
grid, mono metadata in the margin, hairline-separated tables of points, and a single blue signal
reserved for structure. Nothing is decorated that is not also information.

## 0. Source of truth and build

* Text: `shared-knowledge/projects/edo-portfolio/CONTENT-alliance-ka.md` — six blocks, **frozen**.
  The HTML is *generated* from it, never retyped: `tools/build-page.py` parses the markdown and
  emits `index.html` (asserted shapes: 5 cover figures, 6 pain points, 6 directions, 4 rollout
  steps, 4 claims, 2 questions). A copy edit belongs in the markdown, then re-run the builder.
* Verification: `tools/extract-text.py` (HTML → `page-text.txt`), `tools/render-check.py`
  (real Chromium geometry at 390/768/820/1280/1440), `tools/verify-page.py` (static contract:
  dashes, copy fidelity, leaks, structure, self-containment, measured contrast, linter, typography).

## 1. Palette (exact hex, contrast measured on the surface actually used)

| Token | Hex | Used for | Measured |
|---|---|---|---|
| `--paper` | `#F6F7F9` | body surface (cool off-white, not warm) | 17.68:1 vs ink |
| `--surface` | `#FFFFFF` | contents strip rows | 18.96:1 vs ink |
| `--band` / `--ink` | `#0A1020` | cover + contact band, text | — |
| `--ink-soft` | `#333C52` | body copy in items / steps / claims | 10.26:1 |
| `--mute` | `#616B82` | section marks, small metadata | 4.98:1 |
| `--accent` | `#1D4ED8` | numbered indices, links, rollout markers, questions | 6.25:1 on paper, 6.7:1 on white |
| `--on-band` | `#EAEEF6` | cover headline, quote | 16.3:1 on band |
| `--on-band-soft` | `#B9C2D4` | cover units, signature, contact meta | 10.59:1 on band |
| `--on-band-num` | `#F0B24C` | the five cover figures, primary button | 10.09:1 on band (and band on it) |
| `--rule` | `#DCE1E9` | hairlines (decorative, 1px) | 5.10:1 vs accent |

Deliberately not used: violet, purple/blue gradients, drop shadows, rounded cards, amber as a
surface. Amber appears only on the cover figures and one button — one signal, as in the brief.
The 10 foreground/background pairs above are asserted ≥4.5:1 by `verify-page.py`.

## 2. Type scale (system stacks only — zero webfont bytes)

- `h1` `clamp(2.125rem, 7.6vw, 4.25rem)` → 34 / 62.3 / 68 px measured at 390 / 820 / 1440.
- `h2` `clamp(1.5rem, 3.5vw, 2.25rem)` → 24 / 28.7 / 36 px. `.sub` (cover subtitle) `clamp(1.125rem, 2.9vw, 1.625rem)`.
- `h3` `1.0625rem`; body `1.0625rem` → `1.0938rem` at 768px; item copy `0.9688rem`; mono meta `0.75rem`.
- Sans: `system-ui, -apple-system, 'Segoe UI', 'Noto Sans Georgian', 'Sylfaen', Arial`.
  Mono (numbers, labels, URLs, section marks): `ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas`.
- Georgian rules: explicit `line-height` — 1.14 for the display `h1`, 1.2–1.45 for headings,
  **≥1.62 on every Georgian paragraph** (body 1.70 measured, items 1.72, quote 1.62, questions 1.65);
  **no `letter-spacing` on any Georgian text** (only on the Latin mono metadata), no
  `text-transform: uppercase` (Mkhedruli has no capitals). Numerals use `font-variant-numeric: tabular-nums`.
- Note the CSS uses single quotes for font families: the Georgian linter reads past `<style>` and
  flags `"…"` as English quotation marks. Single quotes keep the file lint-clean and change nothing.

## 3. Spacing, grid and rhythm

- 4px base; container `max-width: 1200px`, padding 20 / 36 / 48px at 0 / 768 / 1000px.
- Sections are separated by 1px hairlines (not whitespace alone): 46 → 62 → 74px vertical air.
- Point tables are `gap:1px` over a `--rule` background with a 1px outer border — the hairlines
  *are* the table, there is no card fill, no radius, no shadow.
- Every grid track carries `min-width: 0` + `overflow-wrap: anywhere` on text: long Georgian
  compounds are what widen a page, and this is measured, not assumed (§5).
- Cover figures: 2 → 3 → 5 columns (18px gutters). Contents strip: 1 → 2 → 3 columns.
  Pain points / directions: 1 → 2. Rollout: 1 → 2 → 4. Claims: 1 → 2. Contact meta: 1 → 2.

## 4. Section order (fixed by the frozen copy)

1. **Cover** (ink band): `PROPOSAL · Alliance Group · alliance.sitech.ge · 2026`, `h1`
   “Alliance Group-ისთვის”, subtitle “ახალი ენერგია და ხელოვნური ინტელექტი”, the five figures as a
   hairline strip (their own numbers, from their own material), the two-paragraph quote in Georgian
   quotes „…“, signed, and two buttons into the document.
2. Contents strip (numbered 01–05, links to the sections; Latin mono numbers, Georgian titles).
3. `[01 position]` “რას ვხედავ გარედან” — lead line plus the six pain points as a hairline table, `01`–`06`.
4. `[02 offer]` “შეთავაზება: ექვსი მიმართულება” — the same table shape, six directions.
5. `[03 rollout]` “როგორ დავნერგავ: 90 დღე” — four steps on a 4-column timeline; each step takes the
   copy's own label (“კვირა 1”, “კვირა 2-4”, “თვე 2”, “თვე 3”) above its title, with a 10px accent square
   as the timeline node.
6. `[04 why me]` “რატომ მე” — four claims (bold sentence + body) in a 2-column hairline table, then the
   portfolio link (`https://edo.sitech.ge`) as the section's one large link.
7. `[05 first step]` “პირველი ნაბიჯი” — the two questions as a two-row hairline table with a decorative
   mono `?` (CSS `::before`, `aria-hidden` by construction, never part of the text stream).
8. `[06 contact]` (ink band) — `SiTech Agency`, `hello@sitech.ge` as the primary action,
   `ბათუმი`, `https://sitech.ge`, signature. Colophon footer: domain, name, year.

## 5. What was measured (not asserted)

| Check | Result |
|---|---|
| Horizontal overflow (page + every leaf element) | 0 px at 390 / 768 / 820 / 1280 / 1440 |
| Clipped leaf (`scrollWidth > clientWidth`) | 0 |
| Elements clipped at `scrollTop = 0` | 0 (the trap: `height:100%` + centred flex; nothing here uses it) |
| Console errors / page errors | 0 — the page ships no JavaScript |
| Network requests | 1, the `file://` document itself — no subresource |
| Structure | cover + 6 labelled `<section>` + `<footer>` visible at every width |
| Contents anchors | 5/5 resolve to an existing section |
| First focus stop | the skip link (visible focus ring, 2px accent, 3px offset) |
| Georgian line-height | h1 1.14, body 1.70, items 1.72, quote 1.62 — all explicit |
| Page weight | 26.9 KB self-contained (brief: under ~120 KB) |

## 6. Copy handling (deliberate, so nothing is "almost verbatim")

* Text is taken from the markdown; only these *rendering* transforms happen, all documented:
  the block-2 and block-4 titles lose their terminating period when promoted to headings
  ("ლიდების ნაკადი.", "აუდიტი." → headings); the ordering ordinal ("1.") is split out of the heading
  into the mono index next to it; the cover quote's straight `"` delimiters become Georgian „…“
  (required by the Georgian style rules); `**bold**` markdown becomes `<h3>`/`<strong>` weight.
  No sentence is re-worded, re-ordered, shortened or added.
* `verify-page.py` asserts all **43** copy lines are present verbatim (normalised) — proved twice:
  on the statically extracted text and again on the browser-rendered DOM text.
* Nothing on the page contradicts the copy's own prohibitions: no prices, no discounts, no
  percentages, no ROI/result guarantees, no Russian, no criticism of the current site or vendors,
  no server IPs / internal paths / API keys / AI model names / agent names. Their figures
  (4 projects, $2 bn, 2 232 000 m², 15 000 apartments, 3 cities) appear only as they wrote them.
* Contact surface is exactly: `hello@sitech.ge`, `https://sitech.ge`, ბათუმი, plus the portfolio link.

## 7. Why this reads corporate, and how it differs from `edo.sitech.ge`

The personal page is warm paper (`#FAF7F2`), a visible hairline grid, nine numbered project
entries and a voice in the first person. This page keeps the craft (tabular figures, mono
metadata, hairline tables, no decoration) and drops the warmth: a cool grey-white surface, a
near-black navy band instead of a warm black, a 1200px measure instead of 1180px, one blue used
as a *structural* signal, and a document order that opens with **their** name and **their**
numbers rather than the author's. Where the portfolio says "here is what I built", this page
says "here is the state of your operations, here are six directions, here is the 90-day path,
here is the first meeting" — the author appears only twice: as the signature and in "რატომ მე".

## 8. Open question for Edo (not decided here)

`robots` is left at the default (indexable). If this page should not be discoverable by search
before the interview, add `<meta name="robots" content="noindex">` — one line, Edo's call.
