#include "esp_err.h"
#include "esp_event.h"
#include "esp_log.h"
#include "esp_netif.h"
#include "kane_fabric_artifact_server.h"
#include "kane_fabric_storage.h"

#include <stddef.h>

#ifndef KF_MS5_006_PROBE_INVENTORY_FILE_SHA256
#error "MS5-006 probe inventory expectation is not defined"
#endif

#ifndef KF_MS5_006_PROBE_ARTIFACT_SHA256
#error "MS5-006 probe artifact expectation is not defined"
#endif

#ifndef KF_MS5_006_PROBE_ARTIFACT_SIZE
#error "MS5-006 probe artifact size is not defined"
#endif

static const char *TAG = "kane-fabric-ms5";

static const kf_storage_ro_config_t STORAGE_CONFIG = {
    .base_path = "/fabric",
    .partition_label = "fabric",
    .max_open_files = 4,
};

static const kf_storage_artifact_expectation_t PROBE_ARTIFACTS[] = {
    {
        .relative_path = "probe.txt",
        .byte_length = KF_MS5_006_PROBE_ARTIFACT_SIZE,
        .sha256_hex = KF_MS5_006_PROBE_ARTIFACT_SHA256,
    },
};

static const kf_storage_verification_config_t PROBE_VERIFICATION = {
    .inventory_relative_path = ".kane-fabric-storage-inventory.json",
    .inventory_file_sha256_hex = KF_MS5_006_PROBE_INVENTORY_FILE_SHA256,
    .artifacts = PROBE_ARTIFACTS,
    .artifact_count = sizeof(PROBE_ARTIFACTS) / sizeof(PROBE_ARTIFACTS[0]),
};

static kf_artifact_server_t ARTIFACT_SERVER;
static httpd_handle_t HTTP_SERVER;

static void cleanup_after_http_failure(void)
{
    if (HTTP_SERVER != NULL) {
        const esp_err_t stop_result = httpd_stop(HTTP_SERVER);
        if (stop_result != ESP_OK) {
            ESP_LOGE(
                TAG,
                "MS5-006 HTTP cleanup stop failed: %s",
                esp_err_to_name(stop_result)
            );
        }
        HTTP_SERVER = NULL;
    }

    const esp_err_t unmount_result =
        kf_storage_unmount_raw_fat_readonly(&STORAGE_CONFIG);
    if (unmount_result != ESP_OK) {
        ESP_LOGE(
            TAG,
            "MS5-006 cleanup unmount failed: %s",
            esp_err_to_name(unmount_result)
        );
    }
}

void app_main(void)
{
    ESP_LOGI(TAG, "MS5-006 mounting fabric partition read-only");

    esp_err_t result = kf_storage_mount_raw_fat_readonly(&STORAGE_CONFIG);
    if (result != ESP_OK) {
        ESP_LOGE(
            TAG,
            "MS5-006 fabric mount failed closed: %s",
            esp_err_to_name(result)
        );
        return;
    }

    ESP_LOGI(TAG, "MS5-006 fabric partition mounted read-only");

    result = kf_storage_verify_exact_image(
        STORAGE_CONFIG.base_path,
        &PROBE_VERIFICATION
    );
    if (result != ESP_OK) {
        ESP_LOGE(
            TAG,
            "MS5-006 fabric verification failed closed: %s",
            esp_err_to_name(result)
        );
        const esp_err_t unmount_result =
            kf_storage_unmount_raw_fat_readonly(&STORAGE_CONFIG);
        if (unmount_result != ESP_OK) {
            ESP_LOGE(
                TAG,
                "MS5-006 cleanup unmount failed: %s",
                esp_err_to_name(unmount_result)
            );
        }
        return;
    }

    ESP_LOGI(
        TAG,
        "MS5-006 probe image verified; inventory_file_sha256=%s artifacts=%u",
        KF_MS5_006_PROBE_INVENTORY_FILE_SHA256,
        (unsigned)PROBE_VERIFICATION.artifact_count
    );

    result = esp_netif_init();
    if (result != ESP_OK) {
        ESP_LOGE(
            TAG,
            "MS5-006 network stack init failed closed: %s",
            esp_err_to_name(result)
        );
        cleanup_after_http_failure();
        return;
    }

    result = esp_event_loop_create_default();
    if (result != ESP_OK) {
        ESP_LOGE(
            TAG,
            "MS5-006 default event loop init failed closed: %s",
            esp_err_to_name(result)
        );
        cleanup_after_http_failure();
        return;
    }

    ESP_LOGI(TAG, "MS5-006 ESP-IDF network runtime initialized");

    httpd_config_t http_config = HTTPD_DEFAULT_CONFIG();
    http_config.uri_match_fn = httpd_uri_match_wildcard;

    result = httpd_start(&HTTP_SERVER, &http_config);
    if (result != ESP_OK) {
        ESP_LOGE(
            TAG,
            "MS5-006 HTTP start failed closed: %s",
            esp_err_to_name(result)
        );
        cleanup_after_http_failure();
        return;
    }

    const kf_artifact_server_config_t artifact_config = {
        .root_path = STORAGE_CONFIG.base_path,
    };

    result = kf_artifact_server_register(
        HTTP_SERVER,
        &ARTIFACT_SERVER,
        &artifact_config
    );
    if (result != ESP_OK) {
        ESP_LOGE(
            TAG,
            "MS5-006 artifact route registration failed closed: %s",
            esp_err_to_name(result)
        );
        cleanup_after_http_failure();
        return;
    }

    ESP_LOGI(
        TAG,
        "MS5-006 HTTP artifact server ready; root=%s port=%u",
        STORAGE_CONFIG.base_path,
        (unsigned)http_config.server_port
    );
}
