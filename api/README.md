# API — Pipeline Monitoring Interface

This directory contains a lightweight REST API for pipeline monitoring and metadata access.

## Endpoints (To Be Implemented)

| Method | Endpoint                    | Description                    |
|--------|-----------------------------|--------------------------------|
| GET    | `/health`                   | Health check                   |
| GET    | `/pipelines`                | List all pipelines and status  |
| GET    | `/pipelines/{pipeline_id}`  | Get specific pipeline details  |
| GET    | `/data-quality`             | Data quality metrics           |
| GET    | `/lineage`                  | Data lineage information       |

## Technology

- **Framework:** FastAPI
- **Server:** Uvicorn

## Running

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## Notes

This API is intended for **pipeline monitoring and metadata access**, not as a replacement for Power BI or Tableau dashboards.
