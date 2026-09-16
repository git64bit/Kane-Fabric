# CPE ESP32-S3 first controlled flash acceptance

## Status

Accepted physical-device evidence observed on 2026-09-16 on `fw`, the CPE Build and Hardware Workstation.

This checkpoint proves the first controlled Kane Fabric flash and a subsequent cold boot of the clean reference ESP32-S3. It does **not** claim that the later MS5 storage, inventory, networking, HTTP, Wiregate, update, rollback, or recovery gates are complete.

## Source/build identity

The firmware was synchronized and built on `fw` from Kane-Fabric `main` at:

```text
14cbda39f7507b3055c208e79a3303987dbd3707
```

The generated application image remained:

```text
project                    kane_fabric_ms5_edge_reference
application image          kane_fabric_ms5_edge_reference.bin
application size           0x28180 bytes / 164224 bytes
smallest app partition     0x100000 bytes
reported free              84%
ESP-IDF                    v6.0.3
target                     esp32s3
```

## Physical board identity

The programmer identified the accepted clean reference board as:

```text
chip                       ESP32-S3 QFN56 revision v0.2
PSRAM                      8 MB
USB mode                   USB-Serial/JTAG
MAC                        b8:f8:62:e2:d5:2c
PROGRAM interface          CPE-USB-1 / Espressif 303a:1001
TERMINAL interface         CPE-USB-2 / CP2102 10c4:ea60
```

## Flash evidence

`cpe-flash` used the durable PROGRAM path:

```text
/dev/serial/by-path/pci-0000:00:1a.0-usb-0:1.1.2:1.0
```

Evidence log:

```text
/home/cpe-build/evidence/Kane-Fabric/20260916T182453Z-flash.log
```

The operation wrote and verified:

```text
0x00000000  bootloader/bootloader.bin
0x00008000  partition_table/partition-table.bin
0x00010000  kane_fabric_ms5_edge_reference.bin
```

Each region completed with `Hash of data verified.` The application write completed as 164224 bytes at `0x00010000`, followed by a hard reset.

## Power-path transition and cold boot

After flashing, the switched USB roles were deliberately transitioned from programming to runtime observation:

```text
PROGRAM / CPE-USB-1    OFF
TERMINAL / CPE-USB-2   ON
```

The board therefore lost power during the transition. This is useful acceptance evidence: the subsequent boot is a true cold boot from persisted flash rather than merely the programmer's reset path.

`cpe-monitor` then used the durable TERMINAL path:

```text
/dev/serial/by-path/pci-0000:00:1a.0-usb-0:1.1.3:1.0-port0
```

Evidence log:

```text
/home/cpe-build/evidence/Kane-Fabric/20260916T183110Z-monitor.log
```

The ROM reported:

```text
rst:0x1 (POWERON)
boot:0x8 (SPI_FAST_FLASH_BOOT)
```

The ESP-IDF second-stage bootloader then loaded the factory application from offset `0x10000` and started the application successfully.

## Runtime identity

The booted application reported:

```text
Project name               kane_fabric_ms5_edge_reference
App version                14cbda3
Compile time               Sep 16 2026 18:24:16
ESP-IDF                    v6.0.3
Chip revision              v0.2
```

The application reached `app_main()` and emitted:

```text
kane-fabric-ms5: MS5-006 storage/range components linked
```

`app_main()` then returned normally. No reset loop, panic, fatal error, or boot failure was observed.

## Flash-capacity observation

The runtime flash probe reported a physical flash size larger than the firmware image header configuration:

```text
physical flash detected    16384k
binary image header        2048k
```

ESP-IDF therefore emitted:

```text
Detected size(16384k) larger than the size in the binary image header(2048k). Using the size in the binary image header.
```

This warning did not prevent the accepted first flash or cold boot. It is, however, a material fact for later physical-storage design: the board appears to contain 16 MB of flash while this build is currently configured to address a 2 MB flash image layout. Storage/runtime integration must not silently assume the larger capacity is available until the partition/storage contract deliberately selects and proves it.

## Acceptance conclusion

```text
first controlled flash           PASS
written-data verification        PASS
cold boot after power loss       PASS
firmware build identity          PASS
serial runtime diagnostics       PASS
reset-loop/fatal-error check     PASS
storage/inventory runtime        NOT YET PROVED
HTTP/range runtime               NOT YET PROVED
Wiregate browser path            NOT YET PROVED
firmware update/recovery         NOT YET PROVED
```

The next implementation work remains within MS5-006: move beyond the current build-probe application and prove the frozen v1 runtime responsibilities on the physical board, beginning with prepared read-only artifact storage, active-inventory verification, and then real HTTP GET/range behavior.
