idf_component_register(
    SRCS "kane_fabric_firmware_policy.c"
    INCLUDE_DIRS "include"
    REQUIRES app_update nvs_flash
)
