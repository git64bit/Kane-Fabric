# Official Source Profiles

This directory contains the five version-controlled acquisition contracts approved for Kane Fabric's initial Kane County profile: county boundary, official building footprints, road centerlines, Fox River, and creeks.

The contracts were inherited from the frozen Kane Condo 0.4 regression oracle and ultimately derive from the exact donor profiles at `git64bit/kane-offline-map` commit `0911eeefeafbb18c58af0618200ba9edead29bdc`. Each profile records the raw donor file SHA-256 and preserves the endpoint, requested fields, identities, geometry declaration, output coordinate system, page size, and source attribution.

Kane Fabric preserves the explicit normalization contract for stable service/layer identity, GeoJSON geometry types, effective missing-geometry policy, exact-object-ID pagination, deterministic ascending numeric ordering, response validation, and coordinated `water-context` updating for Fox River and creeks.

The directory contains contracts only. It contains no downloaded responses, harvested county data, GeoPackages, operational state, or credentials. Validation and hashing are offline and make no network requests.
