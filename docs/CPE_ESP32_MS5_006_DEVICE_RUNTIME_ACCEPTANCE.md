# CPE ESP32-S3 MS5-006 device-runtime acceptance

## Status

Accepted physical-device evidence observed on 2026-09-17 on `fw`, the CPE Build and Hardware Workstation.

This checkpoint closes the physical-device runtime portion of MS5-006 for the ESP32-S3 v1 artifact appliance. It proves prepared read-only Fabric storage, active-inventory verification before serving, deployment-network attachment, ordinary HTTP GET, exact closed byte-range behavior, rejection of unsupported ranges and unsafe paths, fail-closed behavior for an invalid active image, and recovery after restoring the accepted image.

It does **not** claim completion of MS5-007 Wiregate/browser integration, MS5-008 management-transport evaluation, MS5-009 firmware update/rollback/recovery, MS5-010 replacement/reprovisioning, MS5-011 constrained-resource acceptance, or overall Milestone 5 closeout.

## Accepted implementation identity

The accepted implementation is Kane-Fabric `main` at:

```text
7aa3c836bae470704d051a36a6261a1140e9d3d0
```

Application identity observed during acceptance:

```text
project                    kane_fabric_ms5_edge_reference
app version                7aa3c83
ESP-IDF                    v6.0.3
target                     esp32s3
application size           0xd0e50 bytes
smallest app partition     0x100000 bytes
reported free              18%
```

Reference hardware:

```text
chip                       ESP32-S3 QFN56 revision v0.2
PSRAM                      8 MB
flash                      16 MB
MAC                        b8:f8:62:e2:d5:2c
PROGRAM                    CPE-USB-1 / Espressif 303a:1001 / /dev/ttyACM0
TERMINAL                   CPE-USB-2 / CP2102 10c4:ea60 / /dev/ttyUSB0
```

## Prepared Fabric image and verification

The physical reference partition remains:

```text
label                      fabric
type/subtype               data/fat
flash offset               0x110000
size                       0x400000 / 4 MiB
mount point                /fabric
runtime mount mode         read-only
```

The accepted probe artifact is exactly:

```text
Kane Fabric MS5-006 physical edge probe\n
```

Accepted artifact facts:

```text
path                       probe.txt
byte length                40
artifact SHA-256           c8dec92f14acc992787526d302d845e53e5801358adcba5693488b08015a27ae
inventory file SHA-256     aa5dacf9efed328c42b08c4e3410f8612bfec01569519cc6ae8cbefbdf8b253b
artifacts                  1
```

A valid boot emitted, in order:

```text
MS5-006 mounting fabric partition read-only
MS5-006 fabric partition mounted read-only
MS5-006 probe image verified; inventory_file_sha256=aa5dacf9efed328c42b08c4e3410f8612bfec01569519cc6ae8cbefbdf8b253b artifacts=1
```

The HTTP server is not started before this verification gate passes.

## Deployment-network attachment

The first-boot provisioning path was exercised physically. The ESP32 setup interface accepted deployment Wi-Fi configuration, persisted it in NVS, rebooted, disabled setup mode, joined the deployment network as a station, obtained DHCP, and then started the artifact server only after Fabric verification.

Observed deployment state:

```text
SSID                       W3PBS-X
security                   WPA2-PSK
station IPv4               10.0.0.185
netmask                    255.255.255.0
gateway                    10.0.0.1
artifact HTTP port         80
```

A later firmware-only reflash did not erase NVS; the stored deployment credentials remained usable.

## HTTP full-object acceptance

From `fw`, the physical ESP32 returned:

```text
HTTP/1.1 200 OK
Content-Type: application/octet-stream
Content-Length: 40
Accept-Ranges: bytes
Access-Control-Allow-Origin: *
Access-Control-Expose-Headers: Accept-Ranges, Content-Length, Content-Range
Cache-Control: public, max-age=31536000, immutable
Connection: close
```

The received object was exactly 40 bytes with:

```text
SHA-256  c8dec92f14acc992787526d302d845e53e5801358adcba5693488b08015a27ae
body     Kane Fabric MS5-006 physical edge probe
```

## Closed byte-range acceptance

A request with:

```text
Range: bytes=0-3
```

returned:

```text
HTTP/1.1 206 Partial Content
Content-Length: 4
Content-Range: bytes 0-3/40
body: Kane
```

The following unsupported or invalid forms were rejected with `416 Range Not Satisfiable`, `Content-Range: bytes */40`, and zero-byte bodies:

```text
bytes=0-
bytes=-4
bytes=0-3,8-11
bytes=100-120
```

Path traversal using the literal request path `/../probe.txt` was rejected with `400 Bad Request` and a zero-byte body.

## HTTPD stack-defect corrections found by physical testing

Physical HTTP testing exposed two stack-pressure defects in the default ESP-IDF HTTP server task.

At `e0dc26de96946121d4ae5496a7bd8ff30bbcb7af`, the 4096-byte artifact streaming buffer was moved from the HTTPD task stack to heap allocation. Full-object HTTP delivery then passed physically.

A subsequent unsupported-range request still exposed stack corruption because the rejected-range response path nested an additional large response-header buffer on the same 4096-byte HTTPD task stack. At the accepted implementation head `7aa3c836bae470704d051a36a6261a1140e9d3d0`, the remaining large artifact response-header allocations were moved off the HTTPD task stack.

After that correction, ordinary `200`, valid `206`, invalid `416`, and traversal-rejection paths all completed without connection reset or device panic.

## Invalid active-storage fail-closed proof

A deterministic invalid Fabric image was created from the generated accepted `fabric.bin` by changing one byte in the unique probe payload occurrence at Fabric-image offset `0x8000`.

Observed image facts:

```text
image size                 4194304 bytes
accepted image SHA-256     87a406a91635ab853ad7414e2619db35b42e87b9fe6fa8eec53beecc032fa364
corrupt image SHA-256      ccc1cbee8fba5d85d0c17e73d79c476abb34a4562922a5ebe3a482e75a326899
probe payload offset       0x8000 within fabric.bin
```

Only the Fabric partition at flash offset `0x110000` was replaced. The application, bootloader, partition table, and NVS were left unchanged.

On a fresh physical boot, the device reported:

```text
App version: 7aa3c83
MS5-006 mounting fabric partition read-only
MS5-006 fabric partition mounted read-only
MS5-006 fabric verification failed closed: ESP_ERR_INVALID_STATE
main_task: Returned from app_main()
```

No Wi-Fi initialization, DHCP acquisition, or HTTP artifact-server startup followed the failed verification. The invalid active image was therefore not exposed.

## Recovery after restoring the accepted image

The accepted generated `fabric.bin` was written back to the Fabric partition only and verified by the programmer.

After restoration, the device again answered at `10.0.0.185` and returned the accepted 40-byte probe by HTTP `200 OK` with the accepted artifact SHA-256:

```text
c8dec92f14acc992787526d302d845e53e5801358adcba5693488b08015a27ae
```

This proves recovery from the deliberate invalid-storage test without changing application firmware or NVS configuration.

## Acceptance conclusion

```text
pinned ESP-IDF build identity                    PASS
physical firmware identity                       PASS
prepared Fabric storage mount read-only          PASS
active inventory verified before serving         PASS
deployment local-network client attachment       PASS
persistent deployment provisioning               PASS
ordinary HTTP GET                                PASS
exact valid closed byte range                    PASS
unsupported/open/suffix/multiple range reject    PASS
out-of-bounds range reject                       PASS
path traversal reject                            PASS
invalid active Fabric generation fail closed     PASS
no network/HTTP exposure after failed verify     PASS
restore accepted Fabric image                    PASS
service recovery after restore                   PASS
HTTPD stack-corruption defects                   RESOLVED
```

The MS5-006 ESP32-S3 v1 artifact-appliance device-runtime gate is therefore accepted at `7aa3c836bae470704d051a36a6261a1140e9d3d0`.

The next normative work item is MS5-007: real browser consumption through Wiregate HTTPS of accepted MS3/MS4 generations served by the ESP32-S3 over plain HTTP. Continued serving during management/upstream loss remains an MS5 integration acceptance requirement and is not pulled backward into this device-runtime closeout.
