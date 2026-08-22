#!/bin/sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ "${1:-}" = "build" ]; then
    python3 "$SCRIPT_DIR/tools/kane_fabric_zlib_guard.py" >/dev/null
fi
exec python3 "$SCRIPT_DIR/tools/kane_fabric_package.py" "$@"
