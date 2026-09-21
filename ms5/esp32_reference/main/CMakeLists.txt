idf_component_register(
    SRCS "app_main.c"
    REQUIRES esp_event esp_netif esp_wifi log kane_fabric_artifact_server kane_fabric_firmware_lifecycle kane_fabric_network kane_fabric_storage
)

# MS5-007 focused participant publication image. The reference ESP32-S3 keeps
# the same read-only `fabric` partition/runtime contract accepted by MS5-006;
# only the bounded artifact set changes from the historical probe to the
# participant publication accepted by the administrative/browser integration.
set(KF_MS5_007_PARTICIPANT_IMAGE_DIR "${CMAKE_CURRENT_LIST_DIR}/../participant_image")
set(KF_MS5_007_PARTICIPANT_INVENTORY
    "${KF_MS5_007_PARTICIPANT_IMAGE_DIR}/.kane-fabric-storage-inventory.json")
set(KF_MS5_007_PARTICIPANT_ARTIFACT
    "${KF_MS5_007_PARTICIPANT_IMAGE_DIR}/participant.json")

# The physical integration build couples the firmware to the exact staged
# participant image it flashes. These expectations verify storage bytes and do
# not make physical device identity part of Fabric logical identity.
file(SHA256 "${KF_MS5_007_PARTICIPANT_INVENTORY}"
    KF_MS5_007_PARTICIPANT_INVENTORY_FILE_SHA256)
file(SHA256 "${KF_MS5_007_PARTICIPANT_ARTIFACT}"
    KF_MS5_007_PARTICIPANT_ARTIFACT_SHA256)
file(SIZE "${KF_MS5_007_PARTICIPANT_ARTIFACT}"
    KF_MS5_007_PARTICIPANT_ARTIFACT_SIZE)

target_compile_definitions(${COMPONENT_LIB} PRIVATE
    KF_MS5_007_PARTICIPANT_INVENTORY_FILE_SHA256=\"${KF_MS5_007_PARTICIPANT_INVENTORY_FILE_SHA256}\"
    KF_MS5_007_PARTICIPANT_ARTIFACT_SHA256=\"${KF_MS5_007_PARTICIPANT_ARTIFACT_SHA256}\"
    KF_MS5_007_PARTICIPANT_ARTIFACT_SIZE=${KF_MS5_007_PARTICIPANT_ARTIFACT_SIZE}
)

fatfs_create_rawflash_image(
    fabric
    "${KF_MS5_007_PARTICIPANT_IMAGE_DIR}"
    FLASH_IN_PROJECT
)
