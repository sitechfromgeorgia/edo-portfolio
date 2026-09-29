#!/usr/bin/env python3
"""Deterministic page-text extractor: HTML -> visible text.

Removes <style>/<script> blocks, strips tags, unescapes entities, drops blank lines.
This is the file the Georgian style linter is pointed at, because a raw single-file page
carries CSS syntax that the linter's punctuation rules would otherwise read as prose
(`:root{`, `;color:#fff`). The browser-rendered text is captured separately by
render-check.py (evidence/rendered-text.txt) and the two are compared here.
Run: python3 alliance/tools/extract-text.py
"""
from __future__ import annotations

import html as htmlmod
import pathlib
import re
import sys

SRC = pathlib.Path(__file__).resolve().parents[1] / "index.html"
OUT = pathlib.Path(__file__).resolve().parents[1] / "page-text.txt"


def main() -> int:
    raw = SRC.read_text(encoding="utf-8")
    body = re.sub(r"<style\b.*?</style>", " ", raw, flags=re.S | re.I)
    body = re.sub(r"<script\b.*?</script>", " ", body, flags=re.S | re.I)
    body = re.sub(r"<!--.*?-->", " ", body, flags=re.S)
    body = re.sub(r"<(br|/p|/li|/h[1-6]|/div|/section|/figcaption|/td|/tr)\b[^>]*>", "\n", body, flags=re.I)
    text = htmlmod.unescape(re.sub(r"<[^>]+>", "", body))
    lines = [re.sub(r"[ \t\u00a0]+", " ", ln).strip() for ln in text.split("\n")]
    out = "\n".join(ln for ln in lines if ln)
    OUT.write_text(out + "\n", encoding="utf-8")
    print(f"page-text.txt: {len(out.splitlines())} lines, {len(out.encode('utf-8'))} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
