#!/usr/bin/env bash

set -euo pipefail

SUBSTRATE_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
export PYTHONDONTWRITEBYTECODE=1

exec python3 "$SUBSTRATE_DIR/tools/kane_fabric_roads_entry.py" "$@"
