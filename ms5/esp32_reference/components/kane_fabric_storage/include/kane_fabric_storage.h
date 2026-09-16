#pragma once

#include "esp_err.h"

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

#define KF_STORAGE_SHA256_HEX_LENGTH 64U

typedef struct {
    const char *base_path;
    const char *partition_label;
    int max_open_files;
} kf_storage_ro_config_t;

typedef struct {
    const char *relative_path;
    size_t byte_length;
    const char *sha256_hex;
} kf_storage_artifact_expectation_t;

typedef struct {
    const char *inventory_relative_path;
    const char *inventory_file_sha256_hex;
    const kf_storage_artifact_expectation_t *artifacts;
    size_t artifact_count;
} kf_storage_verification_config_t;

/*
 * Mount a host-generated raw FAT partition read-only.
 *
 * The partition is immutable while mounted. Formatting is never attempted.
 * Exact partition sizing and flash placement are deployment details and are
 * deliberately absent from the Fabric logical identity.
 */
esp_err_t kf_storage_mount_raw_fat_readonly(const kf_storage_ro_config_t *config);

esp_err_t kf_storage_unmount_raw_fat_readonly(const kf_storage_ro_config_t *config);

/*
 * Verify an already mounted immutable image against trusted expectations.
 *
 * The verification source is deliberately separate from the FAT image being
 * checked. For the MS5-006 physical probe it is supplied by the build. A later
 * activation mechanism may supply the same expectations from trusted local
 * state without changing the filesystem-verification primitive.
 *
 * This function checks the exact inventory-file SHA-256 and every expected
 * artifact's byte length and SHA-256. Any mismatch fails closed.
 */
esp_err_t kf_storage_verify_exact_image(
    const char *base_path,
    const kf_storage_verification_config_t *config
);

#ifdef __cplusplus
}
#endif
