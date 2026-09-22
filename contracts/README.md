# Data Contracts

This directory contains data contract definitions that specify the expected schema, data types, validation rules, and quality expectations for each dataset flowing through the pipeline.

## Structure

```
contracts/
├── schemas/         — Active contract definitions
│   └── transaction_contract.json
└── versions/        — Versioned contract history
    └── v1/
        └── transaction_contract.json
```

## Contract Specification

Each contract defines:

| Property         | Description                                      |
|------------------|--------------------------------------------------|
| `dataset`        | Logical name of the dataset                      |
| `version`        | Semantic version of the contract                 |
| `owner`          | Team or individual responsible                   |
| `description`    | Purpose of the dataset                           |
| `required_fields`| Fields that must be present                      |
| `fields`         | Field-level specifications (type, nullable, etc.)|
| `rules`          | Business validation rules (hard/soft)            |

## Field Specification

Each field in the `fields` object can specify:

- `type` — Expected data type (string, integer, float, date, etc.)
- `nullable` — Whether null values are allowed
- `min_value` / `max_value` — Numeric range constraints
- `allowed_values` — Enumerated valid values
- `format` — Expected format pattern (e.g., date format)

## Rule Severity

- **hard** — Violations cause record rejection (quarantine)
- **soft** — Violations are logged as warnings but records pass through

## Versioning

Contracts are versioned to support backward compatibility and schema evolution. Each version is preserved in `versions/vN/`.
