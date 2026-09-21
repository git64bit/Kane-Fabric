#include "kane_fabric_firmware_authorization.h"

#include "esp_err.h"
#include "psa/crypto.h"

#include <stddef.h>
#include <stdint.h>
#include <string.h>

static const uint8_t AUTH_DOMAIN[32] = {
    'k','a','n','e','-','f','a','b','r','i','c','-','f','i','r','m',
    'w','a','r','e','-','a','u','t','h','-','v','1',0,0,0,0
};
static const uint8_t DEVICE_FAMILY[16] = {
    'e','s','p','3','2','-','s','3',0,0,0,0,0,0,0,0
};
static const uint8_t TARGET[16] = {
    'e','s','p','3','2','s','3',0,0,0,0,0,0,0,0,0
};

static void write_u64_be(uint8_t out[8], uint64_t value)
{
    for (unsigned i = 0U; i < 8U; i++) {
        out[7U - i] = (uint8_t)(value & 0xFFU);
        value >>= 8U;
    }
}

static esp_err_t build_payload_sha256(
    const kf_firmware_authorization_payload_t *payload,
    uint8_t digest[KF_FIRMWARE_AUTH_SHA256_BYTES]
)
{
    if (
        payload->firmware_byte_length == 0U ||
        payload->release_sequence == 0U ||
        payload->rollback_floor_sequence > payload->release_sequence
    ) {
        return ESP_ERR_INVALID_ARG;
    }

    uint8_t encoded[KF_FIRMWARE_AUTH_PAYLOAD_BYTES] = {0};
    size_t offset = 0U;

    memcpy(encoded + offset, AUTH_DOMAIN, sizeof(AUTH_DOMAIN));
    offset += sizeof(AUTH_DOMAIN);
    memcpy(encoded + offset, DEVICE_FAMILY, sizeof(DEVICE_FAMILY));
    offset += sizeof(DEVICE_FAMILY);
    memcpy(encoded + offset, TARGET, sizeof(TARGET));
    offset += sizeof(TARGET);
    memcpy(
        encoded + offset,
        payload->manifest_sha256,
        KF_FIRMWARE_AUTH_SHA256_BYTES
    );
    offset += KF_FIRMWARE_AUTH_SHA256_BYTES;
    memcpy(
        encoded + offset,
        payload->firmware_sha256,
        KF_FIRMWARE_AUTH_SHA256_BYTES
    );
    offset += KF_FIRMWARE_AUTH_SHA256_BYTES;
    write_u64_be(encoded + offset, payload->firmware_byte_length);
    offset += 8U;
    write_u64_be(encoded + offset, payload->release_sequence);
    offset += 8U;
    write_u64_be(encoded + offset, payload->rollback_floor_sequence);
    offset += 8U;

    if (offset != sizeof(encoded)) {
        return ESP_ERR_INVALID_SIZE;
    }

    size_t digest_length = 0U;
    const psa_status_t status = psa_hash_compute(
        PSA_ALG_SHA_256,
        encoded,
        sizeof(encoded),
        digest,
        KF_FIRMWARE_AUTH_SHA256_BYTES,
        &digest_length
    );
    if (
        status != PSA_SUCCESS ||
        digest_length != KF_FIRMWARE_AUTH_SHA256_BYTES
    ) {
        return ESP_FAIL;
    }
    return ESP_OK;
}

static esp_err_t derive_key_id(
    const uint8_t public_key[KF_FIRMWARE_AUTH_P256_PUBLIC_KEY_BYTES],
    uint8_t key_id[KF_FIRMWARE_AUTH_KEY_ID_BYTES]
)
{
    size_t digest_length = 0U;
    const psa_status_t status = psa_hash_compute(
        PSA_ALG_SHA_256,
        public_key,
        KF_FIRMWARE_AUTH_P256_PUBLIC_KEY_BYTES,
        key_id,
        KF_FIRMWARE_AUTH_KEY_ID_BYTES,
        &digest_length
    );
    if (
        status != PSA_SUCCESS ||
        digest_length != KF_FIRMWARE_AUTH_KEY_ID_BYTES
    ) {
        return ESP_FAIL;
    }
    return ESP_OK;
}

esp_err_t kf_firmware_authorization_verify(
    const uint8_t public_key[KF_FIRMWARE_AUTH_P256_PUBLIC_KEY_BYTES],
    const kf_firmware_authorization_payload_t *payload,
    const kf_firmware_authorization_t *authorization
)
{
    if (
        public_key == NULL ||
        payload == NULL ||
        authorization == NULL
    ) {
        return ESP_ERR_INVALID_ARG;
    }
    if (public_key[0] != 0x04U) {
        return ESP_ERR_INVALID_ARG;
    }

    if (psa_crypto_init() != PSA_SUCCESS) {
        return ESP_FAIL;
    }

    uint8_t derived_key_id[KF_FIRMWARE_AUTH_KEY_ID_BYTES] = {0};
    esp_err_t result = derive_key_id(public_key, derived_key_id);
    if (result != ESP_OK) {
        return result;
    }
    if (
        memcmp(
            derived_key_id,
            authorization->key_id_sha256,
            KF_FIRMWARE_AUTH_KEY_ID_BYTES
        ) != 0
    ) {
        return ESP_ERR_INVALID_CRC;
    }

    uint8_t payload_sha256[KF_FIRMWARE_AUTH_SHA256_BYTES] = {0};
    result = build_payload_sha256(payload, payload_sha256);
    if (result != ESP_OK) {
        return result;
    }
    if (
        memcmp(
            payload_sha256,
            authorization->authorization_payload_sha256,
            KF_FIRMWARE_AUTH_SHA256_BYTES
        ) != 0
    ) {
        return ESP_ERR_INVALID_CRC;
    }

    psa_key_attributes_t attributes = PSA_KEY_ATTRIBUTES_INIT;
    psa_set_key_type(
        &attributes,
        PSA_KEY_TYPE_ECC_PUBLIC_KEY(PSA_ECC_FAMILY_SECP_R1)
    );
    psa_set_key_bits(&attributes, 256);
    psa_set_key_usage_flags(&attributes, PSA_KEY_USAGE_VERIFY_HASH);
    psa_set_key_algorithm(
        &attributes,
        PSA_ALG_ECDSA(PSA_ALG_SHA_256)
    );
    psa_set_key_lifetime(&attributes, PSA_KEY_LIFETIME_VOLATILE);

    psa_key_id_t key_id = 0;
    const psa_status_t import_status = psa_import_key(
        &attributes,
        public_key,
        KF_FIRMWARE_AUTH_P256_PUBLIC_KEY_BYTES,
        &key_id
    );
    psa_reset_key_attributes(&attributes);
    if (import_status != PSA_SUCCESS) {
        return ESP_ERR_INVALID_ARG;
    }

    const psa_status_t verify_status = psa_verify_hash(
        key_id,
        PSA_ALG_ECDSA(PSA_ALG_SHA_256),
        payload_sha256,
        KF_FIRMWARE_AUTH_SHA256_BYTES,
        authorization->signature,
        KF_FIRMWARE_AUTH_P256_SIGNATURE_BYTES
    );
    const psa_status_t destroy_status = psa_destroy_key(key_id);

    if (verify_status == PSA_ERROR_INVALID_SIGNATURE) {
        return ESP_ERR_INVALID_CRC;
    }
    if (verify_status != PSA_SUCCESS || destroy_status != PSA_SUCCESS) {
        return ESP_FAIL;
    }
    return ESP_OK;
}
