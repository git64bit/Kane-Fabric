# MS5-009 Firmware Update Descriptor

The update descriptor is the normalized transport-independent object handed
from release distribution into the ESP32-S3 update path.

Repository implementation:

```text
ms5/tools/kane_fabric_firmware_update_descriptor.py
```

It can only be constructed from:

1. a valid canonical firmware release manifest; and
2. a structurally valid authorization envelope whose signed fixed-binary
   payload identity exactly matches the manifest identity, firmware
   digest/length, release sequence, rollback floor, family, and target.

For the ESP32-S3 reference family it carries:

```text
manifest_sha256
firmware_sha256 / firmware_byte_length
release_sequence / rollback_floor_sequence
authorization_payload_sha256
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

The descriptor itself does not create authorization. The edge reconstructs
the same fixed binary payload from the descriptor fields, hashes it, compares
that identity to the envelope, and only then verifies the public-key signature.
Changing any installation field therefore invalidates the authorization.
