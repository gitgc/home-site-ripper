#!/usr/bin/env bash
set -euo pipefail

apt-get update -qq && apt-get install -y -qq wget

wget \
    --mirror \
    --no-host-directories \
    --cut-dirs="${WGET_CUT_DIRS}" \
    --page-requisites \
    --convert-links \
    --adjust-extension \
    --no-verbose \
    --directory-prefix=/site \
    "${SITE_URL}"
