#include "kane_fabric_storage.h"

#include "esp_vfs_fat.h"

#include <stdbool.h>
#include <string.h>

static bool valid_config(const kf_storage_ro_config_t *config)
{
    if (config == NULL || config->base_path == NULL ||
        config->partition_label == NULL) {
        return false;
    }
    const size_t base_len = strlen(config->base_path);
    const size_t label_len = strlen(config->partition_label);
    return base_len >= 2U &&
           config->base_path[0] == '/' &&
           config->base_path[base_len - 1U] != '/' &&
           label_len > 0U &&
           config->max_open_files > 0;
}

esp_err_t kf_storage_mount_raw_fat_readonly(const kf_storage_ro_config_t *config)
{
    if (!valid_config(config)) {
        return ESP_ERR_INVALID_ARG;
    }

    const esp_vfs_fat_mount_config_t mount = {
        .format_if_mount_failed = false,
        .max_files = config->max_open_files,
        .allocation_unit_size = 0,
    };

    /*
     * ESP-IDF v6.0.3 does not expose a read_only field in
     * esp_vfs_fat_mount_config_t. Read-only raw-flash behavior is provided by
     * esp_vfs_fat_spiflash_mount_ro() itself.
     */
    return esp_vfs_fat_spiflash_mount_ro(
        config->base_path,
        config->partition_label,
        &mount
    );
}

esp_err_t kf_storage_unmount_raw_fat_readonly(const kf_storage_ro_config_t *config)
{
    if (!valid_config(config)) {
        return ESP_ERR_INVALID_ARG;
    }
    return esp_vfs_fat_spiflash_unmount_ro(
        config->base_path,
        config->partition_label
    );
}
