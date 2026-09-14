#pragma once

#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    const char *base_path;
    const char *partition_label;
    int max_open_files;
} kf_storage_ro_config_t;

/*
 * Mount a host-generated raw FAT partition read-only.
 *
 * The partition is immutable while mounted. Formatting is never attempted.
 * Exact partition sizing and flash placement are deployment details and are
 * deliberately absent from the Fabric logical identity.
 */
esp_err_t kf_storage_mount_raw_fat_readonly(const kf_storage_ro_config_t *config);

esp_err_t kf_storage_unmount_raw_fat_readonly(const kf_storage_ro_config_t *config);

#ifdef __cplusplus
}
#endif
