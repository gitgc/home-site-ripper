#!/usr/bin/env bash
set -euo pipefail

npx \
    -y pagefind@latest \
    --site /site \
    --output-path /index \
    --glob "${PAGEFIND_GLOB}"
