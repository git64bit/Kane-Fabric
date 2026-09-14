idf_component_register(
    SRCS "kane_fabric_artifact_server.c"
    INCLUDE_DIRS "include"
    REQUIRES esp_http_server kane_fabric_http
)
