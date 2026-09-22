# Dashboard — Business Intelligence Layer

The BI layer provides interactive dashboards and visualizations consuming curated analytical datasets from the data warehouse semantic layer.

## Supported Tools

| Tool       | Directory   | Description                          |
|------------|-------------|--------------------------------------|
| Power BI   | `powerbi/`  | Interactive dashboards and reports   |
| Tableau    | `tableau/`  | Advanced analytics and visualizations|

## Important Principles

1. **Consume curated data only.** Dashboards should connect to analytical views and marts, never directly to raw or staging tables.
2. **Standardized KPIs.** All KPIs should be defined in the semantic layer and consumed consistently across tools.
3. **Refresh strategy.** Dashboards should follow scheduled refresh aligned with pipeline execution.
