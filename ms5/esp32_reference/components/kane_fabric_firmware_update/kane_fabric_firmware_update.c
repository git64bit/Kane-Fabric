#include "kane_fabric_firmware_update.h"

#include "esp_log.h"
#include "esp_ota_ops.h"
#include "esp_partition.h"
#include "psa/crypto.h"

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

static const char *TAG = "kane-fabric-fw-update";

typedef struct {
    bool active;
    esp_ota_handle_t ota_handle;
    const esp_partition_t *partition;
    size_t expected_length;
    size_t written;
    uint8_t expected_sha256[KF_FIRMWARE_SHA256_BYTES];
    psa_hash_operation_t hash_operation;
} kf_firmware_update_context_t;

static kf_firmware_update_context_t UPDATE;

static void reset_context(void)
{
    UPDATE = (kf_firmware_update_context_t){0};
}

static esp_err_t abort_active_update(esp_err_t reason)
{
    if (!UPDATE.active) {
        return reason;
    }

    (void)psa_hash_abort(&UPDATE.hash_operation);
    const esp_err_t ota_result = esp_ota_abort(UPDATE.ota_handle);
    reset_context();

    if (reason != ESP_OK) {
        return reason;
    }
    return ota_result;
}

esp_err_t kf_firmware_update_begin_authorized(
    const kf_firmware_authorized_image_t *image
)
{
    if (image == NULL || image->firmware_byte_length == 0U) {
        return ESP_ERR_INVALID_ARG;
    }
    if (UPDATE.active) {
        return ESP_ERR_INVALID_STATE;
    }

    const esp_partition_t *partition =
        esp_ota_get_next_update_partition(NULL);
    if (partition == NULL) {
        return ESP_ERR_NOT_FOUND;
    }
    if (image->firmware_byte_length > partition->size) {
        return ESP_ERR_INVALID_SIZE;
    }

    psa_status_t psa_result = psa_crypto_init();
    if (psa_result != PSA_SUCCESS) {
        return ESP_FAIL;
    }

    reset_context();
    UPDATE.hash_operation = psa_hash_operation_init();
    psa_result = psa_hash_setup(
        &UPDATE.hash_operation,
        PSA_ALG_SHA_256
    );
    if (psa_result != PSA_SUCCESS) {
        reset_context();
        return ESP_FAIL;
    }

    esp_ota_handle_t handle = 0;
    const esp_err_t ota_result = esp_ota_begin(
        partition,
        image->firmware_byte_length,
        &handle
    );
    if (ota_result != ESP_OK) {
        (void)psa_hash_abort(&UPDATE.hash_operation);
        reset_context();
        return ota_result;
    }

    UPDATE.active = true;
    UPDATE.ota_handle = handle;
    UPDATE.partition = partition;
    UPDATE.expected_length = image->firmware_byte_length;
    UPDATE.written = 0U;
    memcpy(
        UPDATE.expected_sha256,
        image->firmware_sha256,
        sizeof(UPDATE.expected_sha256)
    );

    ESP_LOGI(
        TAG,
        "MS5-009 authorized update staging started; partition=%s offset=0x%lx expected_bytes=%u",
        partition->label,
        (unsigned long)partition->address,
        (unsigned)UPDATE.expected_length
    );
    return ESP_OK;
}

esp_err_t kf_firmware_update_write(
    const void *data,
    size_t length
)
{
    if (!UPDATE.active) {
        return ESP_ERR_INVALID_STATE;
    }
    if (length == 0U) {
        return ESP_OK;
    }
    if (data == NULL) {
        return abort_active_update(ESP_ERR_INVALID_ARG);
    }
    if (length > UPDATE.expected_length - UPDATE.written) {
        return abort_active_update(ESP_ERR_INVALID_SIZE);
    }

    esp_err_t result = esp_ota_write(
        UPDATE.ota_handle,
        data,
        length
    );
    if (result != ESP_OK) {
        return abort_active_update(result);
    }

    const psa_status_t psa_result = psa_hash_update(
        &UPDATE.hash_operation,
        data,
        length
    );
    if (psa_result != PSA_SUCCESS) {
        return abort_active_update(ESP_FAIL);
    }

    UPDATE.written += length;
    return ESP_OK;
}

esp_err_t kf_firmware_update_finish(void)
{
    if (!UPDATE.active) {
        return ESP_ERR_INVALID_STATE;
    }
    if (UPDATE.written != UPDATE.expected_length) {
        return abort_active_update(ESP_ERR_INVALID_SIZE);
    }

    uint8_t digest[KF_FIRMWARE_SHA256_BYTES] = {0};
    size_t digest_length = 0U;
    const psa_status_t psa_result = psa_hash_finish(
        &UPDATE.hash_operation,
        digest,
        sizeof(digest),
        &digest_length
    );
    if (
        psa_result != PSA_SUCCESS ||
        digest_length != KF_FIRMWARE_SHA256_BYTES
    ) {
        return abort_active_update(ESP_FAIL);
    }

    if (
        memcmp(
            digest,
            UPDATE.expected_sha256,
            KF_FIRMWARE_SHA256_BYTES
        ) != 0
    ) {
        ESP_LOGE(TAG, "MS5-009 staged firmware SHA-256 mismatch");
        return abort_active_update(ESP_ERR_INVALID_CRC);
    }

    const esp_ota_handle_t handle = UPDATE.ota_handle;
    const esp_partition_t *partition = UPDATE.partition;

    /*
     * esp_ota_end() consumes the OTA handle regardless of result. Mark the
     * context inactive before calling it so an error path never aborts a
     * handle that ESP-IDF has already finalized/freed.
     */
    UPDATE.active = false;
    const esp_err_t end_result = esp_ota_end(handle);
    if (end_result != ESP_OK) {
        reset_context();
        return end_result;
    }

    const esp_err_t boot_result =
        esp_ota_set_boot_partition(partition);
    if (boot_result != ESP_OK) {
        reset_context();
        return boot_result;
    }

    ESP_LOGI(
        TAG,
        "MS5-009 authorized firmware staged and selected for trial boot; partition=%s bytes=%u",
        partition->label,
        (unsigned)UPDATE.expected_length
    );
    reset_context();
    return ESP_OK;
}

esp_err_t kf_firmware_update_abort(void)
{
    if (!UPDATE.active) {
        return ESP_ERR_INVALID_STATE;
    }
    return abort_active_update(ESP_OK);
}
