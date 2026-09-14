#include "kane_fabric_http.h"

#include <assert.h>
#include <stdint.h>
#include <string.h>

static void expect_valid(const char *text, uint64_t size, uint64_t start, uint64_t end)
{
    kf_http_range_t range = {0};
    assert(kf_http_parse_closed_range(text, strlen(text), size, &range) == KF_HTTP_RANGE_VALID);
    assert(range.start == start);
    assert(range.end == end);
}

static void expect_invalid(const char *text, uint64_t size)
{
    kf_http_range_t range = {0};
    assert(kf_http_parse_closed_range(text, strlen(text), size, &range) == KF_HTTP_RANGE_INVALID);
}

int main(void)
{
    kf_http_range_t range = {0};
    assert(kf_http_parse_closed_range(NULL, 0, 100, &range) == KF_HTTP_RANGE_ABSENT);

    expect_valid("bytes=0-0", 100, 0, 0);
    expect_valid("bytes=0-99", 100, 0, 99);
    expect_valid("bytes=17-31", 100, 17, 31);

    expect_invalid("bytes=0-", 100);
    expect_invalid("bytes=-10", 100);
    expect_invalid("bytes=0-1,4-5", 100);
    expect_invalid("bytes=99-100", 100);
    expect_invalid("bytes=20-19", 100);
    expect_invalid("bytes= 0-1", 100);
    expect_invalid("Bytes=0-1", 100);
    expect_invalid("bytes=18446744073709551616-18446744073709551616", UINT64_MAX);
    expect_invalid("bytes=0-0", 0);

    assert(kf_http_artifact_uri_is_safe("/substrate/roads-lod.kfs", strlen("/substrate/roads-lod.kfs")));
    assert(kf_http_artifact_uri_is_safe("/composition/partitions/west.json", strlen("/composition/partitions/west.json")));
    assert(!kf_http_artifact_uri_is_safe("/", 1));
    assert(!kf_http_artifact_uri_is_safe("/../escape", strlen("/../escape")));
    assert(!kf_http_artifact_uri_is_safe("/a/../escape", strlen("/a/../escape")));
    assert(!kf_http_artifact_uri_is_safe("/a/./b", strlen("/a/./b")));
    assert(!kf_http_artifact_uri_is_safe("/a//b", strlen("/a//b")));
    assert(!kf_http_artifact_uri_is_safe("/a/%2e%2e/b", strlen("/a/%2e%2e/b")));
    assert(!kf_http_artifact_uri_is_safe("/a\\b", strlen("/a\\b")));
    assert(!kf_http_artifact_uri_is_safe("/a?x=1", strlen("/a?x=1")));

    return 0;
}
