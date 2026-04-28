#!/usr/bin/env bash
set -euo pipefail

# Load Env From Repo Root
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [[ -f "$SCRIPT_DIR/../.env" ]]; then
  set -a
  source "$SCRIPT_DIR/../.env"
  set +a
fi

: "${RESOURCE_URL:?RESOURCE_URL must be set in .env or environment}"
: "${OWS_WALLET:?OWS_WALLET must be set in .env or environment}"

ows pay request "$RESOURCE_URL" --wallet "$OWS_WALLET"
