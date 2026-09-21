#pragma once

#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    KF_FIRMWARE_BOOT_FACTORY = 0,
    KF_FIRMWARE_BOOT_OTA_VALID,
    KF_FIRMWARE_BOOT_OTA_PENDING_VERIFY,
    KF_FIRMWARE_BOOT_OTA_OTHER,
} kf_firmware_boot_state_t;

esp_err_t kf_firmware_lifecycle_get_boot_state(
    kf_firmware_boot_state_t *state
);

esp_err_t kf_firmware_lifecycle_confirm_healthy_boot(void);

esp_err_t kf_firmware_lifecycle_reject_trial_and_rollback(void);

#ifdef __cplusplus
}
#endif
