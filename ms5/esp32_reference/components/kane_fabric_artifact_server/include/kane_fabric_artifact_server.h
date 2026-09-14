#pragma once

#include "esp_err.h"
#include "esp_http_server.h"

#ifdef __cplusplus
extern "C" {
#endif

#define KF_ARTIFACT_ROOT_PATH_MAX 384U

typedef struct {
    const char *root_path;
} kf_artifact_server_config_t;

typedef struct {
    char root_path[KF_ARTIFACT_ROOT_PATH_MAX];
} kf_artifact_server_t;

/*
 * Register the wildcard GET artifact handler.
 *
 * The caller owns both `instance` and the ESP-IDF HTTP server. `instance`
 * must remain alive for the lifetime of the registered handler.
 *
 * The caller MUST configure:
 *     httpd_config_t.uri_match_fn = httpd_uri_match_wildcard
 * before starting the server.
 *
 * The Kane Fabric ESP32-S3 reference attaches this component to a plain HTTP
 * server. Browser HTTPS and certificate trust terminate at the Wiregate hub;
 * this component does not create, terminate, or manage browser TLS.
 */
esp_err_t kf_artifact_server_register(
    httpd_handle_t server,
    kf_artifact_server_t *instance,
    const kf_artifact_server_config_t *config
);

#ifdef __cplusplus
}
#endif
