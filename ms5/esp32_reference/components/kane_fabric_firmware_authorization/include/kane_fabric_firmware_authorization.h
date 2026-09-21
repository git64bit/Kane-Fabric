#pragma once

#include "esp_err.h"

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define KF_FIRMWARE_AUTH_MANIFEST_SHA256_BYTES 32U
#define KF_FIRMWARE_AUTH_KEY_ID_BYTES 32U
#define KF_FIRMWARE_AUTH_P256_PUBLIC_KEY_BYTES 65U
#define KF_FIRMWARE_AUTH_P256_SIGNATURE_BYTES 64U

/*
 * Binary form of the frozen MS5-009 authorization envelope after JSON/base64
 * decoding by the caller. Signature is fixed-width P1363 r||s.
 */
typedef struct {
    uint8_t key_id_sha256[KF_FIRMWARE_AUTH_KEY_ID_BYTES];
    uint8_t manifest_sha256[KF_FIRMWARE_AUTH_MANIFEST_SHA256_BYTES];
    uint8_t signature[KF_FIRMWARE_AUTH_P256_SIGNATURE_BYTES];
} kf_firmware_authorization_t;

/*
 * Verify an authorization envelope with public verification material only.
 *
 * public_key must be a 65-byte SEC1 uncompressed P-256 point:
 * 0x04 || X(32) || Y(32).
 *
 * No private release-signing key is accepted or stored by this API.
 */
esp_err_t kf_firmware_authorization_verify(
    const uint8_t public_key[KF_FIRMWARE_AUTH_P256_PUBLIC_KEY_BYTES],
    const kf_firmware_authorization_t *authorization
);

#ifdef __cplusplus
}
#endif
