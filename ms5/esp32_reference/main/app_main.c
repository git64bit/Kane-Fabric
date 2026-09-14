#include "esp_log.h"
#include "kane_fabric_artifact_server.h"
#include "kane_fabric_storage.h"

static const char *TAG = "kane-fabric-ms5";

void app_main(void)
{
    /*
     * MS5-006 build probe only.
     *
     * Storage mount selection, browser-trusted HTTPS server startup, and
     * Wi-Fi AP/STA provisioning are deployment/runtime integration work.
     * The immutable storage and artifact-serving components are linked here
     * so the pinned ESP-IDF build gate compiles the actual reference code.
     */
    ESP_LOGI(TAG, "MS5-006 storage/range components linked");
}
