#pragma once

#include "esp_err.h"

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define KF_FIRMWARE_SHA256_BYTES 32U

/*
 * Input to the OTA writer after a higher layer has authenticated and accepted
 * the canonical Kane Fabric firmware release manifest.
 *
 * This component does not authorize manifests and does not contain release
 * verification keys. It binds the bytes written to the exact length and
 * SHA-256 already accepted by the authorization layer.
 */
typedef struct {
    size_t firmware_byte_length;
    uint8_t firmware_sha256[KF_FIRMWARE_SHA256_BYTES];
    uint64_t release_sequence;
    uint64_t rollback_floor_sequence;
} kf_firmware_authorized_image_t;

/*
 * Begin writing an already-authorized firmware image to the inactive OTA slot.
 * Only one update may be active at a time.
 */
esp_err_t kf_firmware_update_begin_authorized(
    const kf_firmware_authorized_image_t *image
);

/*
 * Append exact firmware bytes. Writes beyond the authorized length are
 * rejected.
 */
esp_err_t kf_firmware_update_write(
    const void *data,
    size_t length
);

/*
 * Finish hashing and validate exact length + SHA-256. Only after both match is
 * the OTA image finalized and selected as the next trial-boot partition.
 *
 * This function does not reboot. The caller deliberately chooses when to
 * reboot after all surrounding state has been safely closed.
 */
esp_err_t kf_firmware_update_finish(void);

/* Abort the active update. The currently running application is unchanged. */
esp_err_t kf_firmware_update_abort(void);

#ifdef __cplusplus
}
#endif
