#!/usr/bin/env bash
# Deploy the portfolio page to the Cloudflare Worker `edo-portfolio` (edo.sitech.ge).
#
# The design source of truth is ./index.html (root). It is a single self-contained
# file, so the only build step is copying it into the assets directory that the
# Worker serves. Nothing else in the repo is published.
set -euo pipefail
cd "$(dirname "$0")/.."

: "${CLOUDFLARE_API_TOKEN:?export CLOUDFLARE_API_TOKEN first}"

if [ ! -f index.html ]; then
  echo "index.html not found in $(pwd)" >&2
  exit 1
fi

cp -f index.html public/index.html
wrangler deploy
