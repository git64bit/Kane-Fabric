#include "kane_fabric_storage.h"

#include "esp_vfs_fat.h"
#include "psa/crypto.h"

#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define KF_STORAGE_VERIFY_BUFFER_SIZE 1024U
#define KF_STORAGE_PATH_MAX 512U
#define KF_SHA256_BYTES 32U

static bool valid_base_path(const char *base_path)
{
    if (base_path == NULL) {
        return false;
    }
    const size_t base_len = strlen(base_path);
    return base_len >= 2U &&
           base_path[0] == '/' &&
           base_path[base_len - 1U] != '/';
}

static bool valid_config(const kf_storage_ro_config_t *config)
{
    if (config == NULL || config->partition_label == NULL) {
        return false;
    }
    const size_t label_len = strlen(config->partition_label);
    return valid_base_path(config->base_path) &&
           label_len > 0U &&
           config->max_open_files > 0;
}

static bool valid_sha256_hex(const char *value)
{
    if (value == NULL || strlen(value) != KF_STORAGE_SHA256_HEX_LENGTH) {
        return false;
    }
    for (size_t i = 0; i < KF_STORAGE_SHA256_HEX_LENGTH; ++i) {
        const char c = value[i];
        if (!((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f'))) {
            return false;
        }
    }
    return true;
}

static bool valid_relative_path(const char *path)
{
    if (path == NULL || path[0] == '\0' || path[0] == '/') {
        return false;
    }

    const char *segment = path;
    size_t segment_len = 0U;
    for (const char *cursor = path;; ++cursor) {
        if (*cursor == '\\') {
            return false;
        }
        if (*cursor == '/' || *cursor == '\0') {
            if (segment_len == 0U ||
                (segment_len == 1U && segment[0] == '.') ||
                (segment_len == 2U && segment[0] == '.' && segment[1] == '.')) {
                return false;
            }
            if (*cursor == '\0') {
                return true;
            }
            segment = cursor + 1;
            segment_len = 0U;
        } else {
            ++segment_len;
        }
    }
}

static bool valid_verification_config(
    const char *base_path,
    const kf_storage_verification_config_t *config
)
{
    if (!valid_base_path(base_path) || config == NULL ||
        !valid_relative_path(config->inventory_relative_path) ||
        !valid_sha256_hex(config->inventory_file_sha256_hex) ||
        config->artifacts == NULL || config->artifact_count == 0U) {
        return false;
    }

    for (size_t i = 0; i < config->artifact_count; ++i) {
        const kf_storage_artifact_expectation_t *artifact = &config->artifacts[i];
        if (!valid_relative_path(artifact->relative_path) ||
            !valid_sha256_hex(artifact->sha256_hex)) {
            return false;
        }
        if (strcmp(config->inventory_relative_path, artifact->relative_path) == 0) {
            return false;
        }
        for (size_t j = 0; j < i; ++j) {
            if (strcmp(config->artifacts[j].relative_path, artifact->relative_path) == 0) {
                return false;
            }
        }
    }
    return true;
}

static esp_err_t join_path(
    const char *base_path,
    const char *relative_path,
    char output[KF_STORAGE_PATH_MAX]
)
{
    const int written = snprintf(
        output,
        KF_STORAGE_PATH_MAX,
        "%s/%s",
        base_path,
        relative_path
    );
    if (written < 0 || (size_t)written >= KF_STORAGE_PATH_MAX) {
        return ESP_ERR_INVALID_SIZE;
    }
    return ESP_OK;
}

static void digest_to_hex(
    const uint8_t digest[KF_SHA256_BYTES],
    char output[KF_STORAGE_SHA256_HEX_LENGTH + 1U]
)
{
    static const char digits[] = "0123456789abcdef";
    for (size_t i = 0; i < KF_SHA256_BYTES; ++i) {
        output[i * 2U] = digits[digest[i] >> 4U];
        output[i * 2U + 1U] = digits[digest[i] & 0x0fU];
    }
    output[KF_STORAGE_SHA256_HEX_LENGTH] = '\0';
}

static esp_err_t sha256_file(
    const char *path,
    size_t *byte_length,
    char digest_hex[KF_STORAGE_SHA256_HEX_LENGTH + 1U]
)
{
    FILE *file = fopen(path, "rb");
    if (file == NULL) {
        return ESP_ERR_NOT_FOUND;
    }

    psa_hash_operation_t operation = PSA_HASH_OPERATION_INIT;
    psa_status_t status = psa_hash_setup(&operation, PSA_ALG_SHA_256);
    if (status != PSA_SUCCESS) {
        fclose(file);
        psa_hash_abort(&operation);
        return ESP_FAIL;
    }

    uint8_t buffer[KF_STORAGE_VERIFY_BUFFER_SIZE];
    size_t total = 0U;
    esp_err_t result = ESP_OK;

    for (;;) {
        const size_t count = fread(buffer, 1U, sizeof(buffer), file);
        if (count > 0U) {
            if (SIZE_MAX - total < count) {
                result = ESP_ERR_INVALID_SIZE;
                break;
            }
            total += count;
            status = psa_hash_update(&operation, buffer, count);
            if (status != PSA_SUCCESS) {
                result = ESP_FAIL;
                break;
            }
        }
        if (count < sizeof(buffer)) {
            if (ferror(file)) {
                result = ESP_FAIL;
            }
            break;
        }
    }

    if (result == ESP_OK) {
        uint8_t digest[KF_SHA256_BYTES];
        size_t digest_length = 0U;
        status = psa_hash_finish(
            &operation,
            digest,
            sizeof(digest),
            &digest_length
        );
        if (status != PSA_SUCCESS || digest_length != sizeof(digest)) {
            result = ESP_FAIL;
        } else {
            digest_to_hex(digest, digest_hex);
            *byte_length = total;
        }
    }

    psa_hash_abort(&operation);
    fclose(file);
    return result;
}

static esp_err_t verify_file(
    const char *base_path,
    const char *relative_path,
    const char *expected_sha256_hex,
    bool check_length,
    size_t expected_length
)
{
    char path[KF_STORAGE_PATH_MAX];
    esp_err_t result = join_path(base_path, relative_path, path);
    if (result != ESP_OK) {
        return result;
    }

    size_t actual_length = 0U;
    char actual_sha256[KF_STORAGE_SHA256_HEX_LENGTH + 1U];
    result = sha256_file(path, &actual_length, actual_sha256);
    if (result != ESP_OK) {
        return result;
    }

    if ((check_length && actual_length != expected_length) ||
        strcmp(actual_sha256, expected_sha256_hex) != 0) {
        return ESP_ERR_INVALID_STATE;
    }
    return ESP_OK;
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

esp_err_t kf_storage_verify_exact_image(
    const char *base_path,
    const kf_storage_verification_config_t *config
)
{
    if (!valid_verification_config(base_path, config)) {
        return ESP_ERR_INVALID_ARG;
    }

    const psa_status_t init_status = psa_crypto_init();
    if (init_status != PSA_SUCCESS) {
        return ESP_FAIL;
    }

    esp_err_t result = verify_file(
        base_path,
        config->inventory_relative_path,
        config->inventory_file_sha256_hex,
        false,
        0U
    );
    if (result != ESP_OK) {
        return result;
    }

    for (size_t i = 0; i < config->artifact_count; ++i) {
        const kf_storage_artifact_expectation_t *artifact = &config->artifacts[i];
        result = verify_file(
            base_path,
            artifact->relative_path,
            artifact->sha256_hex,
            true,
            artifact->byte_length
        );
        if (result != ESP_OK) {
            return result;
        }
    }

    return ESP_OK;
}
