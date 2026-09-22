# Monitoring Documentation

## Overview

The monitoring system tracks data quality and pipeline health across four major indicators.

## Quality Indicators

### 1. Freshness
- **Question:** How recent is the data?
- **Metric:** Time since last successful ingestion
- **Threshold:** Configurable (default: 24 hours)
- **Module:** `src/monitoring/freshness.py`

### 2. Completeness
- **Question:** Are all expected fields and records present?
- **Metric:** Percentage of non-null values per field; expected vs. actual row count
- **Threshold:** Configurable (default: 95%)
- **Module:** `src/monitoring/completeness.py`

### 3. Accuracy
- **Question:** Do values conform to expected ranges and formats?
- **Metric:** Percentage of records passing range and format checks
- **Threshold:** Configurable (default: 98%)
- **Module:** `src/monitoring/accuracy.py`

### 4. Contract Adherence
- **Question:** Does data satisfy registered contracts?
- **Metric:** Percentage of records passing all contract rules
- **Threshold:** Configurable (default: 99%)
- **Module:** `src/monitoring/contract_adherence.py`

## Pipeline Metrics

| Metric               | Description                              |
|-----------------------|------------------------------------------|
| Pipeline status       | Success / failure / partial              |
| Processing duration   | Total and per-stage timing               |
| Record counts         | Total, valid, invalid, quarantined       |
| Throughput            | Records processed per second             |

## Alerts

Alerts are triggered when quality thresholds are breached or pipeline failures occur.
- **Module:** `src/monitoring/alert_manager.py`
- **Severity levels:** Info, Warning, Critical

## Logs

Structured monitoring logs are written by `src/monitoring/monitoring_logger.py` to `logs/` directories.
