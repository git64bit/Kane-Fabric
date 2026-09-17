#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BROWSER="${KF_BROWSER:-$(command -v chromium || command -v chromium-browser || command -v google-chrome || true)}"

if [[ -z "$BROWSER" ]]; then
  echo "BROWSER=NOT_FOUND"
  exit 2
fi

TMP="$(mktemp -d)"
DOM="$TMP/admin-dom.html"
HTTP_LOG="$TMP/http.log"
CHROME_LOG="$TMP/chromium.log"

if [[ -n "${KF_ADMIN_BROWSER_PORT:-}" ]]; then
  PORT="$KF_ADMIN_BROWSER_PORT"
else
  PORT="$(python3 - <<'PY'
import socket
with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    print(sock.getsockname()[1])
PY
)"
fi

cleanup() {
  if [[ -n "${SERVER_PID:-}" ]]; then
    kill "$SERVER_PID" 2>/dev/null || true
  fi
  if [[ "${KF_KEEP_ADMIN_BROWSER_ARTIFACTS:-0}" != "1" ]]; then
    rm -rf "$TMP"
  else
    echo "admin_browser_artifacts=$TMP"
  fi
}
trap cleanup EXIT

cd "$ROOT"
python3 -m http.server "$PORT" --bind 127.0.0.1 >"$HTTP_LOG" 2>&1 &
SERVER_PID=$!
sleep 1

echo "BROWSER=$BROWSER"
echo "URL=http://127.0.0.1:${PORT}/web/"

"$BROWSER" \
  --headless \
  --no-sandbox \
  --disable-gpu \
  --virtual-time-budget=3000 \
  --dump-dom \
  "http://127.0.0.1:${PORT}/web/" \
  >"$DOM" 2>"$CHROME_LOG"

python3 "$ROOT/web/validate-admin-browser-dump.py" "$DOM"

echo
echo "dom_bytes=$(wc -c <"$DOM")"
echo "admin_browser_acceptance=PASS"
