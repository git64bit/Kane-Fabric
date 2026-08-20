#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
    echo "usage: $0 PACKAGE_DIR [EXPECTED_SUBSTRATE_CONTENT_SHA256]" >&2
    exit 2
fi

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
PACKAGE_DIR=$1
EXPECTED_CONTENT=${2:-}

command -v node >/dev/null 2>&1 || {
    echo "ERROR: node is required for the browser Web API probe" >&2
    exit 3
}

TMPDIR=$(mktemp -d)
SERVER_LOG="$TMPDIR/http.jsonl"
SERVER_STDOUT="$TMPDIR/server.out"
SERVER_STDERR="$TMPDIR/server.err"

cleanup() {
    if [ -n "${SERVER_PID:-}" ]; then
        kill "$SERVER_PID" 2>/dev/null || true
        wait "$SERVER_PID" 2>/dev/null || true
    fi
    rm -rf "$TMPDIR"
}
trap cleanup EXIT

python3 "$SCRIPT_DIR/range_server.py" \
    "$PACKAGE_DIR" \
    --host 127.0.0.1 \
    --port 0 \
    --log "$SERVER_LOG" \
    >"$SERVER_STDOUT" 2>"$SERVER_STDERR" &
SERVER_PID=$!

for _ in $(seq 1 100); do
    if [ -s "$SERVER_STDOUT" ]; then
        break
    fi
    if ! kill -0 "$SERVER_PID" 2>/dev/null; then
        cat "$SERVER_STDERR" >&2 || true
        echo "ERROR: range probe server exited before startup" >&2
        exit 4
    fi
    sleep 0.05
done

if [ ! -s "$SERVER_STDOUT" ]; then
    echo "ERROR: timed out waiting for range probe server startup" >&2
    exit 4
fi

PORT=$(python3 - "$SERVER_STDOUT" <<'PY'
import json
import sys
print(json.loads(open(sys.argv[1], encoding="utf-8").readline())["port"])
PY
)
BASE_URL="http://127.0.0.1:${PORT}/"

if [ -n "$EXPECTED_CONTENT" ]; then
    node "$SCRIPT_DIR/probe.mjs" "$BASE_URL" "$EXPECTED_CONTENT"
else
    node "$SCRIPT_DIR/probe.mjs" "$BASE_URL"
fi

python3 "$SCRIPT_DIR/validate_probe.py" "$SERVER_LOG"
