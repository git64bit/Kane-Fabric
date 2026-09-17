idf_component_register(
    SRCS "kane_fabric_network.c"
    INCLUDE_DIRS "include"
    REQUIRES esp_event esp_http_server esp_netif esp_system esp_wifi nvs_flash
)
