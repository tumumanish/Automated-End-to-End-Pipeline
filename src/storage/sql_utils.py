"""
Module: sql_utils
Purpose:
    Shared helpers for executing SQL scripts across PostgreSQL and the
    local SQLite fallback warehouse.

The SQL scripts in ``sql/postgres`` contain line comments and semicolons
inside string literals, so a naive ``sql.split(";")`` skips statements or
produces broken fragments. These helpers split scripts safely and adapt
PostgreSQL DDL to SQLite where needed.
"""

from __future__ import annotations

import re

_SCHEMAS = ("raw", "staging", "warehouse", "analytics", "metadata", "monitoring")
_CREATE_VIEW_RE = re.compile(r"^\s*CREATE\s+(?:OR\s+REPLACE\s+)?VIEW\s", re.IGNORECASE)


def strip_line_comments(sql: str) -> str:
    """
    Remove ``--`` line comments without touching comment markers inside
    single- or double-quoted literals.
    """
    cleaned_lines = []
    for line in sql.splitlines():
        in_single = False
        in_double = False
        cut = len(line)
        i = 0
        while i < len(line):
            ch = line[i]
            if ch == "'" and not in_double:
                # SQL escapes a quote by doubling it.
                if in_single and i + 1 < len(line) and line[i + 1] == "'":
                    i += 2
                    continue
                in_single = not in_single
            elif ch == '"' and not in_single:
                in_double = not in_double
            elif (
                ch == "-"
                and not in_single
                and not in_double
                and i + 1 < len(line)
                and line[i + 1] == "-"
            ):
                cut = i
                break
            i += 1
        cleaned_lines.append(line[:cut])
    return "\n".join(cleaned_lines)


def split_sql_statements(sql: str) -> list[str]:
    """
    Split a SQL script into individual statements.

    Handles line comments and semicolons inside string literals. Empty
    statements are discarded.
    """
    sql = strip_line_comments(sql)
    statements: list[str] = []
    buffer: list[str] = []
    in_single = False
    in_double = False

    i = 0
    while i < len(sql):
        ch = sql[i]
        if ch == "'" and not in_double:
            if in_single and i + 1 < len(sql) and sql[i + 1] == "'":
                buffer.append("''")
                i += 2
                continue
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double

        if ch == ";" and not in_single and not in_double:
            stmt = "".join(buffer).strip()
            if stmt:
                statements.append(stmt)
            buffer = []
        else:
            buffer.append(ch)
        i += 1

    tail = "".join(buffer).strip()
    if tail:
        statements.append(tail)
    return statements


def adapt_sql_for_sqlite(stmt: str) -> str:
    """
    Adapt a PostgreSQL DDL statement for the SQLite fallback warehouse.

    SQLite supports attached databases but does not allow views to reference
    tables in another attached database. Because the fallback attaches every
    logical schema to the same file, view bodies are rewritten with
    unqualified table names, which resolve against that shared file.
    """
    s = stmt.strip()
    if s.upper().startswith("CREATE SCHEMA"):
        return ""

    if _CREATE_VIEW_RE.match(s):
        head, sep, body = s.partition(" AS ")
        if sep:
            for schema in _SCHEMAS:
                body = body.replace(f"{schema}.", "")
            s = head + sep + body
        s = re.sub(
            r"^\s*CREATE\s+OR\s+REPLACE\s+VIEW",
            "CREATE VIEW IF NOT EXISTS",
            s,
            flags=re.IGNORECASE,
        )
        return s

    # Types and defaults
    s = s.replace("SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
    s = s.replace("DEFAULT NOW()", "DEFAULT CURRENT_TIMESTAMP")
    s = s.replace("DEFAULT now()", "DEFAULT CURRENT_TIMESTAMP")
    s = s.replace("TIMESTAMP WITH TIME ZONE DEFAULT NOW()", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    s = s.replace("TIMESTAMP WITH TIME ZONE", "TIMESTAMP")
    s = s.replace("BOOLEAN NOT NULL DEFAULT FALSE", "INTEGER NOT NULL DEFAULT 0")
    s = s.replace("BOOLEAN NOT NULL DEFAULT TRUE", "INTEGER NOT NULL DEFAULT 1")
    s = s.replace("BOOLEAN DEFAULT TRUE", "INTEGER DEFAULT 1")
    s = s.replace("BOOLEAN DEFAULT FALSE", "INTEGER DEFAULT 0")
    s = s.replace("::jsonb", "")
    s = s.replace("JSONB", "TEXT")
    s = s.replace("WHERE is_current = TRUE", "WHERE is_current = 1")
    s = s.replace("NUMERIC(15, 2)", "REAL")
    s = s.replace("NUMERIC(10, 2)", "REAL")
    s = s.replace("NUMERIC(5, 2)", "REAL")
    s = s.replace("RESTART IDENTITY CASCADE", "")
    for schema in _SCHEMAS:
        s = s.replace(f"REFERENCES {schema}.", "REFERENCES ")
    return s
