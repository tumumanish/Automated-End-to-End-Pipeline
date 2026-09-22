# Validation Documentation

## Overview

Data validation enforces quality through schema checks, contract rules, and business rule validation.

## Validation Layers

1. **Schema Validation:** Field presence, data types, nullable constraints
2. **Contract Validation:** Business rules (hard/soft), value ranges, allowed values
3. **Batch Validation:** Aggregate checks (row counts, completeness)

## Quarantine

Records failing hard rules are quarantined with full context:
- Record data, rejection reason, rule violated, timestamp, batch ID, source, pipeline stage

## Details

*(To be documented during Phase 2 implementation)*
