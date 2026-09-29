#!/usr/bin/env python3
"""Build alliance/index.html from the frozen copy file.

Source of truth for text: projects/edo-portfolio/CONTENT-alliance-ka.md (read, never retyped).
Nothing is written by hand into the HTML text nodes: every string comes from the parser.
Run: python3 alliance/tools/build-page.py
"""
from __future__ import annotations

import html
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]          # /root/projects
CONTENT = pathlib.Path("/root/.hermes/shared-knowledge/projects/edo-portfolio/CONTENT-alliance-ka.md")
OUT = pathlib.Path(__file__).resolve().parents[1] / "index.html"

BOLD_ONLY = re.compile(r"^\*\*(.+?)\*\*$")
ITEM_TITLE = re.compile(r"^\*\*(\d+)\.\s*(.+?)\.?\*\*$")
STEP_TITLE = re.compile(r"^\*\*([^*]+?)\s+-\s+([^*]+?)\.?\*\*$")
BOLD_LEAD = re.compile(r"^\*\*(.+?)\*\*\s*(.*)$")
BLOCK = re.compile(r"^##\s*ბლოკი\s*(\d)\s*-\s*(.+?)\s*$")


def esc(s: str) -> str:
    return html.escape(s, quote=False)


def bullets(lines: list[str]) -> list[str]:
    return [ln.strip() for ln in lines if ln.strip()]


def paragraphs(chunk: list[str]) -> list[str]:
    out, cur = [], []
    for ln in chunk:
        if ln.strip():
            cur.append(ln.strip())
        elif cur:
            out.append(" ".join(cur))
            cur = []
    if cur:
        out.append(" ".join(cur))
    return out


def parse(content_path: pathlib.Path) -> dict:
    raw = content_path.read_text(encoding="utf-8")
    head, _, tail = raw.partition("## ბლოკი 1")
    blocks: dict[int, dict] = {}
    for chunk in ("## ბლოკი 1" + tail).split("\n## ბლოკი "):
        first, _, rest = (chunk if chunk.startswith("## ბლოკი") else "## ბლოკი " + chunk).partition("\n")
        m = BLOCK.match(first.strip())
        assert m, f"unparsable block header: {first!r}"
        lines = rest.split("\n")
        cut = next((i for i, ln in enumerate(lines) if ln.strip() == "---"), len(lines))
        blocks[int(m.group(1))] = {"title": m.group(2), "lines": lines[:cut]}
    assert sorted(blocks) == [1, 2, 3, 4, 5, 6, 7], sorted(blocks)

    doc_title = next(ln.lstrip("# ").strip() for ln in head.split("\n") if ln.startswith("# "))

    # ---- block 1: cover -----------------------------------------------------
    b1 = bullets(blocks[1]["lines"])
    h1 = next(ln.lstrip("# ").strip() for ln in b1 if ln.startswith("# "))
    sub = next(ln.lstrip("# ").strip() for ln in b1 if ln.startswith("## "))
    fig_line = next(ln for ln in b1 if ln.startswith(tuple("0123456789$")))
    figures = []
    for part in fig_line.split(" · "):
        m = re.match(r"^([$]?\d[\d\s]*)\s+(.+)$", part)
        figures.append({"num": m.group(1).strip(), "unit": m.group(2).strip()} if m else {"num": "", "unit": part})
    assert len(figures) == 5, figures
    b1_lines = blocks[1]["lines"]
    i_fig = next(i for i, ln in enumerate(b1_lines) if ln.strip() == fig_line)
    i_sig = next(i for i, ln in enumerate(b1_lines) if ln.strip().startswith("**ედო"))
    q_lines = [ln.strip() for ln in b1_lines[i_fig + 1:i_sig] if ln.strip()]
    assert len(q_lines) == 2, q_lines
    quote = [ln.strip('"').strip() for ln in q_lines]
    sig_line = b1_lines[i_sig]
    sig_name = BOLD_LEAD.match(sig_line.strip()).group(1).strip()
    sig_role = sig_line.strip().split("·", 1)[1].strip()

    # ---- block 2: position (6 pain points) ----------------------------------
    b2 = blocks[2]["lines"]
    lead2 = next(ln.lstrip("# ").strip() for ln in b2 if ln.startswith("### "))
    items2 = []
    for ln in b2:
        m = ITEM_TITLE.match(ln.strip())
        if m:
            items2.append({"ix": int(m.group(1)), "title": m.group(2).strip(), "body": []})
        elif items2 and ln.strip() and not ln.strip().startswith("#"):
            items2[-1]["body"].append(ln.strip())
    assert len(items2) == 6, len(items2)

    # ---- block 3: offer (6 directions) --------------------------------------
    b3 = blocks[3]["lines"]
    items3 = []
    for ln in b3:
        if ln.startswith("### "):
            t = ln[4:].strip()
            m = re.match(r"^(\d+)\.\s*(.+)$", t)
            items3.append({"ix": int(m.group(1)), "title": m.group(2).strip(), "body": []})
        elif items3 and ln.strip():
            items3[-1]["body"].append(ln.strip())
    assert len(items3) == 6, len(items3)

    # ---- block 4: rollout (90 days) ----------------------------------------
    steps = []
    for ln in blocks[4]["lines"]:
        m = STEP_TITLE.match(ln.strip())
        if m:
            steps.append({"label": m.group(1).strip(), "title": m.group(2).strip(), "body": []})
        elif steps and ln.strip():
            steps[-1]["body"].append(ln.strip())
    assert len(steps) == 4, steps

    # ---- block 5: how we work together (numbered 5 steps) -------------------
    b5_lead, steps5, closer5 = None, [], None
    for ln in blocks[5]["lines"]:
        s = ln.strip()
        if not s:
            continue
        m = re.match(r"^\*\*(\d+)\.\s*(.+?)\*\*\s*(.*)$", s)
        if m:
            steps5.append({"ix": int(m.group(1)), "title": m.group(2).strip(),
                           "body": m.group(3).strip()})
            continue
        bm = BOLD_LEAD.match(s)
        assert bm, f"unexpected block-5 line: {s!r}"
        entry = {"lead": bm.group(1).strip(), "body": bm.group(2).strip()}
        if s.startswith("**მოკლედ"):
            closer5 = entry
        else:
            b5_lead = entry
    assert b5_lead and closer5, (b5_lead, closer5)
    assert [s["ix"] for s in steps5] == [1, 2, 3, 4, 5], steps5

    # ---- block 6: why me ----------------------------------------------------
    claims, portfolio = [], None
    for ln in paragraphs(blocks[6]["lines"]):
        m = BOLD_LEAD.match(ln)
        assert m, f"unexpected block-6 line: {ln!r}"
        title, body = m.group(1).strip(), m.group(2).strip()
        if re.match(r"^https?://\S+$", body):
            portfolio = {"label": title.rstrip(":"), "url": body}
        else:
            claims.append({"title": title, "body": body})
    assert len(claims) == 4 and portfolio, (claims, portfolio)

    # ---- block 7: first step + contact -------------------------------------
    b6 = bullets(blocks[7]["lines"])
    q_title = BOLD_ONLY.match(b6[0]).group(1)
    questions = [ln for ln in b6 if ln.endswith("?")]
    para = next(ln for ln in b6 if not ln.endswith("?") and not ln.startswith("**") and "@" not in ln)
    name = BOLD_ONLY.match([ln for ln in b6 if ln.startswith("**")][-1]).group(1)
    meta_line = next(ln for ln in b6 if "·" in ln and "@" not in ln and not ln.startswith("**"))
    contact_line = next(ln for ln in b6 if "@" in ln)
    assert len(questions) == 2, questions
    c_mail, c_site = [p.strip() for p in contact_line.split("·")]
    agency, city = [p.strip() for p in meta_line.split("·")]

    return {
        "doc_title": doc_title,
        "cover": {"h1": h1, "sub": sub, "figures": figures, "quote": quote,
                  "sig": {"name": sig_name, "role": sig_role}},
        "p2": {"title": blocks[2]["title"], "lead": lead2, "items": items2},
        "p3": {"title": blocks[3]["title"], "items": items3},
        "p4": {"title": blocks[4]["title"], "steps": steps},
        "p5": {"title": blocks[5]["title"], "lead": b5_lead, "steps": steps5, "closer": closer5},
        "p6": {"title": blocks[6]["title"], "claims": claims, "portfolio": portfolio},
        "p7": {"title": blocks[7]["title"], "q_title": q_title, "questions": questions, "para": para},
        "contact": {"name": name, "agency": agency, "city": city, "mail": c_mail, "site": c_site},
    }


CSS = """
:root{
  --paper:#F6F7F9;
  --surface:#FFFFFF;
  --band:#0A1020;
  --ink:#0A1020;
  --ink-soft:#333C52;
  --mute:#616B82;
  --accent:#1D4ED8;
  --rule:#DCE1E9;
  --rule-ink:rgba(255,255,255,.18);
  --on-band:#EAEEF6;
  --on-band-soft:#B9C2D4;
  --on-band-num:#F0B24C;
  --sans:system-ui,-apple-system,'Segoe UI','Noto Sans Georgian','Sylfaen','Helvetica Neue',Arial,sans-serif;
  --mono:ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'DejaVu Sans Mono',monospace;
  --pad:20px; --maxw:1200px;
}
*,*::before,*::after{box-sizing:border-box}
html{-webkit-text-size-adjust:100%;scroll-behavior:smooth}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);
  font-size:1.0625rem;line-height:1.7;font-weight:400;
  -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
h1,h2,h3,p,ul,ol,figure{margin:0}
ul,ol{padding:0;list-style:none}
a{color:var(--accent);text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:3px}
a:hover{text-decoration-thickness:2px}
:focus-visible{outline:2px solid var(--accent);outline-offset:3px;border-radius:2px}
.band-ink :focus-visible{outline-color:var(--on-band-num)}
.sr{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;border:0}
.skip{position:absolute;left:16px;top:0;transform:translateY(-140%);z-index:9;background:var(--band);
  color:var(--surface);border:1px solid var(--surface);padding:10px 16px;text-decoration:none}
.skip:focus{transform:translateY(12px)}
.wrap{width:100%;max-width:var(--maxw);margin-inline:auto;padding-inline:var(--pad)}

/* ---------- cover ---------- */
.cover{background-color:var(--band);color:var(--on-band);padding-block:34px 44px;
  background-image:repeating-linear-gradient(90deg,rgba(255,255,255,.055) 0 1px,transparent 1px 120px)}
.meta{display:flex;flex-wrap:wrap;gap:10px 22px;align-items:baseline;
  font-family:var(--mono);font-size:.75rem;letter-spacing:.12em;color:var(--on-band-soft);
  border-bottom:1px solid var(--rule-ink);padding-bottom:14px}
.meta .tag{color:var(--on-band-num)}
h1{font-size:clamp(2.125rem,7.6vw,4.25rem);line-height:1.14;font-weight:600;
  letter-spacing:normal;margin-top:30px;max-width:22ch;overflow-wrap:anywhere}
.sub{font-size:clamp(1.125rem,2.9vw,1.625rem);line-height:1.45;font-weight:500;
  color:var(--on-band);margin-top:14px;max-width:32ch;overflow-wrap:anywhere}
.figures{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px 24px;margin-top:34px}
.fig{border-top:1px solid var(--rule-ink);padding-top:12px;min-width:0}
.fig .num{display:block;font-family:var(--mono);font-size:clamp(1.375rem,4.2vw,1.875rem);
  line-height:1.15;font-weight:600;color:var(--on-band-num);font-variant-numeric:tabular-nums}
.fig-plain .unit{color:var(--on-band);margin-top:0}
.fig .unit{display:block;font-size:.9375rem;line-height:1.62;color:var(--on-band-soft);
  margin-top:4px;overflow-wrap:anywhere}
.thesis{border-top:1px solid var(--rule-ink);margin-top:38px;padding-top:26px}
.quote{font-size:clamp(1.0625rem,2.5vw,1.4375rem);line-height:1.62;color:var(--on-band);
  max-width:54ch;text-wrap:pretty}
.quote + .quote{margin-top:12px}
.sig{margin-top:18px;font-size:.9375rem;line-height:1.65;color:var(--on-band-soft)}
.sig b{color:var(--on-band);font-weight:600}
.actions{display:flex;flex-wrap:wrap;gap:12px;margin-top:30px}
.btn{display:inline-flex;align-items:center;gap:10px;padding:13px 20px;border:1px solid var(--rule-ink);
  border-radius:2px;font-size:1rem;line-height:1.25;font-weight:600;text-decoration:none}
.btn-primary{background:var(--on-band-num);border-color:var(--on-band-num);color:var(--band)}
.btn-ghost{color:var(--on-band)}
.btn .arw{font-family:var(--mono);font-weight:400}

/* ---------- contents ---------- */
.toc{background:var(--surface);border-bottom:1px solid var(--rule)}
.toc ul{display:grid;grid-template-columns:1fr;gap:1px;background:var(--rule)}
.toc li{background:var(--surface);min-width:0}
.toc a{display:flex;gap:14px;align-items:baseline;padding:15px 18px;color:var(--ink);
  text-decoration:none;font-size:.9375rem;line-height:1.62;overflow-wrap:anywhere}
.toc a:hover{background:#EEF1F6}
.toc .n{font-family:var(--mono);font-size:.75rem;letter-spacing:.1em;color:var(--accent);flex:0 0 auto}

/* ---------- sections ---------- */
.sec{padding-block:46px;border-top:1px solid var(--rule)}
.sec-head{display:flex;flex-wrap:wrap;gap:10px 20px;align-items:baseline;justify-content:space-between}
h2{font-size:clamp(1.5rem,3.5vw,2.25rem);line-height:1.2;font-weight:600;max-width:30ch;overflow-wrap:anywhere}
.mark{font-family:var(--mono);font-size:.75rem;letter-spacing:.1em;color:var(--mute);flex:0 0 auto}
.lead{font-size:1.0625rem;line-height:1.65;color:var(--ink-soft);margin-top:16px;max-width:58ch}
.items{display:grid;grid-template-columns:1fr;gap:1px;background:var(--rule);
  border:1px solid var(--rule);margin-top:26px}
.items > li{background:var(--paper);padding:20px 18px 22px;min-width:0}
.ix{font-family:var(--mono);font-size:.75rem;letter-spacing:.1em;color:var(--accent);
  font-variant-numeric:tabular-nums}
h3{font-size:1.0625rem;line-height:1.45;font-weight:600;margin-top:8px;overflow-wrap:anywhere}
.items p,.claims p,.steps p,.next p{margin-top:8px;color:var(--ink-soft);font-size:.9688rem;
  line-height:1.72;overflow-wrap:anywhere;max-width:52ch}
.steps{display:grid;grid-template-columns:1fr;gap:26px;margin-top:30px}
.step{min-width:0;border-top:1px solid var(--rule);padding-top:16px}
.step::before{content:'';display:block;width:10px;height:10px;background:var(--accent);margin-bottom:14px}
.step .label{font-family:var(--mono);font-size:.75rem;letter-spacing:.08em;color:var(--mute);
  font-variant-numeric:tabular-nums}
.step h3{margin-top:6px}
.claims{display:grid;grid-template-columns:1fr;gap:1px;background:var(--rule);
  border-block:1px solid var(--rule);margin-top:26px}
.claims > li{background:var(--paper);padding:22px 18px 24px;min-width:0;border-left:2px solid var(--accent)}
.claims p + p{margin-top:8px}
.closer{margin-top:26px;border-top:1px solid var(--rule);padding-top:18px;color:var(--ink-soft);
  font-size:.9688rem;line-height:1.72;max-width:58ch}
.portfolio{margin-top:30px;border-top:1px solid var(--rule);padding-top:20px}
.portfolio .lbl{font-family:var(--mono);font-size:.75rem;letter-spacing:.1em;color:var(--mute);
  display:block;margin-bottom:8px}
.portfolio a{font-family:var(--mono);font-size:clamp(1.125rem,3.6vw,1.625rem);line-height:1.3;
  font-weight:600;overflow-wrap:anywhere}
.qs{display:grid;gap:1px;background:var(--rule);border:1px solid var(--rule);margin-top:24px}
.qs li{background:var(--paper);padding:20px 18px;min-width:0;display:grid;grid-template-columns:auto minmax(0,1fr);
  gap:14px;align-items:baseline}
.qs li::before{content:'?';font-family:var(--mono);font-size:1.125rem;line-height:1;
  color:var(--accent);font-weight:600}
.qs span{font-size:clamp(1.0625rem,2.3vw,1.25rem);line-height:1.65;overflow-wrap:anywhere}

/* ---------- contact + footer ---------- */
.band-ink{background-color:var(--band);color:var(--on-band);padding-block:48px 40px;
  background-image:repeating-linear-gradient(90deg,rgba(255,255,255,.055) 0 1px,transparent 1px 120px)}
.band-ink h2{color:var(--on-band)}
.band-ink .mark{color:var(--on-band-soft)}
.mail{display:inline-block;margin-top:22px;font-size:clamp(1.375rem,5.2vw,2.25rem);line-height:1.25;
  font-weight:600;color:var(--on-band);text-decoration-color:var(--on-band-num);
  text-decoration-thickness:2px;text-underline-offset:8px;overflow-wrap:anywhere}
.mail:hover{color:var(--on-band-num)}
.cmeta{margin-top:26px;border-top:1px solid var(--rule-ink);padding-top:18px;display:grid;
  grid-template-columns:1fr;gap:12px;font-size:.9375rem;line-height:1.62;color:var(--on-band-soft)}
.cmeta a{font-family:var(--mono);font-size:.875rem;color:var(--on-band)}
footer{padding-block:24px 42px;display:flex;flex-wrap:wrap;gap:10px 24px;justify-content:space-between;
  color:var(--mute);font-size:.8125rem;line-height:1.62}
footer span{font-family:var(--mono);overflow-wrap:anywhere}

@media (min-width:640px){
  .figures{grid-template-columns:repeat(3,minmax(0,1fr))}
  .items{grid-template-columns:repeat(2,minmax(0,1fr))}
  .qs li{padding:22px 22px}
}
@media (min-width:768px){
  :root{--pad:36px}
  body{font-size:1.0938rem}
  .cover{padding-block:44px 56px}
  .sec{padding-block:62px}
  .steps{grid-template-columns:repeat(2,minmax(0,1fr))}
  .toc ul{grid-template-columns:repeat(2,minmax(0,1fr))}
  .cmeta{grid-template-columns:repeat(2,minmax(0,1fr));gap:14px 24px}
}
@media (min-width:1000px){
  :root{--pad:48px}
  .cover{padding-block:52px 66px}
  .sec{padding-block:74px}
  .figures{grid-template-columns:repeat(5,minmax(0,1fr));gap:0 22px}
  .steps{grid-template-columns:repeat(4,minmax(0,1fr))}
  .claims{grid-template-columns:repeat(2,minmax(0,1fr))}
  .toc ul{grid-template-columns:repeat(3,minmax(0,1fr))}
  h1{max-width:18ch}
}
@media (prefers-reduced-motion: no-preference){
  .reveal{opacity:0;animation:rise .4s cubic-bezier(.22,1,.36,1) forwards;animation-delay:calc(var(--d,0) * 60ms)}
  @keyframes rise{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
  a,.btn{transition:color .16s ease,background-color .16s ease,text-decoration-thickness .16s ease}
  .toc a{transition:background-color .16s ease}
}
@media print{
  .cover,.band-ink{background-image:none;background-color:#fff;color:#000}
  h1,.sub,.quote,.sig,.fig .num,.fig .unit,.sig b{color:#000}
  .btn,.mail,.cmeta a{color:#000;border-color:#000}
  :root{--pad:0px}
}
"""

TEMPLATE = """<!DOCTYPE html>
<html lang="ka">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="color-scheme" content="light">
<meta name="theme-color" content="#0A1020">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='5' fill='%230A1020'/%3E%3Cpath d='M9 23V9h3.4l5.1 8.6V9H21v14h-3.4L12.4 14v9z' fill='%23F0B24C'/%3E%3C/svg%3E">
<style>{css}</style>
</head>
<body>
<a class="skip" href="#main">{skip}</a>

<header class="cover">
  <div class="wrap">
    <p class="meta"><span class="tag">PROPOSAL</span><span>Alliance Group</span><span>{domain}</span><span>2026</span></p>
    <h1>{h1}</h1>
    <p class="sub">{sub}</p>
    <ul class="figures">
{figures}
    </ul>
    <figure class="thesis">
{quote}
      <figcaption class="sig"><b>{sig_name}</b> · {sig_role}</figcaption>
    </figure>
    <p class="actions">
      <a class="btn btn-primary" href="#offer">{btn_offer} <span class="arw" aria-hidden="true">↓</span></a>
      <a class="btn btn-ghost" href="#next">{btn_next}</a>
    </p>
  </div>
</header>

<nav class="toc" aria-label="{toc_label}">
  <div class="wrap">
    <ul>
{toc}
    </ul>
  </div>
</nav>

<main id="main">

  <section class="sec wrap reveal" id="position" aria-labelledby="position-h" style="--d:0">
    <div class="sec-head"><h2 id="position-h">{p2[title]}</h2><span class="mark">01 / POSITION</span></div>
    <p class="lead">{p2[lead]}</p>
    <ul class="items">
{p2items}
    </ul>
  </section>

  <section class="sec wrap reveal" id="offer" aria-labelledby="offer-h" style="--d:0">
    <div class="sec-head"><h2 id="offer-h">{p3[title]}</h2><span class="mark">02 / OFFER</span></div>
    <ul class="items">
{p3items}
    </ul>
  </section>

  <section class="sec wrap reveal" id="rollout" aria-labelledby="rollout-h" style="--d:0">
    <div class="sec-head"><h2 id="rollout-h">{p4[title]}</h2><span class="mark">03 / ROLLOUT</span></div>
    <ol class="steps">
{steps}
    </ol>
  </section>

  <section class="sec wrap reveal" id="how" aria-labelledby="how-h" style="--d:0">
    <div class="sec-head"><h2 id="how-h">{p5[title]}</h2><span class="mark">04 / HOW WE WORK</span></div>
    <p class="lead">{p5lead}</p>
    <ol class="steps">
{howsteps}
    </ol>
    <p class="closer">{p5closer}</p>
  </section>

  <section class="sec wrap reveal" id="why" aria-labelledby="why-h" style="--d:0">
    <div class="sec-head"><h2 id="why-h">{p6[title]}</h2><span class="mark">05 / WHY ME</span></div>
    <ul class="claims">
{claims}
    </ul>
    <p class="portfolio"><span class="lbl">{portfolio_label}</span>
      <a href="{portfolio_url}" target="_blank" rel="noopener noreferrer">{portfolio_url}<span class="sr"> {new_window}</span></a></p>
  </section>

  <section class="sec wrap reveal" id="next" aria-labelledby="next-h" style="--d:0">
    <div class="sec-head"><h2 id="next-h">{p7[title]}</h2><span class="mark">06 / FIRST STEP</span></div>
    <h3>{p7[q_title]}</h3>
    <ul class="qs">
{questions}
    </ul>
    <p>{p7[para]}</p>
  </section>

  <section class="band-ink" id="contact" aria-labelledby="contact-h">
    <div class="wrap">
      <div class="sec-head"><h2 id="contact-h">{contact[agency]}</h2><span class="mark">07 / CONTACT</span></div>
      <a class="mail" href="mailto:{contact[mail]}">{contact[mail]}</a>
      <div class="cmeta">
        <div>{contact[city]}</div>
        <div><a href="{contact[site]}" target="_blank" rel="noopener noreferrer">{contact[site]}<span class="sr"> {new_window}</span></a></div>
        <div>{contact[name]} · {contact[agency]}</div>
      </div>
    </div>
  </section>
</main>

<footer class="wrap">
  <span>{domain}</span>
  <span>{contact[name]} · {contact[agency]} · {contact[city]}</span>
  <span>2026</span>
</footer>
</body>
</html>
"""


def render(d: dict) -> str:
    c = d["cover"]
    figures = "\n".join(
        '      <li class="fig{cls}">{num}<span class="unit">{unit}</span></li>'.format(
            cls="" if f["num"] else " fig-plain",
            num=f'<span class="num">{esc(f["num"])}</span>' if f["num"] else "", unit=esc(f["unit"]))
        for f in c["figures"])
    qt = c["quote"]
    quote = ('      <p class="quote">„' + esc(qt[0]) + '</p>\n'
             + '      <p class="quote">' + esc(qt[1]) + '“</p>')
    p2items = "\n".join(
        f'      <li><p class="ix">{it["ix"]:02d}</p><h3>{esc(it["title"])}</h3>\n'
        f'        <p>{esc(" ".join(it["body"]))}</p></li>' for it in d["p2"]["items"])
    p3items = "\n".join(
        f'      <li><p class="ix">{it["ix"]:02d}</p><h3>{esc(it["title"])}</h3>\n'
        f'        <p>{esc(" ".join(it["body"]))}</p></li>' for it in d["p3"]["items"])
    steps = "\n".join(
        f'      <li class="step"><p class="label">{esc(s["label"])}</p><h3>{esc(s["title"])}</h3>\n'
        f'        <p>{esc(" ".join(s["body"]))}</p></li>' for s in d["p4"]["steps"])
    howsteps = "\n".join(
        f'      <li class="step"><p class="label">{s["ix"]:02d}</p><h3>{esc(s["title"])}</h3>\n'
        f'        <p>{esc(s["body"])}</p></li>' for s in d["p5"]["steps"])
    p5lead = f'<b>{esc(d["p5"]["lead"]["lead"])}</b> {esc(d["p5"]["lead"]["body"])}'
    p5closer = f'<b>{esc(d["p5"]["closer"]["lead"])}</b> {esc(d["p5"]["closer"]["body"])}'
    claims = "\n".join(
        f'      <li><h3>{esc(cl["title"])}</h3><p>{esc(cl["body"])}</p></li>' for cl in d["p6"]["claims"])
    questions = "\n".join(
        f'      <li><span>{esc(q)}</span></li>' for q in d["p7"]["questions"])
    toc_items = [(2, d["p2"]["title"]), (3, d["p3"]["title"]), (4, d["p4"]["title"]),
                 (5, d["p5"]["title"]), (6, d["p6"]["title"]), (7, d["p7"]["title"])]
    ids = {2: "position", 3: "offer", 4: "rollout", 5: "how", 6: "why", 7: "next"}
    toc = "\n".join(f'      <li><a href="#{ids[n]}"><span class="n">{i:02d}</span><span>{esc(t)}</span></a></li>'
                    for i, (n, t) in enumerate(toc_items, start=1))

    return TEMPLATE.format(
        title=esc(f'{c["h1"]} · {d["doc_title"].split("-", 1)[1].strip() if "-" in d["doc_title"] else d["doc_title"]} · SiTech Agency'),
        desc=esc(f'{c["h1"]}: {c["sub"]}'),
        css=CSS, skip="მთავარ შიგთავსზე გადასვლა", h1=esc(c["h1"]), sub=esc(c["sub"]),
        figures=figures, quote=quote, sig_name=esc(c["sig"]["name"]), sig_role=esc(c["sig"]["role"]),
        btn_offer=esc(d["p3"]["title"].split(":", 1)[1].strip()),
        btn_next=esc(d["p7"]["title"]),
        toc_label="გვერდის სექციები", toc=toc,
        p2=d["p2"], p2items=p2items, p3=d["p3"], p3items=p3items, p4=d["p4"], steps=steps,
        p5=d["p5"], p5lead=p5lead, p5closer=p5closer, howsteps=howsteps,
        claims=claims, portfolio_label=esc(d["p6"]["portfolio"]["label"]),
        portfolio_url=d["p6"]["portfolio"]["url"], p6=d["p6"], p7=d["p7"], questions=questions,
        contact=d["contact"], domain=esc("alliance.sitech.ge"), new_window="(ახალი ფანჯარა)")


def main() -> int:
    data = parse(CONTENT)
    page = render(data)
    OUT.write_text(page, encoding="utf-8")
    print(f"written {OUT}  {len(page.encode('utf-8'))} bytes")
    print(f"cover h1: {data['cover']['h1']!r}")
    print(f"sections: {[data[k]['title'] for k in ('p2','p3','p4','p5','p6','p7')]}")
    print(f"counts: figures={len(data['cover']['figures'])} position={len(data['p2']['items'])} "
          f"offer={len(data['p3']['items'])} steps={len(data['p4']['steps'])} how={len(data['p5']['steps'])} "
          f"claims={len(data['p6']['claims'])} questions={len(data['p7']['questions'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
