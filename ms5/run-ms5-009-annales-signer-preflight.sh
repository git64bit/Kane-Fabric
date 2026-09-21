#!/usr/bin/env bash
set -euo pipefail

EXPECTED_HOST="annales"
CONTAINER="firmware-authority"

fail() {
    printf 'MS5_009_ANNALES_SIGNER_PREFLIGHT=FAIL reason=%s\n' "$*" >&2
    exit 1
}

warn() {
    printf 'WARN %s\n' "$*" >&2
}

[[ "$(hostname -s)" == "$EXPECTED_HOST" ]] || fail "must run on annales"
[[ "$(id -u)" -eq 0 ]] || fail "must run as root on annales"
command -v lxc >/dev/null 2>&1 || fail "lxc command unavailable"

printf 'host=%s\n' "$(hostname -s)"
printf 'kernel=%s\n' "$(uname -r)"
printf 'lxc_version=%s\n' "$(lxc version | head -n1)"
printf 'timestamp_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"

printf '%s\n' '--- container inert-boundary verification ---'
STATUS=$(lxc list "$CONTAINER" --format csv -c s 2>/dev/null || true)
printf 'container_status=%s\n' "$STATUS"
[[ "$STATUS" == "RUNNING" ]] || fail "firmware-authority container is not running"

EXPANDED=$(lxc config show "$CONTAINER" --expanded)
if grep -Eq '^[[:space:]]+type:[[:space:]]+(usb|gpu|proxy)[[:space:]]*$' <<<"$EXPANDED"; then
    fail "firmware-authority has a prohibited usb/gpu/proxy device"
fi
printf 'container_usb_passthrough=NO\n'
printf 'container_gpu_passthrough=NO\n'
printf 'container_proxy_device=NO\n'

INNER=$(lxc exec "$CONTAINER" -- sh -lc '
set -eu
printf "status_file_begin\n"
cat /etc/civicus-firmware-authority/STATUS
printf "status_file_end\n"
printf "wg_count=%s\n" "$(find /sys/class/net -maxdepth 1 -type l -name "wg*" 2>/dev/null | wc -l)"
printf "state_file_count=%s\n" "$(find /var/lib/civicus-firmware-authority -type f 2>/dev/null | wc -l)"
printf "private_key_like_file_count=%s\n" "$(
    find /var/lib/civicus-firmware-authority /etc/civicus-firmware-authority       -type f \( -iname "*.pem" -o -iname "*.key" -o -iname "*.p12" -o -iname "*.pfx" \)       2>/dev/null | wc -l
)"
')
printf '%s\n' "$INNER"

grep -Fq 'private_signing_key=NOT_CREATED' <<<"$INNER" || fail "container no longer reports private key NOT_CREATED"
grep -Fq 'signing=DISABLED' <<<"$INNER" || fail "container no longer reports signing DISABLED"
grep -Fq 'wg_count=0' <<<"$INNER" || fail "container has unexpected WireGuard interface"
grep -Fq 'private_key_like_file_count=0' <<<"$INNER" || fail "private-key-like file found in authority roots"
printf 'container_inert_boundary=PASS\n'

printf '%s\n' '--- host USB signer inventory ---'
USB_COUNT=0
CANDIDATE_COUNT=0
for dev in /sys/bus/usb/devices/*; do
    [[ -f "$dev/idVendor" && -f "$dev/idProduct" ]] || continue
    VID=$(tr 'A-F' 'a-f' < "$dev/idVendor")
    PID=$(tr 'A-F' 'a-f' < "$dev/idProduct")
    PRODUCT=$(cat "$dev/product" 2>/dev/null || true)
    MANUFACTURER=$(cat "$dev/manufacturer" 2>/dev/null || true)
    BUSDEV=$(basename "$dev")
    USB_COUNT=$((USB_COUNT + 1))
    printf 'usb[%s]=%s:%s manufacturer=%q product=%q\n'         "$BUSDEV" "$VID" "$PID" "$MANUFACTURER" "$PRODUCT"

    case "$VID" in
        1050|20a0|096e|2ccf|2581)
            CANDIDATE_COUNT=$((CANDIDATE_COUNT + 1))
            printf 'hardware_signer_candidate[%s]=%s:%s manufacturer=%q product=%q\n'                 "$BUSDEV" "$VID" "$PID" "$MANUFACTURER" "$PRODUCT"
            ;;
    esac
done
printf 'usb_device_count=%d\n' "$USB_COUNT"
printf 'hardware_signer_candidate_count=%d\n' "$CANDIDATE_COUNT"

printf '%s\n' '--- host signing-tool inventory ---'
for tool in openssl ykman pkcs11-tool p11tool p11-kit gpg2 gpg python3; do
    if command -v "$tool" >/dev/null 2>&1; then
        printf 'tool_%s=present path=%s\n' "$tool" "$(command -v "$tool")"
    else
        printf 'tool_%s=absent\n' "$tool"
    fi
done

OPENSC_MODULE=""
for candidate in     /usr/lib/x86_64-linux-gnu/opensc-pkcs11.so     /usr/lib64/opensc-pkcs11.so     /usr/lib/opensc-pkcs11.so
do
    if [[ -f "$candidate" ]]; then
        OPENSC_MODULE="$candidate"
        break
    fi
done

if [[ -n "$OPENSC_MODULE" ]]; then
    printf 'opensc_pkcs11_module=present path=%s\n' "$OPENSC_MODULE"
else
    printf 'opensc_pkcs11_module=absent\n'
fi

printf '%s\n' '--- hidraw/smartcard visibility ---'
HIDRAW_COUNT=$(find /dev -maxdepth 1 -type c -name 'hidraw*' 2>/dev/null | wc -l)
printf 'hidraw_count=%s\n' "$HIDRAW_COUNT"

if command -v pcsc_scan >/dev/null 2>&1; then
    printf 'pcsc_scan=present\n'
else
    printf 'pcsc_scan=absent\n'
fi

if systemctl is-active --quiet pcscd 2>/dev/null; then
    printf 'pcscd_active=YES\n'
else
    printf 'pcscd_active=NO\n'
fi

printf 'usb_passthrough_changed=NO\n'
printf 'key_generated=NO\n'
printf 'key_imported=NO\n'
printf 'pin_prompted=NO\n'
printf 'signing_performed=NO\n'
printf 'container_mutated=NO\n'
printf 'MS5_009_ANNALES_SIGNER_PREFLIGHT=PASS\n'
