#!/usr/bin/env python3
"""Independent checks for edo-portfolio/index.html (design subtask, Sizmara).

Checks, all from the file on disk:
  1. no em dash / en dash (or other dash lookalikes) in the raw file or rendered text
  2. frozen copy fidelity: every CONTENT-ka.md line survives as an ordered word subsequence
  3. no leaked internals (IPs, /root paths, secrets, model names, phone numbers)
  4. structure: lang=ka, title, meta description, favicon, one h1, landmarks, labelled sections
  5. self-contained: zero external subresources (no CDN, no webfont, no analytics)
  6. every link in CONTENT-ka.md appears as an href
Usage: python3 tools/verify-page.py [--live-file index.html]
"""
import html
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path("/root/.hermes/shared-knowledge/projects/edo-portfolio")
COPY = ROOT / "CONTENT-ka.md"
PAGE = Path(sys.argv[sys.argv.index("--live-file") + 1]) if "--live-file" in sys.argv else Path("index.html")

DASHES = {"\u2014": "em dash", "\u2013": "en dash", "\u2012": "figure dash",
          "\u2015": "horizontal bar", "\u2212": "minus sign"}

fails, warns = [], []


def check(cond, label, detail=""):
    (print(f"  PASS  {label}") if cond else fails.append(f"{label} {detail}".strip()))
    return cond


class Text(HTMLParser):
    SKIP = {"script", "style", "title", "head"}
    VOID = {"meta", "link", "br", "img", "hr", "input", "source"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.stack = [], []
        self.meta, self.links, self.external = {}, [], []
        self.tags = []
        self.h1 = 0
        self.imgs_no_alt = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags.append(tag)
        if tag in self.SKIP:
            self.stack.append(tag)
        if tag == "h1":
            self.h1 += 1
        if tag == "img" and not a.get("alt"):
            self.imgs_no_alt += 1
        if tag == "html":
            self.meta["lang"] = a.get("lang", "")
        if tag == "meta" and (a.get("name") or a.get("property")):
            self.meta[(a.get("name") or a.get("property"))] = a.get("content", "")
        if tag == "link":
            self.meta[a.get("rel", "?")] = a.get("href", "")
        if tag in ("a", "link", "script", "img", "iframe", "source", "video", "audio"):
            url = a.get("href") or a.get("src")
            if url:
                self.links.append(url)
                if tag != "a" and not url.startswith(("data:", "#", "mailto:")):
                    self.external.append(f"{tag}:{url}")
        if tag == "section":
            self.meta.setdefault("sections", []).append((a.get("id", ""), a.get("aria-labelledby", "")))

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.stack and self.stack[-1] == tag:
            self.stack.pop()

    def handle_data(self, d):
        if not self.stack:
            self.parts.append(d)

    @property
    def text(self):
        return re.sub(r"\s+", " ", " ".join(self.parts)).strip()

    @property
    def words(self):
        return self.text.split()


def md_lines():
    out = []
    for raw in COPY.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s or s.startswith(("#", ">", "_", "|")):
            continue
        s = re.sub(r"^\-\s+", "", s).replace("**", "")
        s = re.sub(r"^(\u10E1\u10D0\u10D7\u10D0\u10E3\u10E0\u10D8|\u10E5\u10D5\u10D4\u10E1\u10D0\u10D7\u10D0\u10E3\u10E0\u10D8|\u10D4\u10E0\u10D7\u10D8 \u10EC\u10D8\u10DC\u10D0\u10D3\u10D0\u10D3\u10D4\u10D1\u10D0|\u10E6\u10D8\u10DA\u10D0\u10D9\u10D8 1|\u10E6\u10D8\u10DA\u10D0\u10D9\u10D8 2):\s*", "", s)
        out.append(s)
    return out


def subsequence(needle, hay):
    it = iter(hay)
    return all(any(w == n for w in it) for n in needle)


print("== edo-portfolio page verification ==")
raw = PAGE.read_text(encoding="utf-8")
p = Text()
p.feed(raw)
text = p.text
body_words = p.words

print("\n[1] dashes")
for ch, name in DASHES.items():
    check(raw.count(ch) == 0, f"raw file has no {name}", f"({raw.count(ch)}x)")
check(text.count("\u2014") == 0 and text.count("\u2013") == 0, "rendered text has no em/en dash")

print("\n[2] copy fidelity vs CONTENT-ka.md")
lines = md_lines()
# Documented normalisations (rendering, not rewriting): "\u00b7" separators become layout
# whitespace; the two skill lists are rendered as chips so their commas become chip gaps;
# external links carry an added screen-reader string "(\u10d0\u10ee\u10d0\u10da\u10d8 \u10e4\u10d0\u10dc\u10ef\u10d0\u10e0\u10d0)".
def _norm(l):
    return re.sub(r"\s+", " ", l.replace(" \u00b7 ", " ")).strip()
page_norm = _norm(text.replace("(\u10d0\u10ee\u10d0\u10da\u10d8 \u10e4\u10d0\u10dc\u10ef\u10d0\u10e0\u10d0)", " "))
CHIPS = ("\u10d3\u10d0\u10e0\u10ec\u10db\u10e3\u10dc\u10d4\u10d1\u10d8\u10d7:", "\u10d5\u10d0\u10e6\u10e0\u10db\u10d0\u10d5\u10d4\u10d1:")
norm = _norm
verbatim = [l for l in lines if not l.startswith(CHIPS)]
chips = [l for l in lines if l.startswith(CHIPS)]
bad_v = [l for l in verbatim if norm(l) not in page_norm]
check(not bad_v, f"all {len(verbatim)} copy lines verbatim on the page",
      "missing: " + " | ".join(m[:70] for m in bad_v[:3]))
def toks(l):
    out = []
    for t in l.split():
        t = t.strip("(),;.:\u00b7")
        if t:
            out.append(t)
    return out
page_toks = [w.strip("(),;.:\u00b7") for w in body_words]
page_toks = [w for w in page_toks if w]
bad_c = [l for l in chips if not subsequence(toks(l), page_toks)]
check(not bad_c, f"both skill lists token-complete in order ({sum(len(toks(l)) for l in chips)} items)",
      "missing: " + " | ".join(m[:70] for m in bad_c[:2]))
copy_words = sum(len(l.split()) for l in lines)
print(f"  INFO  copy words={copy_words} page words={len(body_words)}")

print("\n[3] leak scan")
leaks = {
    "ipv4": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
    "abs path": r"/root/|/home/|/var/www|/etc/",
    "secret-ish": r"sk-[A-Za-z0-9]|api[_-]?key|bearer\s|BEGIN [A-Z ]*PRIVATE",
    "model names": r"\b(GPT|Claude|Gemini|DeepSeek|Qwen|Llama|Midjourney|DALL)\b",
    "phone": r"\+995|\b5\d{2}[\s-]?\d{2}[\s-]?\d{2}[\s-]?\d{2}\b",
    "localhost": r"localhost|127\.0\.0\.1|\.internal\b",
}
for label, pat in leaks.items():
    hits = sorted(set(re.findall(pat, raw, re.I)))
    check(not hits, f"no {label}", f"hits={hits[:4]}")

print("\n[4] structure and a11y")
check(p.meta.get("lang") == "ka", 'html lang="ka"', f"got {p.meta.get('lang')!r}")
check(bool(p.meta.get("description")), "meta description present")
check(len(p.meta.get("description", "")) <= 165, "meta description <= 165 chars",
      f"({len(p.meta.get('description',''))})")
check(bool(re.search(r"<title>[^<]{10,}</title>", raw)), "title present")
check("icon" in p.meta and str(p.meta.get("icon", "")).startswith("data:image/svg"), "inline data-URI favicon")
check(p.h1 == 1, "exactly one h1", f"({p.h1})")
for lm in ("header", "main", "footer"):
    check(lm in p.tags, f"<{lm}> landmark")
check(p.imgs_no_alt == 0, "every <img> has alt (0 images by design)", f"({p.imgs_no_alt} unlabelled)")
check("prefers-reduced-motion" in raw, "prefers-reduced-motion respected")
secs = p.meta.get("sections", [])
check(all(i and l for i, l in secs) and len(secs) >= 5, "every section has id + aria-labelledby",
      f"{secs}")

print("\n[5] self-contained")
check(not p.external, "no external subresources (no CDN/webfont/analytics)", f"{p.external[:4]}")
check(not re.search(r"url\(\s*['\"]?https?:", raw) and "@import" not in raw, "no remote url()/@import in CSS")
check("http://" not in raw.replace("http://www.w3.org/", ""), "no insecure http:// reference")
check(raw.count("<script") == 0, "no JavaScript")

print("\n[6] links from the frozen copy are on the page")
urls = sorted(set(re.findall(r"https?://[^\s)\u00b7]+", COPY.read_text(encoding="utf-8"))))
hrefs = set(re.findall(r'href="([^"]+)"', raw))
missing = [u for u in urls if u not in hrefs]
check(not missing, f"all {len(urls)} copy URLs present as hrefs", f"missing={missing}")
check(all(u.startswith("https://") for u in urls), "all copy URLs are https")

print("\n== RESULT ==")
if fails:
    print(f"FAIL ({len(fails)})")
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("PASS: all checks green")
