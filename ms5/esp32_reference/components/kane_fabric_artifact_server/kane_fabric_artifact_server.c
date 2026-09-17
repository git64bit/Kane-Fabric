#include "kane_fabric_artifact_server.h"

#include "kane_fabric_http.h"

#include <errno.h>
#include <inttypes.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>

#define KF_IO_BUFFER_BYTES 4096U
#define KF_HEADER_BUFFER_BYTES 768U
#define KF_PATH_BUFFER_BYTES 512U
#define KF_RANGE_HEADER_MAX_BYTES 96U

static const char *content_type_for_path(const char *path)
{
    const char *ext = strrchr(path, '.');
    if (ext == NULL) {
        return "application/octet-stream";
    }
    if (strcmp(ext, ".json") == 0) {
        return "application/json";
    }
    if (strcmp(ext, ".kfs") == 0) {
        return "application/octet-stream";
    }
    if (strcmp(ext, ".html") == 0) {
        return "text/html; charset=utf-8";
    }
    if (strcmp(ext, ".js") == 0 || strcmp(ext, ".mjs") == 0) {
        return "text/javascript; charset=utf-8";
    }
    if (strcmp(ext, ".css") == 0) {
        return "text/css; charset=utf-8";
    }
    return "application/octet-stream";
}

static esp_err_t raw_send_all(httpd_req_t *req, const char *buffer, size_t length)
{
    size_t offset = 0;
    while (offset < length) {
        const int sent = httpd_send(req, buffer + offset, length - offset);
        if (sent <= 0) {
            return ESP_FAIL;
        }
        offset += (size_t)sent;
    }
    return ESP_OK;
}

static esp_err_t send_empty_response(
    httpd_req_t *req,
    const char *status,
    const char *extra_header
)
{
    char header[KF_HEADER_BUFFER_BYTES];
    const int count = snprintf(
        header,
        sizeof(header),
        "HTTP/1.1 %s\r\n"
        "Content-Length: 0\r\n"
        "Accept-Ranges: bytes\r\n"
        "Access-Control-Allow-Origin: *\r\n"
        "Access-Control-Expose-Headers: Accept-Ranges, Content-Length, Content-Range\r\n"
        "%s"
        "Connection: close\r\n"
        "\r\n",
        status,
        extra_header == NULL ? "" : extra_header
    );
    if (count < 0 || (size_t)count >= sizeof(header)) {
        return ESP_ERR_INVALID_SIZE;
    }
    return raw_send_all(req, header, (size_t)count);
}

static esp_err_t send_file_region(
    httpd_req_t *req,
    FILE *stream,
    uint64_t offset,
    uint64_t length
)
{
    if (offset > (uint64_t)LONG_MAX) {
        return ESP_ERR_INVALID_SIZE;
    }
    if (fseek(stream, (long)offset, SEEK_SET) != 0) {
        return ESP_FAIL;
    }

    char *buffer = malloc(KF_IO_BUFFER_BYTES);
    if (buffer == NULL) {
        return ESP_ERR_NO_MEM;
    }

    uint64_t remaining = length;
    esp_err_t result = ESP_OK;

    while (remaining > 0U) {
        const size_t wanted = remaining > KF_IO_BUFFER_BYTES
            ? KF_IO_BUFFER_BYTES
            : (size_t)remaining;
        const size_t got = fread(buffer, 1U, wanted, stream);
        if (got == 0U) {
            result = ESP_FAIL;
            break;
        }
        result = raw_send_all(req, buffer, got);
        if (result != ESP_OK) {
            break;
        }
        remaining -= (uint64_t)got;
    }

    free(buffer);
    return result;
}

static esp_err_t artifact_get_handler(httpd_req_t *req)
{
    if (req == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    const kf_artifact_server_t *ctx = (const kf_artifact_server_t *)req->user_ctx;
    if (ctx == NULL) {
        return ESP_FAIL;
    }

    const size_t uri_len = strlen(req->uri);
    if (!kf_http_artifact_uri_is_safe(req->uri, uri_len)) {
        return send_empty_response(req, "400 Bad Request", NULL);
    }

    char full_path[KF_PATH_BUFFER_BYTES];
    const int path_count = snprintf(
        full_path,
        sizeof(full_path),
        "%s%s",
        ctx->root_path,
        req->uri
    );
    if (path_count < 0 || (size_t)path_count >= sizeof(full_path)) {
        return send_empty_response(req, "414 URI Too Long", NULL);
    }

    struct stat st;
    if (stat(full_path, &st) != 0 || !S_ISREG(st.st_mode) || st.st_size < 0) {
        return send_empty_response(req, "404 Not Found", NULL);
    }

    const uint64_t file_size = (uint64_t)st.st_size;
    char range_value[KF_RANGE_HEADER_MAX_BYTES];
    const size_t range_len = httpd_req_get_hdr_value_len(req, "Range");

    kf_http_range_t range = {0};
    kf_http_range_result_t range_result = KF_HTTP_RANGE_ABSENT;

    if (range_len > 0U) {
        if (range_len + 1U > sizeof(range_value)) {
            char extra[96];
            const int n = snprintf(
                extra,
                sizeof(extra),
                "Content-Range: bytes */%" PRIu64 "\r\n",
                file_size
            );
            if (n < 0 || (size_t)n >= sizeof(extra)) {
                return ESP_ERR_INVALID_SIZE;
            }
            return send_empty_response(req, "416 Range Not Satisfiable", extra);
        }
        esp_err_t err = httpd_req_get_hdr_value_str(
            req,
            "Range",
            range_value,
            sizeof(range_value)
        );
        if (err != ESP_OK) {
            return ESP_FAIL;
        }
        range_result = kf_http_parse_closed_range(
            range_value,
            range_len,
            file_size,
            &range
        );
    }

    if (range_result == KF_HTTP_RANGE_INVALID) {
        char extra[96];
        const int n = snprintf(
            extra,
            sizeof(extra),
            "Content-Range: bytes */%" PRIu64 "\r\n",
            file_size
        );
        if (n < 0 || (size_t)n >= sizeof(extra)) {
            return ESP_ERR_INVALID_SIZE;
        }
        return send_empty_response(req, "416 Range Not Satisfiable", extra);
    }

    FILE *stream = fopen(full_path, "rb");
    if (stream == NULL) {
        return send_empty_response(req, "404 Not Found", NULL);
    }

    const char *content_type = content_type_for_path(full_path);
    uint64_t send_offset = 0U;
    uint64_t send_length = file_size;
    char content_range[128] = "";
    const char *status = "200 OK";

    if (range_result == KF_HTTP_RANGE_VALID) {
        send_offset = range.start;
        send_length = range.end - range.start + 1U;
        status = "206 Partial Content";
        const int n = snprintf(
            content_range,
            sizeof(content_range),
            "Content-Range: bytes %" PRIu64 "-%" PRIu64 "/%" PRIu64 "\r\n",
            range.start,
            range.end,
            file_size
        );
        if (n < 0 || (size_t)n >= sizeof(content_range)) {
            fclose(stream);
            return ESP_ERR_INVALID_SIZE;
        }
    }

    char header[KF_HEADER_BUFFER_BYTES];
    const int header_count = snprintf(
        header,
        sizeof(header),
        "HTTP/1.1 %s\r\n"
        "Content-Type: %s\r\n"
        "Content-Length: %" PRIu64 "\r\n"
        "%s"
        "Accept-Ranges: bytes\r\n"
        "Access-Control-Allow-Origin: *\r\n"
        "Access-Control-Expose-Headers: Accept-Ranges, Content-Length, Content-Range\r\n"
        "Cache-Control: public, max-age=31536000, immutable\r\n"
        "Connection: close\r\n"
        "\r\n",
        status,
        content_type,
        send_length,
        content_range
    );
    if (header_count < 0 || (size_t)header_count >= sizeof(header)) {
        fclose(stream);
        return ESP_ERR_INVALID_SIZE;
    }

    esp_err_t result = raw_send_all(req, header, (size_t)header_count);
    if (result == ESP_OK && send_length > 0U) {
        result = send_file_region(req, stream, send_offset, send_length);
    }
    fclose(stream);
    return result;
}

esp_err_t kf_artifact_server_register(
    httpd_handle_t server,
    kf_artifact_server_t *instance,
    const kf_artifact_server_config_t *config
)
{
    if (server == NULL || instance == NULL ||
        config == NULL || config->root_path == NULL) {
        return ESP_ERR_INVALID_ARG;
    }

    const size_t root_len = strlen(config->root_path);
    if (root_len == 0U || root_len >= sizeof(instance->root_path) - 1U ||
        config->root_path[0] != '/' ||
        (root_len > 1U && config->root_path[root_len - 1U] == '/')) {
        return ESP_ERR_INVALID_ARG;
    }

    memset(instance, 0, sizeof(*instance));
    memcpy(instance->root_path, config->root_path, root_len + 1U);

    const httpd_uri_t route = {
        .uri = "/*",
        .method = HTTP_GET,
        .handler = artifact_get_handler,
        .user_ctx = instance,
    };

    return httpd_register_uri_handler(server, &route);
}
