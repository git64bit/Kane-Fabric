#include "kane_fabric_firmware_install.h"

#include "kane_fabric_firmware_update.h"

#include "esp_err.h"

#include <stddef.h>
#include <stdint.h>
#include <string.h>

esp_err_t kf_firmware_install_begin(
    const uint8_t public_key[KF_FIRMWARE_AUTH_P256_PUBLIC_KEY_BYTES],
    const kf_firmware_install_request_t *request
)
{
    if (public_key == NULL || request == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    esp_err_t result = kf_firmware_authorization_verify(
        public_key,
        &request->payload,
        &request->authorization
    );
    if (result != ESP_OK) {
        return result;
    }

    kf_firmware_authorized_image_t image = {
        .firmware_byte_length =
            (size_t)request->payload.firmware_byte_length,
        .release_sequence = request->payload.release_sequence,
        .rollback_floor_sequence =
            request->payload.rollback_floor_sequence,
    };

    if (
        (uint64_t)image.firmware_byte_length !=
        request->payload.firmware_byte_length
    ) {
        return ESP_ERR_INVALID_SIZE;
    }

    memcpy(
        image.firmware_sha256,
        request->payload.firmware_sha256,
        sizeof(image.firmware_sha256)
    );

    return kf_firmware_update_begin_authorized(&image);
}

esp_err_t kf_firmware_install_write(
    const void *data,
    size_t length
)
{
    return kf_firmware_update_write(data, length);
}

esp_err_t kf_firmware_install_finish(void)
{
    return kf_firmware_update_finish();
}

esp_err_t kf_firmware_install_abort(void)
{
    return kf_firmware_update_abort();
}
