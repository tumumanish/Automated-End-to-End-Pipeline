# BI Exports

This directory is populated by:

```powershell
python scripts/export_bi_data.py
```

Each run overwrites the CSV/JSON files with the current warehouse state. The
files are generated artifacts and are ignored by git; only this README and
`.gitkeep` are tracked.

| File | Description |
|------|-------------|
| `analytics_v_*.csv` | Curated analytical views |
| `monitoring_*.csv` | Pipeline, quality, and alert history |
| `metadata_lineage_events.csv` | Stage-by-stage lineage events |
| `kpi_summary.json` | Headline KPIs used by the HTML report |
| `manifest.json` | Generation time, backend, row counts, columns, errors |

Consume the CSVs in Power BI, Tableau, Excel, or a notebook. See
`../README.md`, `../powerbi/README.md`, and `../tableau/README.md` for binding
instructions.
