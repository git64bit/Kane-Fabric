idf_component_register(
    SRCS "kane_fabric_firmware_install.c"
    INCLUDE_DIRS "include"
    REQUIRES
        kane_fabric_firmware_authorization
        kane_fabric_firmware_update
)
