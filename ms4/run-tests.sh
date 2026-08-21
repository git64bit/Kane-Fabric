#!/usr/bin/env bash
set -euo pipefail
ROOT=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"
python3 -m unittest discover -s ms4/tests -p 'test_*.py' -v
node --test ms4/browser/test-ms4.mjs
