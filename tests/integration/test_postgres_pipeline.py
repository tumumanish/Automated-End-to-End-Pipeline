"""
Integration Tests: PostgreSQL Pipeline

Tests that require a running PostgreSQL instance.
Tests will be SKIPPED (not falsely pass) when PostgreSQL is unavailable.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def _postgres_available() -> bool:
    """Check if PostgreSQL is reachable."""
    try:
        from src.storage.postgres.connection import test_connection
        return test_connection()
    except Exception:
        return False


# Skip entire module if DB is unavailable
pytestmark = pytest.mark.skipif(
    not _postgres_available(),
    reason="BLOCKED — PostgreSQL unavailable",
)


@pytest.fixture(scope="module")
def setup_schemas():
    """Run schema creation once for the test module."""
    from sqlalchemy import text
    from src.storage.postgres.connection import get_connection

    sql_dir = PROJECT_ROOT / "sql" / "postgres"
    for sql_file in ["01_create_schemas.sql", "02_create_raw_tables.sql"]:
        filepath = sql_dir / sql_file
        if filepath.exists():
            sql = filepath.read_text(encoding="utf-8")
            stmts = [s.strip() for s in sql.split(";") if s.strip() and not s.strip().startswith("--")]
            with get_connection() as conn:
                for stmt in stmts:
                    conn.execute(text(stmt))
    yield


@pytest.fixture
def sample_df():
    """Small DataFrame for loading tests."""
    return pd.DataFrame({
        "transaction_id": ["TEST-001", "TEST-002"],
        "customer_id": ["CUST-9999", "CUST-9998"],
        "product_id": ["PROD-001", "PROD-002"],
        "transaction_date": ["2024-06-01", "2024-06-02"],
        "quantity": [1, 3],
        "unit_price": [100.00, 200.00],
        "total_amount": [100.00, 600.00],
        "location": ["TestCity", "TestCity"],
        "source_system": ["test", "test"],
        "ingestion_batch_id": ["test_batch_001", "test_batch_001"],
    })


class TestPostgresConnection:
    """Tests for PostgreSQL connectivity."""

    def test_connection(self):
        """Database is reachable."""
        from src.storage.postgres.connection import test_connection
        assert test_connection() is True


class TestPostgresLoader:
    """Tests for PostgreSQL data loading."""

    def test_load_dataframe(self, setup_schemas, sample_df):
        """Loading a DataFrame into raw.transactions succeeds."""
        from src.storage.postgres.loader import load_dataframe
        count = load_dataframe(sample_df, table_name="transactions", schema="raw")
        assert count == 2

    def test_batch_lifecycle(self, setup_schemas):
        """Create → complete batch record lifecycle."""
        import uuid
        from src.storage.postgres.loader import (
            create_batch_record,
            complete_batch,
            insert_audit_event,
        )
        from src.storage.postgres.connection import get_connection
        from sqlalchemy import text

        bid = f"test_{uuid.uuid4().hex[:8]}"

        create_batch_record(bid, "csv", "test.csv", "transactions")

        # Verify RUNNING
        with get_connection() as conn:
            row = conn.execute(
                text("SELECT status FROM metadata.ingestion_batches WHERE batch_id = :bid"),
                {"bid": bid},
            ).fetchone()
        assert row is not None
        assert row[0] == "RUNNING"

        # Complete
        complete_batch(bid, record_count=10, file_path="/data/raw/test.csv")

        with get_connection() as conn:
            row = conn.execute(
                text("SELECT status, record_count FROM metadata.ingestion_batches WHERE batch_id = :bid"),
                {"bid": bid},
            ).fetchone()
        assert row[0] == "SUCCESS"
        assert row[1] == 10

    def test_audit_event(self, setup_schemas):
        """Audit events can be inserted and queried."""
        import uuid
        from src.storage.postgres.loader import (
            create_batch_record,
            insert_audit_event,
        )
        from src.storage.postgres.connection import get_connection
        from sqlalchemy import text

        bid = f"test_audit_{uuid.uuid4().hex[:8]}"
        create_batch_record(bid, "csv", "test.csv", "transactions")
        insert_audit_event(bid, "extract", "COMPLETED", "Test audit", record_count=5)

        with get_connection() as conn:
            row = conn.execute(
                text("SELECT stage, event_type, record_count FROM metadata.ingestion_audit WHERE batch_id = :bid"),
                {"bid": bid},
            ).fetchone()
        assert row is not None
        assert row[0] == "extract"
        assert row[1] == "COMPLETED"
        assert row[2] == 5
