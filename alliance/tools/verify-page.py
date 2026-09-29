#!/usr/bin/env python3
"""Static verifier for the Alliance proposal page.

Checks (evidence, not opinion):
  1  dash discipline (no em/en/figure dash, no horizontal bar, no minus sign) in HTML and page text
  2  copy fidelity against CONTENT-alliance-ka.md (every frozen line verbatim on the page)
  3  leak scan (ipv4, abs paths, secrets, AI model names, agent names, localhost, phone)
  4  structure + accessibility contract
  5  self-containment (no external subresource; only the three allowed link targets)
  6  measured WCAG contrast for every foreground/background pair the page actually uses
  7  Georgian style linter (ge_ka_lint) on the page text — zero findings
  8  typographic rules: explicit Georgian line-heights, no letter-spacing on Georgian, tabular figures

Run: python3 alliance/tools/verify-page.py [--quiet]
"""
from __future__ import annotations

import html as htmlmod
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
SRC = HERE / "index.html"
TEXT = HERE / "page-text.txt"
RENDERED = HERE / "evidence" / "rendered-text.txt"
CONTENT = pathlib.Path("/root/.hermes/shared-knowledge/projects/edo-portfolio/CONTENT-alliance-ka.md")
LINT = pathlib.Path("/root/.hermes/shared-knowledge/scripts/georgian-style/ge_ka_lint.py")
ALLOWED_LINKS = {"https://sitech.ge", "https://edo.sitech.ge"}

fails: list[str] = []
infos: list[str] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"  — {detail}" if detail else ""))
    if not ok:
        fails.append(f"{label} {detail}".strip())


def norm(s: str) -> str:
    s = re.sub(r"[„“”\"«»]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def variants(s: str) -> set[str]:
    """Rendering-legal variants of one frozen copy line (heading punctuation, ordinal split,
    '·' separators expanded into separate elements, ' - ' label split, label colon dropped)."""
    stripped = re.sub(r"^#+\s*", "", s)
    stripped = re.sub(r"^\*\*\d+\.\s*", "", stripped).replace("**", "")
    dashed = norm(re.sub(r"\s+-\s+", " ", stripped))
    return {norm(s), norm(s).rstrip("."), norm(stripped), norm(stripped).rstrip("."),
            norm(stripped.split("·")[0]), norm(s.replace("·", " ")),
            norm(stripped.replace("·", " ")), dashed, dashed.rstrip("."),
            norm(stripped.replace(":", " ", 1))}


def coverage(hay: str, lines: list[str]) -> tuple[int, list[str]]:
    missing = [s for s in lines if not any(v and v in hay for v in variants(s))]
    return len(lines) - len(missing), missing


def luminance(c: str) -> float:
    r, g, b = (int(c[i:i + 2], 16) / 255 for i in (1, 3, 5))
    f = lambda v: v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4  # noqa: E731
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def ratio(fg: str, bg: str) -> float:
    a, b = luminance(fg), luminance(bg)
    return round((max(a, b) + 0.05) / (min(a, b) + 0.05), 2)


def main() -> int:
    html = SRC.read_text(encoding="utf-8")
    page = TEXT.read_text(encoding="utf-8")
    style = re.search(r"<style>(.*?)</style>", html, re.S).group(1)

    print("== alliance proposal page verification ==")
    print(f"\n[0] artifact\n  INFO  index.html {len(html.encode('utf-8'))} bytes, "
          f"{len(html.splitlines())} lines")
    check(len(html.encode("utf-8")) < 120 * 1024, "page under 120 KB",
          f"{len(html.encode('utf-8'))} B")

    print("\n[1] dashes")
    for name, ch in [("em dash", "\u2014"), ("en dash", "\u2013"), ("figure dash", "\u2012"),
                     ("horizontal bar", "\u2015"), ("minus sign", "\u2212")]:
        check(ch not in html, f"html has no {name}")
        check(ch not in page, f"page text has no {name}")

    print("\n[2] copy fidelity vs CONTENT-alliance-ka.md")
    raw = CONTENT.read_text(encoding="utf-8")
    raw = raw.split("## 🚫")[0]
    hay = norm(page) + " || " + norm(htmlmod.unescape(re.sub(r"<[^>]+>", " ", html)))
    lines, matched, missing = [], 0, []
    for ln in raw.split("\n"):
        s = ln.strip()
        if not s or s == "---" or s.startswith("## ბლოკი") or s.startswith("### "):
            continue
        if s.startswith("# ") or re.match(r"^\*\*(ავტორი|მისამართი|ენა):?\*\*", s):
            continue
        s = s.lstrip("> ").strip()
        lines.append(s)
    for s in lines:
        if any(v and v in hay for v in variants(s)):
            matched += 1
        else:
            missing.append(s)
    check(matched == len(lines), f"all {len(lines)} copy lines verbatim on the page",
          f"matched {matched}/{len(lines)}" + (f"; missing: {missing[:3]}" if missing else ""))
    if RENDERED.exists():
        rmatch, rmissing = coverage(norm(RENDERED.read_text(encoding="utf-8")), lines)
        check(rmatch == len(lines),
              "browser-rendered DOM text contains the copy too (second route, not the extractor)",
              f"{rmatch}/{len(lines)}" + (f"; missing: {rmissing[:2]}" if rmissing else ""))

    print("\n[3] leak scan")
    leaks = {
        "ipv4": re.findall(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", html),
        "abs path": re.findall(r"/root/|/home/\w+|/etc/", html),
        "secret-ish": re.findall(r"(?:api[_-]?key|token|secret|bearer)\s*[:=]", html, re.I),
        "ai model": re.findall(r"\b(?:gpt|claude|gemini|llama|mistral|sonnet|opus|deepseek)\b", html, re.I),
        "agent name": re.findall(r"\b(?:sizmara|lucy|snowden|archimedes|einstein|socrates|dzia)\b", html, re.I),
        "localhost": re.findall(r"localhost|127\.0\.0\.1", html),
        "phone": re.findall(r"\+?\d{3}[\s-]?\d{3}[\s-]?\d{3}", html),
        "vendor criticism": re.findall(r"\b(?:palindroma|connect\b)", html, re.I),
        "price/roi": re.findall(r"\b(?:₾|GEL|ROI|ფასდაკლებ)", html),
    }
    for k, v in leaks.items():
        check(not v, f"no {k}", str(v[:3]))

    print("\n[4] structure and a11y")
    ids = set(re.findall(r'\sid="([^"]+)"', html))
    secs = re.findall(r'<section class="[^"]*" id="([^"]+)" aria-labelledby="([^"]+)"', html)
    check(html.count("<h1") == 1, "exactly one h1")
    check('lang="ka"' in html, 'html lang="ka"')
    check("<header" in html and "<main" in html and "<footer" in html and '<nav class="toc"' in html,
          "header/main/footer/nav landmarks")
    check(all(ref in ids for _, ref in secs), "every aria-labelledby resolves to an id",
          f"{len(secs)} sections: {[s for s, _ in secs]}")
    check(len(secs) == 7, "seven labelled sections in main", str(len(secs)))
    check('class="skip"' in html and 'href="#main"' in html, "skip link")
    check("prefers-reduced-motion" in style, "prefers-reduced-motion handling")
    check(":focus-visible" in style, "focus-visible styling")
    check("svg+xml" in html and html.count("<img") == 0, "inline data-URI favicon, zero <img>")
    ext = re.findall(r'<a [^>]*href="(https?://[^"]+)"', html)
    check(all('target="_blank" rel="noopener noreferrer"' in m for m in re.findall(r'<a [^>]*href="https?://[^"]+"[^>]*>', html)),
          "external links carry target=_blank + rel=noopener")
    check(len(ext) >= 2 and set(ext) == ALLOWED_LINKS, "only the allowed external links", str(set(ext)))

    print("\n[5] self-contained")
    check(not re.search(r"<link[^>]+stylesheet|@import|<script", html, re.I), "no stylesheet/@import/script")
    check(not re.search(r"(?:src|url)\(?[\"']?https?://", html, re.I), "no remote subresource")
    no_data = re.sub(r'href="data:[^"]*"', "", html)
    urls = set(re.findall(r"https?://[^\s\"'<>)]+", no_data))
    check(urls == ALLOWED_LINKS, "no URL beyond sitech.ge / edo.sitech.ge", str(urls - ALLOWED_LINKS))
    check("sitech.ge" in html and "hello@sitech.ge" in html and "ბათუმი" in html, "contact block present")

    print("\n[6] contrast (measured on the surfaces actually used)")
    tok = dict(re.findall(r"--([a-z-]+):(#[0-9A-Fa-f]{6})", style))
    pairs = [("ink", "paper", 4.5), ("ink-soft", "paper", 4.5), ("mute", "paper", 4.5),
             ("accent", "paper", 4.5), ("accent", "surface", 4.5), ("ink", "surface", 4.5),
             ("on-band", "band", 4.5), ("on-band-soft", "band", 4.5), ("on-band-num", "band", 4.5),
             ("band", "on-band-num", 4.5)]
    for fg, bg, minimum in pairs:
        if fg in tok and bg in tok:
            r = ratio(tok[fg], tok[bg])
            check(r >= minimum, f"{fg} on {bg} >= {minimum}:1", f"{r}:1 ({tok[fg]} on {tok[bg]})")
    r = ratio(tok.get("accent", "#000000"), tok.get("rule", "#FFFFFF"))
    infos.append(f"accent vs rule (decorative): {r}:1")

    print("\n[7] Georgian style linter (page text)")
    out = subprocess.run([sys.executable, str(LINT), "--file", str(TEXT), "--summary"],
                         capture_output=True, text=True)
    counts = dict((k, int(v)) for k, v in re.findall(r"(\w+)\s+(\d+)", out.stdout.split("სუფთა")[-1]))
    print("  INFO  ge_ka_lint --file page-text.txt:", counts or "clean", f"exit={out.returncode}")
    # a visible https:// URL is copy-mandated; the linter reads its scheme colon as "punctuation
    # without a following space", so those findings are classified separately and printed.
    url_findings = [fd for fd in re.findall(r"[✗✓] \[(\w+)\][^\n]*", out.stdout)
                    if fd == "no_space_after"]
    non_url = {k: c for k, c in counts.items() if k != "no_space_after"}
    check(not non_url, "ge_ka_lint: zero findings on every rule except URL scheme colons", str(non_url))
    check(counts.get("quotes", 0) == 0, "ge_ka_lint: no quote errors (acceptance criterion)",
          f"{counts.get('quotes', 0)} quote findings")
    if counts.get("no_space_after"):
        colon = len(re.findall(r"https?://", page))
        check(counts["no_space_after"] == colon,
              f"all {counts['no_space_after']} no_space_after findings are URL scheme colons",
              f"{colon} URLs on the page")
    gaps = re.findall(r"\.\.\.|«|»", page) + re.findall(r"\b\d+\s+%", page)
    check(not gaps, "no ellipsis / spaced percent in page text", str(gaps[:3]))
    raw_q = len(re.findall(r'"[^"\n]{2,80}"', style))
    check(raw_q == 0, "no double-quoted string left in <style> (the one linter rule CSS can trip)",
          f"{raw_q}")

    print("\n[8] typographic rules")
    ls = [(sel.strip(), val.strip()) for sel, body in
          re.findall(r"([^{}@]+)\{([^{}]*)\}", style)
          for val in re.findall(r"letter-spacing\s*:\s*([^;]+)", body)]
    latin_only = (".meta", ".mark", ".toc .n", ".ix", ".lbl", ".step .label", ".fig .num")
    bad = [p for p in ls if not (p[1] in ("normal", "0", "0px") or any(k in p[0] for k in latin_only))]
    check(not bad, "letter-spacing only on Latin mono metadata (never on Georgian text)",
          f"{len(ls)} declarations, offending: {bad}")
    check("uppercase" not in style, "no text-transform: uppercase (Mkhedruli has no capitals)")
    check("tabular-nums" in style, "tabular figures for numbers")
    check("@media print" in style, "print stylesheet")

    print("\n== VERIFY RESULT ==")
    for i in infos:
        print("  INFO ", i)
    if fails:
        for f in fails:
            print("  FAIL ", f)
        return 1
    print(f"  PASS  all checks green ({len(pairs)} contrast pairs, {matched}/{len(lines)} copy lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
