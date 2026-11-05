"""
Unit Tests: SQL Query Builders

Covers the centralized Postgres/Snowflake query helpers used by the
storage and warehouse layers.
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.storage.postgres import queries as pg_queries
from src.storage.snowflake import queries as sf_queries
from src.storage.snowflake.connection import SnowflakeConfig


class TestPostgresQueries:
    def test_qualified_name(self):
        assert pg_queries.qualified_name("warehouse", "dim_date") == "warehouse.dim_date"

    def test_identifier_validation(self):
        with pytest.raises(ValueError):
            pg_queries.qualified_name("warehouse; DROP TABLE x", "dim_date")
        with pytest.raises(ValueError):
            pg_queries.validate_identifier("1_invalid")

    def test_insert_statement(self):
        sql = pg_queries.insert_statement(
            "raw", "transactions", ["transaction_id", "amount"]
        )
        assert sql == (
            "INSERT INTO raw.transactions (transaction_id, amount) "
            "VALUES (:transaction_id, :amount)"
        )

    def test_insert_on_conflict(self):
        sql = pg_queries.insert_statement(
            "raw", "transactions", ["id"], on_conflict_do_nothing=True
        )
        assert sql.endswith("ON CONFLICT DO NOTHING")

    def test_select_statement(self):
        sql = pg_queries.select_statement(
            "warehouse",
            "fact_transactions",
            ["transaction_key", "amount"],
            where="amount > 0",
            order_by="amount DESC",
            limit=10,
        )
        assert sql == (
            "SELECT transaction_key, amount FROM warehouse.fact_transactions "
            "WHERE amount > 0 ORDER BY amount DESC LIMIT 10"
        )

    def test_select_rejects_negative_limit(self):
        with pytest.raises(ValueError):
            pg_queries.select_statement("raw", "transactions", limit=-1)

    def test_count_and_truncate(self):
        assert pg_queries.count_statement("raw", "transactions") == (
            "SELECT COUNT(*) FROM raw.transactions"
        )
        assert pg_queries.truncate_statement("warehouse", "dim_date") == (
            "TRUNCATE TABLE warehouse.dim_date RESTART IDENTITY CASCADE"
        )

    def test_batch_templates_are_bound_parameterized(self):
        assert ":batch_id" in pg_queries.CREATE_BATCH
        assert ":record_count" in pg_queries.COMPLETE_BATCH
        assert ":error_message" in pg_queries.FAIL_BATCH
        assert ":stage" in pg_queries.INSERT_AUDIT_EVENT


class TestSnowflakeQueries:
    def test_qualified_name_and_select(self):
        assert sf_queries.qualified_name("ANALYTICS", "V_DAILY_SALES") == (
            "ANALYTICS.V_DAILY_SALES"
        )
        assert sf_queries.select_statement("ANALYTICS", "V_DAILY_SALES", limit=5) == (
            "SELECT * FROM ANALYTICS.V_DAILY_SALES LIMIT 5"
        )

    def test_count_and_truncate(self):
        assert sf_queries.count_statement("WAREHOUSE", "DIM_DATE") == (
            "SELECT COUNT(*) FROM WAREHOUSE.DIM_DATE"
        )
        assert sf_queries.truncate_statement("WAREHOUSE", "DIM_DATE") == (
            "TRUNCATE TABLE IF EXISTS WAREHOUSE.DIM_DATE"
        )

    def test_identifier_validation(self):
        with pytest.raises(ValueError):
            sf_queries.qualified_name("PUBLIC", "x; DROP TABLE y")


class TestSnowflakeConfig:
    def test_from_env(self, monkeypatch):
        monkeypatch.setenv("SNOWFLAKE_ACCOUNT", "acct")
        monkeypatch.setenv("SNOWFLAKE_USER", "user")
        monkeypatch.setenv("SNOWFLAKE_PASSWORD", "pass")
        monkeypatch.setenv("SNOWFLAKE_DATABASE", "DB")
        monkeypatch.setenv("SNOWFLAKE_SCHEMA", "RAW")
        monkeypatch.setenv("SNOWFLAKE_WAREHOUSE", "WH")
        monkeypatch.setenv("SNOWFLAKE_ROLE", "ROLE")

        cfg = SnowflakeConfig.from_env()
        assert cfg.is_configured
        kwargs = cfg.to_connect_kwargs()
        assert kwargs["account"] == "acct"
        assert kwargs["database"] == "DB"
        assert kwargs["schema"] == "RAW"
        assert kwargs["warehouse"] == "WH"
        assert kwargs["role"] == "ROLE"

    def test_unconfigured(self, monkeypatch):
        for key in ("SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD"):
            monkeypatch.delenv(key, raising=False)
        assert not SnowflakeConfig.from_env().is_configured
