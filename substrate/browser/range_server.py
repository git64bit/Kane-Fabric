#!/usr/bin/env python3
"""Serve one substrate package with ordinary GET and single-byte-range support."""

from __future__ import annotations

import argparse
import json
import mimetypes
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

RANGE_RE = re.compile(r"^bytes=(\d+)-(\d+)$")


class Handler(BaseHTTPRequestHandler):
    server_version = "KaneFabricRangeProbe/1"

    def log_message(self, _format: str, *_args: object) -> None:
        return

    @property
    def root(self) -> Path:
        return self.server.root  # type: ignore[attr-defined]

    @property
    def log_path(self) -> Path:
        return self.server.log_path  # type: ignore[attr-defined]

    def _record(self, **values: object) -> None:
        with self.log_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(values, sort_keys=True, separators=(",", ":")) + "\n")

    def _headers(self, *, status: int, length: int, content_type: str, content_range: str | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header(
            "Access-Control-Expose-Headers",
            "Accept-Ranges, Content-Length, Content-Range",
        )
        if content_range is not None:
            self.send_header("Content-Range", content_range)
        self.end_headers()

    def _resolve(self) -> tuple[str, Path] | None:
        path_text = unquote(urlparse(self.path).path)
        relative = path_text.lstrip("/")
        if not relative or ".." in Path(relative).parts:
            return None
        path = (self.root / relative).resolve()
        try:
            path.relative_to(self.root)
        except ValueError:
            return None
        if not path.is_file():
            return None
        return path_text, path

    def do_GET(self) -> None:  # noqa: N802
        resolved = self._resolve()
        if resolved is None:
            self.send_error(404)
            return
        request_path, path = resolved
        total = path.stat().st_size
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        range_header = self.headers.get("Range")

        if range_header is None:
            self._headers(status=200, length=total, content_type=content_type)
            with path.open("rb") as stream:
                while True:
                    chunk = stream.read(64 * 1024)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
            self._record(
                end=total - 1,
                length=total,
                method="GET",
                path=request_path,
                range=None,
                start=0,
                status=200,
                total=total,
            )
            return

        match = RANGE_RE.fullmatch(range_header.strip())
        if match is None:
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{total}")
            self.send_header("Content-Length", "0")
            self.end_headers()
            self._record(
                method="GET",
                path=request_path,
                range=range_header,
                status=416,
                total=total,
            )
            return

        start = int(match.group(1))
        end = int(match.group(2))
        if start > end or start >= total or end >= total:
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{total}")
            self.send_header("Content-Length", "0")
            self.end_headers()
            self._record(
                method="GET",
                path=request_path,
                range=range_header,
                status=416,
                total=total,
            )
            return

        length = end - start + 1
        self._headers(
            status=206,
            length=length,
            content_type=content_type,
            content_range=f"bytes {start}-{end}/{total}",
        )
        with path.open("rb") as stream:
            stream.seek(start)
            remaining = length
            while remaining:
                chunk = stream.read(min(64 * 1024, remaining))
                if not chunk:
                    break
                self.wfile.write(chunk)
                remaining -= len(chunk)
        self._record(
            end=end,
            length=length,
            method="GET",
            path=request_path,
            range=range_header,
            start=start,
            status=206,
            total=total,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=41883)
    parser.add_argument("--log", type=Path, required=True)
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.is_dir():
        raise SystemExit(f"package directory does not exist: {root}")
    log_path = args.log.resolve()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("", encoding="utf-8")

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    server.root = root  # type: ignore[attr-defined]
    server.log_path = log_path  # type: ignore[attr-defined]
    host, port = server.server_address
    print(
        json.dumps(
            {"host": host, "port": port, "root": str(root)},
            sort_keys=True,
            separators=(",", ":"),
        ),
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
