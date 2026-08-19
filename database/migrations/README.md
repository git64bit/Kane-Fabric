# Kane Fabric Database Migrations

These migrations are the first Kane Fabric-owned geographic database schema.

They are derived behavior-preservingly from the frozen Kane Condo 0.4 donor, but the migration history and ownership now belong to Kane Fabric.

## Core sequence

1. GeoPackage 1.4.0 foundation and immutable migration ledger.
2. County/source/dataset/harvest/file/release provenance.
3. County-boundary geometry storage.
4. Roads and water geometry storage.
5. Official building-footprint storage.
6. Durable geographic building identity and source-footprint mappings.
7. Append-only promotion and rollback history.

There is deliberately no Kane Condo classification migration. Classification values and history are application-owned state and are not required for Kane Fabric geographic operation.

During MS-2, the donor table names `project_building` and `project_building_source_mapping` are retained as transitional schema compatibility. Kane Fabric treats those rows as durable geographic building identities, not Condo application records. Renaming physical tables is deferred until behavior-preserving extraction no longer depends on the donor schema.

A fresh Fabric database is created with:

```bash
bash database/kane-fabric-db.sh init /tmp/kane-fabric.gpkg
```

The migration ledger records the exact filename and SHA-256 of each Fabric migration. Normal operations must not edit an applied migration; schema changes require a new ordered migration.
