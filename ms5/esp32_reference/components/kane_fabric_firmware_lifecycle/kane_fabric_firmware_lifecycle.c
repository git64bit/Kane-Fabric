#include "kane_fabric_firmware_lifecycle.h"

#include "kane_fabric_firmware_policy.h"

#include "esp_log.h"
#include "esp_ota_ops.h"
#include "esp_partition.h"

static const char *TAG = "kane-fabric-fw-life";

esp_err_t kf_firmware_lifecycle_get_boot_state(
    kf_firmware_boot_state_t *state
)
{
    if (state == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    const esp_partition_t *running = esp_ota_get_running_partition();
    if (running == NULL || running->type != ESP_PARTITION_TYPE_APP) {
        return ESP_ERR_INVALID_STATE;
    }

    if (running->subtype == ESP_PARTITION_SUBTYPE_APP_FACTORY) {
        *state = KF_FIRMWARE_BOOT_FACTORY;
        return ESP_OK;
    }

    esp_ota_img_states_t ota_state;
    const esp_err_t result = esp_ota_get_state_partition(running, &ota_state);
    if (result != ESP_OK) {
        return result;
    }

    if (ota_state == ESP_OTA_IMG_PENDING_VERIFY) {
        *state = KF_FIRMWARE_BOOT_OTA_PENDING_VERIFY;
    } else if (ota_state == ESP_OTA_IMG_VALID) {
        *state = KF_FIRMWARE_BOOT_OTA_VALID;
    } else {
        *state = KF_FIRMWARE_BOOT_OTA_OTHER;
    }

    return ESP_OK;
}

esp_err_t kf_firmware_lifecycle_confirm_healthy_boot(void)
{
    kf_firmware_boot_state_t state;
    esp_err_t result = kf_firmware_lifecycle_get_boot_state(&state);
    if (result != ESP_OK) {
        ESP_LOGE(
            TAG,
            "MS5-009 cannot determine running firmware state: %s",
            esp_err_to_name(result)
        );
        return result;
    }

    if (state == KF_FIRMWARE_BOOT_FACTORY) {
        ESP_LOGI(TAG, "MS5-009 factory image healthy; OTA confirmation not required");
        return kf_firmware_policy_reconcile_healthy_running_partition();
    }

    if (state == KF_FIRMWARE_BOOT_OTA_VALID) {
        ESP_LOGI(TAG, "MS5-009 OTA image already confirmed valid");
        return kf_firmware_policy_reconcile_healthy_running_partition();
    }

    if (state != KF_FIRMWARE_BOOT_OTA_PENDING_VERIFY) {
        ESP_LOGE(TAG, "MS5-009 OTA image is not in a confirmable state");
        return ESP_ERR_INVALID_STATE;
    }

    result = esp_ota_mark_app_valid_cancel_rollback();
    if (result != ESP_OK) {
        ESP_LOGE(
            TAG,
            "MS5-009 OTA confirmation failed: %s",
            esp_err_to_name(result)
        );
        return result;
    }

    result = kf_firmware_policy_reconcile_healthy_running_partition();
    if (result == ESP_OK) {
        ESP_LOGI(TAG, "MS5-009 OTA trial image confirmed healthy");
    } else {
        ESP_LOGE(
            TAG,
            "MS5-009 release-state promotion failed: %s",
            esp_err_to_name(result)
        );
    }
    return result;
}

esp_err_t kf_firmware_lifecycle_reject_trial_and_rollback(void)
{
    kf_firmware_boot_state_t state;
    esp_err_t result = kf_firmware_lifecycle_get_boot_state(&state);
    if (result != ESP_OK) {
        return result;
    }
    if (state != KF_FIRMWARE_BOOT_OTA_PENDING_VERIFY) {
        return ESP_ERR_INVALID_STATE;
    }

    ESP_LOGE(TAG, "MS5-009 rejecting OTA trial image and requesting rollback");
    return esp_ota_mark_app_invalid_rollback_and_reboot();
}
