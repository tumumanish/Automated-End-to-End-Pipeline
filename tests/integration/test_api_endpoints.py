"""
Integration Tests: API Endpoints

Tests for the FastAPI REST API endpoints using TestClient.
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestPipelineEndpoints:
    """Tests for pipeline management endpoints."""

    def test_list_pipelines(self, client):
        response = client.get("/api/v1/pipelines")
        assert response.status_code == 200
        data = response.json()
        assert "pipelines" in data
        assert data["count"] >= 2  # At least etlt_plus_plus and eltl_plus_plus

    def test_get_pipeline(self, client):
        response = client.get("/api/v1/pipelines/etlt_plus_plus")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "etlt_plus_plus"
        assert data["class_name"] == "ETLTPlusPlusPipeline"

    def test_get_nonexistent_pipeline(self, client):
        response = client.get("/api/v1/pipelines/nonexistent")
        assert response.status_code == 404


class TestQualityEndpoints:
    """Tests for data quality endpoints."""

    def test_get_quality_metrics(self, client):
        response = client.get("/api/v1/quality/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        assert "count" in data

    def test_get_quarantine(self, client):
        response = client.get("/api/v1/quality/quarantine")
        assert response.status_code == 200
        data = response.json()
        assert "entries" in data


class TestLineageEndpoints:
    """Tests for lineage endpoints."""

    def test_list_batches(self, client):
        response = client.get("/api/v1/lineage/batches")
        assert response.status_code == 200
        data = response.json()
        assert "batches" in data

    def test_get_nonexistent_batch_lineage(self, client):
        response = client.get("/api/v1/lineage/batch/no_such_batch")
        assert response.status_code == 404


class TestSampleDataEndpoint:
    """Tests for the sample data endpoint."""

    def test_get_sample_transactions(self, client):
        response = client.get("/api/v1/sample/transactions?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert data["record_count"] == 5
        assert len(data["records"]) == 5


class TestBIEndpoints:
    """Tests for the generated BI deliverables."""

    def test_export_manifest(self, client):
        response = client.get("/api/v1/bi/exports")
        assert response.status_code == 200
        data = response.json()
        assert "datasets" in data
        assert "count" in data

    def test_report_metadata(self, client):
        response = client.get("/api/v1/bi/report")
        assert response.status_code == 200
        data = response.json()
        assert "available" in data
        assert data["url"] == "/reports/project-outcome"

    def test_outcome_report_route(self, client):
        response = client.get("/reports/project-outcome")
        # The report is a generated artifact; accept 404 on a fresh checkout.
        assert response.status_code in (200, 404)
        if response.status_code == 200:
            assert "Project Outcome Report" in response.text
