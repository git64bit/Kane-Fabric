# CPE ESP32-S3 first controlled flash acceptance

## Status

Accepted physical-device evidence observed on 2026-09-16 on `fw`, the CPE Build and Hardware Workstation.

This checkpoint proves the first controlled Kane Fabric flash, a subsequent cold boot of the clean reference ESP32-S3, and the correction of the reference firmware flash geometry from the ESP-IDF 2 MB default to the board's observed 16 MB flash capacity.

It does **not** claim that the later MS5 storage, inventory, networking, HTTP, Wiregate, update, rollback, or recovery gates are complete.

## First accepted source/build identity

The first controlled firmware was synchronized and built on `fw` from Kane-Fabric `main` at:

```text
14cbda39f7507b3055c208e79a3303987dbd3707
```

The generated application image was:

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

## First flash evidence

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

## Power-path transition and first cold boot

After flashing, the switched USB roles were deliberately transitioned from programming to runtime observation:

```text
PROGRAM / CPE-USB-1    OFF
TERMINAL / CPE-USB-2   ON
```

The board therefore lost power during the transition. The subsequent boot is a true cold boot from persisted flash rather than merely the programmer's reset path.

`cpe-monitor` used the durable TERMINAL path:

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

The ESP-IDF second-stage bootloader loaded the factory application from offset `0x10000` and started the application successfully.

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

## Flash-capacity mismatch found during first boot

The first cold boot exposed a configuration defect:

```text
physical flash detected    16384k
binary image header        2048k
```

ESP-IDF emitted:

```text
Detected size(16384k) larger than the size in the binary image header(2048k). Using the size in the binary image header.
```

The physical board therefore has 16 MB flash while the generated firmware configuration still inherited ESP-IDF's 2 MB default.

The tracked `sdkconfig.defaults` at that point pinned only:

```text
CONFIG_IDF_TARGET="esp32s3"
```

This was the same class of reproducibility defect as an unpinned chip target: the physical reference hardware characteristic was known but not encoded in the tracked build defaults.

## Repository correction

Kane-Fabric `main` was corrected at:

```text
d26ec418751b7b2f82a8814297204e1b62bceda4
```

The reference defaults now pin both:

```text
CONFIG_IDF_TARGET="esp32s3"
CONFIG_ESPTOOLPY_FLASHSIZE_16MB=y
```

A repository test was added requiring both settings so the reference build cannot silently regress to the generic target or 2 MB flash-size default.

The existing generated build configuration on `fw` still contained the old value and was deliberately regenerated from the tracked defaults. The resulting effective configuration was observed as:

```text
CONFIG_IDF_TARGET="esp32s3"
CONFIG_ESPTOOLPY_FLASHSIZE_16MB=y
CONFIG_ESPTOOLPY_FLASHSIZE="16MB"
```

The regenerated flash command likewise contained:

```text
--chip esp32s3
--flash-size 16MB
```

## Corrective reflash and second cold boot

The corrected firmware at `d26ec418751b7b2f82a8814297204e1b62bceda4` was flashed through PROGRAM.

Corrective flash evidence log:

```text
/home/cpe-build/evidence/Kane-Fabric/20260916T184413Z-flash.log
```

The programmer again identified:

```text
chip                       ESP32-S3 QFN56 revision v0.2
PSRAM                      8 MB
USB mode                   USB-Serial/JTAG
MAC                        b8:f8:62:e2:d5:2c
flash size argument        16MB
```

Bootloader, partition table, and application writes each completed with `Hash of data verified.`

The board was then power-cycled by switching:

```text
PROGRAM / CPE-USB-1    OFF
TERMINAL / CPE-USB-2   ON
```

Second cold-boot monitor log:

```text
/home/cpe-build/evidence/Kane-Fabric/20260916T184558Z-monitor.log
```

The ROM again reported a genuine power-on boot:

```text
rst:0x1 (POWERON)
boot:0x8 (SPI_FAST_FLASH_BOOT)
```

The corrected second-stage bootloader reported:

```text
Boot SPI Speed : 80MHz
SPI Mode       : DIO
SPI Flash Size : 16MB
```

The application identity was:

```text
Project name               kane_fabric_ms5_edge_reference
App version                d26ec41
Compile time               Sep 16 2026 18:42:46
ELF file SHA256 prefix     13f8a9b8c
ESP-IDF                    v6.0.3
Chip revision              v0.2
```

The previous `16384k` versus `2048k` warning was absent. The application reached `app_main()`, emitted the expected MS5-006 build-probe diagnostic, and returned normally without reset loop, panic, fatal error, or boot failure.

## Acceptance conclusion

```text
first controlled flash                  PASS
written-data verification               PASS
cold boot after power loss              PASS
firmware build identity                 PASS
serial runtime diagnostics              PASS
reference target pinned                 PASS / esp32s3
reference flash geometry pinned         PASS / 16MB
generated sdkconfig regenerated         PASS
corrective 16 MB reflash                PASS
16 MB cold-boot recognition             PASS
2 MB mismatch warning                   RESOLVED
reset-loop/fatal-error check            PASS
storage/inventory runtime               NOT YET PROVED
HTTP/range runtime                      NOT YET PROVED
Wiregate browser path                   NOT YET PROVED
firmware update/recovery                NOT YET PROVED
```

The accepted physical firmware checkpoint for continuing MS5-006 is therefore:

```text
firmware source              d26ec418751b7b2f82a8814297204e1b62bceda4
target                       esp32s3
physical/reference flash     16 MB
runtime boot flash size      16MB
current runtime connection   TERMINAL / CPE-USB-2
```

The next implementation work remains within MS5-006: move beyond the current build-probe application and prove prepared read-only artifact storage, active-inventory verification, and then real HTTP GET/range behavior on the physical board.
