"""
Package: storage
Handles database connections, data loading, versioning, and checkpoints
for PostgreSQL and Snowflake.

Subpackages:
    - postgres: PostgreSQL connection, loader, and queries
    - snowflake: Snowflake connection, loader, and queries

Modules:
    - raw_storage: Raw data zone management
    - versioning: Append-only versioned storage engine
    - checkpoint_manager: Pipeline checkpoint save/restore
"""
