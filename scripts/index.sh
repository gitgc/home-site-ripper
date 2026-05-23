#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

docker compose --profile index run --rm indexer

echo "Done. Commit ./site/_pagefind/ to git."
