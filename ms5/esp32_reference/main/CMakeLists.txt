idf_component_register(
    SRCS "app_main.c"
    REQUIRES log kane_fabric_artifact_server kane_fabric_storage
)

# MS5-006 physical integration probe only. This is not an accepted Fabric
# artifact release. It exercises the real read-only `fabric` partition image
# path on the reference ESP32-S3. Accepted artifacts replace this source tree
# without changing the runtime storage contract.
set(KF_MS5_006_PROBE_IMAGE_DIR "${CMAKE_CURRENT_LIST_DIR}/../probe_image")
fatfs_create_rawflash_image(fabric "${KF_MS5_006_PROBE_IMAGE_DIR}" FLASH_IN_PROJECT)
