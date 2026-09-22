# Validation Engine

## Purpose
The validation engine ensures that data extracted from various sources adheres to predefined data contracts before it enters the analytical staging zones. 

## Flow
1. **Raw Storage**: Data is ingested and saved exactly as received.
2. **Contract Loading**: The data contract is dynamically loaded from `contracts/versions/` based on the requested dataset and version.
3. **Schema Validation**: The raw data's structure (columns, names) is validated against the contract. Missing required columns result in total batch quarantine.
4. **Row-level Validation**: Field types, nullability, minimum/maximum ranges, formats, and allowed values are enforced.
5. **Split & Quarantine**: Valid rows are passed through for transformation. Invalid rows are sent to `data/quarantine/validation_errors` along with a detailed JSON metadata trace.

## Data Contracts
Data contracts are written in JSON and define the exact shape of a dataset.

Example fields:
- `required`: Must the column exist in the dataset?
- `nullable`: Can the field contain nulls?
- `type`: Data type (string, integer, number, boolean, date).
- `minimum`/`maximum`: Numeric boundaries.
- `allowed_values`: Enumerated lists.
- `format`: String formats (e.g. YYYY-MM-DD).

## Quarantine Metadata
For every isolated batch, a companion JSON file is created detailing every specific rule violation, the row index, the exact field that failed, the expected state, and the actual payload.
