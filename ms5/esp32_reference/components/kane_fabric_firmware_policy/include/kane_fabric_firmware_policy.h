#pragma once

#include "esp_err.h"

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    uint64_t accepted_sequence;
    uint64_t rollback_floor_sequence;
    bool pending;
    uint64_t pending_sequence;
    uint64_t pending_rollback_floor_sequence;
    uint32_t pending_partition_address;
} kf_firmware_policy_state_t;

esp_err_t kf_firmware_policy_get_state(
    kf_firmware_policy_state_t *state
);

/*
 * Normal-path release policy:
 * - candidate sequence must be strictly newer than the accepted sequence;
 * - rollback floor may never decrease;
 * - candidate sequence must not fall below the current rollback floor.
 */
esp_err_t kf_firmware_policy_check_candidate(
    uint64_t release_sequence,
    uint64_t rollback_floor_sequence
);

/*
 * Record candidate metadata before changing the boot partition. This makes a
 * power loss between policy commit and boot selection recoverable.
 */
esp_err_t kf_firmware_policy_stage_candidate(
    uint64_t release_sequence,
    uint64_t rollback_floor_sequence,
    uint32_t target_partition_address
);

/* Remove a matching pending record if later boot selection fails. */
esp_err_t kf_firmware_policy_cancel_pending(
    uint32_t target_partition_address
);

/*
 * Called only after the current runtime passes its health boundary.
 * If this is the staged target, promote its release state. If the bootloader
 * rolled back to another partition, discard the stale pending record.
 */
esp_err_t kf_firmware_policy_reconcile_healthy_running_partition(void);

#ifdef __cplusplus
}
#endif
