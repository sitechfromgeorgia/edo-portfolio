#!/usr/bin/env python3
"""Live render checks for edo-portfolio/index.html at the designed breakpoints.

Measures real geometry in Chromium: horizontal overflow (page + every leaf), viewport clipping at
scrollTop=0, section order/visibility, computed Georgian line-heights, focus-visible outline,
and writes full-page screenshots as artifacts.
Run: /root/.hermes/hermes-agent/venv/bin/python tools/render-check.py
"""
import json
import pathlib
import sys

from playwright.sync_api import sync_playwright

CHROME = "/root/.cache/ms-playwright/chromium-1217/chrome-linux64/chrome"
PAGE = pathlib.Path("index.html").resolve().as_uri()
OUT = pathlib.Path("evidence")
OUT.mkdir(exist_ok=True)
WIDTHS = [390, 720, 768, 980, 1280, 1440]

PROBE = """() => {
  const doc = document.documentElement;
  const leaf = [];
  const wide = [];
  document.querySelectorAll('body *').forEach(el => {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || el.classList.contains('sr')) return;
    const r = el.getBoundingClientRect();
    if (r.right > window.innerWidth + 1 || r.left < -1) {
      wide.push({sel: el.tagName.toLowerCase() + '.' + (el.className||'-'),
                 l: Math.round(r.left), r: Math.round(r.right),
                 text: (el.textContent||'').trim().slice(0,30)});
    }
    if (el.scrollWidth - el.clientWidth > 1 && !el.querySelector('*') && !el.classList.contains('sr')) {
      leaf.push({sel: el.tagName.toLowerCase() + '.' + (el.className||'-'),
                 over: el.scrollWidth - el.clientWidth,
                 text: (el.textContent||'').trim().slice(0,40)});
    }
  });
  const clipped = [];
  document.querySelectorAll('section, .masthead, .stat, .proj, .step, .chips li').forEach(el => {
    const r = el.getBoundingClientRect();
    if (r.top < -2 || r.bottom < 1) clipped.push({id: el.id || el.className, top: Math.round(r.top)});
  });
  const secs = [...document.querySelectorAll('main section')].map(s => ({
    id: s.id, top: Math.round(s.getBoundingClientRect().top + window.scrollY),
    h: Math.round(s.getBoundingClientRect().height),
    heading: (s.querySelector('h2')||{}).textContent || ''
  }));
  const body = getComputedStyle(document.body);
  const h1 = getComputedStyle(document.querySelector('h1'));
  const role = getComputedStyle(document.querySelector('.role'));
  const projRow = document.querySelector('.proj-in');
  const hero = document.querySelector('.masthead');
  return {
    win: {w: window.innerWidth, h: window.innerHeight},
    doc: {scrollW: doc.scrollWidth, clientW: doc.clientWidth, scrollH: doc.scrollHeight},
    bodyOverflowX: doc.scrollWidth - doc.clientWidth,
    leafOverflow: leaf,
    widerThanViewport: wide.slice(0, 6),
    clippedAtTop: clipped,
    sections: secs,
    counts: {proj: document.querySelectorAll('.proj').length,
             steps: document.querySelectorAll('.step').length,
             links: document.querySelectorAll('a[href^="http"]').length,
             statColumns: getComputedStyle(document.querySelector('.stats')).gridTemplateColumns.split(' ').length,
             projCols: projRow ? getComputedStyle(projRow).gridTemplateColumns.split(' ').length : 0},
    type: {bodyFont: body.fontFamily.slice(0, 40), bodyLH: body.lineHeight, h1LH: h1.lineHeight,
           h1Size: h1.fontSize, roleLH: role.lineHeight,
           letterSpacingGeorgian: h1.letterSpacing, h1Transform: h1.textTransform,
           heroH: Math.round(hero.getBoundingClientRect().height)},
    contrastPairs: {paper: body.backgroundColor, ink: body.color}
  };
}"""

results = {}
with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=CHROME,
                                 args=["--no-sandbox", "--disable-dev-shm-usage"])
    for w in WIDTHS:
        page = browser.new_page(viewport={"width": w, "height": 900}, device_scale_factor=1)
        page.goto(PAGE, wait_until="load")
        page.wait_for_timeout(250)
        data = page.evaluate(PROBE)
        page.screenshot(path=str(OUT / f"page-{w}.png"), full_page=True)
        page.evaluate("window.scrollTo(0,0)")
        page.keyboard.press("Tab")
        focus = page.evaluate("()=>{const e=document.activeElement;const cs=getComputedStyle(e);"
                              "return {tag:e.tagName, text:(e.textContent||'').trim().slice(0,30),"
                              " outline:cs.outlineColor+' '+cs.outlineWidth+' '+cs.outlineStyle};}")
        data["firstTabStop"] = focus
        results[w] = data
        page.close()
    browser.close()

problems = []
for w, d in results.items():
    if d["bodyOverflowX"] > 0:
        problems.append(f"{w}px: page overflows horizontally by {d['bodyOverflowX']}px")
    if d["widerThanViewport"]:
        problems.append(f"{w}px: elements wider than viewport: {d['widerThanViewport'][:3]}")
    if d["leafOverflow"]:
        problems.append(f"{w}px: {len(d['leafOverflow'])} clipped leaf elements: {d['leafOverflow'][:3]}")
    if d["clippedAtTop"]:
        problems.append(f"{w}px: elements clipped at scrollTop=0: {d['clippedAtTop'][:3]}")
    if d["doc"]["scrollH"] < 2000:
        problems.append(f"{w}px: page height suspiciously short ({d['doc']['scrollH']}px)")

print(json.dumps(results, ensure_ascii=False, indent=1))
print("\n== RENDER RESULT ==")
if problems:
    for p in problems:
        print("  FAIL", p)
    sys.exit(1)
print("PASS: no horizontal overflow, no clipped leaf, no viewport clipping, all breakpoints render")
