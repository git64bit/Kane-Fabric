#include "esp_err.h"
#include "esp_event.h"
#include "esp_log.h"
#include "esp_netif.h"
#include "esp_wifi.h"
#include "kane_fabric_artifact_server.h"
#include "kane_fabric_firmware_lifecycle.h"
#include "kane_fabric_network.h"
#include "kane_fabric_storage.h"

#include <stddef.h>

#ifndef KF_MS5_007_PARTICIPANT_INVENTORY_FILE_SHA256
#error "MS5-007 participant inventory expectation is not defined"
#endif

#ifndef KF_MS5_007_PARTICIPANT_ARTIFACT_SHA256
#error "MS5-007 participant artifact expectation is not defined"
#endif

#ifndef KF_MS5_007_PARTICIPANT_ARTIFACT_SIZE
#error "MS5-007 participant artifact size is not defined"
#endif

static const char *TAG = "kane-fabric-ms5";

static const kf_storage_ro_config_t STORAGE_CONFIG = {
    .base_path = "/fabric",
    .partition_label = "fabric",
    .max_open_files = 4,
};

static const kf_storage_artifact_expectation_t PARTICIPANT_ARTIFACTS[] = {
    {
        .relative_path = "participant.json",
        .byte_length = KF_MS5_007_PARTICIPANT_ARTIFACT_SIZE,
        .sha256_hex = KF_MS5_007_PARTICIPANT_ARTIFACT_SHA256,
    },
};

static const kf_storage_verification_config_t PARTICIPANT_VERIFICATION = {
    .inventory_relative_path = ".kane-fabric-storage-inventory.json",
    .inventory_file_sha256_hex = KF_MS5_007_PARTICIPANT_INVENTORY_FILE_SHA256,
    .artifacts = PARTICIPANT_ARTIFACTS,
    .artifact_count = sizeof(PARTICIPANT_ARTIFACTS) / sizeof(PARTICIPANT_ARTIFACTS[0]),
};

static kf_artifact_server_t ARTIFACT_SERVER;
static httpd_handle_t HTTP_SERVER;

static void provisioning_diagnostic_event_handler(
    void *arg,
    esp_event_base_t event_base,
    int32_t event_id,
    void *event_data
)
{
    (void)arg;

    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_AP_STACONNECTED) {
        const wifi_event_ap_staconnected_t *event =
            (const wifi_event_ap_staconnected_t *)event_data;
        ESP_LOGI(
            TAG,
            "MS5-007 provisioning client associated; aid=%u",
            (unsigned)event->aid
        );
        return;
    }

    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_AP_STADISCONNECTED) {
        const wifi_event_ap_stadisconnected_t *event =
            (const wifi_event_ap_stadisconnected_t *)event_data;
        ESP_LOGI(
            TAG,
            "MS5-007 provisioning client disconnected; aid=%u reason=%u",
            (unsigned)event->aid,
            (unsigned)event->reason
        );
        return;
    }

    if (event_base == IP_EVENT && event_id == IP_EVENT_ASSIGNED_IP_TO_CLIENT) {
        const ip_event_assigned_ip_to_client_t *event =
            (const ip_event_assigned_ip_to_client_t *)event_data;
        ESP_LOGI(
            TAG,
            "MS5-007 provisioning client assigned IPv4=" IPSTR,
            IP2STR(&event->ip)
        );
    }
}

static esp_err_t enable_provisioning_diagnostics(void)
{
    esp_err_t result = esp_event_handler_register(
        WIFI_EVENT,
        WIFI_EVENT_AP_STACONNECTED,
        provisioning_diagnostic_event_handler,
        NULL
    );
    if (result != ESP_OK) {
        return result;
    }

    result = esp_event_handler_register(
        WIFI_EVENT,
        WIFI_EVENT_AP_STADISCONNECTED,
        provisioning_diagnostic_event_handler,
        NULL
    );
    if (result != ESP_OK) {
        return result;
    }

    return esp_event_handler_register(
        IP_EVENT,
        IP_EVENT_ASSIGNED_IP_TO_CLIENT,
        provisioning_diagnostic_event_handler,
        NULL
    );
}

static void unmount_storage(void)
{
    const esp_err_t unmount_result =
        kf_storage_unmount_raw_fat_readonly(&STORAGE_CONFIG);
    if (unmount_result != ESP_OK) {
        ESP_LOGE(
            TAG,
            "MS5-007 cleanup unmount failed: %s",
            esp_err_to_name(unmount_result)
        );
    }
}

static void cleanup_after_http_failure(void)
{
    if (HTTP_SERVER != NULL) {
        const esp_err_t stop_result = httpd_stop(HTTP_SERVER);
        if (stop_result != ESP_OK) {
            ESP_LOGE(
                TAG,
                "MS5-007 HTTP cleanup stop failed: %s",
                esp_err_to_name(stop_result)
            );
        }
        HTTP_SERVER = NULL;
    }

    unmount_storage();
}

void app_main(void)
{
    ESP_LOGI(TAG, "MS5-007 mounting fabric partition read-only");

    esp_err_t result = kf_storage_mount_raw_fat_readonly(&STORAGE_CONFIG);
    if (result != ESP_OK) {
        ESP_LOGE(
            TAG,
            "MS5-007 fabric mount failed closed: %s",
            esp_err_to_name(result)
        );
        return;
    }

    ESP_LOGI(TAG, "MS5-007 fabric partition mounted read-only");

    result = kf_storage_verify_exact_image(
        STORAGE_CONFIG.base_path,
        &PARTICIPANT_VERIFICATION
    );
    if (result != ESP_OK) {
        ESP_LOGE(
            TAG,
            "MS5-007 fabric verification failed closed: %s",
            esp_err_to_name(result)
        );
        unmount_storage();
        return;
    }

    ESP_LOGI(
        TAG,
        "MS5-007 participant image verified; inventory_file_sha256=%s artifacts=%u",
        KF_MS5_007_PARTICIPANT_INVENTORY_FILE_SHA256,
        (unsigned)PARTICIPANT_VERIFICATION.artifact_count
    );

    kf_network_state_t network_state = KF_NETWORK_STATE_NONE;
    result = kf_network_start(&network_state);
    if (result != ESP_OK) {
        ESP_LOGE(
            TAG,
            "MS5-007 deployment network/provisioning failed closed: %s",
            esp_err_to_name(result)
        );
        unmount_storage();
        return;
    }

    if (network_state == KF_NETWORK_STATE_PROVISIONING) {
        result = enable_provisioning_diagnostics();
        if (result != ESP_OK) {
            ESP_LOGE(
                TAG,
                "MS5-007 provisioning diagnostics registration failed: %s",
                esp_err_to_name(result)
            );
        } else {
            ESP_LOGI(TAG, "MS5-007 provisioning client diagnostics enabled");
        }

        unmount_storage();
        ESP_LOGI(
            TAG,
            "MS5-007 local provisioning portal active; artifact HTTP remains disabled"
        );

        result = kf_firmware_lifecycle_confirm_healthy_boot();
        if (result != ESP_OK) {
            ESP_LOGE(
                TAG,
                "MS5-009 provisioning-path firmware confirmation failed: %s",
                esp_err_to_name(result)
            );
        }
        return;
    }

    if (network_state != KF_NETWORK_STATE_READY) {
        ESP_LOGE(TAG, "MS5-007 invalid network state; artifact HTTP remains disabled");
        unmount_storage();
        return;
    }

    httpd_config_t http_config = HTTPD_DEFAULT_CONFIG();
    http_config.uri_match_fn = httpd_uri_match_wildcard;

    result = httpd_start(&HTTP_SERVER, &http_config);
    if (result != ESP_OK) {
        ESP_LOGE(
            TAG,
            "MS5-007 HTTP start failed closed: %s",
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
            "MS5-007 artifact route registration failed closed: %s",
            esp_err_to_name(result)
        );
        cleanup_after_http_failure();
        return;
    }

    ESP_LOGI(
        TAG,
        "MS5-007 HTTP artifact server ready; root=%s port=%u",
        STORAGE_CONFIG.base_path,
        (unsigned)http_config.server_port
    );

    result = kf_firmware_lifecycle_confirm_healthy_boot();
    if (result != ESP_OK) {
        ESP_LOGE(
            TAG,
            "MS5-009 artifact-serving firmware confirmation failed: %s",
            esp_err_to_name(result)
        );
    }
}
