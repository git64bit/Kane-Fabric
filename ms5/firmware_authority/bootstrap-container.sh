#!/usr/bin/env bash
set -euo pipefail

ROLE_USER="firmware-authority"
ROLE_GROUP="firmware-authority"
STATE_ROOT="/var/lib/civicus-firmware-authority"
CONFIG_ROOT="/etc/civicus-firmware-authority"
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
section() { printf '\n== %s ==\n' "$*"; }

[ "$(id -u)" -eq 0 ] || fail "run as root inside the firmware-authority container"

if command -v systemd-detect-virt >/dev/null 2>&1; then
    systemd-detect-virt --container >/dev/null 2>&1 || fail "reference bootstrap must run inside a container"
fi

section "Create locked service identity"
if ! getent group "${ROLE_GROUP}" >/dev/null; then
    groupadd --system "${ROLE_GROUP}"
fi
if ! id "${ROLE_USER}" >/dev/null 2>&1; then
    useradd \
        --system \
        --gid "${ROLE_GROUP}" \
        --home-dir "${STATE_ROOT}" \
        --no-create-home \
        --shell /usr/sbin/nologin \
        "${ROLE_USER}"
fi
passwd -l "${ROLE_USER}" >/dev/null 2>&1 || true

section "Create non-secret authority state tree"
install -d -o "${ROLE_USER}" -g "${ROLE_GROUP}" -m 0750 \
    "${STATE_ROOT}" \
    "${STATE_ROOT}/incoming" \
    "${STATE_ROOT}/manifests" \
    "${STATE_ROOT}/authorizations" \
    "${STATE_ROOT}/public-keys" \
    "${STATE_ROOT}/evidence"
install -d -o root -g "${ROLE_GROUP}" -m 0750 "${CONFIG_ROOT}"

[ -r "${SCRIPT_DIR}/authority-state.json" ] || fail "authority-state.json must be adjacent to bootstrap script"
install -o root -g "${ROLE_GROUP}" -m 0640 \
    "${SCRIPT_DIR}/authority-state.json" \
    "${CONFIG_ROOT}/authority-state.json"

cat > "${CONFIG_ROOT}/STATUS" <<'EOF'
role=firmware-authority
state=implementation-scaffold
private_signing_key=NOT_CREATED
persistent_private_signing_key_in_container=PROHIBITED
signing=DISABLED
network_identity=NOT_ASSIGNED
acceptance=MS5-009
EOF
chown root:"${ROLE_GROUP}" "${CONFIG_ROOT}/STATUS"
chmod 0640 "${CONFIG_ROOT}/STATUS"

section "Verify prohibited activation has not occurred"
python3 - "${CONFIG_ROOT}/authority-state.json" <<'PY'
import json
import sys
from pathlib import Path
p = Path(sys.argv[1])
doc = json.loads(p.read_text())
assert doc["private_signing_key_created"] is False
assert doc["signing_enabled"] is False
assert doc["network_identity"] is None
assert doc["authority_boundary"]["container_private_signing_key_file_present"] is False
assert doc["authority_boundary"]["hardware_backed_signer_required_for_activation"] is True
print("authority placeholder state: valid")
PY

section "Scaffold complete"
printf '%s\n' \
    "${CONFIG_ROOT}/authority-state.json" \
    "${CONFIG_ROOT}/STATUS" \
    "${STATE_ROOT}/incoming" \
    "${STATE_ROOT}/manifests" \
    "${STATE_ROOT}/authorizations" \
    "${STATE_ROOT}/public-keys" \
    "${STATE_ROOT}/evidence"

echo
echo "No signing key was created. Signing remains disabled."
