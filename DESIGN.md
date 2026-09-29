# DESIGN — edo-portfolio (ედო მჟავანაძე, ერთი გვერდი)

Concept: **"ინდექსი" (the index)**. The page is built like a printed dossier: a visible hairline
grid, tabular figures, mono metadata, and numbered project entries. Structure carries the design,
so it never reads as "hero + three grey cards + gradient". No CDN, no webfonts, no images, no JS.

## 1. Palette (exact hex, measured WCAG contrast on the surface it is used on)
| Token | Hex | Used for | Measured |
|---|---|---|---|
| `--paper` | `#FAF7F2` | body surface (warm off-white, not grey) | 17.19:1 vs ink |
| `--ink` | `#17140F` | text, masthead + contact band surface | 17.19:1 vs paper |
| `--ink-soft` / `--ink-mute` | `#4B453C` / `#6E675C` | body copy / labels, meta | 8.87:1 / 5.23:1 |
| `--accent` | `#A34700` | project numbers, signal text on paper | 5.68:1 |
| `--amber` | `#E9A23B` | numbers on ink, primary button | 8.48:1 on ink / with ink text |
| `--link` | `#1D4ED8` | links | 6.27:1 |
| `--rule` | `#E3DCD1` | hairline rules (decorative, 1px) | n/a |

Deliberately not used: violet, purple gradients, drop shadows, card fills. SiTech blue survives
only as the link colour; brand amber is the single signal colour.

## 2. Type scale (system stacks only, no webfonts)
- Display `clamp(2.5rem, 8.5vw, 5rem)`, h2 `clamp(1.75rem, 4.2vw, 2.75rem)`, h3 `1.25rem`,
  body `1.0625rem` -> `1.125rem` at 768px, label `0.8125rem`.
- Sans stack: `system-ui, -apple-system, "Segoe UI", "Noto Sans Georgian", "Sylfaen", Arial`.
  Mono stack (numbers, labels, URLs): `ui-monospace, SFMono-Regular, Menlo, Consolas`.
- Georgian rules applied: explicit `line-height` 1.14 display / 1.68 body, **no letter-spacing on
  Georgian**, no `text-transform: uppercase` (Mkhedruli has no capitals); letter-spacing only on Latin
  mono meta; numerals use `font-variant-numeric: tabular-nums`.

## 3. Spacing and grid
- 4px base; container `max-width 1180px`, padding 20 / 40 / 56px at 0 / 768 / 1280px.
- Sections separated by 1px `--rule` hairlines (not by whitespace alone) and 64-104px vertical air.
- Densities: one column < 720px; at 720-979px stats 4 columns, steps 2 columns, skills 1.6fr/1fr;
  from 980px the project index is 64px / 300px / 1fr and the steps become 5 columns.
- Every grid track carries `min-width: 0` plus `overflow-wrap: anywhere`, because long Georgian
  compounds are the thing that widens a page; measured at 390/720/768/980/1280/1440px.

## 4. Section order (fixed by CONTENT-ka.md)
1. Masthead (ink band): name, subtitle, one-liner, two buttons.
2. Numbers strip: 2x2 -> 4 columns, hairline-divided, tabular figures.
3. ჩემ შესახებ: one lede paragraph + two body paragraphs, measure 62ch.
4. პროექტები: numbered index 01-09, supports the 8 client links as one link list.
5. როგორ ვმუშაობ: the copy's own 1.-5. steps, one -> two -> five columns.
6. უნარები: two groups as hairline chips.
7. დაკავშირება (ink band) + colophon footer.

## 5. Motion
- Load reveal only: opacity 0 -> 1 with `translateY(10px) -> 0`, 420ms `cubic-bezier(.22,1,.36,1)`,
  60ms stagger; hover/focus 160ms colour and underline only. Everything sits inside
  `@media (prefers-reduced-motion: no-preference)`; reduced motion renders the final state, and there
  are no scroll effects, no parallax and no autoplay.

## 6. Accessibility contract
`lang="ka"`, skip link, `header/main/section/footer` landmarks with `aria-labelledby`, one `h1`,
`focus-visible` 2px outline at 3px offset, external links get `rel="noopener"` plus a visually hidden
"(ახალი ფანჯარა)", inline SVG favicon, zero images (so nothing needs alt), tabular figures.

## 7. Distinctive / risk
Distinctive: the grid itself is the ornament - rules, tabular figures, mono metadata, a numbered
index instead of cards. Risk: blue survives only as a link colour, and Windows machines without
"Noto Sans Georgian" fall back to Sylfaen for Georgian glyphs (mixed but legible), not defects.
