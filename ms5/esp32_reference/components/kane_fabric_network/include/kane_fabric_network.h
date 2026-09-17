#pragma once

#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    KF_NETWORK_STATE_NONE = 0,
    KF_NETWORK_STATE_READY,
    KF_NETWORK_STATE_PROVISIONING,
} kf_network_state_t;

/*
 * Initialize the ESP-IDF network runtime for the reference edge.
 *
 * If deployment Wi-Fi credentials are present in NVS, this function attaches
 * as a station and returns KF_NETWORK_STATE_READY only after DHCP succeeds.
 *
 * If deployment credentials are absent, it starts the local first-boot
 * provisioning AP/web form and returns KF_NETWORK_STATE_PROVISIONING. The
 * provisioning path is local-only and does not start the Fabric artifact
 * server or depend on an external account/service.
 */
esp_err_t kf_network_start(kf_network_state_t *state);

#ifdef __cplusplus
}
#endif
