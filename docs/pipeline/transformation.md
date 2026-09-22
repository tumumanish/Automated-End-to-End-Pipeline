# Transformation Documentation

## Overview

The transformation layer applies data cleaning, normalization, deduplication, type conversion, business rules, and enrichment.

## Transformation Steps

| Step             | Module               | Description                              |
|------------------|----------------------|------------------------------------------|
| Cleaning         | `cleaning.py`        | Missing values, whitespace, formats      |
| Normalization    | `normalization.py`   | Case, encoding, value standardization    |
| Deduplication    | `deduplication.py`   | Duplicate detection and removal          |
| Type Conversion  | `type_conversion.py` | Data type casting per contract           |
| Business Rules   | `business_rules.py`  | Domain-specific transformation logic     |
| Enrichment       | `enrichment.py`      | Derived fields, lookup enrichment        |

## Composability

`transformation_factory.py` composes transformation steps into a pipeline based on configuration.

## Details

*(To be documented during Phase 2 implementation)*
