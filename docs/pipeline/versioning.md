# Versioning Documentation

## Overview

The versioning system provides append-only, versioned data storage with full metadata for auditability and replayability.

## Versioning Metadata

| Field                | Description                                    |
|----------------------|------------------------------------------------|
| `record_id`          | Unique record identifier                       |
| `source_system`      | Origin of the data                             |
| `batch_id`           | Processing batch identifier                    |
| `ingestion_timestamp`| When the record was ingested                   |
| `valid_from`         | Start of record validity period                |
| `valid_to`           | End of record validity (null if current)       |
| `record_hash`        | Hash of record content for change detection    |
| `schema_version`     | Version of the contract/schema used            |

## Details

*(To be documented during Phase 2 implementation)*
