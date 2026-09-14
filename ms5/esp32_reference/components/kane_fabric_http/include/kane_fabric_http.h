#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    KF_HTTP_RANGE_ABSENT = 0,
    KF_HTTP_RANGE_VALID = 1,
    KF_HTTP_RANGE_INVALID = 2,
} kf_http_range_result_t;

typedef struct {
    uint64_t start;
    uint64_t end;
} kf_http_range_t;

kf_http_range_result_t kf_http_parse_closed_range(
    const char *value,
    size_t value_len,
    uint64_t file_size,
    kf_http_range_t *out_range
);

bool kf_http_artifact_uri_is_safe(const char *uri, size_t uri_len);

#ifdef __cplusplus
}
#endif
