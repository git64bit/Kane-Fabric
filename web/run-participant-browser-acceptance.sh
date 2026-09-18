#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BROWSER="${KF_BROWSER:-$(command -v chromium || command -v chromium-browser || command -v google-chrome || true)}"

if [[ $# -ne 2 ]]; then
  echo "usage: $0 ACCEPTED_MS3_SUBSTRATE_DIR ACCEPTED_MS4_COMPOSITION_DIR" >&2
  exit 2
fi
if [[ -z "$BROWSER" ]]; then
  echo "BROWSER=NOT_FOUND"
  exit 2
fi

SUBSTRATE_DIR="$(cd "$1" && pwd)"
COMPOSITION_DIR="$(cd "$2" && pwd)"
TMP="$(mktemp -d)"
COMPOSITION_SERVE="$TMP/composition"
DOM="$TMP/participant-dom.html"
CHROME_LOG="$TMP/chromium.log"
APP_LOG="$TMP/app-http.log"
SUBSTRATE_LOG="$TMP/substrate-http.jsonl"
COMPOSITION_LOG="$TMP/composition-http.jsonl"

free_port() {
  python3 - <<'PY'
import socket
with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    print(sock.getsockname()[1])
PY
}

APP_PORT="${KF_PARTICIPANT_APP_PORT:-$(free_port)}"
SUBSTRATE_PORT="${KF_PARTICIPANT_SUBSTRATE_PORT:-$(free_port)}"
COMPOSITION_PORT="${KF_PARTICIPANT_COMPOSITION_PORT:-$(free_port)}"

cleanup() {
  for pid in "${APP_PID:-}" "${SUBSTRATE_PID:-}" "${COMPOSITION_PID:-}"; do
    if [[ -n "$pid" ]]; then kill "$pid" 2>/dev/null || true; fi
  done
  if [[ "${KF_KEEP_PARTICIPANT_BROWSER_ARTIFACTS:-0}" != "1" ]]; then
    rm -rf "$TMP"
  else
    echo "participant_browser_artifacts=$TMP"
  fi
}
trap cleanup EXIT

mkdir -p "$COMPOSITION_SERVE"
cp -a "$COMPOSITION_DIR/." "$COMPOSITION_SERVE/"
python3 "$ROOT/web/make-participant-browser-fixture.py" \
  "$COMPOSITION_SERVE" "$COMPOSITION_SERVE/participant.json"

python3 "$ROOT/substrate/browser/range_server.py" \
  "$SUBSTRATE_DIR" --port "$SUBSTRATE_PORT" --log "$SUBSTRATE_LOG" \
  >"$TMP/substrate-server.out" 2>&1 &
SUBSTRATE_PID=$!

python3 "$ROOT/substrate/browser/range_server.py" \
  "$COMPOSITION_SERVE" --port "$COMPOSITION_PORT" --log "$COMPOSITION_LOG" \
  >"$TMP/composition-server.out" 2>&1 &
COMPOSITION_PID=$!

cd "$ROOT"
python3 -m http.server "$APP_PORT" --bind 127.0.0.1 >"$APP_LOG" 2>&1 &
APP_PID=$!
sleep 1

URL="$(python3 - "$APP_PORT" "$SUBSTRATE_PORT" "$COMPOSITION_PORT" <<'PY'
import sys
from urllib.parse import urlencode
app, substrate, composition = sys.argv[1:]
query = urlencode({
    "substrate": f"http://127.0.0.1:{substrate}/",
    "composition": f"http://127.0.0.1:{composition}/",
    "partition": "west",
    "participant": f"http://127.0.0.1:{composition}/participant.json",
    "label": "Participant publication acceptance",
})
print(f"http://127.0.0.1:{app}/web/?{query}")
PY
)"

echo "BROWSER=$BROWSER"
echo "URL=$URL"

"$BROWSER" \
  --headless \
  --no-sandbox \
  --disable-gpu \
  --virtual-time-budget=10000 \
  --dump-dom \
  "$URL" \
  >"$DOM" 2>"$CHROME_LOG"

python3 "$ROOT/web/validate-participant-browser-dump.py" "$DOM"

echo
echo "dom_bytes=$(wc -c <"$DOM")"
echo "participant_browser_acceptance=PASS"
