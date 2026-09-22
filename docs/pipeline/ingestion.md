# Ingestion Documentation

## Overview

The ingestion layer extracts data from multiple source types through a unified factory interface.

## Supported Sources

| Source     | Module              | Description                    |
|------------|---------------------|--------------------------------|
| REST API   | `api_ingestion.py`  | HTTP endpoint extraction       |
| CSV        | `csv_ingestion.py`  | CSV file reading               |
| Excel      | `excel_ingestion.py`| Excel workbook reading         |
| Database   | `database_ingestion.py` | SQL database extraction    |

## Factory Pattern

`ingestion_factory.py` provides a unified interface that selects the appropriate extraction strategy based on source configuration.

## Details

*(To be documented during Phase 2 implementation)*
