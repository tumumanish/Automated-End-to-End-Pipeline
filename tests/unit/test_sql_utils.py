"""
Unit Tests: SQL Script Utilities

Verifies comment-aware statement splitting and SQLite DDL adaptation,
which previously caused setup_database.py to silently skip statements.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.storage.sql_utils import (
    adapt_sql_for_sqlite,
    split_sql_statements,
    strip_line_comments,
)


class TestCommentStripping:
    def test_strips_line_comments(self):
        sql = "-- header\nSELECT 1;\n  -- trailing\nSELECT 2;"
        assert strip_line_comments(sql).strip() == "SELECT 1;\n  \nSELECT 2;"

    def test_preserves_comment_markers_inside_strings(self):
        sql = "SELECT 'a--b' AS value; -- real comment"
        assert strip_line_comments(sql).strip() == "SELECT 'a--b' AS value;"


class TestStatementSplitting:
    def test_skips_comment_only_blocks(self):
        sql = """
        -- ============================================
        -- Create table
        -- ============================================
        CREATE TABLE IF NOT EXISTS raw.transactions (id INTEGER);

        -- Index
        CREATE INDEX IF NOT EXISTS idx ON raw.transactions (id);
        """
        statements = split_sql_statements(sql)
        assert len(statements) == 2
        assert statements[0].startswith("CREATE TABLE")
        assert statements[1].startswith("CREATE INDEX")

    def test_semicolon_inside_string_is_not_a_separator(self):
        sql = "INSERT INTO t (value) VALUES ('a;b'); SELECT 1;"
        statements = split_sql_statements(sql)
        assert len(statements) == 2
        assert "'a;b'" in statements[0]

    def test_escaped_quote_inside_string(self):
        sql = "INSERT INTO t (value) VALUES ('it''s; fine'); SELECT 1;"
        statements = split_sql_statements(sql)
        assert len(statements) == 2

    def test_trailing_statement_without_semicolon(self):
        statements = split_sql_statements("SELECT 1")
        assert statements == ["SELECT 1"]


class TestSqliteAdaptation:
    def test_drops_create_schema(self):
        assert adapt_sql_for_sqlite("CREATE SCHEMA IF NOT EXISTS raw;") == ""

    def test_adapts_types_and_defaults(self):
        stmt = (
            "CREATE TABLE IF NOT EXISTS warehouse.dim_date ("
            "id SERIAL PRIMARY KEY, "
            "created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), "
            "is_current BOOLEAN NOT NULL DEFAULT TRUE)"
        )
        adapted = adapt_sql_for_sqlite(stmt)
        assert "INTEGER PRIMARY KEY AUTOINCREMENT" in adapted
        assert "TIMESTAMP DEFAULT CURRENT_TIMESTAMP" in adapted
        assert "INTEGER NOT NULL DEFAULT 1" in adapted

    def test_view_body_uses_unqualified_tables(self):
        stmt = (
            "CREATE OR REPLACE VIEW analytics.v_daily_sales AS\n"
            "SELECT d.full_date, SUM(f.amount) AS total\n"
            "FROM warehouse.fact_transactions f\n"
            "JOIN warehouse.dim_date d ON f.date_key = d.date_key;"
        )
        adapted = adapt_sql_for_sqlite(stmt)
        assert adapted.startswith("CREATE VIEW IF NOT EXISTS analytics.v_daily_sales AS")
        assert "warehouse." not in adapted
        assert "FROM fact_transactions f" in adapted

    def test_references_are_unqualified(self):
        stmt = (
            "CREATE TABLE IF NOT EXISTS warehouse.fact_transactions ("
            "date_key INTEGER REFERENCES warehouse.dim_date(date_key))"
        )
        adapted = adapt_sql_for_sqlite(stmt)
        assert "REFERENCES dim_date" in adapted
        assert "REFERENCES warehouse." not in adapted
