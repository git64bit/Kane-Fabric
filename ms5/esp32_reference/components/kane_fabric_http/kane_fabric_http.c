#include "kane_fabric_http.h"

#include <limits.h>
#include <string.h>

static bool parse_u64(const char *text, size_t len, uint64_t *out)
{
    if (text == NULL || out == NULL || len == 0) {
        return false;
    }

    uint64_t value = 0;
    for (size_t i = 0; i < len; ++i) {
        const unsigned char ch = (unsigned char)text[i];
        if (ch < '0' || ch > '9') {
            return false;
        }
        const uint64_t digit = (uint64_t)(ch - '0');
        if (value > (UINT64_MAX - digit) / 10U) {
            return false;
        }
        value = value * 10U + digit;
    }
    *out = value;
    return true;
}

kf_http_range_result_t kf_http_parse_closed_range(
    const char *value,
    size_t value_len,
    uint64_t file_size,
    kf_http_range_t *out_range
)
{
    static const char prefix[] = "bytes=";
    const size_t prefix_len = sizeof(prefix) - 1U;

    if (value == NULL || value_len == 0U) {
        return KF_HTTP_RANGE_ABSENT;
    }
    if (out_range == NULL || file_size == 0U || value_len <= prefix_len) {
        return KF_HTTP_RANGE_INVALID;
    }
    if (memcmp(value, prefix, prefix_len) != 0) {
        return KF_HTTP_RANGE_INVALID;
    }

    const char *spec = value + prefix_len;
    const size_t spec_len = value_len - prefix_len;

    size_t dash = SIZE_MAX;
    for (size_t i = 0; i < spec_len; ++i) {
        const char ch = spec[i];
        if (ch == ',') {
            return KF_HTTP_RANGE_INVALID;
        }
        if (ch == '-') {
            if (dash != SIZE_MAX) {
                return KF_HTTP_RANGE_INVALID;
            }
            dash = i;
        }
    }

    if (dash == SIZE_MAX || dash == 0U || dash + 1U >= spec_len) {
        return KF_HTTP_RANGE_INVALID;
    }

    uint64_t start = 0;
    uint64_t end = 0;
    if (!parse_u64(spec, dash, &start) ||
        !parse_u64(spec + dash + 1U, spec_len - dash - 1U, &end)) {
        return KF_HTTP_RANGE_INVALID;
    }

    if (start > end || end >= file_size) {
        return KF_HTTP_RANGE_INVALID;
    }

    out_range->start = start;
    out_range->end = end;
    return KF_HTTP_RANGE_VALID;
}

bool kf_http_artifact_uri_is_safe(const char *uri, size_t uri_len)
{
    if (uri == NULL || uri_len < 2U || uri[0] != '/') {
        return false;
    }

    size_t segment_start = 1U;
    for (size_t i = 1U; i <= uri_len; ++i) {
        const bool at_end = i == uri_len;
        const unsigned char ch = at_end ? (unsigned char)'/' : (unsigned char)uri[i];

        if (!at_end &&
            (ch == '?' || ch == '#' || ch == '\\' || ch == '%' ||
             ch < 0x21U || ch == 0x7fU)) {
            return false;
        }

        if (ch == '/') {
            const size_t segment_len = i - segment_start;
            if (segment_len == 0U) {
                return false;
            }
            if (segment_len == 1U && uri[segment_start] == '.') {
                return false;
            }
            if (segment_len == 2U &&
                uri[segment_start] == '.' &&
                uri[segment_start + 1U] == '.') {
                return false;
            }
            segment_start = i + 1U;
        }
    }

    return true;
}
