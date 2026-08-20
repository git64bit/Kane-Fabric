#!/usr/bin/env python3
"""Inspect the native/runtime dependency identities used by Kane Fabric."""

from __future__ import annotations

import importlib.util
import json
import platform
import sqlite3
import ssl
import subprocess
import sys
import zlib
from pathlib import Path


def module_origin(name: str) -> str:
    spec = importlib.util.find_spec(name)
    if spec is None:
        return "not-found"
    return str(spec.origin or "unknown")


def ldd(path: str) -> list[str]:
    candidate = Path(path)
    if not candidate.is_file():
        return []
    try:
        completed = subprocess.run(
            ["ldd", str(candidate)],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return []
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def package_version(name: str) -> str | None:
    try:
        completed = subprocess.run(
            ["dpkg-query", "-W", "-f=${Version}", name],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return completed.stdout.strip() or None


def main() -> int:
    native_origins = {
        "_sqlite3": module_origin("_sqlite3"),
        "_ssl": module_origin("_ssl"),
        "zlib": module_origin("zlib"),
    }
    linkage_targets = [sys.executable]
    linkage_targets.extend(
        origin
        for origin in native_origins.values()
        if origin not in {"built-in", "frozen", "unknown", "not-found"}
    )
    linkage = {target: ldd(target) for target in dict.fromkeys(linkage_targets)}

    packages = {}
    for name in (
        "python3",
        "python3.11",
        "libpython3.11-stdlib",
        "libsqlite3-0",
        "zlib1g",
        "libssl3",
        "libc6",
        "ca-certificates",
        "nodejs",
    ):
        value = package_version(name)
        if value is not None:
            packages[name] = value

    result = {
        "native_module_origins": native_origins,
        "native_linkage": linkage,
        "packages": packages,
        "python": {
            "executable": sys.executable,
            "implementation": platform.python_implementation(),
            "version": sys.version,
        },
        "sqlite": {
            "python_binding_version": sqlite3.version,
            "runtime_version": sqlite3.sqlite_version,
        },
        "tls": {
            "openssl_version": ssl.OPENSSL_VERSION,
            "openssl_version_info": list(ssl.OPENSSL_VERSION_INFO),
        },
        "zlib": {
            "compile_version": zlib.ZLIB_VERSION,
            "runtime_version": zlib.ZLIB_RUNTIME_VERSION,
        },
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
