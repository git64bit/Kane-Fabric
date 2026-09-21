#pragma once

#include "esp_err.h"

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define KF_FIRMWARE_AUTH_SHA256_BYTES 32U
#define KF_FIRMWARE_AUTH_KEY_ID_BYTES 32U
#define KF_FIRMWARE_AUTH_P256_PUBLIC_KEY_BYTES 65U
#define KF_FIRMWARE_AUTH_P256_SIGNATURE_BYTES 64U
#define KF_FIRMWARE_AUTH_PAYLOAD_BYTES 152U

typedef struct {
    uint8_t manifest_sha256[KF_FIRMWARE_AUTH_SHA256_BYTES];
    uint8_t firmware_sha256[KF_FIRMWARE_AUTH_SHA256_BYTES];
    uint64_t firmware_byte_length;
    uint64_t release_sequence;
    uint64_t rollback_floor_sequence;
} kf_firmware_authorization_payload_t;

typedef struct {
    uint8_t key_id_sha256[KF_FIRMWARE_AUTH_KEY_ID_BYTES];
    uint8_t authorization_payload_sha256[KF_FIRMWARE_AUTH_SHA256_BYTES];
    uint8_t signature[KF_FIRMWARE_AUTH_P256_SIGNATURE_BYTES];
} kf_firmware_authorization_t;

/*
 * Reconstruct the frozen fixed-binary authorization payload, verify its
 * SHA-256 identity, and verify the P1363 ECDSA P-256 signature using public
 * verification material only.
 *
 * public_key is SEC1 uncompressed P-256: 0x04 || X(32) || Y(32).
 * No private release-signing key is accepted or stored by this API.
 */
esp_err_t kf_firmware_authorization_verify(
    const uint8_t public_key[KF_FIRMWARE_AUTH_P256_PUBLIC_KEY_BYTES],
    const kf_firmware_authorization_payload_t *payload,
    const kf_firmware_authorization_t *authorization
);

#ifdef __cplusplus
}
#endif
