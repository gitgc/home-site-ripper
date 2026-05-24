#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

docker compose --profile clean run --rm cleaner

echo "Finished cleaning."
