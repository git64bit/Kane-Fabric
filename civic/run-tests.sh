#!/usr/bin/env bash
set -euo pipefail

ROOT=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s civic/tests -p 'test_*.py' -v
