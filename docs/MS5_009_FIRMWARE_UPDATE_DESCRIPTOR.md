# MS5-009 Firmware Update Descriptor

The update descriptor is the normalized transport-independent object handed
from release distribution into the ESP32-S3 update path.

Repository implementation:

```text
ms5/tools/kane_fabric_firmware_update_descriptor.py
```

It can only be constructed from:

1. a valid canonical firmware release manifest; and
2. a structurally valid authorization envelope whose
   `manifest_sha256` exactly equals the manifest identity.

For the ESP32-S3 reference family it carries:

```text
manifest_sha256
key_id_sha256
authorization_algorithm
signature_encoding
signature_base64
release_sequence
rollback_floor_sequence
firmware_byte_length
firmware_sha256
```

The descriptor is deliberately transport-neutral. HTTP, WireGuard, removable
media, USB laboratory transfer, or a future synchronization transport may
carry the same descriptor and firmware bytes without changing authorization or
Fabric identity.

The descriptor itself does not create authorization. Its authorization fields
remain valid only because they are copied from an envelope bound to the exact
canonical manifest identity.
