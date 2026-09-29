#!/usr/bin/env python3
"""Browser checks for alliance/index.html at the designed breakpoints.

Measures real Chromium geometry: horizontal overflow (page + every leaf), viewport clipping at
scrollTop=0, section inventory, computed Georgian line-heights / letter-spacing, focus order,
console errors and network requests (a self-contained page must request nothing but the file).
Writes full-page screenshots + render-report.json + rendered-text.txt into alliance/evidence/.
Run: /root/.hermes/hermes-agent/venv/bin/python alliance/tools/render-check.py
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

from playwright.sync_api import sync_playwright

CHROME = "/root/.cache/ms-playwright/chromium-1217/chrome-linux64/chrome"
HERE = pathlib.Path(__file__).resolve().parents[1]
PAGE = (HERE / "index.html").as_uri()
OUT = HERE / "evidence"
OUT.mkdir(exist_ok=True)
WIDTHS = [390, 820, 1440, 768, 1280]
PLAIN = "AI Alliance"  # latin-only selector probe placeholder

PROBE = """() => {
  const doc = document.documentElement;
  const leaf = [], wide = [];
  document.querySelectorAll('body *').forEach(el => {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || el.classList.contains('sr')) return;
    const r = el.getBoundingClientRect();
    if (r.right > window.innerWidth + 1 || r.left < -1) {
      wide.push({sel: el.tagName.toLowerCase() + '.' + (el.className || '-'),
                 l: Math.round(r.left), r: Math.round(r.right),
                 text: (el.textContent || '').trim().slice(0, 30)});
    }
    if (el.scrollWidth - el.clientWidth > 1 && !el.querySelector('*') && !el.classList.contains('sr')) {
      leaf.push({sel: el.tagName.toLowerCase() + '.' + (el.className || '-'),
                 over: el.scrollWidth - el.clientWidth,
                 text: (el.textContent || '').trim().slice(0, 40)});
    }
  });
  const clipped = [];
  document.querySelectorAll('header.cover, main section, footer, .fig, .items > li, .step').forEach(el => {
    const r = el.getBoundingClientRect();
    if (r.top < -2 || r.bottom < 1) clipped.push({id: el.id || el.className, top: Math.round(r.top)});
  });
  const secs = [...document.querySelectorAll('main > section')].map(s => ({
    id: s.id, label: s.getAttribute('aria-labelledby'),
    top: Math.round(s.getBoundingClientRect().top + window.scrollY),
    h: Math.round(s.getBoundingClientRect().height),
    heading: (s.querySelector('h2') || {}).textContent || ''
  }));
  const cs = getComputedStyle;
  const bg = el => { let n = el; while (n && n !== document.documentElement) {
      const c = cs(n).backgroundColor;
      if (c && c !== 'rgba(0, 0, 0, 0)' && c !== 'transparent') return c; n = n.parentElement; }
    return cs(document.documentElement).backgroundColor; };
  const SEL = ['body', '.items > li p:not(.ix)', '.step p:not(.label)', '.step .label', '.claims p', '.mark', '.ix',
               '.quote', '.fig .num', '.fig .unit', '.sig', '.toc a', '.toc .n', '.btn-primary',
               '.mail', '.cmeta a', '.qs span', '.portfolio a', 'footer'];
  const contrast = SEL.map(s => { const el = document.querySelector(s); if (!el) return {sel: s, missing: true};
    const c = cs(el); return {sel: s, color: c.color, bg: bg(el),
      size: parseFloat(c.fontSize), weight: c.fontWeight, text: (el.textContent || '').trim().slice(0, 18)}; });
  const h1 = document.querySelector('h1'), sub = document.querySelector('.sub');
  const body = cs(document.body), quote = cs(document.querySelector('.quote'));
  const item = document.querySelector('.items > li p:not(.ix)');
  const px = v => parseFloat(v);
  return {
    win: {w: window.innerWidth, h: window.innerHeight},
    doc: {scrollW: doc.scrollWidth, clientW: doc.clientWidth, scrollH: doc.scrollHeight},
    bodyOverflowX: doc.scrollWidth - doc.clientWidth,
    leafOverflow: leaf.slice(0, 8),
    widerThanViewport: wide.slice(0, 8),
    clippedAtTop: clipped,
    sections: secs,
    counts: {
      cards: document.querySelectorAll('.items > li').length,
      steps: document.querySelectorAll('.step').length,
      claims: document.querySelectorAll('.claims > li').length,
      questions: document.querySelectorAll('.qs > li').length,
      figures: document.querySelectorAll('.fig').length,
      toc: document.querySelectorAll('.toc a').length
    },
    type: {
      bodyFont: body.fontFamily.slice(0, 46),
      bodyLH: body.lineHeight, bodySize: body.fontSize,
      bodyRatio: +(px(body.lineHeight) / px(body.fontSize)).toFixed(3),
      h1Size: h1 ? cs(h1).fontSize : null, h1LH: h1 ? cs(h1).lineHeight : null,
      h1Ratio: h1 ? +(px(cs(h1).lineHeight) / px(cs(h1).fontSize)).toFixed(3) : null,
      h1LetterSpacing: h1 ? cs(h1).letterSpacing : null,
      h1Transform: h1 ? cs(h1).textTransform : null,
      subLH: sub ? cs(sub).lineHeight : null,
      subRatio: sub ? +(px(cs(sub).lineHeight) / px(cs(sub).fontSize)).toFixed(3) : null,
      quoteRatio: +(px(quote.lineHeight) / px(quote.fontSize)).toFixed(3),
      itemLH: item ? cs(item).lineHeight : null,
      itemRatio: item ? +(px(cs(item).lineHeight) / px(cs(item).fontSize)).toFixed(3) : null,
      coverH: Math.round(document.querySelector('header.cover').getBoundingClientRect().height)
    },
    colors: {paper: body.backgroundColor, ink: body.color},
    contrast: contrast,
    cover: {h1: h1 ? h1.textContent.trim() : null, sub: sub ? sub.textContent.trim() : null},
    footer: document.querySelector('footer') ? document.querySelector('footer').textContent.trim().slice(0, 90) : null
  };
}"""

results: dict = {}
console_errors: dict = {}
requests: dict = {}

with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox", "--disable-dev-shm-usage"])
    for w in WIDTHS:
        page = browser.new_page(viewport={"width": w, "height": 900}, device_scale_factor=1)
        console_errors[str(w)] = []
        requests[str(w)] = []
        page.on("console", lambda m, w=w: console_errors[str(w)].append(f"{m.type}: {m.text}")
                if m.type in ("error", "warning") else None)
        page.on("pageerror", lambda e, w=w: console_errors[str(w)].append(f"pageerror: {e}"))
        page.on("request", lambda r, w=w: requests[str(w)].append(r.url))
        page.goto(PAGE, wait_until="load")
        page.wait_for_timeout(300)
        data = page.evaluate(PROBE)
        page.screenshot(path=str(OUT / f"page-{w}.png"), full_page=True)
        page.evaluate("window.scrollTo(0,0)")
        page.keyboard.press("Tab")
        data["firstTabStop"] = page.evaluate(
            "()=>{const e=document.activeElement;const c=getComputedStyle(e);"
            "return {tag:e.tagName,text:(e.textContent||'').trim().slice(0,26),"
            "outline:c.outlineColor+' '+c.outlineWidth+' '+c.outlineStyle};}")
        data["anchors"] = page.evaluate(
            "()=>[...document.querySelectorAll('.toc a')].map(a=>{"
            "const t=document.querySelector(a.getAttribute('href'));"
            "return {href:a.getAttribute('href'), target:!!t, "
            "top: t?Math.round(t.getBoundingClientRect().top+window.scrollY):null};})")
        if w == 1440:
            (OUT / "rendered-text.txt").write_text(page.evaluate("document.body.innerText"), encoding="utf-8")
        results[str(w)] = data
        page.close()
    browser.close()

def _lin(v: float) -> float:
    v /= 255.0
    return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4


def _lum(css_rgb: str) -> float:
    nums = [float(x) for x in re.findall(r"[\d.]+", css_rgb)][:3]
    r, g, b = (v / 255.0 for v in nums)
    f = lambda v: v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4  # noqa: E731
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def _ratio(fg: str, bg: str) -> float:
    a, b = _lum(fg), _lum(bg)
    return round((max(a, b) + 0.05) / (min(a, b) + 0.05), 2)


live_contrast: dict = {}
problems: list[str] = []
for w, d in results.items():
    if d["bodyOverflowX"] > 0:
        problems.append(f"{w}px: page overflows horizontally by {d['bodyOverflowX']}px")
    if d["widerThanViewport"]:
        problems.append(f"{w}px: elements extend past the viewport: {d['widerThanViewport'][:3]}")
    if d["leafOverflow"]:
        problems.append(f"{w}px: {len(d['leafOverflow'])} clipped leaf elements: {d['leafOverflow'][:3]}")
    if d["clippedAtTop"]:
        problems.append(f"{w}px: elements clipped at scrollTop=0: {d['clippedAtTop'][:3]}")
    if console_errors[w]:
        problems.append(f"{w}px: console/page errors: {console_errors[w][:3]}")
    off = [u for u in requests[w] if not u.startswith("file:")]
    if off:
        problems.append(f"{w}px: external requests: {off[:3]}")
    if [s["id"] for s in d["sections"]] != ["position", "offer", "rollout", "how", "why", "next", "contact"]:
        problems.append(f"{w}px: section inventory/order wrong: {[s['id'] for s in d['sections']]}")
    if not d["footer"]:
        problems.append(f"{w}px: no footer text")
    if d["doc"]["scrollH"] < 3000:
        problems.append(f"{w}px: page suspiciously short ({d['doc']['scrollH']}px)")
    if any(not s["target"] for s in d["anchors"]):
        problems.append(f"{w}px: TOC anchor without target: {[s for s in d['anchors'] if not s['target']]}")
    t = d["type"]
    if not (1.10 <= (t["h1Ratio"] or 0) <= 1.20):
        problems.append(f"{w}px: h1 line-height ratio {t['h1Ratio']} outside 1.10-1.20")
    if (t["bodyRatio"] or 0) < 1.6:
        problems.append(f"{w}px: body line-height ratio {t['bodyRatio']} below 1.6")
    if (t["itemRatio"] or 9) < 1.6:
        problems.append(f"{w}px: item line-height ratio {t['itemRatio']} below 1.6")
    if (t["quoteRatio"] or 9) < 1.6:
        problems.append(f"{w}px: quote line-height ratio {t['quoteRatio']} below 1.6")
    if (t["subRatio"] or 9) < 1.4:
        problems.append(f"{w}px: sub-heading line-height ratio {t['subRatio']} below 1.4")
    if t["h1LetterSpacing"] not in ("normal", "0px"):
        problems.append(f"{w}px: letter-spacing {t['h1LetterSpacing']} on Georgian h1")
    if t["h1Transform"] != "none":
        problems.append(f"{w}px: text-transform {t['h1Transform']} on Georgian h1")

# rendered-colour contrast: measured on computed styles, not on the stylesheet tokens
for pair in results["1440"]["contrast"]:
    if pair.get("missing"):
        problems.append(f"contrast probe selector missing: {pair['sel']}")
        continue
    ratio = _ratio(pair["color"], pair["bg"])
    large = pair["size"] >= 24 or (pair["size"] >= 18.66 and int(pair["weight"]) >= 600)
    minimum = 3.0 if large else 4.5
    live_contrast[pair["sel"]] = {"ratio": ratio, "min": minimum, "size": pair["size"],
                                  "color": pair["color"], "bg": pair["bg"], "large": large}
    if ratio < minimum:
        problems.append(f"contrast {pair['sel']}: {ratio}:1 < {minimum}:1 "
                        f"({pair['color']} on {pair['bg']}, {pair['size']}px)")

report = {"widths": WIDTHS, "results": results, "console": console_errors,
          "liveContrast": live_contrast,
          "requests": requests, "problems": problems}
(OUT / "render-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")

for w in WIDTHS:
    d = results[str(w)]
    print(f"{w:>5}px  overflowX={d['bodyOverflowX']}  leaf={len(d['leafOverflow'])}  "
          f"sections={len(d['sections'])}  h={d['doc']['scrollH']}  "
          f"cards={d['counts']['cards']} steps={d['counts']['steps']} claims={d['counts']['claims']} "
          f"q={d['counts']['questions']} figs={d['counts']['figures']}  "
          f"h1LH={d['type']['h1Ratio']} bodyLH={d['type']['bodyRatio']}  tab={d['firstTabStop']['tag']}")
print("\n== live contrast (computed styles at 1440px) ==")
for sel, v in live_contrast.items():
    print(f"  {'OK ' if v['ratio'] >= v['min'] else 'LOW'} {sel:<28} {v['ratio']:>6}:1 "
          f"(min {v['min']}, {v['size']}px{' large' if v['large'] else ''})")

print("\n== RENDER RESULT ==")
if problems:
    for p in problems:
        print("  FAIL", p)
    sys.exit(1)
print("PASS: no horizontal overflow or clipped leaf, no viewport clipping, no console error, "
      "no external request, 7 sections (position/offer/rollout/how/why/next/contact) + cover + footer "
      "render at every width")
