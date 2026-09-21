idf_component_register(
    SRCS "kane_fabric_firmware_lifecycle.c"
    INCLUDE_DIRS "include"
    REQUIRES app_update esp_partition log
)
