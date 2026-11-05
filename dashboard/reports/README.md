# Project Outcome Report

This directory is populated by:

```powershell
python scripts/generate_project_report.py --open
```

The script writes `project_outcome.html`, a self-contained report with inline
CSS and SVG charts. It needs no network connection and can be opened directly
from disk, served by FastAPI at `/reports/project-outcome`, or printed to PDF
from the browser.

## Sections

1. Executive summary and KPI cards
2. Daily and monthly revenue trends
3. Product performance
4. Regional performance
5. Customer segments and top customers
6. Data quality and pipeline health
7. Warehouse and lineage flow
8. BI deliverables and downloads
9. Reproduction process
10. Conclusions, scope, and limitations

The report is generated from `../exports/` and is ignored by git.
