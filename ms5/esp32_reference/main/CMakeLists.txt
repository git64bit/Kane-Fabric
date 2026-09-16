idf_component_register(
    SRCS "app_main.c"
    REQUIRES log kane_fabric_artifact_server kane_fabric_storage
)

# MS5-006 physical integration probe only. This is not an accepted Fabric
# artifact release. It exercises the real read-only `fabric` partition image
# path on the reference ESP32-S3. Accepted artifacts replace this source tree
# without changing the runtime storage contract.
set(KF_MS5_006_PROBE_IMAGE_DIR "${CMAKE_CURRENT_LIST_DIR}/../probe_image")
set(KF_MS5_006_PROBE_INVENTORY
    "${KF_MS5_006_PROBE_IMAGE_DIR}/.kane-fabric-storage-inventory.json")
set(KF_MS5_006_PROBE_ARTIFACT "${KF_MS5_006_PROBE_IMAGE_DIR}/probe.txt")

# The physical probe couples this firmware build to the exact staged image it
# flashes. These are verification expectations, not Fabric logical identity.
file(SHA256 "${KF_MS5_006_PROBE_INVENTORY}" KF_MS5_006_PROBE_INVENTORY_FILE_SHA256)
file(SHA256 "${KF_MS5_006_PROBE_ARTIFACT}" KF_MS5_006_PROBE_ARTIFACT_SHA256)
file(SIZE "${KF_MS5_006_PROBE_ARTIFACT}" KF_MS5_006_PROBE_ARTIFACT_SIZE)

target_compile_definitions(${COMPONENT_LIB} PRIVATE
    KF_MS5_006_PROBE_INVENTORY_FILE_SHA256=\"${KF_MS5_006_PROBE_INVENTORY_FILE_SHA256}\"
    KF_MS5_006_PROBE_ARTIFACT_SHA256=\"${KF_MS5_006_PROBE_ARTIFACT_SHA256}\"
    KF_MS5_006_PROBE_ARTIFACT_SIZE=${KF_MS5_006_PROBE_ARTIFACT_SIZE}
)

fatfs_create_rawflash_image(fabric "${KF_MS5_006_PROBE_IMAGE_DIR}" FLASH_IN_PROJECT)
