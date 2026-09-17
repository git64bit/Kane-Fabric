#include "kane_fabric_network.h"

#include "esp_event.h"
#include "esp_http_server.h"
#include "esp_log.h"
#include "esp_netif.h"
#include "esp_random.h"
#include "esp_system.h"
#include "esp_wifi.h"
#include "freertos/FreeRTOS.h"
#include "freertos/event_groups.h"
#include "freertos/task.h"
#include "nvs.h"
#include "nvs_flash.h"

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define KF_WIFI_NAMESPACE "kane_net"
#define KF_WIFI_SSID_KEY "ssid"
#define KF_WIFI_PASSWORD_KEY "password"
#define KF_SETUP_NAMESPACE "kane_setup"
#define KF_SETUP_PASSWORD_KEY "ap_password"
#define KF_WIFI_CONNECT_TIMEOUT_MS 30000U
#define KF_WIFI_MAX_RETRIES 5
#define KF_WIFI_CONNECTED_BIT BIT0
#define KF_WIFI_FAILED_BIT BIT1
#define KF_PROVISION_SCAN_MAX 20U
#define KF_PROVISION_BODY_MAX 512U
#define KF_SETUP_PASSWORD_LENGTH 12U

static const char *TAG = "kane-fabric-net";
static EventGroupHandle_t WIFI_EVENTS;
static int WIFI_RETRY_COUNT;
static httpd_handle_t PROVISION_HTTP_SERVER;
static wifi_ap_record_t PROVISION_APS[KF_PROVISION_SCAN_MAX];
static uint16_t PROVISION_AP_COUNT;

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

static esp_err_t store_wifi_credentials(
    const char *ssid,
    const char *password
)
{
    if (ssid == NULL || password == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    const size_t ssid_length = strlen(ssid);
    const size_t password_length = strlen(password);
    if (ssid_length == 0U || ssid_length > 32U || password_length > 63U) {
        return ESP_ERR_INVALID_SIZE;
    }

    nvs_handle_t handle;
    esp_err_t result = nvs_open(KF_WIFI_NAMESPACE, NVS_READWRITE, &handle);
    if (result != ESP_OK) {
        return result;
    }

    result = nvs_set_str(handle, KF_WIFI_SSID_KEY, ssid);
    if (result == ESP_OK) {
        result = nvs_set_str(handle, KF_WIFI_PASSWORD_KEY, password);
    }
    if (result == ESP_OK) {
        result = nvs_commit(handle);
    }

    nvs_close(handle);
    return result;
}

static esp_err_t load_or_create_setup_password(
    char *password,
    size_t capacity
)
{
    if (password == NULL || capacity <= KF_SETUP_PASSWORD_LENGTH) {
        return ESP_ERR_INVALID_ARG;
    }

    nvs_handle_t handle;
    esp_err_t result = nvs_open(KF_SETUP_NAMESPACE, NVS_READWRITE, &handle);
    if (result != ESP_OK) {
        return result;
    }

    size_t length = capacity;
    result = nvs_get_str(
        handle,
        KF_SETUP_PASSWORD_KEY,
        password,
        &length
    );
    if (result == ESP_OK) {
        nvs_close(handle);
        return ESP_OK;
    }
    if (result != ESP_ERR_NVS_NOT_FOUND) {
        nvs_close(handle);
        return result;
    }

    static const char alphabet[] =
        "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789";
    const size_t alphabet_length = sizeof(alphabet) - 1U;

    for (size_t i = 0; i < KF_SETUP_PASSWORD_LENGTH; i++) {
        password[i] = alphabet[esp_random() % alphabet_length];
    }
    password[KF_SETUP_PASSWORD_LENGTH] = '\0';

    result = nvs_set_str(handle, KF_SETUP_PASSWORD_KEY, password);
    if (result == ESP_OK) {
        result = nvs_commit(handle);
    }
    nvs_close(handle);
    return result;
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
            ESP_LOGE(TAG, "Wi-Fi connect request failed: %s", esp_err_to_name(result));
            xEventGroupSetBits(WIFI_EVENTS, KF_WIFI_FAILED_BIT);
        }
        return;
    }

    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
        if (WIFI_RETRY_COUNT < KF_WIFI_MAX_RETRIES) {
            WIFI_RETRY_COUNT++;
            ESP_LOGW(
                TAG,
                "Wi-Fi disconnected; reconnect attempt %d/%d",
                WIFI_RETRY_COUNT,
                KF_WIFI_MAX_RETRIES
            );
            const esp_err_t result = esp_wifi_connect();
            if (result != ESP_OK) {
                ESP_LOGE(TAG, "Wi-Fi reconnect request failed: %s", esp_err_to_name(result));
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
        ESP_LOGI(TAG, "Wi-Fi client acquired IPv4=" IPSTR, IP2STR(&event->ip_info.ip));
        xEventGroupSetBits(WIFI_EVENTS, KF_WIFI_CONNECTED_BIT);
    }
}

static esp_err_t wifi_station_connect(
    const char *ssid,
    const char *password
)
{
    WIFI_EVENTS = xEventGroupCreate();
    if (WIFI_EVENTS == NULL) {
        return ESP_ERR_NO_MEM;
    }

    esp_netif_t *station = esp_netif_create_default_wifi_sta();
    if (station == NULL) {
        return ESP_FAIL;
    }

    wifi_init_config_t init_config = WIFI_INIT_CONFIG_DEFAULT();
    esp_err_t result = esp_wifi_init(&init_config);
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

    ESP_LOGI(TAG, "Wi-Fi station started; awaiting DHCP");

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

static bool html_escape(
    const char *source,
    size_t source_length,
    char *destination,
    size_t destination_capacity
)
{
    if (source == NULL || destination == NULL || destination_capacity == 0U) {
        return false;
    }

    size_t out = 0U;
    for (size_t i = 0U; i < source_length; i++) {
        const char *replacement = NULL;
        switch (source[i]) {
            case '&': replacement = "&amp;"; break;
            case '<': replacement = "&lt;"; break;
            case '>': replacement = "&gt;"; break;
            case '"': replacement = "&quot;"; break;
            case '\'': replacement = "&#39;"; break;
            default: break;
        }

        if (replacement != NULL) {
            const size_t replacement_length = strlen(replacement);
            if (out + replacement_length + 1U > destination_capacity) {
                return false;
            }
            memcpy(destination + out, replacement, replacement_length);
            out += replacement_length;
        } else {
            if (out + 2U > destination_capacity) {
                return false;
            }
            destination[out++] = source[i];
        }
    }

    destination[out] = '\0';
    return true;
}

static int hex_value(char value)
{
    if (value >= '0' && value <= '9') {
        return value - '0';
    }
    if (value >= 'a' && value <= 'f') {
        return value - 'a' + 10;
    }
    if (value >= 'A' && value <= 'F') {
        return value - 'A' + 10;
    }
    return -1;
}

static bool url_decode(
    const char *source,
    char *destination,
    size_t destination_capacity
)
{
    if (source == NULL || destination == NULL || destination_capacity == 0U) {
        return false;
    }

    size_t out = 0U;
    for (size_t i = 0U; source[i] != '\0'; i++) {
        unsigned char decoded;
        if (source[i] == '+') {
            decoded = (unsigned char)' ';
        } else if (source[i] == '%') {
            const int high = hex_value(source[i + 1U]);
            const int low = high < 0 ? -1 : hex_value(source[i + 2U]);
            if (high < 0 || low < 0) {
                return false;
            }
            decoded = (unsigned char)((high << 4) | low);
            i += 2U;
        } else {
            decoded = (unsigned char)source[i];
        }

        if (decoded == 0U || out + 2U > destination_capacity) {
            return false;
        }
        destination[out++] = (char)decoded;
    }

    destination[out] = '\0';
    return true;
}

static esp_err_t provisioning_get_handler(httpd_req_t *req)
{
    static const char page_start[] =
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        "<title>Kane Fabric Setup</title></head><body>"
        "<h1>Kane Fabric Setup</h1>"
        "<p>This local page configures the deployment Wi-Fi network. "
        "No account or external service is required.</p>"
        "<form method=\"post\" action=\"/provision\">"
        "<label>Wi-Fi network<br><input name=\"ssid\" list=\"networks\" "
        "maxlength=\"32\" required autocomplete=\"off\"></label>"
        "<datalist id=\"networks\">";
    static const char page_end[] =
        "</datalist><br><br>"
        "<label>Wi-Fi password<br><input name=\"password\" type=\"password\" "
        "maxlength=\"63\" autocomplete=\"new-password\"></label>"
        "<br><br><button type=\"submit\">Save and connect</button>"
        "</form></body></html>";

    httpd_resp_set_type(req, "text/html; charset=utf-8");
    httpd_resp_set_hdr(req, "Cache-Control", "no-store");

    esp_err_t result = httpd_resp_send_chunk(req, page_start, HTTPD_RESP_USE_STRLEN);
    if (result != ESP_OK) {
        return result;
    }

    for (uint16_t i = 0U; i < PROVISION_AP_COUNT; i++) {
        const char *ssid = (const char *)PROVISION_APS[i].ssid;
        const size_t ssid_length = strnlen(ssid, sizeof(PROVISION_APS[i].ssid));
        if (ssid_length == 0U) {
            continue;
        }

        char escaped[257];
        if (!html_escape(ssid, ssid_length, escaped, sizeof(escaped))) {
            continue;
        }

        char option[320];
        const int count = snprintf(
            option,
            sizeof(option),
            "<option value=\"%s\"></option>",
            escaped
        );
        if (count < 0 || (size_t)count >= sizeof(option)) {
            continue;
        }

        result = httpd_resp_send_chunk(req, option, (size_t)count);
        if (result != ESP_OK) {
            return result;
        }
    }

    result = httpd_resp_send_chunk(req, page_end, HTTPD_RESP_USE_STRLEN);
    if (result != ESP_OK) {
        return result;
    }
    return httpd_resp_send_chunk(req, NULL, 0U);
}

static esp_err_t send_form_error(httpd_req_t *req, const char *message)
{
    httpd_resp_set_status(req, "400 Bad Request");
    httpd_resp_set_type(req, "text/plain; charset=utf-8");
    httpd_resp_set_hdr(req, "Cache-Control", "no-store");
    return httpd_resp_sendstr(req, message);
}

static esp_err_t provisioning_post_handler(httpd_req_t *req)
{
    if (req->content_len <= 0 || (size_t)req->content_len >= KF_PROVISION_BODY_MAX) {
        return send_form_error(req, "Invalid provisioning form size.\n");
    }

    char body[KF_PROVISION_BODY_MAX];
    size_t total = 0U;
    while (total < (size_t)req->content_len) {
        const int received = httpd_req_recv(
            req,
            body + total,
            (size_t)req->content_len - total
        );
        if (received == HTTPD_SOCK_ERR_TIMEOUT) {
            continue;
        }
        if (received <= 0) {
            return ESP_FAIL;
        }
        total += (size_t)received;
    }
    body[total] = '\0';

    char ssid[33] = {0};
    char password[64] = {0};
    bool have_ssid = false;
    bool have_password = false;

    char *save = NULL;
    for (char *field = strtok_r(body, "&", &save);
         field != NULL;
         field = strtok_r(NULL, "&", &save)) {
        char *equals = strchr(field, '=');
        if (equals == NULL) {
            continue;
        }
        *equals = '\0';
        const char *value = equals + 1;

        if (strcmp(field, "ssid") == 0) {
            have_ssid = url_decode(value, ssid, sizeof(ssid));
            if (!have_ssid) {
                return send_form_error(req, "Invalid SSID encoding.\n");
            }
        } else if (strcmp(field, "password") == 0) {
            have_password = url_decode(value, password, sizeof(password));
            if (!have_password) {
                return send_form_error(req, "Invalid password encoding.\n");
            }
        }
    }

    if (!have_ssid || ssid[0] == '\0') {
        return send_form_error(req, "Wi-Fi SSID is required.\n");
    }
    if (!have_password) {
        password[0] = '\0';
    }

    const esp_err_t result = store_wifi_credentials(ssid, password);
    if (result != ESP_OK) {
        ESP_LOGE(TAG, "Provisioning NVS write failed: %s", esp_err_to_name(result));
        httpd_resp_set_status(req, "500 Internal Server Error");
        httpd_resp_set_type(req, "text/plain; charset=utf-8");
        return httpd_resp_sendstr(req, "Could not save network configuration.\n");
    }

    ESP_LOGI(TAG, "Deployment Wi-Fi configuration saved; rebooting into station mode");
    httpd_resp_set_type(req, "text/html; charset=utf-8");
    httpd_resp_set_hdr(req, "Cache-Control", "no-store");
    esp_err_t send_result = httpd_resp_sendstr(
        req,
        "<!doctype html><html><body><h1>Configuration saved</h1>"
        "<p>The appliance is rebooting and will join the selected network.</p>"
        "</body></html>"
    );

    vTaskDelay(pdMS_TO_TICKS(750U));
    esp_restart();
    return send_result;
}

static esp_err_t start_provisioning_portal(void)
{
    esp_netif_t *ap = esp_netif_create_default_wifi_ap();
    if (ap == NULL) {
        return ESP_FAIL;
    }
    if (esp_netif_create_default_wifi_sta() == NULL) {
        return ESP_FAIL;
    }

    wifi_init_config_t init_config = WIFI_INIT_CONFIG_DEFAULT();
    esp_err_t result = esp_wifi_init(&init_config);
    if (result != ESP_OK) {
        return result;
    }

    result = esp_wifi_set_mode(WIFI_MODE_APSTA);
    if (result != ESP_OK) {
        return result;
    }

    uint8_t mac[6] = {0};
    result = esp_wifi_get_mac(WIFI_IF_AP, mac);
    if (result != ESP_OK) {
        return result;
    }

    char setup_password[KF_SETUP_PASSWORD_LENGTH + 1U] = {0};
    result = load_or_create_setup_password(
        setup_password,
        sizeof(setup_password)
    );
    if (result != ESP_OK) {
        return result;
    }

    char setup_ssid[33] = {0};
    const int ssid_count = snprintf(
        setup_ssid,
        sizeof(setup_ssid),
        "Kane-Fabric-Setup-%02X%02X%02X",
        mac[3],
        mac[4],
        mac[5]
    );
    if (ssid_count < 0 || (size_t)ssid_count >= sizeof(setup_ssid)) {
        return ESP_ERR_INVALID_SIZE;
    }

    wifi_config_t ap_config = {0};
    memcpy(ap_config.ap.ssid, setup_ssid, (size_t)ssid_count);
    ap_config.ap.ssid_len = (uint8_t)ssid_count;
    memcpy(
        ap_config.ap.password,
        setup_password,
        KF_SETUP_PASSWORD_LENGTH
    );
    ap_config.ap.channel = 1U;
    ap_config.ap.max_connection = 4U;
    ap_config.ap.authmode = WIFI_AUTH_WPA2_PSK;

    result = esp_wifi_set_config(WIFI_IF_AP, &ap_config);
    if (result != ESP_OK) {
        return result;
    }

    result = esp_wifi_start();
    if (result != ESP_OK) {
        return result;
    }

    PROVISION_AP_COUNT = KF_PROVISION_SCAN_MAX;
    result = esp_wifi_scan_start(NULL, true);
    if (result == ESP_OK) {
        uint16_t count = PROVISION_AP_COUNT;
        result = esp_wifi_scan_get_ap_records(&count, PROVISION_APS);
        if (result == ESP_OK) {
            PROVISION_AP_COUNT = count;
        } else {
            PROVISION_AP_COUNT = 0U;
            ESP_LOGW(TAG, "Wi-Fi scan result retrieval failed: %s", esp_err_to_name(result));
        }
    } else {
        PROVISION_AP_COUNT = 0U;
        ESP_LOGW(TAG, "Wi-Fi scan failed: %s", esp_err_to_name(result));
    }

    httpd_config_t http_config = HTTPD_DEFAULT_CONFIG();
    http_config.uri_match_fn = httpd_uri_match_wildcard;

    result = httpd_start(&PROVISION_HTTP_SERVER, &http_config);
    if (result != ESP_OK) {
        return result;
    }

    const httpd_uri_t provision_route = {
        .uri = "/provision",
        .method = HTTP_POST,
        .handler = provisioning_post_handler,
        .user_ctx = NULL,
    };
    result = httpd_register_uri_handler(PROVISION_HTTP_SERVER, &provision_route);
    if (result != ESP_OK) {
        return result;
    }

    const httpd_uri_t page_route = {
        .uri = "/*",
        .method = HTTP_GET,
        .handler = provisioning_get_handler,
        .user_ctx = NULL,
    };
    result = httpd_register_uri_handler(PROVISION_HTTP_SERVER, &page_route);
    if (result != ESP_OK) {
        return result;
    }

    esp_netif_ip_info_t ip_info = {0};
    result = esp_netif_get_ip_info(ap, &ip_info);
    if (result != ESP_OK) {
        return result;
    }

    ESP_LOGI(TAG, "Local provisioning mode active");
    ESP_LOGI(TAG, "Provisioning SSID=%s", setup_ssid);
    ESP_LOGI(TAG, "Provisioning WPA2 password=%s", setup_password);
    ESP_LOGI(TAG, "Provisioning URL=http://" IPSTR "/", IP2STR(&ip_info.ip));
    ESP_LOGI(TAG, "Provisioning is local-only; no account or external service is used");
    return ESP_OK;
}

esp_err_t kf_network_start(kf_network_state_t *state)
{
    if (state == NULL) {
        return ESP_ERR_INVALID_ARG;
    }
    *state = KF_NETWORK_STATE_NONE;

    esp_err_t result = nvs_flash_init();
    if (result != ESP_OK) {
        return result;
    }

    result = esp_netif_init();
    if (result != ESP_OK) {
        return result;
    }

    result = esp_event_loop_create_default();
    if (result != ESP_OK) {
        return result;
    }

    char ssid[33] = {0};
    char password[65] = {0};
    result = read_wifi_credentials(
        ssid,
        sizeof(ssid),
        password,
        sizeof(password)
    );

    if (result == ESP_ERR_NVS_NOT_FOUND) {
        result = start_provisioning_portal();
        if (result == ESP_OK) {
            *state = KF_NETWORK_STATE_PROVISIONING;
        }
        return result;
    }
    if (result != ESP_OK) {
        return result;
    }

    result = wifi_station_connect(ssid, password);
    if (result != ESP_OK) {
        return result;
    }

    *state = KF_NETWORK_STATE_READY;
    return ESP_OK;
}
