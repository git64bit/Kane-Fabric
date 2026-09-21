#pragma once

#include "esp_err.h"
#include "kane_fabric_firmware_authorization.h"

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    kf_firmware_authorization_payload_t payload;
    kf_firmware_authorization_t authorization;
} kf_firmware_install_request_t;

/*
 * Begin the only accepted MS5-009 install path:
 *
 * 1. verify the signed authorization payload with public verification material;
 * 2. enforce sequence / rollback-floor policy;
 * 3. open the inactive OTA slot for the exact authorized firmware bytes.
 */
esp_err_t kf_firmware_install_begin(
    const uint8_t public_key[KF_FIRMWARE_AUTH_P256_PUBLIC_KEY_BYTES],
    const kf_firmware_install_request_t *request
);

esp_err_t kf_firmware_install_write(
    const void *data,
    size_t length
);

esp_err_t kf_firmware_install_finish(void);

esp_err_t kf_firmware_install_abort(void);

#ifdef __cplusplus
}
#endif
