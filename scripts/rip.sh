#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

docker compose --profile rip run --rm ripper

echo "Done. Commit ./site/ to git."
