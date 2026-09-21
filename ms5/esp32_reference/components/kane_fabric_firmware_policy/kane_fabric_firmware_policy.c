#include "kane_fabric_firmware_policy.h"

#include "esp_ota_ops.h"
#include "esp_partition.h"
#include "nvs.h"

#include <stdbool.h>
#include <stdint.h>

#define KF_FW_NAMESPACE "kane_fw"
#define KF_FW_ACCEPTED_SEQ_KEY "accepted_seq"
#define KF_FW_ROLLBACK_FLOOR_KEY "rollback_floor"
#define KF_FW_PENDING_SEQ_KEY "pending_seq"
#define KF_FW_PENDING_FLOOR_KEY "pending_floor"
#define KF_FW_PENDING_ADDR_KEY "pending_addr"

static esp_err_t read_u64_default_zero(
    nvs_handle_t handle,
    const char *key,
    uint64_t *value
)
{
    const esp_err_t result = nvs_get_u64(handle, key, value);
    if (result == ESP_ERR_NVS_NOT_FOUND) {
        *value = 0U;
        return ESP_OK;
    }
    return result;
}

static esp_err_t read_state_from_handle(
    nvs_handle_t handle,
    kf_firmware_policy_state_t *state
)
{
    *state = (kf_firmware_policy_state_t){0};

    esp_err_t result = read_u64_default_zero(
        handle,
        KF_FW_ACCEPTED_SEQ_KEY,
        &state->accepted_sequence
    );
    if (result != ESP_OK) {
        return result;
    }

    result = read_u64_default_zero(
        handle,
        KF_FW_ROLLBACK_FLOOR_KEY,
        &state->rollback_floor_sequence
    );
    if (result != ESP_OK) {
        return result;
    }

    result = nvs_get_u64(
        handle,
        KF_FW_PENDING_SEQ_KEY,
        &state->pending_sequence
    );
    if (result == ESP_ERR_NVS_NOT_FOUND) {
        state->pending = false;
        return ESP_OK;
    }
    if (result != ESP_OK) {
        return result;
    }

    state->pending = true;
    result = nvs_get_u64(
        handle,
        KF_FW_PENDING_FLOOR_KEY,
        &state->pending_rollback_floor_sequence
    );
    if (result != ESP_OK) {
        return result;
    }

    return nvs_get_u32(
        handle,
        KF_FW_PENDING_ADDR_KEY,
        &state->pending_partition_address
    );
}

static esp_err_t erase_pending(nvs_handle_t handle)
{
    const char *keys[] = {
        KF_FW_PENDING_SEQ_KEY,
        KF_FW_PENDING_FLOOR_KEY,
        KF_FW_PENDING_ADDR_KEY,
    };

    for (size_t i = 0U; i < sizeof(keys) / sizeof(keys[0]); i++) {
        const esp_err_t result = nvs_erase_key(handle, keys[i]);
        if (result != ESP_OK && result != ESP_ERR_NVS_NOT_FOUND) {
            return result;
        }
    }
    return ESP_OK;
}

esp_err_t kf_firmware_policy_get_state(
    kf_firmware_policy_state_t *state
)
{
    if (state == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    nvs_handle_t handle;
    esp_err_t result = nvs_open(
        KF_FW_NAMESPACE,
        NVS_READWRITE,
        &handle
    );
    if (result != ESP_OK) {
        return result;
    }

    result = read_state_from_handle(handle, state);
    nvs_close(handle);
    return result;
}

esp_err_t kf_firmware_policy_check_candidate(
    uint64_t release_sequence,
    uint64_t rollback_floor_sequence
)
{
    if (
        release_sequence == 0U ||
        rollback_floor_sequence > release_sequence
    ) {
        return ESP_ERR_INVALID_ARG;
    }

    kf_firmware_policy_state_t state;
    esp_err_t result = kf_firmware_policy_get_state(&state);
    if (result != ESP_OK) {
        return result;
    }
    if (state.rollback_floor_sequence > state.accepted_sequence) {
        return ESP_ERR_INVALID_STATE;
    }
    if (state.pending) {
        return ESP_ERR_INVALID_STATE;
    }
    if (release_sequence <= state.accepted_sequence) {
        return ESP_ERR_INVALID_VERSION;
    }
    if (release_sequence < state.rollback_floor_sequence) {
        return ESP_ERR_INVALID_VERSION;
    }
    if (rollback_floor_sequence < state.rollback_floor_sequence) {
        return ESP_ERR_INVALID_VERSION;
    }

    return ESP_OK;
}

esp_err_t kf_firmware_policy_stage_candidate(
    uint64_t release_sequence,
    uint64_t rollback_floor_sequence,
    uint32_t target_partition_address
)
{
    if (target_partition_address == 0U) {
        return ESP_ERR_INVALID_ARG;
    }

    esp_err_t result = kf_firmware_policy_check_candidate(
        release_sequence,
        rollback_floor_sequence
    );
    if (result != ESP_OK) {
        return result;
    }

    nvs_handle_t handle;
    result = nvs_open(
        KF_FW_NAMESPACE,
        NVS_READWRITE,
        &handle
    );
    if (result != ESP_OK) {
        return result;
    }

    result = nvs_set_u64(
        handle,
        KF_FW_PENDING_SEQ_KEY,
        release_sequence
    );
    if (result == ESP_OK) {
        result = nvs_set_u64(
            handle,
            KF_FW_PENDING_FLOOR_KEY,
            rollback_floor_sequence
        );
    }
    if (result == ESP_OK) {
        result = nvs_set_u32(
            handle,
            KF_FW_PENDING_ADDR_KEY,
            target_partition_address
        );
    }
    if (result == ESP_OK) {
        result = nvs_commit(handle);
    }

    nvs_close(handle);
    return result;
}

esp_err_t kf_firmware_policy_cancel_pending(
    uint32_t target_partition_address
)
{
    nvs_handle_t handle;
    esp_err_t result = nvs_open(
        KF_FW_NAMESPACE,
        NVS_READWRITE,
        &handle
    );
    if (result != ESP_OK) {
        return result;
    }

    kf_firmware_policy_state_t state;
    result = read_state_from_handle(handle, &state);
    if (result == ESP_OK && state.pending) {
        if (state.pending_partition_address != target_partition_address) {
            result = ESP_ERR_INVALID_STATE;
        } else {
            result = erase_pending(handle);
            if (result == ESP_OK) {
                result = nvs_commit(handle);
            }
        }
    }

    nvs_close(handle);
    return result;
}

esp_err_t kf_firmware_policy_reconcile_healthy_running_partition(void)
{
    const esp_partition_t *running = esp_ota_get_running_partition();
    if (running == NULL) {
        return ESP_ERR_INVALID_STATE;
    }

    nvs_handle_t handle;
    esp_err_t result = nvs_open(
        KF_FW_NAMESPACE,
        NVS_READWRITE,
        &handle
    );
    if (result != ESP_OK) {
        return result;
    }

    kf_firmware_policy_state_t state;
    result = read_state_from_handle(handle, &state);
    if (result != ESP_OK || !state.pending) {
        nvs_close(handle);
        return result;
    }

    if (running->address == state.pending_partition_address) {
        result = nvs_set_u64(
            handle,
            KF_FW_ACCEPTED_SEQ_KEY,
            state.pending_sequence
        );
        if (result == ESP_OK) {
            const uint64_t promoted_floor =
                state.pending_rollback_floor_sequence >
                state.rollback_floor_sequence
                    ? state.pending_rollback_floor_sequence
                    : state.rollback_floor_sequence;
            result = nvs_set_u64(
                handle,
                KF_FW_ROLLBACK_FLOOR_KEY,
                promoted_floor
            );
        }
    }

    if (result == ESP_OK) {
        result = erase_pending(handle);
    }
    if (result == ESP_OK) {
        result = nvs_commit(handle);
    }

    nvs_close(handle);
    return result;
}
