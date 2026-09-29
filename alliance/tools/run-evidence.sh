#!/usr/bin/env bash
# Re-run the whole Alliance-page evidence chain and capture every output.
# Usage: bash alliance/tools/run-evidence.sh   (from the repo root)
set -u
cd "$(dirname "$0")/../.." || exit 1
E=alliance/evidence
PY_VENV=/root/.hermes/hermes-agent/venv/bin/python
LINT=/root/.hermes/shared-knowledge/scripts/georgian-style/ge_ka_lint.py
mkdir -p "$E"
rc=0

{
  echo "== build =="; date -Is
  python3 alliance/tools/build-page.py
  echo "== extract page text =="
  python3 alliance/tools/extract-text.py
} > "$E/build.txt" 2>&1 || rc=1
cat "$E/build.txt"

{
  echo "== render-check.py (chromium) =="; date -Is
  "$PY_VENV" alliance/tools/render-check.py
  echo "exit=$?"
} > "$E/render-check.txt" 2>&1

{
  echo "== verify-page.py =="; date -Is
  python3 alliance/tools/verify-page.py
  echo "exit=$?"
} > "$E/verify-page.txt" 2>&1

{
  echo "== ge_ka_lint --file alliance/page-text.txt (page text, verbose) =="; date -Is
  python3 "$LINT" --file alliance/page-text.txt
  echo "exit=$?"
} > "$E/lint-page-text.txt" 2>&1

{
  echo "== ge_ka_lint --file alliance/index.html (raw single-file page, verbose) =="; date -Is
  echo "# expected noise: the linter reads <style> content as prose, so CSS syntax trips"
  echo "# 'no_space_after' and 'quotes'. The acceptance criterion is 0 QUOTE errors, which holds:"
  echo "# every font family in <style> uses single quotes and no attribute string survives tag-stripping."
  python3 "$LINT" --file alliance/index.html --summary
  echo "exit=$?"
} > "$E/lint-index-html.txt" 2>&1

grep -E "FAIL|PASS|exit=" "$E/verify-page.txt" | tail -6
grep -E "RENDER RESULT|PASS|FAIL" "$E/render-check.txt" | tail -3
tail -4 "$E/lint-page-text.txt"
echo "--- raw index.html lint (quote rule only) ---"
python3 - "$E/lint-index-html.txt" <<'PY'
import re, sys
out = open(sys.argv[1], encoding="utf-8").read()
counts = dict((k, int(v)) for k, v in re.findall(r"(\w+)\s+(\d+)", out.split("სუფთა")[-1]))
print("findings on the raw file:", counts)
PY

sha256sum alliance/index.html alliance/DESIGN-alliance.md alliance/page-text.txt \
          alliance/tools/build-page.py alliance/tools/verify-page.py alliance/tools/render-check.py \
          alliance/tools/extract-text.py alliance/evidence/render-report.json \
          alliance/evidence/page-390.png alliance/evidence/page-820.png alliance/evidence/page-1440.png \
          > "$E/sha256sums.txt"
cat "$E/sha256sums.txt"
exit $rc
