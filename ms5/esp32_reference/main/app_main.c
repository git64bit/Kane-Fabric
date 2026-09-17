#include "esp_err.h"
#include "esp_event.h"
#include "esp_log.h"
#include "esp_netif.h"
#include "esp_wifi.h"
#include "freertos/FreeRTOS.h"
#include "freertos/event_groups.h"
#include "kane_fabric_artifact_server.h"
#include "kane_fabric_storage.h"
#include "nvs.h"
#include "nvs_flash.h"

#include <stddef.h>
#include <stdint.h>
#include <string.h>

#ifndef KF_MS5_006_PROBE_INVENTORY_FILE_SHA256
#error "MS5-006 probe inventory expectation is not defined"
#endif

#ifndef KF_MS5_006_PROBE_ARTIFACT_SHA256
#error "MS5-006 probe artifact expectation is not defined"
#endif

#ifndef KF_MS5_006_PROBE_ARTIFACT_SIZE
#error "MS5-006 probe artifact size is not defined"
#endif

#define KF_WIFI_NAMESPACE "kane_net"
#define KF_WIFI_SSID_KEY "ssid"
#define KF_WIFI_PASSWORD_KEY "password"
#define KF_WIFI_CONNECT_TIMEOUT_MS 30000U
#define KF_WIFI_MAX_RETRIES 5
#define KF_WIFI_CONNECTED_BIT BIT0
#define KF_WIFI_FAILED_BIT BIT1

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
static EventGroupHandle_t WIFI_EVENTS;
static int WIFI_RETRY_COUNT;

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

static esp_err_t read_wifi_credentials(
    char *ssid,
    size_t ssid_capacity,
    char *password,
    size_t password_capacity
)
{
    if (ssid == NULL || ssid_capacity < 2U ||
        password == NULL || password_capacity < 1U) {
        return ESP_ERR_INVALID_ARG;
    }

    nvs_handle_t handle;
    esp_err_t result = nvs_open(KF_WIFI_NAMESPACE, NVS_READONLY, &handle);
    if (result != ESP_OK) {
        return result;
    }

    size_t ssid_length = ssid_capacity;
    result = nvs_get_str(handle, KF_WIFI_SSID_KEY, ssid, &ssid_length);
    if (result != ESP_OK) {
        nvs_close(handle);
        return result;
    }

    if (ssid_length < 2U || ssid_length > ssid_capacity) {
        nvs_close(handle);
        return ESP_ERR_INVALID_SIZE;
    }

    size_t password_length = password_capacity;
    result = nvs_get_str(
        handle,
        KF_WIFI_PASSWORD_KEY,
        password,
        &password_length
    );
    nvs_close(handle);

    if (result == ESP_ERR_NVS_NOT_FOUND) {
        password[0] = '\0';
        return ESP_OK;
    }
    if (result != ESP_OK) {
        return result;
    }
    if (password_length > password_capacity) {
        return ESP_ERR_INVALID_SIZE;
    }

    return ESP_OK;
}

static void wifi_event_handler(
    void *arg,
    esp_event_base_t event_base,
    int32_t event_id,
    void *event_data
)
{
    (void)arg;

    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        const esp_err_t result = esp_wifi_connect();
        if (result != ESP_OK) {
            ESP_LOGE(TAG, "MS5-006 Wi-Fi connect request failed: %s", esp_err_to_name(result));
            xEventGroupSetBits(WIFI_EVENTS, KF_WIFI_FAILED_BIT);
        }
        return;
    }

    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
        if (WIFI_RETRY_COUNT < KF_WIFI_MAX_RETRIES) {
            WIFI_RETRY_COUNT++;
            ESP_LOGW(
                TAG,
                "MS5-006 Wi-Fi disconnected; reconnect attempt %d/%d",
                WIFI_RETRY_COUNT,
                KF_WIFI_MAX_RETRIES
            );
            const esp_err_t result = esp_wifi_connect();
            if (result != ESP_OK) {
                ESP_LOGE(TAG, "MS5-006 Wi-Fi reconnect request failed: %s", esp_err_to_name(result));
                xEventGroupSetBits(WIFI_EVENTS, KF_WIFI_FAILED_BIT);
            }
        } else {
            xEventGroupSetBits(WIFI_EVENTS, KF_WIFI_FAILED_BIT);
        }
        return;
    }

    if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        const ip_event_got_ip_t *event = (const ip_event_got_ip_t *)event_data;
        WIFI_RETRY_COUNT = 0;
        ESP_LOGI(
            TAG,
            "MS5-006 Wi-Fi client acquired IPv4=" IPSTR,
            IP2STR(&event->ip_info.ip)
        );
        xEventGroupSetBits(WIFI_EVENTS, KF_WIFI_CONNECTED_BIT);
    }
}

static esp_err_t wifi_station_connect_from_nvs(void)
{
    char ssid[33] = {0};
    char password[65] = {0};

    esp_err_t result = nvs_flash_init();
    if (result != ESP_OK) {
        return result;
    }

    result = read_wifi_credentials(
        ssid,
        sizeof(ssid),
        password,
        sizeof(password)
    );
    if (result != ESP_OK) {
        return result;
    }

    WIFI_EVENTS = xEventGroupCreate();
    if (WIFI_EVENTS == NULL) {
        return ESP_ERR_NO_MEM;
    }

    esp_netif_t *station = esp_netif_create_default_wifi_sta();
    if (station == NULL) {
        return ESP_FAIL;
    }

    wifi_init_config_t init_config = WIFI_INIT_CONFIG_DEFAULT();
    result = esp_wifi_init(&init_config);
    if (result != ESP_OK) {
        return result;
    }

    result = esp_event_handler_register(
        WIFI_EVENT,
        ESP_EVENT_ANY_ID,
        &wifi_event_handler,
        NULL
    );
    if (result != ESP_OK) {
        return result;
    }

    result = esp_event_handler_register(
        IP_EVENT,
        IP_EVENT_STA_GOT_IP,
        &wifi_event_handler,
        NULL
    );
    if (result != ESP_OK) {
        return result;
    }

    wifi_config_t wifi_config = {0};
    const size_t ssid_length = strlen(ssid);
    const size_t password_length = strlen(password);

    if (ssid_length > sizeof(wifi_config.sta.ssid) ||
        password_length > sizeof(wifi_config.sta.password)) {
        return ESP_ERR_INVALID_SIZE;
    }

    memcpy(wifi_config.sta.ssid, ssid, ssid_length);
    memcpy(wifi_config.sta.password, password, password_length);

    result = esp_wifi_set_mode(WIFI_MODE_STA);
    if (result != ESP_OK) {
        return result;
    }

    result = esp_wifi_set_config(WIFI_IF_STA, &wifi_config);
    if (result != ESP_OK) {
        return result;
    }

    WIFI_RETRY_COUNT = 0;
    result = esp_wifi_start();
    if (result != ESP_OK) {
        return result;
    }

    ESP_LOGI(TAG, "MS5-006 Wi-Fi station started; awaiting DHCP");

    const EventBits_t bits = xEventGroupWaitBits(
        WIFI_EVENTS,
        KF_WIFI_CONNECTED_BIT | KF_WIFI_FAILED_BIT,
        pdFALSE,
        pdFALSE,
        pdMS_TO_TICKS(KF_WIFI_CONNECT_TIMEOUT_MS)
    );

    if ((bits & KF_WIFI_CONNECTED_BIT) != 0U) {
        return ESP_OK;
    }
    if ((bits & KF_WIFI_FAILED_BIT) != 0U) {
        return ESP_FAIL;
    }
    return ESP_ERR_TIMEOUT;
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

    result = wifi_station_connect_from_nvs();
    if (result != ESP_OK) {
        ESP_LOGE(
            TAG,
            "MS5-006 deployment network attachment failed closed: %s",
            esp_err_to_name(result)
        );
        cleanup_after_http_failure();
        return;
    }

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
