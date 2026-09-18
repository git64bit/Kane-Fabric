#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
node --test \
  "$ROOT/test-app-config.mjs" \
  "$ROOT/test-app-view.mjs" \
  "$ROOT/test-app-interaction.mjs" \
  "$ROOT/test-app-status.mjs" \
  "$ROOT/test-admin-descriptor.mjs" \
  "$ROOT/test-admin-identity-contract.mjs" \
  "$ROOT/test-participant-publication.mjs" \
  "$ROOT/test-participant-publication-generation.mjs" \
  "$ROOT/test-participant-edge-placement.mjs" \
  "$ROOT/test-participant-composition.mjs"
