idf_component_register(
    SRCS "kane_fabric_firmware_update.c"
    INCLUDE_DIRS "include"
    REQUIRES app_update esp_partition kane_fabric_firmware_policy log mbedtls
)
